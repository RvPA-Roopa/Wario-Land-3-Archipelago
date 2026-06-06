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
NUM_TOTAL_SLOTS        = 83
TABLE_SIZE             = SLOT_SIZE * NUM_TOTAL_SLOTS

# Option B partition — each color's 21/20 slot bucket dispatches through
# CommonObjects_<Color> so chest/key sprites keep their vanilla color
# after enemy_group remap. Per-bucket layout: most slots "any-random",
# 3 throwable-forced slots (one each for VRAM slots 0/1/2 — vanilla has
# no slot-3 throwables) so throw-block rooms in any color can still
# reach a throwable. Must match src/constants/object_constants.asm.
ENEMIZER_BUCKET_COUNTS = [21, 21, 21, 20]   # [Grey, Red, Green, Blue]
assert sum(ENEMIZER_BUCKET_COUNTS) == NUM_TOTAL_SLOTS
ENEMIZER_BUCKET_BASES = [0,
                         ENEMIZER_BUCKET_COUNTS[0],
                         ENEMIZER_BUCKET_COUNTS[0] + ENEMIZER_BUCKET_COUNTS[1],
                         ENEMIZER_BUCKET_COUNTS[0] + ENEMIZER_BUCKET_COUNTS[1] + ENEMIZER_BUCKET_COUNTS[2]]
THROWABLE_VRAM_SLOTS_PER_BUCKET = (0, 1, 2)   # one throwable slot per bucket per VRAM slot

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
    2: {"DoughnuteerGfx", "RockGfx", "SpearBotGfx"},
    3: {"BeamBotGfx", "FireBotGfx"},
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


def _pick_random_per_slot(rng, fixed_slots: dict[int, dict],
                          force_throwable_slot: int | None = None) -> list[dict]:
    """Pick an enemy package per VRAM slot. fixed_slots maps slot_idx -> a
    package dict (from a signature's protected slot); those slots are
    returned as-is. If force_throwable_slot is set, that VRAM slot is
    constrained to a throwable from THROWABLE_GFX_BY_SLOT[idx]."""
    chosen: list[Any] = [None, None, None, None]
    for i in range(4):
        chosen[i] = fixed_slots.get(i)

    def names_for(slot_idx: int) -> list[str]:
        avail = sorted(SLOT_PACKAGES[slot_idx].keys())
        if force_throwable_slot == slot_idx:
            avail = [n for n in avail
                     if n in THROWABLE_GFX_BY_SLOT.get(slot_idx, set())]
        return avail

    # Slot 0
    if chosen[0] is None:
        names = names_for(0)
        if chosen[1] is not None:
            names = [n for n in names if n not in PAIRED_GFX]
        name0 = rng.choice(names)
        chosen[0] = SLOT_PACKAGES[0][name0]
        name0_key = name0
    else:
        name0_key = None

    # Slot 1
    if chosen[1] is None:
        if name0_key in PAIRED_GFX:
            chosen[1] = SLOT_PACKAGES[1][PAIRED_GFX[name0_key]]
        else:
            names = [n for n in names_for(1) if n not in PAIRED_GFX_REVERSE]
            chosen[1] = SLOT_PACKAGES[1][rng.choice(names)]

    # Slots 2 and 3
    for i in (2, 3):
        if chosen[i] is None:
            chosen[i] = SLOT_PACKAGES[i][rng.choice(names_for(i))]
    return chosen


def _emit_slot_bytes(chosen: list[dict],
                     target_data_counts: list[int],
                     palette_lookup) -> bytes:
    out = bytearray()
    out.append(0x00)  # bank_offset
    # 4 gfx ptrs
    for pkg in chosen:
        addr = pkg["gfx_addr"]
        out.append(addr & 0xff)
        out.append((addr >> 8) & 0xff)
    # Data ptrs per slot, padded to target counts
    for i, pkg in enumerate(chosen):
        target = target_data_counts[i]
        ptrs = list(pkg["data_addrs"])
        if len(ptrs) > target:
            ptrs = ptrs[:target]
        while len(ptrs) < target:
            ptrs.append(DUMMY_OBJECT_DATA_ADDR)
        for addr in ptrs:
            out.append(addr & 0xff)
            out.append((addr >> 8) & 0xff)
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
                         force_throwable_slot: int | None = None
                         ) -> tuple[bytes, tuple[int, int, int, int]]:
    """Return (slot_bytes, gfx_addrs_tuple). The tuple lets the room
    assignment step filter out slots whose VRAM-0 enemy matches the
    room's vanilla VRAM-0 — implements the "don't roll vanilla in your
    own room" rule (like palette shuffle clamping away from 0/1)."""
    chosen = _pick_random_per_slot(rng, fixed_slots={},
                                   force_throwable_slot=force_throwable_slot)
    slot_bytes = _emit_slot_bytes(
        chosen, [len(pkg["data_addrs"]) for pkg in chosen], palette_lookup)
    return slot_bytes, tuple(pkg["gfx_addr"] for pkg in chosen)


def _compose_custom_slot(rng, sig: tuple, palette_lookup,
                         force_throwable_slot: int | None = None,
                         rep_pal_offsets: list[int] | None = None
                         ) -> tuple[bytes, tuple[int, int, int, int]]:
    """Compose a custom slot that preserves the protected ("P") slots
    from `sig` and randomizes the rest. Returns (slot_bytes,
    gfx_addrs_tuple) — same shape as _compose_random_slot.

    rep_pal_offsets[i] is the vanilla room's palette offset for slot i;
    when provided, unprotected slots use it instead of the picked enemy's
    canonical palette so randomized enemies pick up the room's palette
    context instead of looking out-of-place colored.
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
    chosen = _pick_random_per_slot(rng, fixed,
                                   force_throwable_slot=force_throwable_slot)
    if rep_pal_offsets is not None:
        for i in range(4):
            if sig[i][0] == "U" and rep_pal_offsets[i]:
                chosen[i] = dict(chosen[i])
                chosen[i]["palette_offset"] = rep_pal_offsets[i]
    slot_bytes = _emit_slot_bytes(chosen, data_counts, palette_lookup)
    return slot_bytes, tuple(pkg["gfx_addr"] for pkg in chosen)


def generate_patch_writes(rng, palette_lookup
                          ) -> list[tuple[int, bytes]]:
    """Return list of (rom_offset, bytes) writes for the enemizer.

    Option B v2: each color bucket independently runs the original
    enemizer's any-random + throwable + custom-slot scheme. The 21 (or
    20) slots per bucket are filled in this order:
      1. K custom slots — one per (sig, tb_slot) throw-block combo that
         appears in this color, then one per most-used signature
         remaining, until the budget runs out.
      2. 3 throwable any-random slots (VRAM 0/1/2).
      3. Remaining = any-random fill.

    Custom slots preserve the sig's protected VRAM slots verbatim
    (Futamogu stepping stones, ClearGate progression blocks, etc.) and
    randomize the unprotected slots — so a room with one Futamogu out of
    4 enemies still gets fresh enemies in 3 of its 4 slots instead of
    being skipped to vanilla like Option B v1 did.

    Room routing:
      - boss → vanilla
      - sig + tb_slot has a matching (sig, tb_slot) custom → that slot
      - sig has a regular custom → that slot
      - sig has neither (budget overflowed) → vanilla
      - no sig + tb_slot has throwable slot in color → throwable slot
      - no sig → any-random in color (preferring non-vanilla VRAM-0)
    """
    groups = enemizer_data.OBJECT_GROUPS
    wgid_to_real = enemizer_data.WGID_TO_REAL_GID
    wgid_to_color = enemizer_data.WGID_TO_COMMON_OBJECTS_COLOR
    rooms = enemizer_data.ROOM_OFFSETS

    # Partition rooms by their vanilla CommonObjects color so we can
    # compute usage-by-sig per bucket and allocate independently.
    rooms_per_color: list[list[tuple[int, int, int | None]]] = [[], [], [], []]
    for eg_off, wgid, tb_slot in rooms:
        color = wgid_to_color.get(wgid)
        if color is not None:
            rooms_per_color[color].append((eg_off, wgid, tb_slot))

    composed = bytearray()
    slot_gfx_addrs: list[tuple[int, int, int, int]] = [None] * NUM_TOTAL_SLOTS
    writes: list[tuple[int, bytes]] = []

    NUM_THROWABLE_PER_BUCKET = len(THROWABLE_VRAM_SLOTS_PER_BUCKET)

    for color in range(4):
        bucket_base = ENEMIZER_BUCKET_BASES[color]
        bucket_size = ENEMIZER_BUCKET_COUNTS[color]
        color_rooms = rooms_per_color[color]

        # ---- Build per-color usage map ----
        # For each ObjectGroup id (real_id) that any room of this color
        # uses, count rooms. Then group by signature.
        rooms_per_real_gid: dict[int, list[int]] = {}
        for eg_off, wgid, _ in color_rooms:
            real_id = wgid_to_real.get(wgid)
            if real_id is not None:
                rooms_per_real_gid.setdefault(real_id, []).append(eg_off)

        sig_to_real_gids: "OrderedDict[tuple, list[int]]" = OrderedDict()
        sig_to_rep_pal_offs: dict[tuple, list[int]] = {}
        for gid in rooms_per_real_gid:
            rec = groups.get(gid)
            if rec is None:
                continue
            sig = _group_signature(rec)
            if sig is None:
                continue
            sig_to_real_gids.setdefault(sig, []).append(gid)
            sig_to_rep_pal_offs.setdefault(sig, list(rec["palette_offsets"]))

        # Throw-block (sig, tb_slot) combos that appear in this color and
        # need a custom-throwable slot to keep solvability.
        throwblock_keys: dict[tuple[tuple, int], None] = OrderedDict()
        for eg_off, wgid, tb_slot in color_rooms:
            if tb_slot is None:
                continue
            real_id = wgid_to_real.get(wgid)
            if real_id is None or real_id not in groups:
                continue
            sig = _group_signature(groups[real_id])
            if sig is None:
                continue  # routed through plain throwable slot, not custom
            if sig[tb_slot][0] == "P":
                continue  # vanilla already has the throwable in that slot
            throwblock_keys[(sig, tb_slot)] = None

        def sig_usage(sig: tuple) -> int:
            return sum(len(rooms_per_real_gid.get(gid, []))
                       for gid in sig_to_real_gids[sig])
        sigs_sorted = sorted(sig_to_real_gids.keys(), key=sig_usage, reverse=True)

        # ---- Allocate this bucket's slots ----
        # Always reserve 3 throwable slots at the end.
        custom_budget = bucket_size - NUM_THROWABLE_PER_BUCKET
        # Tb-keys first (solvability priority), then regular sigs by
        # usage, until budget is exhausted. Reserve 1 slot minimum for
        # any-random so unprotected rooms in this color always have a
        # destination.
        max_customs = max(0, custom_budget - 1)
        tb_keys_to_emit = list(throwblock_keys.keys())[:max_customs]
        remaining = max_customs - len(tb_keys_to_emit)
        regular_sigs_to_emit = sigs_sorted[:remaining]
        num_any = bucket_size - NUM_THROWABLE_PER_BUCKET \
                  - len(tb_keys_to_emit) - len(regular_sigs_to_emit)
        assert num_any >= 1, f"color {color}: no any-random slots left"

        # Compose in this layout order:
        #   [any-random × num_any] [regular custom × N] [tb custom × M]
        #   [throwable × 3 (VRAM 0/1/2)]
        slot_idx = bucket_base
        any_pool: list[int] = []
        for _ in range(num_any):
            slot_bytes, gfx_sig = _compose_random_slot(rng, palette_lookup)
            composed.extend(slot_bytes)
            slot_gfx_addrs[slot_idx] = gfx_sig
            any_pool.append(slot_idx)
            slot_idx += 1

        sig_to_regular_id: dict[tuple, int] = {}
        for sig in regular_sigs_to_emit:
            slot_bytes, gfx_sig = _compose_custom_slot(
                rng, sig, palette_lookup,
                rep_pal_offsets=sig_to_rep_pal_offs[sig])
            composed.extend(slot_bytes)
            slot_gfx_addrs[slot_idx] = gfx_sig
            sig_to_regular_id[sig] = slot_idx
            slot_idx += 1

        tb_key_to_id: dict[tuple[tuple, int], int] = {}
        for (sig, tb_slot) in tb_keys_to_emit:
            slot_bytes, gfx_sig = _compose_custom_slot(
                rng, sig, palette_lookup,
                force_throwable_slot=tb_slot,
                rep_pal_offsets=sig_to_rep_pal_offs[sig])
            composed.extend(slot_bytes)
            slot_gfx_addrs[slot_idx] = gfx_sig
            tb_key_to_id[(sig, tb_slot)] = slot_idx
            slot_idx += 1

        throwable_by_vram: dict[int, int] = {}
        for vs in THROWABLE_VRAM_SLOTS_PER_BUCKET:
            slot_bytes, gfx_sig = _compose_random_slot(
                rng, palette_lookup, force_throwable_slot=vs)
            composed.extend(slot_bytes)
            slot_gfx_addrs[slot_idx] = gfx_sig
            throwable_by_vram[vs] = slot_idx
            slot_idx += 1

        assert slot_idx == bucket_base + bucket_size, \
            f"color {color}: composed {slot_idx - bucket_base} slots, expected {bucket_size}"

        # Build wgid → regular_id mapping for this color.
        wgid_to_regular_id: dict[int, int] = {}
        for sig, custom_id in sig_to_regular_id.items():
            for gid in sig_to_real_gids[sig]:
                # Multiple wgids can map to the same real_id (color-
                # specific aliasing); only patch the ones whose color
                # actually matches this bucket.
                for wgid, real in wgid_to_real.items():
                    if real == gid and wgid_to_color.get(wgid) == color:
                        wgid_to_regular_id[wgid] = custom_id

        # ---- Patch room enemy_group bytes for this color ----
        for eg_off, wgid, tb_slot in color_rooms:
            real_id = wgid_to_real.get(wgid)
            real_g = groups.get(real_id) if real_id is not None else None
            if real_g is not None and real_g["bank_offset"] != 0:
                continue   # boss → vanilla
            sig = _group_signature(real_g) if real_g is not None else None

            if sig is not None and tb_slot is not None \
                    and (sig, tb_slot) in tb_key_to_id:
                slot = tb_key_to_id[(sig, tb_slot)]
            elif wgid in wgid_to_regular_id:
                slot = wgid_to_regular_id[wgid]
            elif sig is not None:
                continue   # sig didn't fit in budget → vanilla
            elif tb_slot is not None and tb_slot in throwable_by_vram:
                slot = throwable_by_vram[tb_slot]
            else:
                # Unprotected, no throw-block: pick any-random, prefer
                # one whose VRAM-0 gfx doesn't match this room's vanilla.
                vanilla_gfx_addrs = tuple(real_g["gfx_addrs"]) if real_g else ()
                vanilla_v0 = vanilla_gfx_addrs[0] if vanilla_gfx_addrs else None
                candidates = list(any_pool)
                if vanilla_v0 is not None:
                    non_match = [s for s in candidates
                                 if slot_gfx_addrs[s][0] != vanilla_v0]
                    if non_match:
                        candidates = non_match
                slot = rng.choice(candidates)
            writes.append((eg_off, bytes([ENEMIZER_GROUP_ID_BASE + slot])))

    assert len(composed) == TABLE_SIZE, \
        f"composed {len(composed)} bytes, expected {TABLE_SIZE}"
    writes.insert(0, (enemizer_data.ENEMIZER_GROUPS_OFFSET, bytes(composed)))
    return writes
