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
NUM_RANDOM_SLOTS       = 48
NUM_TOTAL_SLOTS        = 78
NUM_CUSTOM_SLOTS       = NUM_TOTAL_SLOTS - NUM_RANDOM_SLOTS
TABLE_SIZE             = SLOT_SIZE * NUM_TOTAL_SLOTS

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


def _pick_random_per_slot(rng, fixed_slots: dict[int, dict]) -> list[dict]:
    chosen: list[Any] = [None, None, None, None]
    for i in range(4):
        chosen[i] = fixed_slots.get(i)

    # Slot 0
    if chosen[0] is None:
        names = sorted(SLOT_PACKAGES[0].keys())
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
            names = sorted(n for n in SLOT_PACKAGES[1]
                           if n not in PAIRED_GFX_REVERSE)
            chosen[1] = SLOT_PACKAGES[1][rng.choice(names)]

    # Slots 2 and 3
    for i in (2, 3):
        if chosen[i] is None:
            names = sorted(SLOT_PACKAGES[i].keys())
            chosen[i] = SLOT_PACKAGES[i][rng.choice(names)]
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
def generate_patch_writes(rng, palette_lookup
                          ) -> list[tuple[int, bytes]]:
    """Return list of (rom_offset, bytes) writes for the enemizer.

    palette_lookup is a callable: palette_lookup(rom_offset) -> bytes
    (8 bytes of palette data). At patch-apply time it returns either the
    vanilla palette bytes (read from the ROM snapshot) or the post-
    shuffle bytes (recolored with the same seed apply_palette_shuffle
    will use), so enemizer slots stay color-consistent.
    """
    groups = enemizer_data.OBJECT_GROUPS
    wgid_to_real = enemizer_data.WGID_TO_REAL_GID
    rooms = enemizer_data.ROOM_OFFSETS

    # Bucket rooms by REAL ObjectGroupXX id (after dispatch translation).
    rooms_per_real_gid: dict[int, list[int]] = {}
    for eg_off, wgid in rooms:
        real_id = wgid_to_real.get(wgid)
        if real_id is not None:
            rooms_per_real_gid.setdefault(real_id, []).append(eg_off)

    # Build signature → real gids.
    sig_to_real_gids: "OrderedDict[tuple, list[int]]" = OrderedDict()
    for gid, rec in groups.items():
        sig = _group_signature(rec)
        if sig is None:
            continue
        sig_to_real_gids.setdefault(sig, []).append(gid)

    def usage(sig: tuple) -> int:
        return sum(len(rooms_per_real_gid.get(gid, []))
                   for gid in sig_to_real_gids[sig])
    sigs_sorted = sorted(sig_to_real_gids.keys(), key=usage, reverse=True)
    sigs_to_emit = sigs_sorted[:NUM_CUSTOM_SLOTS]

    real_gid_to_custom_id: dict[int, int] = {}
    for slot_idx, sig in enumerate(sigs_to_emit):
        cid = ENEMIZER_GROUP_ID_BASE + NUM_RANDOM_SLOTS + slot_idx
        for gid in sig_to_real_gids[sig]:
            real_gid_to_custom_id[gid] = cid
    wgid_to_custom_id = {
        wgid: real_gid_to_custom_id[real]
        for wgid, real in wgid_to_real.items()
        if real in real_gid_to_custom_id
    }

    # Compose the EnemizerGroups table.
    composed = bytearray()
    for _ in range(NUM_RANDOM_SLOTS):
        chosen = _pick_random_per_slot(rng, fixed_slots={})
        composed.extend(_emit_slot_bytes(
            chosen, [len(pkg["data_addrs"]) for pkg in chosen],
            palette_lookup))
    for sig in sigs_to_emit:
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
        chosen = _pick_random_per_slot(rng, fixed)
        composed.extend(_emit_slot_bytes(chosen, data_counts, palette_lookup))
    while len(composed) < TABLE_SIZE:
        chosen = _pick_random_per_slot(rng, fixed_slots={})
        composed.extend(_emit_slot_bytes(
            chosen, [len(pkg["data_addrs"]) for pkg in chosen],
            palette_lookup))
    assert len(composed) == TABLE_SIZE

    writes: list[tuple[int, bytes]] = [
        (enemizer_data.ENEMIZER_GROUPS_OFFSET, bytes(composed)),
    ]

    # Patch each room's enemy_group byte.
    for eg_off, wgid in rooms:
        if wgid in wgid_to_custom_id:
            new = wgid_to_custom_id[wgid]
        else:
            real_id = wgid_to_real.get(wgid)
            real_g = groups.get(real_id) if real_id is not None else None
            if real_g is not None and real_g["bank_offset"] != 0:
                continue   # boss → vanilla
            if real_g is not None and _group_signature(real_g) is not None:
                continue   # overflow protected → vanilla
            new = ENEMIZER_GROUP_ID_BASE + rng.randrange(NUM_RANDOM_SLOTS)
        writes.append((eg_off, bytes([new])))

    return writes
