from dataclasses import dataclass
from Options import Toggle, Choice, Range, PerGameCommonOptions


# class StartingArea(Choice):
#     """Which compass area Wario starts in.
#     North is the default starting area and always has items accessible.
#     Changing this requires the corresponding area-unlock items to be in logic.
#     """
#     display_name = "Starting Area"
#     option_north = 0
#     option_west  = 1
#     option_south = 2
#     option_east  = 3
#     default = 0

class StartWithAxe(Toggle):
    """Start Wario with the Axe, which unlocks 3 additional early locations
    (Out of the Woods has axe-gated locations right at the start).
    """
    display_name = "Start with Axe"
    default = 1


class MusicBoxesRequired(Range):
    """How many of the 5 music boxes Wario must collect before
    the Temple opens and the final boss becomes accessible.
    Set to 0 to make the Temple always open.
    """
    display_name = "Music Boxes Required"
    range_start = 0
    range_end   = 5
    default     = 5


class MusicBoxShuffle(Choice):
    """Controls where the 5 music boxes can be placed.
    Any Boss: music boxes can be placed at any of the 10 boss chest locations.
    Anywhere: music boxes can be placed anywhere in the multiworld (default).
    """
    display_name = "Music Box Shuffle"
    option_any_boss = 0
    option_anywhere = 1
    default = 1


class GolfPrice(Choice):
    """Sets the coin cost for the mini-games (golf). 
    Vanilla: Tier-based cost (10 / 30 / 50 coins).
    Free: FREE GOLF!
    Cheap: Reduced tier-based cost (5 / 10 / 15 coins).
    The Golf Building courses are always free regardless of this setting.
    """
    display_name = "Golf Price"
    option_vanilla = 0
    option_free    = 1
    option_cheap   = 2
    default = 1


class GolfBuilding(Choice):
    """Controls whether the Golf Building is always open or requires crayons to open.
    Open: Golf Building can always be entered (always free to play).
    Vanilla: the Golf Building requires all 7 crayons to open (vanilla behavior).
    """
    display_name = "Golf Building"
    option_open    = 0
    option_vanilla = 1
    default = 0


class MusicShuffle(Choice):
    """Randomize the background music played in each level.
    Split: Day and night music are shuffled within their own groups (day with day, night with night).
    Full:  All music tracks are fully randomized regardless of day/night.
    """
    display_name = "Music Shuffle"
    option_vanilla = 0
    option_split   = 1
    option_full    = 2
    default = 0


class PaletteShuffle(Choice):
    """Randomize colors in the game.
    Enemies: randomizes enemy sprite palettes.
    Wario: randomizes Wario's outline/overalls color.
    Both: randomizes enemies and Wario.
    """
    display_name = "Palette Shuffle"
    option_off      = 0
    option_enemies  = 1
    option_wario    = 2
    option_both     = 3
    default = 0


class CombinedLevelUnlocks(Toggle):
    """With this on, combine multi-item level unlocks into single item unlocks.
    (Blue Tablet and Green Tablet turn into "Tablets")
    This helps create seed variety and allows for more flexible item placement.
    With this off, pre-fill will place early level unlocks in your own game to guarantee progression.
    """
    display_name = "Combined Level Unlocks"
    default = 0


# ---------------------------------------------------------------------------
# Quality of Life
# ---------------------------------------------------------------------------

class StartWithMagnifyingGlass(Toggle):
    """Start with the Magnifying Glass, which shows what treasures/chests have been collected
    in the overworld map (Press B while hovering a level)."""
    display_name = "Start with Magnifying Glass"
    default = 0


@dataclass
class WL3Options(PerGameCommonOptions):
    # starting_area:          StartingArea
    start_with_axe:               StartWithAxe
    combined_level_unlocks:       CombinedLevelUnlocks
    music_boxes_required:         MusicBoxesRequired
    music_box_shuffle:            MusicBoxShuffle
    # QoL
    golf_price:                   GolfPrice
    golf_building:                GolfBuilding
    start_with_magnifying_glass:  StartWithMagnifyingGlass
    # Cosmetics
    music_shuffle:                MusicShuffle
    palette_shuffle:              PaletteShuffle

