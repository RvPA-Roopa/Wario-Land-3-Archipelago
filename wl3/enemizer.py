"""WL3 enemizer — runs at AP generation time, returns ROM patch writes.

Mirrors tools/enemize.py but reads pre-baked metadata (room offsets,
group structs, palette bytes) from enemizer_data.py instead of parsing
the .sym / .asm files. Same protection logic (walkable enemies, gates,
platforms preserved at vanilla positions; ~1781 rooms randomized).

Public API:
    generate_patch_writes(rng) -> list[(offset, bytes)]
"""
from collections import OrderedDict
from typing import Any

from . import enemizer_data
from .enemy_registry import (SLOT_0_PACKAGES, SLOT_1_PACKAGES,
                             SLOT_2_PACKAGES, SLOT_3_PACKAGES)

# All protection / categorization is precomputed by
# tools/build_apworld_enemizer_data.py and dumped into enemizer_data.
# This module only needs slot composition + signature dedup + room
# patching logic — no category_of / label lookups at runtime.


# ---------------------------------------------------------------------------
# Constants — must match tools/enemize.py + src/constants/object_constants.asm
# ---------------------------------------------------------------------------
ENEMIZER_GROUP_ID_BASE = 0x92
SLOT_SIZE              = 64
NUM_TOTAL_SLOTS        = 82
TABLE_SIZE             = SLOT_SIZE * NUM_TOTAL_SLOTS

# Option B partition — each color's 21/20 slot bucket dispatches through
# CommonObjects_<Color> so chest/key sprites keep their vanilla color
# after enemy_group remap. Per-bucket layout: most slots "any-random",
# 3 throwable-forced slots (one each for VRAM slots 0/1/2 — vanilla has
# no slot-3 throwables) so throw-block rooms in any color can still
# reach a throwable. Must match src/constants/object_constants.asm.
ENEMIZER_BUCKET_COUNTS = [21, 21, 20, 20]   # [Grey, Red, Green, Blue]
assert sum(ENEMIZER_BUCKET_COUNTS) == NUM_TOTAL_SLOTS
ENEMIZER_BUCKET_BASES = [0,
                         ENEMIZER_BUCKET_COUNTS[0],
                         ENEMIZER_BUCKET_COUNTS[0] + ENEMIZER_BUCKET_COUNTS[1],
                         ENEMIZER_BUCKET_COUNTS[0] + ENEMIZER_BUCKET_COUNTS[1] + ENEMIZER_BUCKET_COUNTS[2]]
THROWABLE_VRAM_SLOTS_PER_BUCKET = (0, 1, 2, 3)   # one throwable slot per bucket per VRAM slot (slot 3 added 2026-07-18 when Barrel joined slot-3 throwables — needed for auto-tb rooms with no sig, e.g. wgid 0x49 Big Bridge)

DUMMY_OBJECT_DATA_ADDR = 0x43c3

# Walkable data labels (enemies that double as stepping stones).
WALKABLE_DATA_LABELS = {
    "FutamoguData", "SmallLeafData", "WebberData", "SnakeData",
    "Dragonfly2Data", "StoveData",
}

# Paired-enemy constraint (Sun1/Sun2 etc. share data, must always be picked
# together with the "1" in slot 0 and the "2" in slot 1).
PAIRED_GFX = {
    "Sun1Gfx":       "Sun2Gfx",
    "Moon1Gfx":      "Moon2Gfx",
    "RoboMouse1Gfx": "RoboMouse2Gfx",
}
PAIRED_GFX_REVERSE = {v: k for k, v in PAIRED_GFX.items()}

# Throwable Gfx labels per VRAM slot. Throw-block rooms need at least one
# of these in the slot their vanilla throwable used to occupy.
THROWABLE_GFX_BY_SLOT: dict[int, set[str]] = {
    0: {"SilkyGfx", "SpearheadGfx"},
    1: {"ParaGoomGfx"},
    2: {"DoughnuteerGfx", "SpearBotGfx"},
    3: {"BeamBotGfx", "FireBotGfx"},
    # Rock@2 and Barrel@3 intentionally excluded from the roll-in pool.
    # Rooms whose vanilla layout HAS them still require a throwable in
    # that slot via AUTO_TB_BY_VANILLA_GFX — the enemizer just picks a
    # different throwable (Doughnuteer/SpearBot for slot 2, BeamBot/FireBot
    # for slot 3).
}

# Electric/STING-damage enemies (Wario becomes Zombie form on touch).
# These may be interchangeable in spike rooms since wl3 seems to use
# the same tile-referencing pattern for all of them. Keyed by NATIVE
# VRAM slot for the enemy's gfx label placement.
ELECTRIC_GFX_BY_SLOT: dict[int, set[str]] = {
    0: set(),                              # (no slot-0-native electric enemies)
    1: {"KushimushiGfx"},                   # confirmed working in ToR
    2: set(),                              # (no slot-2-native electric enemies)
    3: {"SparkGfx"},                        # native vanilla — confirmed working
    # Untested and REMOVED per user 2026-07-18 (keeping the pool minimal):
    #   - BirdGfx (crashed ToR)
    #   - TogebaGfx (untested; user chose safety)
}

# Extra spike-family enemy pkgs NOT in the general SLOT_N_PACKAGES
# registry (excluded there because they're "hazard" category, on
# POOL_EXCLUDE_GFX, or have data-label ownership quirks). Only
# consumed by electric_pool() — never by random_pool() — so they
# stay out of regular random rooms. Confirmed working:
#   - KushimushiGfx (already in main registry; cross-slot to slot 3)
# Untested but eligible for electric_pool:
#   - SparkGfx (native slot 3)
#   - TogebaGfx (native slot 3, POOL_EXCLUDE_GFX in general pool)
#   - BirdGfx (native slot 1)
SPIKE_EXTRA_PKGS: dict[int, dict[str, dict]] = {
    3: {
        "SparkGfx": {"gfx_addr": 0x6398,
                     "data_addrs": [0x473c, 0x4744],
                     "palette_offset": 0x066729},
    },
}


# All protection decisions live in enemizer_data.OBJECT_GROUPS as
# precomputed `prot_per_slot` / `has_walkable_gfx` flags — no need for
# category lookups at runtime. (Build script: tools/build_apworld_enemizer_data.py
# reuses tools/enemize.py's slot_is_protected/group_has_walkable_or_platform_gfx
# so the apworld and standalone tool produce identical patches for the same seed.)


# ---------------------------------------------------------------------------
# Slot composition
# ---------------------------------------------------------------------------
SLOT_PACKAGES = {
    0: SLOT_0_PACKAGES, 1: SLOT_1_PACKAGES,
    2: SLOT_2_PACKAGES, 3: SLOT_3_PACKAGES,
}


def _encode_data_ptr(addr: int, target_slot: int, native_slot: int) -> int:
    """Encode a data_ptr for the engine's spawn-time bit extraction.

    Vanilla (native == target): return addr unchanged → engine reads
    bit 7 == 0, takes vanilla path, tile_offset = 0.

    Cross-slot (native != target): bit 15 set, bits 13-14 hold
    (target - native) mod 4 as tile_offset_index, bits 0-12 hold
    (addr - $4000). Engine extracts tile_offset = index × $40 and
    applies it to every OAM tile_id with mod-256 wrap so a slot-0
    enemy placed in VRAM 1 renders with the right tiles."""
    if native_slot == target_slot:
        return addr
    offset_idx = (target_slot - native_slot) & 3
    rel = (addr - 0x4000) & 0x1FFF
    return rel | (offset_idx << 13) | 0x8000


def _encode_gfx_ptr(addr: int, target_slot: int, native_slot: int) -> int:
    """Encode a gfx_ptr — mirror of _encode_data_ptr's layout but the
    bits 13-14 hold the SOURCE slot (so the engine's DecodeGfxSlot
    picks the right "Enemy Gfx 1 Slot N" bank to decompress from).

    Vanilla (native == target): return addr unchanged → engine reads
    from BANK("Enemy Gfx 1 Slot {target+1}") as today."""
    if native_slot == target_slot:
        return addr
    rel = (addr - 0x4000) & 0x1FFF
    return rel | (native_slot << 13) | 0x8000


def _pick_random_per_slot(rng, fixed_slots: dict[int, dict],
                          force_throwable_slot: int | None = None,
                          force_throwable_slots: frozenset[int] | None = None,
                          force_electric_slot: int | None = None,
                          avoid_vanilla_gfx_addrs: tuple | None = None
                          ) -> tuple[list[dict], list[int]]:
    """Pick an enemy package per VRAM slot — native-only (no cross-slot).

    fixed_slots maps slot_idx -> a package dict (from a sig's protected
    slot); those slots are returned as-is.

    force_throwable_slot: if VRAM slot i needs a throwable (for a
    throw-block room), it's constrained to a throwable from
    THROWABLE_GFX_BY_SLOT[i].

    avoid_vanilla_gfx_addrs[i] is the vanilla room's gfx_addr for VRAM
    slot i; when provided, slot i's random pool excludes packages with
    that gfx_addr (falls back to full pool if non-vanilla pool < 2)."""
    chosen: list[Any] = [None, None, None, None]
    native_slots: list[int] = [0, 1, 2, 3]
    for i in range(4):
        chosen[i] = fixed_slots.get(i)

    # Cross-slot encoding limit: the engine's encoded data_ptr / gfx_ptr
    # format (see load_objects.asm:222-246 and DecodeGfxSlot) packs the
    # address into 13 bits — bits 13-14 hold the tile_offset_index /
    # native_slot, so the decoder rebuilds the address as
    # ((encoded & $1FFF) | $4000), which silently truncates any source
    # address in $6000-$7FFF down to $4000-$5FFF. Enemies whose gfx
    # lives above $5FFF (FireGfx, OctohonGfx, SparkGfx, WaterSparkGfx,
    # etc. — 12 in total) therefore CANNOT be cross-slotted; they have
    # to be picked in their native slot only. Picking them native is
    # fine because the encoder returns the vanilla address unchanged
    # when native_slot == target_slot.
    CROSS_SLOT_GFX_MAX = 0x5FFF

    def _can_cross_slot(native: int, name: str) -> bool:
        return SLOT_PACKAGES[native][name]["gfx_addr"] <= CROSS_SLOT_GFX_MAX

    def random_pool(slot_idx: int) -> list[tuple[int, str]]:
        """Cross-slot pool: UNION of enemies from all 4 native slots.
        Engine support for the tile-id offset is in place — see
        load_objects.asm + object_mechanics.asm. Enemies whose gfx are
        above CROSS_SLOT_GFX_MAX are limited to their own native slot
        (encoding truncates the address otherwise).
        """
        candidates: list[tuple[int, str]] = []
        for native in range(4):
            for name in sorted(SLOT_PACKAGES[native].keys()):
                if native != slot_idx and not _can_cross_slot(native, name):
                    continue
                candidates.append((native, name))
        if avoid_vanilla_gfx_addrs is not None:
            vanilla = avoid_vanilla_gfx_addrs[slot_idx]
            if vanilla is not None:
                non_match = [(ns, n) for ns, n in candidates
                             if SLOT_PACKAGES[ns][n]["gfx_addr"] != vanilla]
                if len(non_match) >= 2:
                    candidates = non_match
        return candidates

    def throwable_pool(slot_idx: int) -> list[tuple[int, str]]:
        """Cross-slot throwable pool — UNION of throwables from all
        non-target native slots. Throw-block rooms typically have a
        slot-N-native throwable in VRAM slot N (e.g. Spearhead/Silky in
        VRAM 0); excluding the target's native throwables guarantees the
        post-randomization throwable is visibly different from vanilla.
        Throwables with high-address gfx (RockGfx) are also restricted
        to their native slot due to the encoding limit.
        Falls back to including target-native if pool would otherwise be
        empty.
        """
        candidates: list[tuple[int, str]] = []
        for native, throw_names in THROWABLE_GFX_BY_SLOT.items():
            if native == slot_idx:
                continue
            for name in sorted(throw_names):
                if name in SLOT_PACKAGES[native] and _can_cross_slot(native, name):
                    candidates.append((native, name))
        if not candidates:
            for name in sorted(THROWABLE_GFX_BY_SLOT.get(slot_idx, set())):
                if name in SLOT_PACKAGES[slot_idx]:
                    candidates.append((slot_idx, name))
        if avoid_vanilla_gfx_addrs is not None:
            vanilla = avoid_vanilla_gfx_addrs[slot_idx]
            if vanilla is not None:
                non_match = [(ns, n) for ns, n in candidates
                             if SLOT_PACKAGES[ns][n]["gfx_addr"] != vanilla]
                if len(non_match) >= 2:
                    candidates = non_match
        return candidates

    def _resolve_pkg(native: int, name: str):
        """Return the pkg dict for name at native slot, consulting the
        main registry first then falling back to SPIKE_EXTRA_PKGS."""
        pkg = SLOT_PACKAGES[native].get(name)
        if pkg is not None:
            return pkg
        return SPIKE_EXTRA_PKGS.get(native, {}).get(name)

    def _has_pkg(native: int, name: str) -> bool:
        return (name in SLOT_PACKAGES[native]
                or name in SPIKE_EXTRA_PKGS.get(native, {}))

    def _pkg_gfx_addr(native: int, name: str) -> int:
        pkg = _resolve_pkg(native, name)
        return pkg["gfx_addr"] if pkg else 0

    def _can_cross_slot_any(native: int, name: str) -> bool:
        return _pkg_gfx_addr(native, name) <= CROSS_SLOT_GFX_MAX

    def electric_pool(slot_idx: int) -> list[tuple[int, str]]:
        """Cross-slot electric-STING pool for spike rooms. Analog of
        throwable_pool but pulls from ELECTRIC_GFX_BY_SLOT. Includes
        target-native picks (Spark at target 3 stays native)."""
        candidates: list[tuple[int, str]] = []
        for native, elec_names in ELECTRIC_GFX_BY_SLOT.items():
            for name in sorted(elec_names):
                if not _has_pkg(native, name):
                    continue
                if native != slot_idx and not _can_cross_slot_any(native, name):
                    continue
                candidates.append((native, name))
        return candidates

    _multi_tb = force_throwable_slots or frozenset()

    def _is_throwable_slot(slot_idx: int) -> bool:
        return slot_idx == force_throwable_slot or slot_idx in _multi_tb

    def pick_for(slot_idx: int) -> list[tuple[int, str]]:
        """Select the correct pool for slot_idx based on force_* flags."""
        if force_electric_slot == slot_idx:
            return electric_pool(slot_idx)
        if _is_throwable_slot(slot_idx):
            return throwable_pool(slot_idx)
        return random_pool(slot_idx)

    # All slot picks now go through cross-slot pools (random_pool for
    # generic picks, throwable_pool for tb_slot constraints,
    # electric_pool for spike-room slots). PAIRED_GFX filtering is
    # preserved in case Sun/Moon ever return to the registry.
    # Slot 0
    if chosen[0] is None:
        pool = pick_for(0)
        if not _is_throwable_slot(0) and force_electric_slot != 0 \
                and chosen[1] is not None:
            pool = [(ns, n) for ns, n in pool if n not in PAIRED_GFX]
        native_slots[0], name0 = rng.choice(pool)
        chosen[0] = _resolve_pkg(native_slots[0], name0)
        name0_key = name0
    else:
        name0_key = None

    # Slot 1
    if chosen[1] is None:
        if _is_throwable_slot(1) or force_electric_slot == 1:
            pool = pick_for(1)
        elif name0_key in PAIRED_GFX:
            chosen[1] = SLOT_PACKAGES[1][PAIRED_GFX[name0_key]]
            pool = None
        else:
            pool = [(ns, n) for ns, n in random_pool(1) if n not in PAIRED_GFX_REVERSE]
        if pool is not None:
            native_slots[1], name1 = rng.choice(pool)
            chosen[1] = _resolve_pkg(native_slots[1], name1)

    # Slots 2 and 3
    for i in (2, 3):
        if chosen[i] is None:
            pool = pick_for(i)
            native_slots[i], name = rng.choice(pool)
            chosen[i] = _resolve_pkg(native_slots[i], name)
    return chosen, native_slots


def _emit_slot_bytes(chosen: list[dict],
                     target_data_counts: list[int],
                     palette_lookup,
                     native_slots: list[int] | None = None) -> bytes:
    if native_slots is None:
        native_slots = [0, 1, 2, 3]
    out = bytearray()
    out.append(0x00)  # bank_offset
    # 4 gfx ptrs — routed through _encode_gfx_ptr. For native picks
    # (native_slots[i] == i) returns the addr unchanged so the byte
    # sequence matches the pre-step-3 build exactly.
    for i, pkg in enumerate(chosen):
        addr = pkg["gfx_addr"]
        enc = _encode_gfx_ptr(addr, target_slot=i, native_slot=native_slots[i])
        out.append(enc & 0xff)
        out.append((enc >> 8) & 0xff)
    # Data ptrs per slot, padded — routed through _encode_data_ptr.
    # Native picks → vanilla addr unchanged.
    for i, pkg in enumerate(chosen):
        target = target_data_counts[i]
        ptrs = list(pkg["data_addrs"])
        if len(ptrs) > target:
            ptrs = ptrs[:target]
        while len(ptrs) < target:
            ptrs.append(DUMMY_OBJECT_DATA_ADDR)
        native = native_slots[i]
        for addr in ptrs:
            enc = _encode_data_ptr(addr, target_slot=i, native_slot=native)
            out.append(enc & 0xff)
            out.append((enc >> 8) & 0xff)
    # NULL terminator
    out.extend(b"\xff\xff")
    # Palettes (4 × 8 bytes). No vanilla palette bytes ship with the
    # apworld — `palette_lookup(offset)` returns 8 bytes from the ROM
    # at patch-apply time (it's wired to read either vanilla snapshot
    # bytes or palette-shuffle-recolored bytes, depending on whether
    # enemy_palette_shuffle is enabled).
    for pkg in chosen:
        src_off = pkg.get("palette_offset")
        if src_off:
            out.extend(palette_lookup(src_off))
        else:
            out.extend(b"\x00" * 8)
    while len(out) < SLOT_SIZE:
        out.append(0x00)
    assert len(out) == SLOT_SIZE
    return bytes(out)


# ObjectGroups confirmed to crash when enemizer changes their gfx
# footprint. Reproduced 2026-07-06 for OG6 (Bank of the Wild River
# Kushimushi rooms) by composing a vanilla-identical custom slot and
# verifying the room loads normally — proving the crash is contents-
# dependent, not byte-lookup dependent. OG88 (Warped Void ladder) and
# OG96 (Tower of Revival climb-up) were confirmed via prior in-game
# testing (see feedback_spearhead_futamogu_crash_pattern.md).
#
# All three share the [SpearheadGfx@slot0, X, FutamoguGfx@slot2, Y]
# structural signature — the "$4000 in slot 0 AND $4000 in slot 2"
# pattern matches 21 total ObjectGroups, but only these 3 have
# reproduced crashes in-game. The other 18 pattern-matches are treated
# as "unconfirmed" and allowed to randomize; if new crash reports come
# in for one of them, add its gid here.
#
# Root mechanism: not fully understood, static analysis exhausted.
# Likely: BG block tiles in these rooms reference specific enemy-VRAM
# tile IDs whose contents depend on the exact gfx decompression
# footprint (compressed size, tile ID layout). A live emulator session
# with breakpoints at the crash PC + VRAM/wRoomBlockTiles diffs would
# pin down the exact reference, but that requires driving BizHawk.
# 2026-07-18: cleared to test if the leading-Dummy fix
# (tools/enemize.py:257-273) resolved these crashes.
#   Confirmed fixed: gid 34 (Castle of Illusions), gid 88 (Warped
#     Void ladder). Removed from the set — they now randomize safely.
#   Still crashing: 6, 96, 101, 104, 105. These rooms depend on
#     specific enemy VRAM tile contents (BG block tiles / object
#     logic hardcoded to vanilla gfx footprint), not just data-ptr
#     positions — Dummy fix doesn't help them.
#   Untested: gid 30 (Volcano's Base), gid 116 (Beneath the Waves)
#     — kept protected until walked.
# 2026-07-18: decoration-slot theory recovered all 6 formerly-confirmed
# crashers. gid 96 (Tower of Revival) uses per-slot electric-pool at
# slot 3 instead. gid 30 (Volcano's Base Nobiiru room) added here after
# user retest confirmed the {0} decoration-slot lock alone wasn't
# enough — full vanilla required.
CRASH_CONFIRMED_GIDS = frozenset({30})
# gid 101 (Above the Clouds day room_00 = wgid 0x7d): same
# [Spearhead@0, Bird@1, Futamogu@2 protected, Spark@3] layout as the
# other confirmed crashers. Reproduced 2026-07-15: entering ATC on a
# new seed crashes on the first room load. Vanilla-identical
# composition via _emit_vanilla_identical_slot keeps the room stable.
# gid 34 (Castle of Illusions rooms 0x39/0x86 = wgid 0x32): same
# [Spearhead@0, ParaGoom@1, Futamogu@2 protected, Togeba@3] pattern.
# Crashed with slot 0/1/3 cross-slotted to Kobatto/Mizuuo/Kobatto —
# fits the [Spearhead + Futamogu@2 protected] signature.
# gid 30, 104, 105, 116: same [Spearhead + Futamogu@2 protected]
# signature, added preemptively 2026-07-17 after the gid 34 crash
# confirmed the pattern is a reliable predictor. Levels covered:
#   gid  30 (wgid 0x3B): The Volcano's Base — Spearhead/ParaGoom/Futamogu/Nobiiru
#   gid 104 (wgid 0x80): Above the Clouds — Spearhead/Bird/Futamogu/Barrel
#                         (barrel is throwable in vanilla so throw-block puzzle
#                          in wRoom 0x76/0x8A still works with whole-vanilla)
#   gid 105 (wgid 0x83): Above the Clouds — Spearhead/Webber/Futamogu/BeamBot
#   gid 116 (wgid 0x8E): Beneath the Waves — Spearhead/Webber/Futamogu/Teruteru

# Per-slot protection overrides — for gids where whole-group vanilla is
# more restrictive than needed. Marks specific VRAM slots as "protected"
# for the given gid so the sig treats them as vanilla (locked) while
# other slots still randomize normally.
#
# gid 59 (The Grasslands room 0x58 = wgid 0x48): only Nobiiru at slot 3
# causes the crash on approach. Bird@1 and Hebarii@2 can still be
# randomized — locking just slot 3 preserves the crash-critical enemy
# while keeping variety in the other two slots.
SLOT_LOCKED_GIDS: dict = {
    59: {3},        # gid 59 Grasslands: lock Nobiiru@3 (crash confirmed
                    # still present after leading-Dummy fix — retested
                    # 2026-07-18, tile-content dependency like the
                    # CRASH_CONFIRMED_GIDS pattern)
    # gid 30 moved to CRASH_CONFIRMED_GIDS 2026-07-18 — {0} decoration-
    # slot lock alone still crashed on user retest. Whole vanilla now.
    # gid 77 (FallingSnow rooms) reverted to FORCE_VANILLA_WGIDS
    # 2026-07-18 — every per-slot recovery attempt crashed.
    42: {2},        # gid 42 Tower of Revival torch room (wgid 0x25/0x26):
                    # FlameBlock@2 must stay vanilla (the actual puzzle
                    # mechanic). Stove@0 already protected (walkable).
                    # ParaGoom@1 and Torch@3 randomize freely.
    # Formerly-CRASH_CONFIRMED_GIDS moved to per-slot locking based on
    # decoration-vs-spawn analysis 2026-07-18. Every one of these gids
    # has Spearhead@0 + Futamogu@2 as DECORATION-ONLY (gfx tiles loaded
    # but nothing spawns from those slots) — the room's BG block_map
    # references those tile bytes for scenery. Locking the decoration
    # slots keeps the block_map's tile references valid; other slots
    # (which actually spawn enemies) can randomize freely.
     6: {0, 1, 3},  # BotWR / OoTW / Tidal: lock all non-Futamogu slots.
                    # CONFIRMED 2026-07-18: BotWR spikes borrow
                    # Kushimushi's tile range (same "shared electric
                    # damage" mechanic as ToR / Spark → spikes). With
                    # slot 1 unlocked, BotWR crashes; with it locked
                    # the room is effectively whole-vanilla.
    96: {0},        # Tower of Revival: lock Spearhead@0 (deco). Slot 3
                    # (Spark spawn) is forced to pick from
                    # ELECTRIC_GFX_BY_SLOT via SPIKE_ELECTRIC_SLOT_BY_GID
                    # so wall spikes' tile references still land on
                    # electric-family tiles. Spark, Kushimushi, Togeba,
                    # BlueBird all eligible.
   101: {0},        # Above The Clouds: Bird@1 + Spark@3 spawn; 0/2 deco
   104: {0},        # Above The Clouds: Bird@1 + Barrel@3 spawn; 0/2 deco
   105: {0, 1},     # Above The Clouds: BeamBot@3 spawn; 0/1/2 deco
   116: {0, 1},     # Beneath The Waves: Teruteru@3 spawn; 0/1/2 deco
    # (Slot 2 is already sig-protected in each — Futamogu categorized
    # as walkable — so we only need to add whichever additional
    # decoration slots aren't already covered.)
    # Omodon slot-2 locks (gids 4, 5, 37, 83, 89) removed 2026-07-18 —
    # user opted to let Omodon/Omodonmeka randomize like any enemy;
    # rules.py adds Flat Form requirements to affected checks.
}


# Current-ROM DummyObjectData address. The module-level
# DUMMY_OBJECT_DATA_ADDR (line ~46) is 0x43c3, which was correct in an
# earlier build but is now stale (sym file: 19:441c DummyObjectData).
# We use the correct address here to reconstruct byte-identical vanilla
# groups. If the padding path (`_emit_slot_bytes` line 276) starts
# spawning phantom enemies from 0x43c3, the module-level constant also
# needs updating — but keeping this local avoids changing that behavior.
_VANILLA_DUMMY_OBJECT_DATA_ADDR = 0x441c


def _emit_vanilla_identical_slot(rec: dict, palette_lookup) -> bytes:
    """Emit a custom slot whose byte layout mirrors the vanilla ObjectGroup
    exactly — same gfx_addrs, same data ptrs (flat), same palette offsets.

    Reconstructs the flat data-ptr list from data_slot_addrs. The build
    script that populates data_slot_addrs (build_apworld_enemizer_data →
    enemize.finalize) DROPS leading DummyObjectData entries that appear
    BEFORE any real slot data — see the "if last_slot is not None"
    branch in enemize.py's finalize. Every vanilla ObjectGroup in the
    [dummy, X, dummy, Y] pattern has exactly one leading DummyObjectData
    (verified for OG6, OG88, OG96 by direct ROM inspection), so prepend
    that entry to reconstruct the vanilla byte layout.
    """
    out = bytearray()
    out.append(0x00)  # bank_offset
    # 4 gfx ptrs — no encoding (native slot == target slot for identity).
    for addr in rec["gfx_addrs"]:
        out.append(addr & 0xff)
        out.append((addr >> 8) & 0xff)
    # Data ptrs — reconstruct the flat vanilla order.
    # Vanilla layout is [leading_dummy] + slot_data_addrs[0..3] concatenated.
    out.append(_VANILLA_DUMMY_OBJECT_DATA_ADDR & 0xff)
    out.append((_VANILLA_DUMMY_OBJECT_DATA_ADDR >> 8) & 0xff)
    for i in range(4):
        for addr in rec["data_slot_addrs"][i]:
            out.append(addr & 0xff)
            out.append((addr >> 8) & 0xff)
    # NULL terminator
    out.extend(b"\xff\xff")
    # Palettes (4 × 8 bytes from vanilla palette_offsets)
    for src_off in rec["palette_offsets"]:
        if src_off:
            out.extend(palette_lookup(src_off))
        else:
            out.extend(b"\x00" * 8)
    while len(out) < SLOT_SIZE:
        out.append(0x00)
    assert len(out) == SLOT_SIZE
    return bytes(out)


# ---------------------------------------------------------------------------
# Protection / signature logic — uses precomputed prot_per_slot and
# has_walkable_gfx flags from enemizer_data so behaviour stays in sync
# with tools/enemize.py without re-implementing category logic here.
# ---------------------------------------------------------------------------
def _group_signature(rec: dict) -> tuple | None:
    """Hashable key for a group's protection + data-section layout.
    Returns None if no slot needs protection.

    Sig uses palette OFFSETS (not content) to avoid shipping vanilla
    palette bytes. Two groups with the same palette CONTENT at different
    offsets won't dedup — small efficiency loss, but the protected-slot
    custom slots still work correctly because each one carries the
    correct source offset for its locked palette."""
    if rec["bank_offset"] != 0:
        return None
    prot = rec["prot_per_slot"]
    if not any(prot):
        return None
    sig = []
    for i in range(4):
        cnt = rec["data_counts"][i]
        if prot[i]:
            sig.append(("P", rec["gfx_addrs"][i],
                        tuple(rec["data_slot_addrs"][i]),
                        rec["palette_offsets"][i], cnt))
        else:
            sig.append(("U", cnt))
    return tuple(sig)


def _group_has_walkable_or_platform_gfx(rec: dict) -> bool:
    """True if any of the group's 4 gfx slots loads a platform_vehicle /
    progression / boss label. Precomputed by build_apworld_enemizer_data."""
    return rec["has_walkable_gfx"]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def _compose_random_slot(rng, palette_lookup,
                         force_throwable_slot: int | None = None,
                         force_throwable_slots: frozenset[int] | None = None
                         ) -> tuple[bytes, tuple[int, int, int, int]]:
    """Return (slot_bytes, gfx_addrs_tuple). The tuple lets the room
    assignment step filter out slots whose VRAM-0 enemy matches the
    room's vanilla VRAM-0 — implements the "don't roll vanilla in your
    own room" rule (like palette shuffle clamping away from 0/1)."""
    chosen, native_slots = _pick_random_per_slot(
        rng, fixed_slots={},
        force_throwable_slot=force_throwable_slot,
        force_throwable_slots=force_throwable_slots)
    slot_bytes = _emit_slot_bytes(
        chosen, [len(pkg["data_addrs"]) for pkg in chosen],
        palette_lookup, native_slots=native_slots)
    return slot_bytes, tuple(pkg["gfx_addr"] for pkg in chosen)


def _compose_custom_slot(rng, sig: tuple, palette_lookup,
                         force_throwable_slot: int | None = None,
                         force_throwable_slots: frozenset[int] | None = None,
                         force_electric_slot: int | None = None,
                         rep_pal_offsets: list[int] | None = None,
                         rep_vanilla_gfx_addrs: tuple | None = None
                         ) -> tuple[bytes, tuple[int, int, int, int]]:
    """Compose a custom slot that preserves the protected ("P") slots
    from `sig` and randomizes the rest. Returns (slot_bytes,
    gfx_addrs_tuple) — same shape as _compose_random_slot.

    rep_pal_offsets[i] is the vanilla room's palette offset for slot i;
    when provided, unprotected slots use it instead of the picked enemy's
    canonical palette so randomized enemies pick up the room's palette
    context instead of looking out-of-place colored.

    rep_vanilla_gfx_addrs[i] is the representative vanilla gfx_addr for
    each VRAM slot. When provided, unprotected slots actively pick a
    random enemy whose gfx_addr DIFFERS from vanilla so the custom slot
    visibly differs from the room's vanilla bundle.
    """
    fixed: dict[int, dict] = {}
    data_counts = []
    for i, part in enumerate(sig):
        if part[0] == "P":
            _, gfx_addr, data_addrs, pal_off, cnt = part
            fixed[i] = {
                "gfx_addr": gfx_addr,
                "data_addrs": list(data_addrs),
                "palette_offset": pal_off,
            }
            data_counts.append(cnt)
        else:
            data_counts.append(part[1])
    chosen, native_slots = _pick_random_per_slot(
        rng, fixed,
        force_throwable_slot=force_throwable_slot,
        force_throwable_slots=force_throwable_slots,
        force_electric_slot=force_electric_slot,
        avoid_vanilla_gfx_addrs=rep_vanilla_gfx_addrs)
    if rep_pal_offsets is not None:
        for i in range(4):
            if sig[i][0] == "U" and rep_pal_offsets[i]:
                chosen[i] = dict(chosen[i])
                chosen[i]["palette_offset"] = rep_pal_offsets[i]
    # When forcing a throwable into a specific VRAM slot for solvability,
    # honor the throwable's own data count instead of the vanilla sig's
    # count. Vanilla ObjectGroups like OG117 have a "dummy" gfx in
    # slot 0 with zero data entries; if we truncate the throwable's data
    # to zero here, the room loses the required throwable enemy (the gfx
    # is there but no enemy spawns), which is exactly the "throw-block
    # room is empty" symptom.
    if force_throwable_slot is not None \
            and sig[force_throwable_slot][0] == "U" \
            and chosen[force_throwable_slot].get("data_addrs"):
        data_counts[force_throwable_slot] = \
            len(chosen[force_throwable_slot]["data_addrs"])
    slot_bytes = _emit_slot_bytes(chosen, data_counts, palette_lookup,
                                  native_slots=native_slots)
    return slot_bytes, tuple(pkg["gfx_addr"] for pkg in chosen)


def generate_patch_writes(rng, palette_lookup
                          ) -> list[tuple[int, bytes]]:
    """Return list of (rom_offset, bytes) writes for the enemizer.

    Option B v3 (2026-07-06): decoupled chest color from slot pool.
    Instead of partitioning 82 slots into 4 color buckets (grey/red/
    green/blue) and patching each room's enemy_group byte to a slot in
    the matching color bucket, we now:

      1. Compose a SINGLE POOL of 82 slots. Sigs are deduplicated across
         all colors (a "Snake@slot0" sig used by both grey and green
         rooms shares one slot).
      2. Patch ObjectGroups[wgid][2..3] (the data_ptr in the vanilla
         dispatch table) to point at the chosen slot's data. The
         CommonObjects_<Color> pointer at ObjectGroups[wgid][0..1] stays
         UNTOUCHED — chest color is preserved via the vanilla lookup.
      3. Room enemy_group bytes stay unchanged.

    Net effect: same wgid → same slot for all rooms with that wgid, but
    chest color routes via the untouched ObjectGroups[wgid][0..1] entry
    so grey chests stay grey even if the slot's own CommonObjects would
    have been a different color.

    Slot allocation (single pool of 82):
      - 4 any-random slots (baseline randomization pool for no-sig wgids)
      - K throw-block custom slots (one per unique (sig, tb_slot))
      - N regular custom slots (one per unique sig with protection)
      - 3 throwable-forced slots (VRAM 0/1/2, for throw-block rooms with
        no matching custom slot)

    Wgid routing:
      - boss (bank_offset != 0) → skip (stays vanilla)
      - FORCE_VANILLA_WGIDS (conditional-spawner cells) → skip
      - FORCE_VANILLA_GFX_PAIRS hit (ZipLine, BigLeaf) → skip
      - sig + tb_slot has matching (sig, tb_slot) custom → that slot
      - sig has a regular custom → that slot (CRASH_CONFIRMED_GIDS get
        vanilla-identical composition)
      - sig didn't fit (rare with 82-slot pool) → skip
      - no sig + tb_slot has throwable-by-vram slot → that slot
      - no sig, no tb_slot → any-random (prefer non-vanilla VRAM-0)
    """
    groups = enemizer_data.OBJECT_GROUPS
    wgid_to_real = enemizer_data.WGID_TO_REAL_GID
    rooms = enemizer_data.ROOM_OFFSETS

    # (slot_index, gfx_addr) pairs that require WHOLE-group vanilla
    # preservation. See prior comments for rationale.
    FORCE_VANILLA_GFX_PAIRS = {
        (2, 0x5d9b),   # ZipLineGfx
        (2, 0x4909),   # BigLeafGfx
        # (2, 0x599f) BubbleGfx moved from force-whole-vanilla to
        # per-slot lock via FORCE_LOCK_GFX_PAIRS below — only slot 2
        # (the BubbleHole spawner) needs vanilla; slots 0/1/3 can
        # randomize freely. Fixes Big Bridge Nobiiru staying vanilla.
        # Tower of Revival torch room (wgid 0x25/0x26, gid 42): no lock.
        # Stove@0 is already protected (walkable). FlameBlock@2 and
        # Torch@3 randomize freely — the room's torch-lighting puzzle
        # doesn't need to be completed anymore under these rules, so
        # neither the flame block nor the torch enemy is required.
    }

    # Per-slot lock GFX pairs — like FORCE_VANILLA_GFX_PAIRS but only
    # locks the matched slot, leaving the rest of the group to
    # randomize. Applied by merging into SLOT_LOCKED_GIDS at runtime.
    FORCE_LOCK_GFX_PAIRS = {
        (2, 0x599f),   # BubbleGfx — bubbles spawn from BubbleHole at
                       # slot 2 and Wario stands on them to reach checks
                       # (Vast Plain Big Coin, etc.). Locking slot 2
                       # preserves the mechanism; slot 3 (e.g. Big Bridge
                       # Nobiiru) still randomizes.
    }
    # Build per-gid slot-lock set from FORCE_LOCK_GFX_PAIRS
    _gfx_pair_slot_locks: dict[int, set] = {}
    for _gid, _g in groups.items():
        for _i, _a in enumerate(_g.get("gfx_addrs", [])):
            if (_i, _a) in FORCE_LOCK_GFX_PAIRS:
                _gfx_pair_slot_locks.setdefault(_gid, set()).add(_i)

    # Wgids whose all-room set stays vanilla (conditional-spawner cells
    # that crash on any enemizer touch and can't be handled per-sig).
    # OOTW BigLeaf: wgid 0x03 — the room in FORCE_VANILLA was OG6 which
    # is CRASH_CONFIRMED and gets vanilla-identical composition anyway,
    # so no explicit wgid entry needed for OOTW.
    # FoF Demon's Blood: wgid 0x61 — 4 crashing rooms + 4 non-crashing
    # rooms game-wide. Under per-wgid patching we can't force-vanilla the
    # 4 crashing rooms individually; excluding wgid 0x61 entirely means
    # the 4 non-crashing rooms also stay vanilla. Acceptable trade to
    # avoid the crash.
    # BotWR barrel platform: wgid 0x6a → ObjectGroup85 slot 3 = Barrel,
    # used as the floating platform to reach Big Coin 6. Categorized as
    # "pickup" so the enemizer would otherwise randomize it out and the
    # coin becomes unreachable.
    # A Town in Chaos throw-block room: wgid 0x91 → gid 117 has Spearhead
    # at slot 0 as gfx-only (data_count=0). The room's block function
    # dispenses a throwable using slot 0's tiles — inserting a throwable
    # data ptr at slot 0 (via _compose_custom_slot's data-count fix)
    # shifts the flat data-ptr indices the room's object_map depends on,
    # so the throwable goes missing. Force-vanilla preserves the
    # dispenser mechanic.
    # 0x61 = FallingSnow rooms (FoF + Frigid Sea, gid 77) — force
    # vanilla. Tested 2026-07-18: locks of {1}, {1, 3}, and {1, 3, 0}
    # all crashed. The block_map borrows tile bytes from every slot in
    # these rooms; no per-slot recovery possible. Whole vanilla only.
    FORCE_VANILLA_WGIDS = {0x61, 0x6a, 0x91}

    # Merge in the player's hand-verified throw-block room data. Multi-slot
    # wgids get force-vanilla'd (single-forced-throwable pass can't cover
    # them). Import lazily so a missing manual_throwable_config file (e.g.
    # a fresh clone before the tool has run) doesn't break enemizer.
    try:
        from . import manual_throwable_config as _mtc
        FORCE_VANILLA_WGIDS = FORCE_VANILLA_WGIDS | _mtc.MANUAL_FORCE_VANILLA_WGIDS
        MANUAL_TB_WGID_SLOT     = dict(_mtc.MANUAL_TB_WGID_SLOT)
        MANUAL_TB_WGID_SLOTS    = {w: frozenset(s) for w, s in
                                   getattr(_mtc, "MANUAL_TB_WGID_SLOTS", {}).items()}
        MANUAL_MARKED_WGIDS     = set(_mtc.MANUAL_MARKED_WGIDS)
        MANUAL_NO_THROWABLE     = set(_mtc.MANUAL_NO_THROWABLE_WGIDS)
    except ImportError:
        MANUAL_TB_WGID_SLOT     = {}
        MANUAL_TB_WGID_SLOTS    = {}
        MANUAL_MARKED_WGIDS     = set()
        MANUAL_NO_THROWABLE     = set()

    def _rec_with_slot_locks(rec: dict, gid: int) -> dict:
        """Return `rec` with any SLOT_LOCKED_GIDS[gid] slots (plus any
        FORCE_LOCK_GFX_PAIRS matches) marked protected. Doesn't mutate
        the original. The signature computed from the returned rec
        treats the locked slot(s) as vanilla."""
        locks = set(SLOT_LOCKED_GIDS.get(gid) or set())
        locks |= _gfx_pair_slot_locks.get(gid, set())
        if not locks:
            return rec
        new = dict(rec)
        prot = list(rec["prot_per_slot"])
        for s in locks:
            if 0 <= s < 4:
                prot[s] = True
        new["prot_per_slot"] = prot
        return new

    # === Build sig → wgids mapping (deduplicated across colors) ===
    sig_to_wgids: "OrderedDict[tuple, list[int]]" = OrderedDict()
    sig_to_rep_pal_offs: dict[tuple, list[int]] = {}
    sig_to_rep_gfx_addrs: dict[tuple, tuple] = {}
    sig_to_real_gids: dict[tuple, set] = {}
    for wgid, gid in wgid_to_real.items():
        rec = groups.get(gid)
        if rec is None or rec.get("bank_offset") != 0:
            continue
        if wgid in FORCE_VANILLA_WGIDS:
            continue
        rec = _rec_with_slot_locks(rec, gid)
        sig = _group_signature(rec)
        if sig is None:
            continue
        sig_to_wgids.setdefault(sig, []).append(wgid)
        sig_to_rep_pal_offs.setdefault(sig, list(rec["palette_offsets"]))
        sig_to_rep_gfx_addrs.setdefault(sig, tuple(rec["gfx_addrs"]))
        sig_to_real_gids.setdefault(sig, set()).add(gid)

    # === Build (sig, tb_slot) throw-block combos ===
    # tb_slot per wgid — the player's manual marks take precedence over
    # the auto-detected value in ROOM_OFFSETS. For any wgid the player
    # marked, we trust their call:
    #   - MANUAL_TB_WGID_SLOT[wgid] present -> force throwable at that slot
    #   - wgid in MANUAL_NO_THROWABLE      -> no throwable needed (skip)
    # For unmarked wgids the auto-detected tb_slot from ROOM_OFFSETS is
    # used as fallback; if that's also None, we auto-force a tb_slot
    # when the vanilla layout has an inherently-throwable enemy
    # (Barrel@3, Rock@2) whose whole purpose IS to be thrown.
    AUTO_TB_BY_VANILLA_GFX = {
        (2, 0x6502): 2,    # RockGfx at slot 2 → slot 2 must stay throwable
        (3, 0x49ec): 3,    # BarrelGfx at slot 3 → slot 3 must stay throwable
    }
    def _auto_tb_from_gfx(rec):
        for (i, a), sl in AUTO_TB_BY_VANILLA_GFX.items():
            if rec.get("gfx_addrs", [None]*4)[i] == a:
                return sl
        return None
    throwblock_keys: "OrderedDict[tuple, None]" = OrderedDict()
    tb_slot_by_wgid: dict[int, int] = {}
    multi_tb_keys: "OrderedDict[tuple, None]" = OrderedDict()
    multi_tb_by_wgid: dict[int, frozenset] = {}
    seen_wgids: set = set()
    for _eg_off, wgid, tb_slot in rooms:
        if wgid in FORCE_VANILLA_WGIDS:
            continue
        # Only decide once per wgid — multiple rooms sharing a wgid
        # would otherwise re-run the same decision loop.
        if wgid in seen_wgids:
            continue
        seen_wgids.add(wgid)
        # Multi-slot manual mark handled first — force throwable at
        # EACH required slot for that wgid. Supports both sig-based
        # (some slots protected) and no-sig (all slots unprotected)
        # cases; the latter uses a random-pool compose keyed only by
        # (None, slots) so wgids sharing this shape share a slot.
        if wgid in MANUAL_TB_WGID_SLOTS:
            real_id = wgid_to_real.get(wgid)
            if real_id is None:
                continue
            rec = groups.get(real_id)
            if rec is None:
                continue
            rec = _rec_with_slot_locks(rec, real_id)
            sig = _group_signature(rec)
            slots = MANUAL_TB_WGID_SLOTS[wgid]
            if sig is not None:
                # Drop slots already vanilla-throwable via sig protection.
                slots = frozenset(s for s in slots if sig[s][0] == "U")
                if not slots:
                    continue
            else:
                slots = frozenset(slots)
            multi_tb_by_wgid[wgid] = slots
            multi_tb_keys[(sig, slots)] = None
            continue
        # Manual single-slot data wins if present.
        if wgid in MANUAL_MARKED_WGIDS:
            if wgid in MANUAL_NO_THROWABLE:
                continue   # player said no throwable needed
            manual_slot = MANUAL_TB_WGID_SLOT.get(wgid)
            if manual_slot is None:
                continue
            tb_slot = manual_slot
        elif tb_slot is None:
            # No auto-detected tb_slot from ROOM_OFFSETS — check whether
            # the vanilla layout has an inherently-throwable enemy at
            # its native slot (Barrel/Rock). If so, force a throwable
            # there so the room's throwable-based mechanics still work.
            real_id = wgid_to_real.get(wgid)
            if real_id is None:
                continue
            rec = groups.get(real_id)
            if rec is None:
                continue
            auto_slot = _auto_tb_from_gfx(rec)
            if auto_slot is None:
                continue
            tb_slot = auto_slot
        tb_slot_by_wgid[wgid] = tb_slot
        real_id = wgid_to_real.get(wgid)
        if real_id is None:
            continue
        rec = groups.get(real_id)
        if rec is None:
            continue
        rec = _rec_with_slot_locks(rec, real_id)
        sig = _group_signature(rec)
        if sig is None:
            continue
        if sig[tb_slot][0] == "P":
            continue  # vanilla already has throwable in that slot
        throwblock_keys[(sig, tb_slot)] = None

    # === Sort sigs by wgid usage (across all rooms) ===
    def sig_usage(sig: tuple) -> int:
        return sum(1 for _eg_off, w, _t in rooms if w in sig_to_wgids.get(sig, []))
    sigs_sorted = sorted(sig_to_wgids.keys(), key=sig_usage, reverse=True)

    # === Allocate 82 slots ===
    NUM_THROWABLE = len(THROWABLE_VRAM_SLOTS_PER_BUCKET)  # 3
    NUM_ANY_MIN   = 4    # baseline any-random pool (matches old sum across buckets)
    custom_budget = NUM_TOTAL_SLOTS - NUM_THROWABLE - NUM_ANY_MIN

    # Option 2 — opportunistic sharing between regular sigs and throwblock
    # combos. Compose regular sigs first (biased at their throwblock tb_slot
    # when they have one) and reuse the same slot for the throwblock combo
    # if the biased pick landed on a throwable at that slot. Only unshared
    # throwblock combos get their own dedicated slot.
    sig_to_tb_slots_needed: dict[tuple, set[int]] = {}
    for (_sig, _tb) in throwblock_keys:
        sig_to_tb_slots_needed.setdefault(_sig, set()).add(_tb)

    # Set of gfx_addrs that qualify as throwables at a given VRAM slot
    # (native pick + cross-slot picks under the encoding limit).
    def _build_throwable_addr_set() -> dict[int, set[int]]:
        out: dict[int, set[int]] = {i: set() for i in range(4)}
        for slot in range(4):
            for native, names in THROWABLE_GFX_BY_SLOT.items():
                for name in names:
                    if name not in SLOT_PACKAGES[native]:
                        continue
                    pkg = SLOT_PACKAGES[native][name]
                    addr = pkg["gfx_addr"]
                    if native == slot or addr <= 0x5FFF:
                        out[slot].add(addr)
        return out
    _throwable_addrs_by_slot = _build_throwable_addr_set()

    # Pessimistic count: assume every throwblock combo needs a dedicated
    # slot. Compose that many regular sigs first, then sharing may free
    # slots that we fill with additional regular sigs afterwards.
    initial_regular_count = max(0, custom_budget
                                - len(throwblock_keys)
                                - len(multi_tb_keys))
    tb_keys_list = list(throwblock_keys.keys())
    num_any = NUM_TOTAL_SLOTS - NUM_THROWABLE \
              - len(tb_keys_list) - len(multi_tb_keys) - initial_regular_count
    assert num_any >= 1, "no any-random slots left"

    composed = bytearray()
    slot_gfx_addrs: list[tuple[int, int, int, int]] = [None] * NUM_TOTAL_SLOTS
    slot_idx = 0

    # Any-random slots
    any_pool: list[int] = []
    for _ in range(num_any):
        slot_bytes, gfx_sig = _compose_random_slot(rng, palette_lookup)
        composed.extend(slot_bytes)
        slot_gfx_addrs[slot_idx] = gfx_sig
        any_pool.append(slot_idx)
        slot_idx += 1

    # Spike rooms: force the unprotected "electric" slot to pick from
    # ELECTRIC_GFX_BY_SLOT so wl3's shared spike-tile references stay
    # compatible. Keyed by gid → slot to force.
    SPIKE_ELECTRIC_SLOT_BY_GID = {
        96: 3,  # Tower of Revival: slot 3 (Spark) drives spike tiles
    }
    # Precompute per-sig electric slot (via the sig's real_gids).
    sig_to_electric_slot: dict[tuple, int] = {}
    for _sig, _gids in sig_to_real_gids.items():
        for _gid in _gids:
            if _gid in SPIKE_ELECTRIC_SLOT_BY_GID:
                sig_to_electric_slot[_sig] = SPIKE_ELECTRIC_SLOT_BY_GID[_gid]
                break

    # Regular custom slots (phase 1 — biased). Vanilla-identical composition
    # for CRASH_CONFIRMED_GIDS (see _emit_vanilla_identical_slot rationale).
    sig_to_regular_id: dict[tuple, int] = {}
    def _compose_regular(sig):
        nonlocal slot_idx
        vanilla_rec = None
        for _gid in sig_to_real_gids[sig]:
            if _gid in CRASH_CONFIRMED_GIDS:
                vanilla_rec = groups.get(_gid)
                if vanilla_rec is not None:
                    break
        if vanilla_rec is not None:
            slot_bytes = _emit_vanilla_identical_slot(vanilla_rec, palette_lookup)
            gfx_sig = tuple(vanilla_rec["gfx_addrs"])
        else:
            # Bias regular composition to force a throwable at one of the
            # tb_slots this sig has. Only unprotected tb_slots qualify —
            # protected ones are already vanilla-throwable via the sig.
            tb_slots = sig_to_tb_slots_needed.get(sig, set())
            biased = None
            for _tb in sorted(tb_slots):
                if sig[_tb][0] == "U":
                    biased = _tb
                    break
            # Force electric pick for this sig's spike slot if applicable.
            elec_slot = sig_to_electric_slot.get(sig)
            if elec_slot is not None and sig[elec_slot][0] != "U":
                elec_slot = None   # already protected → nothing to force
            slot_bytes, gfx_sig = _compose_custom_slot(
                rng, sig, palette_lookup,
                force_throwable_slot=biased,
                force_electric_slot=elec_slot,
                rep_pal_offsets=sig_to_rep_pal_offs[sig],
                rep_vanilla_gfx_addrs=sig_to_rep_gfx_addrs[sig])
        composed.extend(slot_bytes)
        slot_gfx_addrs[slot_idx] = gfx_sig
        sig_to_regular_id[sig] = slot_idx
        slot_idx += 1

    for sig in sigs_sorted[:initial_regular_count]:
        _compose_regular(sig)

    # Check throwblock sharing — if the regular slot for this sig rolled
    # a throwable at tb_slot, reuse that slot instead of dedicating one.
    tb_key_to_id: dict[tuple[tuple, int], int] = {}
    unshared_tb_keys: list[tuple[tuple, int]] = []
    for (sig, tb_slot) in tb_keys_list:
        reg_id = sig_to_regular_id.get(sig)
        if reg_id is not None:
            gfx_at_tb = slot_gfx_addrs[reg_id][tb_slot]
            if gfx_at_tb in _throwable_addrs_by_slot[tb_slot]:
                tb_key_to_id[(sig, tb_slot)] = reg_id
                continue
        unshared_tb_keys.append((sig, tb_slot))

    # Fill slots freed by sharing with additional regular sigs (from
    # further down sigs_sorted).
    freed = len(tb_keys_list) - len(unshared_tb_keys)
    for sig in sigs_sorted[initial_regular_count:initial_regular_count + freed]:
        _compose_regular(sig)

    # Throw-block custom slots (only for combos that couldn't share).
    for (sig, tb_slot) in unshared_tb_keys:
        slot_bytes, gfx_sig = _compose_custom_slot(
            rng, sig, palette_lookup,
            force_throwable_slot=tb_slot,
            rep_pal_offsets=sig_to_rep_pal_offs[sig],
            rep_vanilla_gfx_addrs=sig_to_rep_gfx_addrs[sig])
        composed.extend(slot_bytes)
        slot_gfx_addrs[slot_idx] = gfx_sig
        tb_key_to_id[(sig, tb_slot)] = slot_idx
        slot_idx += 1

    # Multi-throwable custom slots — force throwables at EACH required
    # slot (for rooms marked with MANUAL_TB_WGID_SLOTS).
    multi_tb_key_to_id: dict[tuple, int] = {}
    for (sig, tb_slots_set) in multi_tb_keys:
        if sig is not None:
            slot_bytes, gfx_sig = _compose_custom_slot(
                rng, sig, palette_lookup,
                force_throwable_slots=tb_slots_set,
                rep_pal_offsets=sig_to_rep_pal_offs[sig],
                rep_vanilla_gfx_addrs=sig_to_rep_gfx_addrs[sig])
        else:
            slot_bytes, gfx_sig = _compose_random_slot(
                rng, palette_lookup,
                force_throwable_slots=tb_slots_set)
        composed.extend(slot_bytes)
        slot_gfx_addrs[slot_idx] = gfx_sig
        multi_tb_key_to_id[(sig, tb_slots_set)] = slot_idx
        slot_idx += 1

    # Throwable-by-vram slots (fallback for TB rooms with no custom slot)
    throwable_by_vram: dict[int, int] = {}
    for vs in THROWABLE_VRAM_SLOTS_PER_BUCKET:
        slot_bytes, gfx_sig = _compose_random_slot(
            rng, palette_lookup, force_throwable_slot=vs)
        composed.extend(slot_bytes)
        slot_gfx_addrs[slot_idx] = gfx_sig
        throwable_by_vram[vs] = slot_idx
        slot_idx += 1

    assert slot_idx == NUM_TOTAL_SLOTS, \
        f"composed {slot_idx} slots, expected {NUM_TOTAL_SLOTS}"

    # === Patch ObjectGroups[wgid] entries ===
    # ObjectGroups table lives at 19:5062 (ROM 0x65062). Each entry is
    # 4 bytes: dw CommonObjects_<Color>, dw ObjectGroupN. Enemizer
    # patches ONLY the ObjectGroupN pointer (bytes [2..3] within each
    # entry) to redirect enemy data loading to the chosen slot. The
    # CommonObjects pointer at [0..1] stays vanilla → chest color
    # preserved regardless of which slot the enemy data comes from.
    #
    # Slot X's data starts at ROM 0x66B58 + X*64. In bank-19 relative
    # form (used by ObjectGroupN pointers): 0x4000 + (0x66B58-0x64000) +
    # X*64 = 0x6B58 + X*64.
    OBJECT_GROUPS_ROM_OFFSET = 0x65062  # 19:5062
    SLOT_BANK_ADDR_BASE = 0x6B58        # bank-19 relative addr of EnemizerGroups

    writes: list[tuple[int, bytes]] = []
    for wgid, gid in wgid_to_real.items():
        rec = groups.get(gid)
        if rec is None:
            continue
        if rec.get("bank_offset") != 0:
            continue   # boss → vanilla
        if wgid in FORCE_VANILLA_WGIDS:
            continue
        gfx_addrs = rec.get("gfx_addrs", [])
        if any((i, a) in FORCE_VANILLA_GFX_PAIRS for i, a in enumerate(gfx_addrs)):
            continue

        rec = _rec_with_slot_locks(rec, gid)
        sig = _group_signature(rec)
        tb_slot = tb_slot_by_wgid.get(wgid)
        multi_tb = multi_tb_by_wgid.get(wgid)

        # Slot selection dispatch (mirrors the old per-room dispatch)
        if multi_tb is not None \
                and (sig, multi_tb) in multi_tb_key_to_id:
            slot = multi_tb_key_to_id[(sig, multi_tb)]
        elif sig is not None and tb_slot is not None \
                and (sig, tb_slot) in tb_key_to_id:
            slot = tb_key_to_id[(sig, tb_slot)]
        elif sig is not None and sig in sig_to_regular_id:
            slot = sig_to_regular_id[sig]
        elif sig is not None:
            continue   # sig didn't fit → stay vanilla
        elif tb_slot is not None and tb_slot in throwable_by_vram:
            slot = throwable_by_vram[tb_slot]
        else:
            # No sig, no tb_slot: any-random, prefer non-vanilla VRAM-0
            vanilla_v0 = gfx_addrs[0] if gfx_addrs else None
            candidates = list(any_pool)
            if vanilla_v0 is not None:
                non_match = [s for s in candidates
                             if slot_gfx_addrs[s][0] != vanilla_v0]
                if non_match:
                    candidates = non_match
            slot = rng.choice(candidates)

        # Patch ObjectGroups[wgid][2..3] = dw (SLOT_BANK_ADDR_BASE + slot*64)
        slot_bank_addr = SLOT_BANK_ADDR_BASE + slot * SLOT_SIZE
        patch_off = OBJECT_GROUPS_ROM_OFFSET + wgid * 4 + 2
        writes.append((patch_off,
                       slot_bank_addr.to_bytes(2, "little")))

    assert len(composed) == TABLE_SIZE, \
        f"composed {len(composed)} bytes, expected {TABLE_SIZE}"
    writes.insert(0, (enemizer_data.ENEMIZER_GROUPS_OFFSET, bytes(composed)))
    return writes
