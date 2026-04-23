from typing import Dict, List, NamedTuple, Optional, Set
from BaseClasses import ItemClassification

BASE_ITEM_ID = 7_770_000

# AP item IDs:
#   Regular items:     BASE_ITEM_ID + treasure_id  (7770001 – 7770100, minus 6 progressive slots)
#   Progressive items: BASE_ITEM_ID + 200 + index  (7770200 – 7770202)
#   Combined items:    BASE_ITEM_ID + 203 + index  (7770203 – 7770210)
#   Key items:         BASE_ITEM_ID + 300 + (owlevel-1)*4 + color  (7770300 – 7770399)

KEY_BASE_ITEM_ID = BASE_ITEM_ID + 300  # 7_770_300


class WL3ItemData(NamedTuple):
    ap_id: int
    classification: ItemClassification
    # For progressive items: in-game treasure IDs per tier (index 0 = tier 1, etc.)
    # For regular items: single-element list with the treasure_id.
    # For combined items: treasure_id is the canonical display ID (first component).
    tier_ids: List[int]

    @property
    def treasure_id(self) -> Optional[int]:
        """Single treasure ID for non-progressive items."""
        return self.tier_ids[0] if len(self.tier_ids) == 1 else None


# ---------------------------------------------------------------------------
# Progressive items (3 groups, 2 tiers each = 6 item instances in the pool)
# ---------------------------------------------------------------------------

PROGRESSIVE_ITEMS: Dict[str, WL3ItemData] = {
    "Progressive Overalls": WL3ItemData(
        ap_id=BASE_ITEM_ID + 200,
        classification=ItemClassification.progression,
        tier_ids=[0x0c, 0x0d],   # Lead Overalls → Super Jump Slam Overalls
    ),
    "Progressive Grab": WL3ItemData(
        ap_id=BASE_ITEM_ID + 201,
        classification=ItemClassification.progression,
        tier_ids=[0x0b, 0x09],   # Grab Glove → Super Grab Gloves
    ),
    "Progressive Flippers": WL3ItemData(
        ap_id=BASE_ITEM_ID + 202,
        classification=ItemClassification.progression,
        tier_ids=[0x07, 0x06],   # Swimming Flippers → Prince Frog's Gloves
    ),
}

# Treasure IDs consumed by progressive items (not in TREASURE_TABLE)
_PROGRESSIVE_TREASURE_IDS = {
    tid for item in PROGRESSIVE_ITEMS.values() for tid in item.tier_ids
}

# ---------------------------------------------------------------------------
# Combined unlock items (used when CombinedItems option is on)
# Each replaces a group of individual items with a single AP item.
# tier_ids[0] is the canonical chest-display treasure ID (first component).
# The client grants all component treasure bits via COMBINED_GRANTS in client.py.
# ---------------------------------------------------------------------------

# Overworld pairs — gate level access.
COMBINED_ITEMS_OVERWORLD: Dict[str, WL3ItemData] = {
    "Lantern & Magical Flame": WL3ItemData(
        ap_id=BASE_ITEM_ID + 203,
        classification=ItemClassification.progression,
        tier_ids=[0x0f],   # display: Lantern; also grants Magical Flame (0x10)
    ),
    "Gears": WL3ItemData(
        ap_id=BASE_ITEM_ID + 204,
        classification=ItemClassification.progression,
        tier_ids=[0x12],   # display: Gear 1; also grants Gear 2 (0x13)
    ),
    "Blue Book & Magic Wand": WL3ItemData(
        ap_id=BASE_ITEM_ID + 205,
        classification=ItemClassification.progression,
        tier_ids=[0x17],   # display: Blue Book; also grants Magic Wand (0x1c)
    ),
    "Trident & Yellow Book": WL3ItemData(
        ap_id=BASE_ITEM_ID + 206,
        classification=ItemClassification.progression,
        tier_ids=[0x1a],   # display: Trident; also grants Yellow Book (0x19)
    ),
    "Skull Ring": WL3ItemData(
        ap_id=BASE_ITEM_ID + 207,
        classification=ItemClassification.progression,
        tier_ids=[0x1d],   # display: Skull Ring Blue; also grants Skull Ring Red (0x1e)
    ),
    "Tablets": WL3ItemData(
        ap_id=BASE_ITEM_ID + 208,
        classification=ItemClassification.progression,
        tier_ids=[0x1f],   # display: Blue Tablet; also grants Green Tablet (0x20)
    ),
    "Scroll": WL3ItemData(
        ap_id=BASE_ITEM_ID + 209,
        classification=ItemClassification.progression,
        tier_ids=[0x22],   # display: Top Half of Scroll; also grants Bottom Half (0x23)
    ),
    "Tusk Set": WL3ItemData(
        ap_id=BASE_ITEM_ID + 210,
        classification=ItemClassification.progression,
        tier_ids=[0x24],   # display: Tusk Blue; also grants Tusk Red (0x25) + Green Flower (0x26)
    ),
}

# In-level pairs — gate chests/keys within a level.
COMBINED_ITEMS_IN_LEVEL: Dict[str, WL3ItemData] = {
    "Storm Pouch": WL3ItemData(
        ap_id=BASE_ITEM_ID + 211,
        classification=ItemClassification.progression,
        tier_ids=[0x49],   # display: Pouch; also grants Eye of the Storm (0x47)
    ),
    "Chemicals": WL3ItemData(
        ap_id=BASE_ITEM_ID + 212,
        classification=ItemClassification.progression,
        tier_ids=[0x27],   # display: Blue Chemical; also grants Red Chemical (0x28)
    ),
    "Glass Eyes": WL3ItemData(
        ap_id=BASE_ITEM_ID + 213,
        classification=ItemClassification.progression,
        tier_ids=[0x43],   # display: Left Glass Eye; also grants Right Glass Eye (0x42)
    ),
    "Golden Eyes": WL3ItemData(
        ap_id=BASE_ITEM_ID + 214,
        classification=ItemClassification.progression,
        tier_ids=[0x41],   # display: Golden Left Eye; also grants Golden Right Eye (0x40)
    ),
    "Sun Medallion": WL3ItemData(
        ap_id=BASE_ITEM_ID + 215,
        classification=ItemClassification.progression,
        tier_ids=[0x45],   # display: Sun Medallion Top; also grants Sun Medallion Bottom (0x46)
    ),
    "Key Cards": WL3ItemData(
        ap_id=BASE_ITEM_ID + 216,
        classification=ItemClassification.progression,
        tier_ids=[0x33],   # display: Key Card Red; also grants Key Card Blue (0x34)
    ),
}

# Combined union (for ITEM_TABLE lookup, classification, etc.)
COMBINED_ITEMS: Dict[str, WL3ItemData] = {**COMBINED_ITEMS_OVERWORLD, **COMBINED_ITEMS_IN_LEVEL}

# Full component treasure-ID lists for each combined item.
# Source of truth for both rom.py (offline pre-grant bits at patch time) and
# client.py (live grants via COMBINED_GRANTS). Keep in sync.
COMBINED_COMPONENTS: Dict[str, List[int]] = {
    "Lantern & Magical Flame": [0x0F, 0x10],
    "Gears":                   [0x12, 0x13],
    "Blue Book & Magic Wand":  [0x17, 0x1C],
    "Trident & Yellow Book":   [0x1A, 0x19],
    "Skull Ring":              [0x1D, 0x1E],
    "Tablets":                 [0x1F, 0x20],
    "Scroll":                  [0x22, 0x23],
    "Tusk Set":                [0x24, 0x25, 0x26],
    "Storm Pouch":             [0x49, 0x47],
    "Chemicals":               [0x27, 0x28],
    "Glass Eyes":              [0x43, 0x42],
    "Golden Eyes":             [0x41, 0x40],
    "Sun Medallion":           [0x45, 0x46],
    "Key Cards":               [0x33, 0x34],
}

# Individual items absorbed by overworld combines (8 combined items replace 17 individuals).
INDIVIDUAL_OVERWORLD_NAMES: Set[str] = {
    "Lantern", "Magical Flame",
    "Gear 1", "Gear 2",
    "Blue Book", "Magic Wand",
    "Yellow Book", "Trident",
    "Skull Ring Blue", "Skull Ring Red",
    "Blue Tablet", "Green Tablet",
    "Top Half of Scroll", "Bottom Half of Scroll",
    "Tusk Blue", "Tusk Red", "Green Flower",
}

# Individual items absorbed by in-level combines (6 combined items replace 12 individuals).
INDIVIDUAL_IN_LEVEL_NAMES: Set[str] = {
    "Pouch", "Eye of the Storm",
    "Blue Chemical", "Red Chemical",
    "Left Glass Eye", "Right Glass Eye",
    "Golden Left Eye", "Golden Right Eye",
    "Sun Medallion Top", "Sun Medallion Bottom",
    "Key Card Red", "Key Card Blue",
}

# Union for backwards-compat with existing code that checks "is this replaced?"
INDIVIDUAL_MULTI_ITEM_NAMES: Set[str] = INDIVIDUAL_OVERWORLD_NAMES | INDIVIDUAL_IN_LEVEL_NAMES

# ---------------------------------------------------------------------------
# Regular (non-progressive) items — one AP item per treasure ID
# ---------------------------------------------------------------------------

_REGULAR: List[tuple] = [
    # music boxes (goal)
    (0x01, ItemClassification.progression, "Yellow Music Box"),
    (0x02, ItemClassification.progression, "Blue Music Box"),
    (0x03, ItemClassification.progression, "Green Music Box"),
    (0x04, ItemClassification.progression, "Red Music Box"),
    (0x05, ItemClassification.progression, "Gold Music Box"),

    # standalone abilities
    (0x08, ItemClassification.progression, "High Jump Boots"),
    (0x0a, ItemClassification.progression, "Garlic"),
    (0x0e, ItemClassification.progression, "Spiked Helmet"),

    # overworld event items
    (0x0f, ItemClassification.progression, "Lantern"),
    (0x10, ItemClassification.progression, "Magical Flame"),
    (0x11, ItemClassification.progression, "Torch"),
    (0x12, ItemClassification.progression, "Gear 1"),
    (0x13, ItemClassification.progression, "Gear 2"),
    (0x14, ItemClassification.progression, "Warp Compact"),
    (0x15, ItemClassification.progression, "Jar"),
    (0x16, ItemClassification.progression, "Treasure Map"),
    (0x17, ItemClassification.progression, "Blue Book"),
    (0x18, ItemClassification.progression, "Sky Key"),
    (0x19, ItemClassification.progression, "Yellow Book"),
    (0x1a, ItemClassification.progression, "Trident"),
    (0x1b, ItemClassification.progression, "Axe"),
    (0x1c, ItemClassification.progression, "Magic Wand"),
    (0x1d, ItemClassification.progression, "Skull Ring Blue"),
    (0x1e, ItemClassification.progression, "Skull Ring Red"),
    (0x1f, ItemClassification.progression, "Blue Tablet"),
    (0x20, ItemClassification.progression, "Green Tablet"),
    (0x21, ItemClassification.progression, "Ornamental Fan"),
    (0x22, ItemClassification.progression, "Top Half of Scroll"),
    (0x23, ItemClassification.progression, "Bottom Half of Scroll"),
    (0x24, ItemClassification.progression, "Tusk Blue"),
    (0x25, ItemClassification.progression, "Tusk Red"),
    (0x26, ItemClassification.progression, "Green Flower"),

    # items that open / change levels or level variants
    (0x27, ItemClassification.progression, "Blue Chemical"),
    (0x28, ItemClassification.progression, "Red Chemical"),
    (0x29, ItemClassification.progression, "Air Pump"),
    (0x2a, ItemClassification.progression, "Sapling of Growth"),
    (0x2b, ItemClassification.progression, "Night Vision Scope"),
    (0x2c, ItemClassification.progression, "Electric Fan Propeller"),
    (0x2d, ItemClassification.progression, "Rust Spray"),
    (0x2e, ItemClassification.progression, "Statue"),
    (0x2f, ItemClassification.progression, "Explosive Plunger Box"),
    (0x30, ItemClassification.progression, "Scissors"),
    (0x31, ItemClassification.progression, "Castle Brick"),
    (0x32, ItemClassification.progression, "Warp Removal Apparatus"),
    (0x33, ItemClassification.progression, "Key Card Red"),
    (0x34, ItemClassification.progression, "Key Card Blue"),
    (0x35, ItemClassification.progression, "Jackhammer"),
    (0x36, ItemClassification.progression, "Pick Axe"),
    (0x37, ItemClassification.filler,      "Rocket"),
    (0x38, ItemClassification.filler,      "Pocket Pet"),
    (0x39, ItemClassification.progression, "Mystery Handle"),
    (0x3a, ItemClassification.progression, "Demon's Blood"),
    (0x3b, ItemClassification.progression, "Gold Magic"),
    (0x3c, ItemClassification.filler,      "Fighter Mannequin"),
    (0x3d, ItemClassification.progression, "Truck Wheel"),
    (0x3e, ItemClassification.progression, "Flute"),
    (0x3f, ItemClassification.progression, "Foot of Stone"),
    (0x40, ItemClassification.progression, "Golden Right Eye"),
    (0x41, ItemClassification.progression, "Golden Left Eye"),
    (0x42, ItemClassification.progression, "Right Glass Eye"),
    (0x43, ItemClassification.progression, "Left Glass Eye"),
    (0x44, ItemClassification.progression, "Scepter"),
    (0x45, ItemClassification.progression, "Sun Medallion Top"),
    (0x46, ItemClassification.progression, "Sun Medallion Bottom"),
    (0x47, ItemClassification.progression, "Eye of the Storm"),
    (0x48, ItemClassification.progression, "Magic Seeds"),
    (0x49, ItemClassification.progression, "Pouch"),
    (0x4a, ItemClassification.progression, "Full Moon Gong"),
    (0x4b, ItemClassification.filler,      "Telephone"),
    (0x4c, ItemClassification.filler,      "Crown"),
    (0x4d, ItemClassification.useful,      "Day or Night Spell"),
    # Crests: ROM grants coins when collected (SetTreasureTransitionParam)
    (0x51, ItemClassification.filler,      "Clubs Crest (1 Coin)"),
    (0x52, ItemClassification.filler,      "Spades Crest (50 Coins)"),
    (0x53, ItemClassification.filler,      "Heart Crest (20 Coins)"),
    (0x54, ItemClassification.filler,      "Diamonds Crest (5 Coins)"),
    (0x55, ItemClassification.filler,      "Earthen Figure"),
    (0x56, ItemClassification.filler,      "Saber"),
    (0x57, ItemClassification.filler,      "Goblet"),
    (0x58, ItemClassification.filler,      "Teapot"),
    (0x59, ItemClassification.useful,      "Magnifying Glass"),
    (0x5a, ItemClassification.filler,      "UFO"),
    (0x5b, ItemClassification.filler,      "Minicar"),
    (0x5c, ItemClassification.filler,      "Locomotive"),
    (0x5d, ItemClassification.progression, "Fire Drencher"),

    # crayons
    (0x5e, ItemClassification.filler,      "Red Crayon"),
    (0x5f, ItemClassification.filler,      "Brown Crayon"),
    (0x60, ItemClassification.filler,      "Yellow Crayon"),
    (0x61, ItemClassification.filler,      "Green Crayon"),
    (0x62, ItemClassification.filler,      "Cyan Crayon"),
    (0x63, ItemClassification.filler,      "Blue Crayon"),
    (0x64, ItemClassification.filler,      "Pink Crayon"),
]

# ---------------------------------------------------------------------------
# Trap items — ap_id = BASE_ITEM_ID + 400 + trap_id
# tier_ids[0] is the ROM-side TRAP_* constant written to wPendingTrap.
# ---------------------------------------------------------------------------

TRAP_BASE_ITEM_ID = BASE_ITEM_ID + 400  # 7_770_400

TRAP_ITEMS: Dict[str, WL3ItemData] = {
    "Fire Trap": WL3ItemData(
        ap_id=TRAP_BASE_ITEM_ID + 0x01,
        classification=ItemClassification.trap,
        tier_ids=[0x01],  # TRAP_FIRE
    ),
    "Yarn Trap": WL3ItemData(
        ap_id=TRAP_BASE_ITEM_ID + 0x02,
        classification=ItemClassification.trap,
        tier_ids=[0x02],  # TRAP_YARN — Ball-O-String Wario
    ),
    "Bouncy Trap": WL3ItemData(
        ap_id=TRAP_BASE_ITEM_ID + 0x03,
        classification=ItemClassification.trap,
        tier_ids=[0x03],  # TRAP_BOUNCY
    ),
    "Electric Trap": WL3ItemData(
        ap_id=TRAP_BASE_ITEM_ID + 0x04,
        classification=ItemClassification.trap,
        tier_ids=[0x04],  # TRAP_ELECTRIC
    ),
    "Ice Skate Trap": WL3ItemData(
        ap_id=TRAP_BASE_ITEM_ID + 0x05,
        classification=ItemClassification.trap,
        tier_ids=[0x05],  # TRAP_ICE_SKATE
    ),
}

# Set of all trap AP IDs — used by _build_chest_assignments to force a
# red-gem visual instead of grabbing tier_ids[0] (which is a TRAP_* constant,
# not a real treasure ID).
TRAP_AP_IDS_SET: set = {item.ap_id for item in TRAP_ITEMS.values()}

# ---------------------------------------------------------------------------
# Transform Unlock items — player-activated abilities via Select+button combos.
# Each unlock sets one bit in wTransformUnlocks or wTransformUnlocks2.
# tier_ids[0] = byte index (0=wTransformUnlocks, 1=wTransformUnlocks2)
# tier_ids[1] = bit index (0-7)
# All are progression items — will be placed in logic by rules.py.
# ---------------------------------------------------------------------------

TRANSFORM_UNLOCK_BASE_ITEM_ID = BASE_ITEM_ID + 500  # 7_770_500

TRANSFORM_UNLOCK_ITEMS: Dict[str, WL3ItemData] = {
    "Zombie Form":          WL3ItemData(ap_id=TRANSFORM_UNLOCK_BASE_ITEM_ID + 0,  classification=ItemClassification.progression, tier_ids=[0, 0]),
    "Progressive Vampire":  WL3ItemData(ap_id=TRANSFORM_UNLOCK_BASE_ITEM_ID + 1,  classification=ItemClassification.progression, tier_ids=[0, 1, 0, 6]),  # tier 1=Vampire, tier 2=Bat (client-ordered)
    "Puffy Form":           WL3ItemData(ap_id=TRANSFORM_UNLOCK_BASE_ITEM_ID + 2,  classification=ItemClassification.progression, tier_ids=[0, 2]),
    "Flat Form":            WL3ItemData(ap_id=TRANSFORM_UNLOCK_BASE_ITEM_ID + 3,  classification=ItemClassification.progression, tier_ids=[0, 3]),
    "Invisible Form":       WL3ItemData(ap_id=TRANSFORM_UNLOCK_BASE_ITEM_ID + 4,  classification=ItemClassification.progression, tier_ids=[0, 4]),
    "Fat Form":             WL3ItemData(ap_id=TRANSFORM_UNLOCK_BASE_ITEM_ID + 5,  classification=ItemClassification.progression, tier_ids=[0, 5]),
    "Ice Skatin' Form":     WL3ItemData(ap_id=TRANSFORM_UNLOCK_BASE_ITEM_ID + 7,  classification=ItemClassification.progression, tier_ids=[0, 7]),
    "Bouncy Form":          WL3ItemData(ap_id=TRANSFORM_UNLOCK_BASE_ITEM_ID + 8,  classification=ItemClassification.progression, tier_ids=[1, 0]),
    "Yarn Form":            WL3ItemData(ap_id=TRANSFORM_UNLOCK_BASE_ITEM_ID + 9,  classification=ItemClassification.progression, tier_ids=[1, 2]),
    "Snowman Form":         WL3ItemData(ap_id=TRANSFORM_UNLOCK_BASE_ITEM_ID + 10, classification=ItemClassification.progression, tier_ids=[1, 3]),
    "Fire Form":            WL3ItemData(ap_id=TRANSFORM_UNLOCK_BASE_ITEM_ID + 11, classification=ItemClassification.progression, tier_ids=[1, 4]),
}

# Progressive Vampire: 2 copies in the pool (tier 1 = Vampire, tier 2 = Bat).
TRANSFORM_UNLOCK_PROGRESSIVE_COUNTS: Dict[str, int] = {
    "Progressive Vampire": 2,
}

TRANSFORM_UNLOCK_AP_IDS_SET: set = {item.ap_id for item in TRANSFORM_UNLOCK_ITEMS.values()}

# Treasures removed from the pool when Transformation Shuffle is ON.
# Each is "replaced" by the corresponding Form item in the pool.
TRANSFORM_SACRIFICED_TREASURES: Set[str] = {
    "Rocket",              # → Fire Form
    "Pocket Pet",          # → Fat Form
    "Fighter Mannequin",   # → Flat Form
    "Telephone",           # → Invisible Form
    "Crown",               # → Vampire Form
    "Earthen Figure",      # → Snowman Form
    "Saber",               # → Zombie Form
    "Goblet",              # → Bouncy Form
    "Teapot",              # → Yarn Form
    "UFO",                 # → Bat Form
    "Minicar",             # → Ice Skatin' Form
    "Locomotive",          # → Puffy Form
}

# Form name → in-chest display treasure ID (the sacrificed treasure's visual).
# Used by _build_chest_assignments so each Form has a unique icon.
# Progressive Vampire has 2 copies: both display as Crown (the sacrificed
# treasure for Vampire); UFO is sacrificed for the 2nd copy's pool slot.
FORM_DISPLAY_TREASURE: Dict[str, int] = {
    "Fire Form":           0x68,  # generated from user's rom
    "Fat Form":            0x6b,  # generated from user's rom
    "Flat Form":           0x70,  # generated from user's rom
    "Invisible Form":      0x6a,  # generated from user's rom
    "Progressive Vampire": 0x69,  # generated from user's rom (bat)
    "Snowman Form":        0x6c,  # generated from user's rom
    "Zombie Form":          0x67,  # generated from user's rom
    "Bat Form":            0x69,  # generated from user's rom
    "Bouncy Form":         0x6d,  # generated from user's rom
    "Yarn Form":           0x6e,  # generated from user's rom
    "Ice Skatin' Form":    0x6f,  # generated from user's rom
    "Puffy Form":          0x71,  # generated from user's rom
}

TREASURE_TABLE: Dict[str, WL3ItemData] = {
    name: WL3ItemData(
        ap_id=BASE_ITEM_ID + tid,
        classification=cls,
        tier_ids=[tid],
    )
    for tid, cls, name in _REGULAR
}

# Sanity check: progressive treasure IDs must not appear in TREASURE_TABLE
_used = {item.tier_ids[0] for item in TREASURE_TABLE.values()}
assert not (_used & _PROGRESSIVE_TREASURE_IDS), "Progressive treasure IDs must not overlap regular table"

# Combined lookup: name → data (regular + progressive + combined + traps + transform unlocks)
ITEM_TABLE: Dict[str, WL3ItemData] = {**TREASURE_TABLE, **PROGRESSIVE_ITEMS, **COMBINED_ITEMS, **TRAP_ITEMS, **TRANSFORM_UNLOCK_ITEMS}

# Reverse lookup by AP ID
ID_TO_ITEM: Dict[int, WL3ItemData] = {item.ap_id: item for item in ITEM_TABLE.values()}

# How many copies of each progressive item go in the pool
PROGRESSIVE_COUNTS: Dict[str, int] = {
    name: len(data.tier_ids) for name, data in PROGRESSIVE_ITEMS.items()
}

# Extra crest copies for default mode to fill the 3 slots freed by removing gems.
# TREASURE_TABLE already has 1 copy of each crest; these are additional copies.
CREST_DEFAULT_EXTRA_COUNTS: Dict[str, int] = {
    "Clubs Crest (1 Coin)":     1,  # 1+1 = 2 total
    "Heart Crest (20 Coins)":   1,  # 1+1 = 2 total
    "Diamonds Crest (5 Coins)": 1,  # 1+1 = 2 total
}

# Extra crest copies added when CombinedLevelUnlocks is on, to fill the 12 freed slots.
# TREASURE_TABLE already has 1 copy of each crest; these are additional copies.
# ROM grants coins for crest treasure IDs via SetTreasureTransitionParam.
CREST_EXTRA_COUNTS: Dict[str, int] = {
    "Clubs Crest (1 Coin)":     6,  # 1+6 = 7 total
    "Spades Crest (50 Coins)":  1,  # 1+1 = 2 total
    "Heart Crest (20 Coins)":   2,  # 1+2 = 3 total
    "Diamonds Crest (5 Coins)": 3,  # 1+3 = 4 total
}

# Pool sizes:
#   Default mode:  91 (TREASURE_TABLE) + 6 (progressive) + 3 (CREST_DEFAULT_EXTRA_COUNTS) = 100
#   Combined mode: 74 (TREASURE_TABLE minus 17 individual) + 8 (combined) + 6 + 12 (extra crests) = 100
_default_total = len(TREASURE_TABLE) + sum(PROGRESSIVE_COUNTS.values()) + sum(CREST_DEFAULT_EXTRA_COUNTS.values())
assert _default_total == 100, f"Default pool size is {_default_total}, expected 100"


# ---------------------------------------------------------------------------
# Key items  (one per level × color; IDs 7_770_300 – 7_770_399)
# Locked at their corresponding key locations — not placed in the item pool.
# ---------------------------------------------------------------------------

class WL3KeyItemData(NamedTuple):
    ap_id: int
    owlevel: int
    color_index: int
    level_name: str
    color_name: str


def _build_key_item_table() -> Dict[str, WL3KeyItemData]:
    from .locations import LEVEL_LIST, COLOR_NAMES
    table: Dict[str, WL3KeyItemData] = {}
    for owlevel, level_name, _region in LEVEL_LIST:
        for color_index, color_name in enumerate(COLOR_NAMES):
            name = f"{level_name} {color_name} Key"
            ap_id = KEY_BASE_ITEM_ID + (owlevel - 1) * 4 + color_index
            table[name] = WL3KeyItemData(
                ap_id=ap_id,
                owlevel=owlevel,
                color_index=color_index,
                level_name=level_name,
                color_name=color_name,
            )
    return table


KEY_ITEM_TABLE: Dict[str, WL3KeyItemData] = _build_key_item_table()


# ---------------------------------------------------------------------------
# Keyring items — one per level. Each keyring, when received, grants all 4
# keys for that level. Activated by the KeyringCount option.
# AP IDs: BASE_ITEM_ID + 700 + (owlevel - 1)
# ---------------------------------------------------------------------------

KEYRING_BASE_ITEM_ID = BASE_ITEM_ID + 700  # 7_770_700


class WL3KeyringItemData(NamedTuple):
    ap_id: int
    owlevel: int
    level_name: str


def _build_keyring_item_table() -> Dict[str, "WL3KeyringItemData"]:
    from .locations import LEVEL_LIST
    table: Dict[str, WL3KeyringItemData] = {}
    for owlevel, level_name, _region in LEVEL_LIST:
        name = f"{level_name} Keyring"
        ap_id = KEYRING_BASE_ITEM_ID + (owlevel - 1)
        table[name] = WL3KeyringItemData(
            ap_id=ap_id,
            owlevel=owlevel,
            level_name=level_name,
        )
    return table


KEYRING_ITEM_TABLE: Dict[str, WL3KeyringItemData] = _build_keyring_item_table()
