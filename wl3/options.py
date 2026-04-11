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

class DifficultyOptions(Choice):
    """Sets whether harder tricks and knowledge checks are necessary in logic.
    Standard: The logic assumes no extra knowledge besides what is used to beat the vanilla game.
    Knowledge Checks: The logic assumes the player will know basic shortcuts like breaking hidden blocks in walls.
    Hard Tricks: The logic assumes that the player will both know knowledge checks and also be able to do more difficult tricks, like jumping off of a thrown enemy in midair.
    """
    display_name = "Difficulty Options"
    option_standard = 0
    option_knowledge_checks = 1
    option_hard_tricks = 2
    default = 0


class MinorGlitches(Toggle):
    """Sets whether minor glitches may be necessary in logic."""
    display_name = "Minor Glitches"
    default = 0


class StartWithAxe(Toggle):
    """Start with the Axe, immediately unlocking The Peaceful Village and The Vast Plain."""
    display_name = "Start with Axe"
    default = 1


class RandomLevelStarts(Range):
    """Start with this many additional randomly chosen level unlock items beyond Out of the Woods.
    0: off (default)
    1-10: that many random level unlock groups are granted at the start.
    Stacks with Start with Axe (Axe is never included in the random pool).
    """
    display_name = "Random Level Starts"
    range_start = 0
    range_end   = 8
    default     = 0


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


class IHateGolf(Toggle):
    """Automatically win the golf mini-game as soon as it starts.
    The hole is immediately cleared without having to play.
    Does not work correctly with the Golf Building"""
    display_name = "I Hate Golf"
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


class EnemyPaletteShuffle(Toggle):
    """Randomize enemy sprite palettes."""
    display_name = "Enemy Palette Shuffle"
    default = 0


class LevelBGPaletteShuffle(Choice):
    """Randomize level/room background (BG) palettes.
    Off: no changes
    Simple: Changes palettes slightly less aggressively
    Full: Fully randomizes background palettes without restrictions
    """
    display_name = "Level/Room BG Palette Shuffle"
    option_off = 0
    option_simple = 1
    option_full = 2
    default = 0


class WarioOverallsShuffle(Toggle):
    """Randomize Wario's overalls/outline color. (This will affect some other in-game colors)"""
    display_name = "Wario Overalls Shuffle"
    default = 0

class WarioShirtShuffle(Toggle):
    """Randomize Wario's shirt/highlight color. (This affects all the white of Wario, including his hat and eyes)"""
    display_name = "Wario Shirt Shuffle"
    default = 0



class CombinedLevelUnlocks(Toggle):
    """With this on, combine multi-item level unlocks into single item unlocks.
    (Blue Tablet and Green Tablet turn into "Tablets")
    This helps create seed variety and allows for more flexible item placement.
    With this off, pre-fill will place early level unlocks in your own game to guarantee progression.
    """
    display_name = "Combined Level Unlocks"
    default = 0


class KeyShuffle(Choice):
    """Controls how the 100 level keys (4 per level × 25 levels) are handled.
    Vanilla: Each key location is vanilla
    Full: Keys and treasures are shuffled together across all 200 locations. (This adds 100 checks)
    """
    display_name = "Key Shuffle"
    option_vanilla = 0
    option_full = 2
    default = 0


# ---------------------------------------------------------------------------
# Quality of Life
# ---------------------------------------------------------------------------

class StartWithMagnifyingGlass(Toggle):
    """Start with the Magnifying Glass, which shows what treasures/chests have been collected
    in the overworld map (Press B while hovering a level)."""
    display_name = "Start with Magnifying Glass"
    default = 1


class NonStopChests(Toggle):
    """Stay in the level after opening a treasure chest instead of exiting to
    the overworld. The treasure is still marked collected and saved. Music box
    chests still exit to play the music-box ceremony."""
    display_name = "Non-Stop Chests"
    default = 0


class TrapFill(Range):
    """Percentage of filler items replaced with traps (currently: Fire Trap).
    When a trap is received, Wario is set on fire the next safe frame.
    0 = no traps (default), 100 = every filler item is a trap.
    """
    display_name = "Trap Fill %"
    range_start = 0
    range_end   = 100
    default     = 0


class ReduceFlashing(Toggle):
    """Disables flashing/blinking background palette cycling in certain rooms
    (e.g. underground areas, Warped Void). Recommended for photosensitivity.
    This option is automatically on if any palette shuffle is active, since palette 
    cycling can be very visually jarring when combined with random palettes."""
    display_name = "Reduce Flashing"
    default = 0


@dataclass
class WL3Options(PerGameCommonOptions):
    # Logic Options
    difficulty:                   DifficultyOptions
    minor_glitches:               MinorGlitches
    # starting_area:              StartingArea
    start_with_axe:               StartWithAxe
    random_level_starts:          RandomLevelStarts
    combined_level_unlocks:       CombinedLevelUnlocks
    key_shuffle:                  KeyShuffle
    music_boxes_required:         MusicBoxesRequired
    music_box_shuffle:            MusicBoxShuffle
    # QoL
    golf_price:                   GolfPrice
    golf_building:                GolfBuilding
    i_hate_golf:                  IHateGolf
    start_with_magnifying_glass:  StartWithMagnifyingGlass
    reduce_flashing:              ReduceFlashing
    non_stop_chests:              NonStopChests
    trap_fill:                    TrapFill
    # Cosmetics
    music_shuffle:                MusicShuffle
    enemy_palette_shuffle:        EnemyPaletteShuffle
    level_bg_palette_shuffle:     LevelBGPaletteShuffle
    wario_overalls_shuffle:       WarioOverallsShuffle
    wario_shirt_shuffle:          WarioShirtShuffle

