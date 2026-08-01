from typing import Dict, List, NamedTuple

BASE_LOC_ID = 7_770_300  # AP location ID = BASE_LOC_ID + (owlevel - 1) * 4 + color_index

# color_index: 0=Grey, 1=Red, 2=Green, 3=Blue
COLOR_NAMES = ["Grey", "Red", "Green", "Blue"]

# wOWLevel order matches level_constants.asm const_def ordering.
# Each entry: (wOWLevel, level_name, compass_region)
LEVEL_LIST: List[tuple] = [
    # North (N1–N6)
    (1,  "Out of the Woods",       "North"),
    (2,  "The Peaceful Village",   "North"),
    (3,  "The Vast Plain",         "North"),
    (4,  "Bank of the Wild River", "North"),
    (5,  "The Tidal Coast",        "North"),
    (6,  "Sea Turtle Rocks",       "North"),
    # West (W1–W6)
    (7,  "Desert Ruins",           "West"),
    (8,  "The Volcano's Base",     "West"),
    (9,  "The Pool of Rain",       "West"),
    (10, "A Town in Chaos",        "West"),
    (11, "Beneath the Waves",      "West"),
    (12, "The West Crater",        "West"),
    # South (S1–S6)
    (13, "The Grasslands",         "South"),
    (14, "The Big Bridge",         "South"),
    (15, "Tower of Revival",       "South"),
    (16, "The Steep Canyon",       "South"),
    (17, "Cave of Flames",         "South"),
    (18, "Above the Clouds",       "South"),
    # East (E1–E7)
    (19, "The Stagnant Swamp",     "East"),
    (20, "The Frigid Sea",         "East"),
    (21, "Castle of Illusions",    "East"),
    (22, "The Colossal Hole",      "East"),
    (23, "The Warped Void",        "East"),
    (24, "The East Crater",        "East"),
    (25, "Forest of Fear",         "East"),
]


class WL3LocationData(NamedTuple):
    ap_id: int
    owlevel: int        # wOWLevel (1–25)
    color_index: int    # 0=Grey, 1=Red, 2=Green, 3=Blue
    region: str         # "North" / "West" / "South" / "East"
    level_name: str
    color_name: str

    @property
    def loc_index(self) -> int:
        """0-based index into the 100-entry chest table: (owlevel-1)*4 + color_index."""
        return (self.owlevel - 1) * 4 + self.color_index


def _build_location_table() -> Dict[str, WL3LocationData]:
    table: Dict[str, WL3LocationData] = {}
    for owlevel, level_name, region in LEVEL_LIST:
        for color_index, color_name in enumerate(COLOR_NAMES):
            loc_name = f"{level_name} - {color_name} Chest"
            ap_id = BASE_LOC_ID + (owlevel - 1) * 4 + color_index
            table[loc_name] = WL3LocationData(
                ap_id=ap_id,
                owlevel=owlevel,
                color_index=color_index,
                region=region,
                level_name=level_name,
                color_name=color_name,
            )
    return table


LOCATION_TABLE: Dict[str, WL3LocationData] = _build_location_table()

assert len(LOCATION_TABLE) == 100, f"Expected 100 locations, got {len(LOCATION_TABLE)}"

# Reverse lookup: ap_id → location name
ID_TO_LOCATION: Dict[int, str] = {loc.ap_id: name for name, loc in LOCATION_TABLE.items()}


# ---------------------------------------------------------------------------
# Key locations  (one per level × color; IDs 7_770_400 – 7_770_499)
# ---------------------------------------------------------------------------

KEY_BASE_LOC_ID = 7_770_400  # AP location ID = KEY_BASE_LOC_ID + (owlevel-1)*4 + color_index


class WL3KeyLocationData(NamedTuple):
    ap_id: int
    owlevel: int        # wOWLevel (1–25)
    color_index: int    # 0=Grey, 1=Red, 2=Green, 3=Blue
    region: str
    level_name: str
    color_name: str


def _build_key_location_table() -> Dict[str, WL3KeyLocationData]:
    table: Dict[str, WL3KeyLocationData] = {}
    for owlevel, level_name, region in LEVEL_LIST:
        for color_index, color_name in enumerate(COLOR_NAMES):
            loc_name = f"{level_name} - {color_name} Key"
            ap_id = KEY_BASE_LOC_ID + (owlevel - 1) * 4 + color_index
            table[loc_name] = WL3KeyLocationData(
                ap_id=ap_id,
                owlevel=owlevel,
                color_index=color_index,
                region=region,
                level_name=level_name,
                color_name=color_name,
            )
    return table


KEY_LOCATION_TABLE: Dict[str, WL3KeyLocationData] = _build_key_location_table()


# ---------------------------------------------------------------------------
# Coin locations (coinsanity)
# 200 musical coins (25 levels × 8 each); AP IDs 7_770_500 – 7_770_699.
# Spawn-order index 0-7 within the level (deterministic per level visit).
# ---------------------------------------------------------------------------

COIN_BASE_LOC_ID = 7_770_500
COINS_PER_LEVEL = 8


class WL3CoinLocationData(NamedTuple):
    ap_id: int
    owlevel: int        # wOWLevel (1–25)
    coin_index: int     # 0–7 (spawn order within the level)
    region: str
    level_name: str

    @property
    def loc_index(self) -> int:
        """0-based index into the 200-entry coin space: (owlevel-1)*8 + coin_index."""
        return (self.owlevel - 1) * COINS_PER_LEVEL + self.coin_index


def _build_coin_location_table() -> Dict[str, WL3CoinLocationData]:
    table: Dict[str, WL3CoinLocationData] = {}
    for owlevel, level_name, region in LEVEL_LIST:
        for coin_index in range(COINS_PER_LEVEL):
            loc_name = f"{level_name} - Big Coin {coin_index + 1}"
            ap_id = COIN_BASE_LOC_ID + (owlevel - 1) * COINS_PER_LEVEL + coin_index
            table[loc_name] = WL3CoinLocationData(
                ap_id=ap_id,
                owlevel=owlevel,
                coin_index=coin_index,
                region=region,
                level_name=level_name,
            )
    return table


COIN_LOCATION_TABLE: Dict[str, WL3CoinLocationData] = _build_coin_location_table()
assert len(COIN_LOCATION_TABLE) == 200, f"Expected 200 coin locations, got {len(COIN_LOCATION_TABLE)}"


# ---------------------------------------------------------------------------
# Boss defeat locations — one check per boss, fires when the boss dies.
# IDs 7_770_700 – 7_770_709. Boss order intentionally matches
# BOSS_CHEST_LOCATIONS in __init__.py so the boss_index below == index into
# wBossDefeatedFlags (ROM-side per-bit tracking).
# ---------------------------------------------------------------------------

BOSS_DEFEAT_BASE_LOC_ID = 7_770_700


class WL3BossDefeatLocationData(NamedTuple):
    ap_id: int
    boss_index: int      # 0-9, matches wBossDefeatedFlags bit index
    owlevel: int
    region: str
    level_name: str
    boss_name: str


# (boss_index, boss_name, owlevel) — owlevel/region come from LEVEL_LIST.
# Order MUST match wBossDefeatedFlags bit index in the ROM.
_BOSSES = [
    (0, "Wormwould",  13, "The Grasslands"),        # Grasslands boss
    (1, "Shoot",      10, "A Town in Chaos"),       # ATiC boss
    (2, "Scowler",     6, "Sea Turtle Rocks"),      # Sea Turtle Rocks boss
    (3, "Jamano",     19, "The Stagnant Swamp"),    # Stagnant Swamp (green chest boss)
    (4, "Anonster",    1, "Out of the Woods"),      # Out of the Woods boss
    (5, "Wolfenboss",  9, "The Pool of Rain"),      # Pool of Rain boss
    (6, "Pesce",       4, "Bank of the Wild River"),# BotWR boss
    (7, "Muddee",     19, "The Stagnant Swamp"),    # Stagnant Swamp (red chest boss)
    (8, "Doll Boy",    8, "The Volcano's Base"),    # Volcano's Base boss
    (9, "Yellow Belly", 7, "Desert Ruins"),         # Desert Ruins boss
]


def _build_boss_defeat_location_table() -> Dict[str, WL3BossDefeatLocationData]:
    table: Dict[str, WL3BossDefeatLocationData] = {}
    level_region = {name: region for _, name, region in LEVEL_LIST}
    for boss_index, boss_name, owlevel, level_name in _BOSSES:
        loc_name = f"{boss_name} - Defeated"
        table[loc_name] = WL3BossDefeatLocationData(
            ap_id=BOSS_DEFEAT_BASE_LOC_ID + boss_index,
            boss_index=boss_index,
            owlevel=owlevel,
            region=level_region[level_name],
            level_name=level_name,
            boss_name=boss_name,
        )
    return table


BOSS_DEFEAT_LOCATION_TABLE: Dict[str, WL3BossDefeatLocationData] = _build_boss_defeat_location_table()
assert len(BOSS_DEFEAT_LOCATION_TABLE) == 10, \
    f"Expected 10 boss defeat locations, got {len(BOSS_DEFEAT_LOCATION_TABLE)}"
