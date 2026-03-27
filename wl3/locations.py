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
