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
NUM_RANDOM_SLOTS       = 36
NUM_TOTAL_SLOTS        = 83
NUM_CUSTOM_SLOTS       = NUM_TOTAL_SLOTS - NUM_RANDOM_SLOTS   # = 47
TABLE_SIZE             = SLOT_SIZE * NUM_TOTAL_SLOTS

# Random pool sub-split — must match tools/enemize.py.
NUM_RANDOM_ANY_SLOTS = 26
NUM_RANDOM_THROWABLE = {0: 4, 1: 1, 2: 5, 3: 0}
assert NUM_RANDOM_ANY_SLOTS + sum(NUM_RANDOM_THROWABLE.values()) == NUM_RANDOM_SLOTS

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
                         force_throwable_slot: int | None = None) -> bytes:
    chosen = _pick_random_per_slot(rng, fixed_slots={},
                                   force_throwable_slot=force_throwable_slot)
    return _emit_slot_bytes(
        chosen, [len(pkg["data_addrs"]) for pkg in chosen], palette_lookup)


def _compose_custom_slot(rng, sig: tuple, palette_lookup,
                         force_throwable_slot: int | None = None,
                         rep_pal_offsets: list[int] | None = None) -> bytes:
    """rep_pal_offsets[i] is the vanilla room's palette offset for slot i;
    when provided, unprotected slots use it instead of the picked enemy's
    canonical palette — so randomized enemies pick up the room's palette
    context instead of looking out-of-place colored."""
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
    return _emit_slot_bytes(chosen, data_counts, palette_lookup)


def generate_patch_writes(rng, palette_lookup
                          ) -> list[tuple[int, bytes]]:
    """Return list of (rom_offset, bytes) writes for the enemizer.

    Mirrors tools/enemize.py main(): random pool sub-split (most slots
    are "any"; small per-VRAM-slot pools force a throwable for throw-
    block room routing), regular custom slots per protection signature,
    plus extra custom slots keyed by (sig, throwable_slot) so throw-
    block rooms with protected groups also keep their solvability.
    """
    groups = enemizer_data.OBJECT_GROUPS
    wgid_to_real = enemizer_data.WGID_TO_REAL_GID
    rooms = enemizer_data.ROOM_OFFSETS  # list of (eg_off, wgid, throwable_slot)

    # Bucket rooms by REAL ObjectGroupXX id (after dispatch translation).
    rooms_per_real_gid: dict[int, list[int]] = {}
    for eg_off, wgid, _ in rooms:
        real_id = wgid_to_real.get(wgid)
        if real_id is not None:
            rooms_per_real_gid.setdefault(real_id, []).append(eg_off)

    # Build signature -> real gids. Also remember the first group's
    # palette offsets per sig — used as the representative vanilla room
    # palette for unprotected slots in custom slot composition.
    sig_to_real_gids: "OrderedDict[tuple, list[int]]" = OrderedDict()
    sig_to_rep_pal_offs: dict[tuple, list[int]] = {}
    for gid, rec in groups.items():
        sig = _group_signature(rec)
        if sig is None:
            continue
        sig_to_real_gids.setdefault(sig, []).append(gid)
        sig_to_rep_pal_offs.setdefault(sig, list(rec["palette_offsets"]))

    # Collect (sig, throwable_slot) combos needed for throw-block rooms
    # with protected groups. Skip cases where the desired slot is already
    # signature-protected (the vanilla throwable is preserved verbatim).
    throwblock_keys: dict[tuple[tuple, int], None] = OrderedDict()
    for eg_off, wgid, tb_slot in rooms:
        if tb_slot is None:
            continue
        real_id = wgid_to_real.get(wgid)
        if real_id is None or real_id not in groups:
            continue
        sig = _group_signature(groups[real_id])
        if sig is None:
            continue  # random-routed; handled by random sub-pool
        if sig[tb_slot][0] == "P":
            continue  # already preserved by signature
        throwblock_keys[(sig, tb_slot)] = None

    def usage(sig: tuple) -> int:
        return sum(len(rooms_per_real_gid.get(gid, []))
                   for gid in sig_to_real_gids[sig])
    sigs_sorted = sorted(sig_to_real_gids.keys(), key=usage, reverse=True)

    # Reserve throw-block customs first (solvability), fill the rest with
    # regular sigs by usage.
    reserved_tb = len(throwblock_keys)
    regular_budget = max(0, NUM_CUSTOM_SLOTS - reserved_tb)
    regular_sigs_to_emit = sigs_sorted[:regular_budget]

    reg_custom_base = ENEMIZER_GROUP_ID_BASE + NUM_RANDOM_SLOTS
    tb_custom_base  = reg_custom_base + len(regular_sigs_to_emit)

    real_gid_to_regular_id: dict[int, int] = {}
    for slot_idx, sig in enumerate(regular_sigs_to_emit):
        cid = reg_custom_base + slot_idx
        for gid in sig_to_real_gids[sig]:
            real_gid_to_regular_id[gid] = cid
    wgid_to_regular_id = {
        wgid: real_gid_to_regular_id[real]
        for wgid, real in wgid_to_real.items()
        if real in real_gid_to_regular_id
    }
    tb_key_to_id: dict[tuple[tuple, int], int] = {}
    for idx, key in enumerate(throwblock_keys.keys()):
        tb_key_to_id[key] = tb_custom_base + idx

    # Compose the EnemizerGroups table:
    #   1. Any-random slots
    #   2. Throwable-forced random slots (per VRAM slot)
    #   3. Regular custom slots
    #   4. Throw-block custom slots
    composed = bytearray()
    for _ in range(NUM_RANDOM_ANY_SLOTS):
        composed.extend(_compose_random_slot(rng, palette_lookup))
    for vram_slot in (0, 1, 2, 3):
        for _ in range(NUM_RANDOM_THROWABLE[vram_slot]):
            composed.extend(_compose_random_slot(rng, palette_lookup,
                                                 force_throwable_slot=vram_slot))
    for sig in regular_sigs_to_emit:
        composed.extend(_compose_custom_slot(rng, sig, palette_lookup))
    for (sig, tb_slot) in throwblock_keys.keys():
        composed.extend(_compose_custom_slot(
            rng, sig, palette_lookup, force_throwable_slot=tb_slot))
    while len(composed) < TABLE_SIZE:
        composed.extend(_compose_random_slot(rng, palette_lookup))
    assert len(composed) == TABLE_SIZE

    writes: list[tuple[int, bytes]] = [
        (enemizer_data.ENEMIZER_GROUPS_OFFSET, bytes(composed)),
    ]

    # Random pool ID ranges for routing.
    any_pool = range(0, NUM_RANDOM_ANY_SLOTS)
    throwable_pool: dict[int, range] = {}
    cursor = NUM_RANDOM_ANY_SLOTS
    for vs in (0, 1, 2, 3):
        cnt = NUM_RANDOM_THROWABLE[vs]
        throwable_pool[vs] = range(cursor, cursor + cnt)
        cursor += cnt

    def pick_random_slot_id(force_slot: int | None) -> int:
        if force_slot is not None and len(throwable_pool[force_slot]) > 0:
            rel = rng.choice(list(throwable_pool[force_slot]))
        else:
            rel = rng.choice(list(any_pool))
        return ENEMIZER_GROUP_ID_BASE + rel

    # Patch each room's enemy_group byte.
    for eg_off, wgid, tb_slot in rooms:
        real_id = wgid_to_real.get(wgid)
        real_g = groups.get(real_id) if real_id is not None else None
        if real_g is not None and real_g["bank_offset"] != 0:
            continue   # boss → vanilla
        sig = _group_signature(real_g) if real_g is not None else None
        # Throw-block custom slot if available.
        if sig is not None and tb_slot is not None \
                and (sig, tb_slot) in tb_key_to_id:
            new = tb_key_to_id[(sig, tb_slot)]
        elif wgid in wgid_to_regular_id:
            new = wgid_to_regular_id[wgid]
        elif sig is not None:
            continue   # overflow protected → vanilla
        else:
            new = pick_random_slot_id(tb_slot)
        writes.append((eg_off, bytes([new])))

    return writes
