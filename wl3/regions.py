"""
Region / connection graph for Wario Land 3.

Open-world model: all four compass maps are always navigable.
Level access is gated purely by per-level item rules (see rules.py).
The four regions exist only as location groupings for spoiler/hint purposes.
"""

from typing import TYPE_CHECKING, Dict

from BaseClasses import Location, Region

from .locations import KEY_LOCATION_TABLE, LOCATION_TABLE

if TYPE_CHECKING:
    from . import WL3World

NORTH = "North"
WEST  = "West"
SOUTH = "South"
EAST  = "East"


def create_regions(world: "WL3World") -> Dict[str, Region]:
    """Create all regions, attach chest locations, and wire connections.
    All regions are unconditionally reachable from Menu.
    Per-level access rules are applied in set_rules().
    """
    player     = world.player
    multiworld = world.multiworld

    menu  = Region("Menu", player, multiworld)
    north = Region(NORTH,  player, multiworld)
    west  = Region(WEST,   player, multiworld)
    south = Region(SOUTH,  player, multiworld)
    east  = Region(EAST,   player, multiworld)

    all_regions = {
        "Menu": menu,
        NORTH:  north,
        WEST:   west,
        SOUTH:  south,
        EAST:   east,
    }

    # Attach each chest location to its compass region
    for loc_name, loc_data in LOCATION_TABLE.items():
        region = all_regions[loc_data.region]
        loc = Location(player, loc_name, loc_data.ap_id, region)
        region.locations.append(loc)

    # Attach each key location to its compass region (no rules — vanilla always accessible)
    for loc_name, loc_data in KEY_LOCATION_TABLE.items():
        region = all_regions[loc_data.region]
        loc = Location(player, loc_name, loc_data.ap_id, region)
        region.locations.append(loc)

    # All regions unconditionally reachable — level entry gated by item rules
    menu.connect(north)
    menu.connect(west)
    menu.connect(south)
    menu.connect(east)

    return all_regions
