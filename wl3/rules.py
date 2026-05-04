"""
Access rules for Wario Land 3.

Level unlock table:
  Axe                              → N2, N3
  Blue Music Box                   → N4, N5
  Garlic                           → N6
  Blue Tablet + Green Tablet       → W1
  Top Half of Scroll + Bottom Half → W2
  Jar                              → W3, W4
  Red Music Box                    → W5
  Tusk Blue+Red + Green Flower     → W6, E4
  Gear 1 + Gear 2                  → S1
  Yellow Music Box                 → S2
  Skull Ring Red + Blue            → S3
  Trident + Yellow Book            → S4
  Green Music Box                  → S5
  Sky Key                          → S6
  Ornamental Fan                   → E1
  Blue Book + Magic Wand           → E2
  Lantern + Magical Flame          → E3
  Warp Compact                     → E5
  Treasure Map                     → E6
  Torch                            → E7
"""

from typing import TYPE_CHECKING, List

from BaseClasses import CollectionState, LocationProgressType

from .locations import COIN_LOCATION_TABLE, COLOR_NAMES, KEY_LOCATION_TABLE, LOCATION_TABLE
from .options import (KeyShuffle, DifficultyOptions, MinorGlitches)

if TYPE_CHECKING:
    from . import WL3World

MUSIC_BOXES = [
    "Yellow Music Box",
    "Blue Music Box",
    "Green Music Box",
    "Red Music Box",
    "Gold Music Box",
]

# ---------------------------------------------------------------------------
# Helper predicates
# ---------------------------------------------------------------------------

def has(item: str, state: CollectionState, player: int) -> bool:
    return state.has(item, player)


def has_all(items: List[str], state: CollectionState, player: int) -> bool:
    return all(state.has(i, player) for i in items)


def has_overalls_1(state, player): return state.count("Progressive Overalls", player) >= 1
def has_overalls_2(state, player): return state.count("Progressive Overalls", player) >= 2
def has_grab_1(state, player):     return state.count("Progressive Grab", player) >= 1
def has_grab_2(state, player):     return state.count("Progressive Grab", player) >= 2
def has_flippers_1(state, player): return state.count("Progressive Flippers", player) >= 1
def has_flippers_2(state, player): return state.count("Progressive Flippers", player) >= 2
def has_vampire_1(state, player): return state.count("Progressive Vampire", player) >= 1
def has_vampire_2(state, player): return state.count("Progressive Vampire", player) >= 2


# ---------------------------------------------------------------------------
# Level unlock predicates
# ---------------------------------------------------------------------------

def unlock_n2_n3(state, player):  return has("Axe", state, player)
def unlock_n4_n5(state, player):  return has("Blue Music Box", state, player)
def unlock_n6(state, player):     return has("Garlic", state, player)
def unlock_w1(state, player):     return has("Blue Tablet", state, player) and has("Green Tablet", state, player)
def unlock_w1c(state, player):    return has("Tablets", state, player)
def unlock_w2(state, player):     return has("Top Half of Scroll", state, player) and has("Bottom Half of Scroll", state, player)
def unlock_w2c(state, player):    return has("Scroll", state, player)
def unlock_w3_w4(state, player):  return has("Jar", state, player)
def unlock_w5(state, player):     return has("Red Music Box", state, player)
def unlock_w6_e4(state, player):  return has("Tusk Blue", state, player) and has("Tusk Red", state, player) and has("Green Flower", state, player)
def unlock_w6_e4c(state, player): return has("Tusk Set", state, player)
def unlock_s1(state, player):     return has("Gear 1", state, player) and has("Gear 2", state, player)
def unlock_s1c(state, player):    return has("Gears", state, player)
def unlock_s2(state, player):     return has("Yellow Music Box", state, player)
def unlock_s3(state, player):     return has("Skull Ring Red", state, player) and has("Skull Ring Blue", state, player)
def unlock_s3c(state, player):    return has("Skull Ring", state, player)
def unlock_s4(state, player):     return has("Trident", state, player) and has("Yellow Book", state, player)
def unlock_s4c(state, player):    return has("Trident & Yellow Book", state, player)
def unlock_s5(state, player):     return has("Green Music Box", state, player)
def unlock_s6(state, player):     return has("Sky Key", state, player)
def unlock_e1(state, player):     return has("Ornamental Fan", state, player)
def unlock_e2(state, player):     return has("Blue Book", state, player) and has("Magic Wand", state, player)
def unlock_e2c(state, player):    return has("Blue Book & Magic Wand", state, player)
def unlock_e3(state, player):     return has("Lantern", state, player) and has("Magical Flame", state, player)
def unlock_e3c(state, player):    return has("Lantern & Magical Flame", state, player)
def unlock_e5(state, player):     return has("Warp Compact", state, player)
def unlock_e6(state, player):     return has("Treasure Map", state, player)
def unlock_e7(state, player):     return has("Torch", state, player)


# Map level name → level unlock predicate (None = always accessible)
LEVEL_RULES: dict = {
    "Out of the Woods":       None,
    "The Peaceful Village":   unlock_n2_n3,
    "The Vast Plain":         unlock_n2_n3,
    "Bank of the Wild River": unlock_n4_n5,
    "The Tidal Coast":        unlock_n4_n5,
    "Sea Turtle Rocks":       unlock_n6,
    "Desert Ruins":           unlock_w1,
    "The Volcano's Base":     unlock_w2,
    "The Pool of Rain":       unlock_w3_w4,
    "A Town in Chaos":        unlock_w3_w4,
    "Beneath the Waves":      unlock_w5,
    "The West Crater":        unlock_w6_e4,
    "The Grasslands":         unlock_s1,
    "The Big Bridge":         unlock_s2,
    "Tower of Revival":       unlock_s3,
    "The Steep Canyon":       unlock_s4,
    "Cave of Flames":         unlock_s5,
    "Above the Clouds":       unlock_s6,
    "The Stagnant Swamp":     unlock_e1,
    "The Frigid Sea":         unlock_e2,
    "Castle of Illusions":    unlock_e3,
    "The Colossal Hole":      unlock_w6_e4,
    "The Warped Void":        unlock_e5,
    "The East Crater":        unlock_e6,
    "Forest of Fear":         unlock_e7,
}

# ---------------------------------------------------------------------------
# Per-chest access rules (additional requirements beyond the level unlock)
# Each entry: [grey_rule, red_rule, green_rule, blue_rule]
# None = no additional requirement for that chest color
# ---------------------------------------------------------------------------

def _c(*fns):
    def rule(s, p):
        return all(f(s, p) for f in fns)
    return rule

def _o(*fns):
    def rule(s, p):
        return any(f(s, p) for f in fns)
    return rule

def _has(item):
    return lambda s, p: has(item, s, p)

# In-level change rule helpers
has_storm_pouch  = _o(_has("Storm Pouch"), _c(_has("Pouch"), _has("Eye of the Storm")))
has_chemicals    = _o(_has("Chemicals"), _c(_has("Blue Chemical"), _has("Red Chemical")))
has_glass_eyes   = _o(_has("Glass Eyes"), _c(_has("Left Glass Eye"), _has("Right Glass Eye")))
has_golden_eyes  = _o(_has("Golden Eyes"), _c(_has("Golden Left Eye"), _has("Golden Right Eye")))
has_sun_medallion = _o(_has("Sun Medallion"), _c(_has("Sun Medallion Top"), _has("Sun Medallion Bottom")))
has_key_cards    = _o(_has("Key Cards"), _c(_has("Key Card Red"), _has("Key Card Blue")))

# Player ability rule helpers
can_pound_cracked_blocks = _o(has_overalls_1, _has("Fat Form"), _has("Snowman Form"))
can_pound_solid_blocks = _o(has_overalls_2, _has("Fat Form"))
can_pound_large_solid_blocks = _o(_c(has_overalls_2, _has("Garlic")), _has("Fat Form"))
can_jump_high = _o(_has("Puffy Form"), _has("Bouncy Form"), _has("High Jump Boots"), has_vampire_2)
can_fly = _o(has_vampire_2, _has("Puffy Form"))
can_shake_screen = _o(has_overalls_2, _has("Fat Form"), _has("Snowman Form"))
can_pass_through_fire = _o(has_vampire_1, _has("Zombie Form"), _has("Fire Form"), _has("Fire Drencher"))
can_bounce = _o(has_vampire_2, _has("Bouncy Form"), _has("Puffy Form"))
can_kill_frogs = _o(has_vampire_1, _has("Fire Form"), _has("Fat Form"), _has("Zombie Form"), _has("Ice Skatin' Form"))
can_sink_in_water = _o(_has("Fat Form"), _has("Flat Form"))
can_pass_spikes = _has("Zombie Form") # TODO: test which forms work

CHEST_RULES: dict = {
    "Out of the Woods": [
        None,                                                                        # grey
        can_pound_cracked_blocks,                                                    # red
        _o(_c(has_storm_pouch, _has("High Jump Boots")), can_fly),                   # green
        _c(_has("Gold Magic"), has_grab_1, has_overalls_1, can_jump_high),           # blue
    ],
    "The Peaceful Village": [
        None,                                                                        # grey
        _o(_has("Flute"), can_jump_high),                                            # red
        _c(_o(_has("Flute"), can_jump_high), 
           _o(can_pound_cracked_blocks, _has("Zombie Form"))),                       # green
        can_pound_large_solid_blocks,                                                # blue
    ],
    "The Vast Plain": [
        None,                                                                        # grey
        can_pound_cracked_blocks,                                                    # red
        _o(_has("Magic Seeds"), can_fly),                                            # green
        has_chemicals,                                                               # blue
    ],
    "Bank of the Wild River": [
        None,                                                                        # grey
        _has("Garlic"),                                                              # red
        has_flippers_2,                                                              # green
        _c(_o(_has("Air Pump"), can_fly), _o(has_grab_1, _has("Fire Form"))),        # blue
    ],
    "The Tidal Coast": [
        None,                                                                        # grey
        _c(has_flippers_1, has_grab_1),                                              # red
        _o(_has("Statue"), can_bounce),                                              # green
        _c(_has("Sapling of Growth"), has_flippers_1, _has("Garlic")),               # blue
    ],
    "Sea Turtle Rocks": [
        _c(_has("Spiked Helmet"), has_flippers_1, can_pound_cracked_blocks),         # grey
        _c(_has("Scepter"), has_flippers_1, can_pound_cracked_blocks),               # red
        _o(can_pound_solid_blocks),                                                  # green
        _c(_has("Night Vision Scope"), _o(can_pound_solid_blocks), can_jump_high),   # blue
    ],
    "Desert Ruins": [
        None,                                                                        # grey
        None,                                                                        # red
        _has("Spiked Helmet"),                                                       # green
        _c(_o(can_pound_solid_blocks, _has("Zombie Form")), 
           _o(has_grab_1, can_bounce), has_overalls_1)                               # blue
    ],
    "The Volcano's Base": [
        None,                                                                        # grey
        _o(_has("Truck Wheel"), can_fly),                                            # red
        _o(_c(_has("Flute"), _has("Truck Wheel")), can_fly),                         # green
        _has("Foot of Stone"),                                                       # blue
    ],
    "The Pool of Rain": [
        _o(has_overalls_1, can_bounce),                                              # grey
        _has("Magic Seeds"),                                                         # red
        has_flippers_1,                                                              # green
        _c(_has("Air Pump"), has_flippers_1),                                        # blue
    ],
    "A Town in Chaos": [
        None,                                                                        # grey
        _o(_has("Spiked Helmet"), can_bounce),                                       # red
        _c(_o(has_grab_2, can_kill_frogs), 
           _o(_c(can_shake_screen, _has("High Jump Boots"), has_grab_1),
              _c(_has("Bouncy Form"), has_grab_1), can_fly)),                        # green
        None,                                                                        # blue
    ],
    "Beneath the Waves": [
        has_flippers_1,                                                              # grey
        _c(has_flippers_1, _o(_has("High Jump Boots"), can_fly)),                    # red
        _c(has_flippers_1, _o(has_grab_1, _has("Yarn Form")), 
           _o(_has("High Jump Boots"), can_fly)),                                    # green
        _c(has_flippers_1, _o(has_grab_1, _has("Fat Form")), 
           _o(_has("High Jump Boots"), can_fly)),                                    # blue
    ],
    "The West Crater": [
        _o(can_pound_cracked_blocks, _has("Yarn Form")),                             # grey
        _o(_c(has_overalls_2, _has("Garlic")), _has("Fat Form")),                    # red
        _o(_c(can_pass_through_fire, can_jump_high),can_fly),                        # green
        _has("Rust Spray"),                                                          # blue
    ],
    "The Grasslands": [
        _o(has_overalls_1, can_fly),                                                 # grey
        _c(_has("Magic Seeds"), _o(has_overalls_1, _has("Zombie Form"))),            # red
        _c(_o(_has("Flute"), can_fly), has_flippers_1),                              # green
        can_jump_high,                                                               # blue
    ],
    "The Big Bridge": [
        None,                                                                        # grey
        _c(has_flippers_1, _o(can_pound_cracked_blocks, _has("Zombie Form"))),       # red
        has_grab_1,                                                                  # green
        _c(_has("Scepter"), has_flippers_1, _o(_c(_has("Garlic"), _has("Spiked Helmet")),
                                               _has("Puffy Form"))),                 # blue
    ],
    "Tower of Revival": [
        None,                                                                        # grey
        has_glass_eyes,                                                              # red
        _has("Statue"),                                                              # green
        _c(has_golden_eyes, _has("Garlic"), has_grab_2, _has("Spiked Helmet"),
           _has("Statue"), _has("High Jump Boots")),                                 # blue
    ],
    "The Steep Canyon": [
        None,                                                                        # grey
        _has("Foot of Stone"),                                                       # red
        _c(_has("Foot of Stone"), has_flippers_2, _o(can_shake_screen, can_fly)),    # green
        _c(_has("Rust Spray"), _o(can_pound_cracked_blocks, _has("Zombie Form"))),   # blue
    ],
    "Cave of Flames": [
        None,                                                                        # grey
        _o(can_bounce, _c(_has("High Jump Boots"), _o(_c(has_grab_1, can_shake_screen),
                                                      _has("Fat Form")))),           # red
        _has("Explosive Plunger Box"),                                               # green
        _c(_has("Rust Spray"), can_pound_cracked_blocks, 
           _o(_c(has_grab_1, _has("High Jump Boots")), can_bounce)),                 # blue
    ],
    "Above the Clouds": [
        None,                                                                        # grey
        _o(_c(_has("High Jump Boots"), has_grab_1, _has("Spiked Helmet")),can_bounce),# red
        _c(_has("Scissors"), can_jump_high),                                         # green
        _c(_has("Scissors"), _has("Full Moon Gong"), _has("High Jump Boots"),
           has_overalls_2, has_grab_1),                                              # blue
    ],
    "The Stagnant Swamp": [
        None,                                                                        # grey
        _c(_has("Foot of Stone"), _o(has_overalls_1, has_vampire_2, 
                                     _c(has_flippers_2, _has("High Jump Boots")))),  # red
        _c(_has("Foot of Stone"), can_jump_high),                                    # green
        _o(_has("Explosive Plunger Box"), can_fly),                                  # blue
    ],
    "The Frigid Sea": [
        None,                                                                        # grey
        _o(has_grab_1, can_fly),                                                     # red
        _c(_has("Scepter"), has_flippers_1),                                         # green
        _o(has_sun_medallion, has_flippers_2),                                       # blue
    ],
    "Castle of Illusions": [
        can_pound_cracked_blocks,                                                    # grey
        _o(has_grab_1, can_fly),                                                     # red
        _o(has_grab_1, can_fly),                                                     # green
        _o(has_grab_1, can_fly),                                                     # blue
    ],
    "The Colossal Hole": [
        None,                                                                        # grey
        _has("Garlic"),                                                              # red
        _o(has_sun_medallion, can_jump_high),                                        # green
        _c(_has("Explosive Plunger Box"), can_jump_high),                            # blue
    ],
    "The Warped Void": [
        None,                                                                        # grey
        _has("Warp Removal Apparatus"),                                              # red
        _c(_has("Warp Removal Apparatus"), _o(has_grab_1, can_fly)),                 # green
        _o(_c(has_key_cards, has_grab_1),
           _c(_has("Warp Removal Apparatus"), can_fly)),                             # blue
    ],
    "The East Crater": [
        _o(has_grab_1, _has("Zombie Form")),                                         # grey
        _c(can_pass_through_fire, _o(_c(has_grab_1, can_pound_cracked_blocks), _has("Fire Form")),
           _o(_has("Zombie Form"), has_grab_1)),                                     # red
        _c(_o(_has("Jackhammer"), can_fly), has_grab_1),                             # green
        _c(_has("Pick Axe"), has_grab_1, can_jump_high),                             # blue
    ],
    "Forest of Fear": [
        None,                                                                        # grey
        _c(_has("Mystery Handle"), _o(has_grab_2, can_bounce)),                      # red
        _c(_has("Mystery Handle"), has_grab_1),                                      # green
        _o(_has("Demon's Blood"), _has("Zombie Form"), has_vampire_2),               # blue
    ],
}


# ---------------------------------------------------------------------------
# Per-key access rules (additional requirements beyond the level unlock)
# Each entry: [grey_rule, red_rule, green_rule, blue_rule]
# ---------------------------------------------------------------------------

KEY_RULES: dict = {
    "Out of the Woods": [
        None,                                                                        # grey
        can_pound_cracked_blocks,                                                    # red
        can_jump_high,                                                               # green
        _c(_has("Gold Magic"), can_jump_high),                                       # blue
    ],
    "The Peaceful Village": [
        None,                                                                        # grey
        _o(_has("Flute"), can_jump_high, can_pound_solid_blocks),                    # red
        _o(_has("Flute"), can_jump_high),                                            # green
        can_pound_large_solid_blocks,                                                # blue
    ],
    "The Vast Plain": [
        None,                                                                        # grey
        can_pound_cracked_blocks,                                                    # red
        _o(_has("Magic Seeds"), can_fly),                                            # green
        has_chemicals,                                                               # blue
    ],
    "Bank of the Wild River": [
        None,                                                                        # grey
        _has("Garlic"),                                                              # red
        has_flippers_2,                                                              # green
        _o(_has("Air Pump"), can_fly),                                               # blue
    ],
    "The Tidal Coast": [
        None,                                                                        # grey
        _c(has_grab_1, _o(_has("Zombie Form"), has_flippers_2, 
                          _c(has_flippers_1, _has("Spiked Helmet")))),               # red
        _has("Garlic"),                                                              # green
        _c(has_flippers_1, _has("Garlic"), _has("Sapling of Growth")),               # blue
    ],
    "Sea Turtle Rocks": [
        _c(_has("Spiked Helmet"), can_pound_cracked_blocks, has_flippers_1),         # grey
        _c(_has("Scepter"), can_pound_cracked_blocks, has_flippers_1),               # red
        can_pound_solid_blocks,                                                      # green
        _c(can_pound_solid_blocks, _has("Night Vision Scope"), can_jump_high),       # blue
    ],
    "Desert Ruins": [
        None,                                                                        # grey
        None,                                                                        # red
        _c(_has("Spiked Helmet"), can_pound_cracked_blocks),                         # green
        _o(can_pound_solid_blocks, _has("Zombie Form")),                             # blue
    ],
    "The Volcano's Base": [
        None,                                                                        # grey
        _o(_has("Truck Wheel"), has_vampire_2),                                      # red
        _c(_o(_has("Truck Wheel"), can_fly), has_flippers_1),                        # green
        _c(_has("Foot of Stone"), _o(has_flippers_2, _c(has_flippers_1, 
                                                        _has("Spiked Helmet")))),    # blue
    ],
    "The Pool of Rain": [
        _o(has_overalls_1, can_bounce),                                              # grey
        _has("Magic Seeds"),                                                         # red
        has_flippers_1,                                                              # green
        _c(_has("Air Pump"), has_flippers_1),                                        # blue
    ],
    "A Town in Chaos": [
        None,                                                                        # grey
        None,                                                                        # red
        _c(_o(has_grab_2, can_kill_frogs), 
           _o(_c(can_shake_screen, _has("High Jump Boots")), can_bounce),has_grab_1),# green
        _o(_c(_has("Electric Fan Propeller"), has_grab_1), can_fly),                 # blue
    ],
    "Beneath the Waves": [
        _o(_has("High Jump Boots"), can_fly),                                        # grey
        _c(has_flippers_2, _has("Spiked Helmet"), has_grab_2),                       # red
        _c(has_flippers_1, _has("Sapling of Growth")),                               # green
        _c(has_flippers_1, has_chemicals),                                           # blue
    ],
    "The West Crater": [
        None,                                                                        # grey
        _c(_o(can_pound_cracked_blocks, _has("Yarn Form")), _o(has_grab_1, can_bounce)),# red
        _o(_c(can_pass_through_fire, can_jump_high), can_fly),                       # green
        _c(_has("Rust Spray"), has_grab_1),                                          # blue
    ],
    "The Grasslands": [
        None,                                                                        # grey
        None,                                                                        # red
        _o(_has("Flute"), can_fly),                                                  # green
        _o(can_jump_high),                                                           # blue
    ],
    "The Big Bridge": [
        None,                                                                        # grey
        _c(_o(can_pound_cracked_blocks, _has("Zombie Form")), has_flippers_1),       # red
        _c(has_flippers_1, has_grab_1, 
           _o(can_pound_cracked_blocks, _has("Zombie Form"))),                       # green
        _c(has_flippers_1, _o(_has("Garlic"), can_fly)),                             # blue
    ],
    "Tower of Revival": [
        None,                                                                        # grey
        _c(has_glass_eyes),                                                          # red
        _has("Statue"),                                                              # green
        _c(_has("Statue"), has_golden_eyes),                                         # blue
    ],
    "The Steep Canyon": [
        None,                                                                        # grey
        _has("Foot of Stone"),                                                       # red
        _c(_has("Foot of Stone"), has_flippers_2, 
           _o(can_shake_screen, can_fly)),                                           # green
        _c(_has("Rust Spray"), _o(can_pound_cracked_blocks, _has("Zombie Form"))),   # blue
    ],
    "Cave of Flames": [
        has_grab_1,                                                                  # grey
        can_jump_high,                                                               # red
        _has("Explosive Plunger Box"),                                               # green
        _c(_has("Rust Spray"), can_pound_cracked_blocks, 
           _o(_c(has_grab_1, _has("High Jump Boots")), can_bounce)),                 # blue
    ],
    "Above the Clouds": [
        None,                                                                        # grey
        _o(_c(_has("High Jump Boots"), has_grab_1, _has("Spiked Helmet")), can_bounce),# red
        _c(_has("Scissors"), can_jump_high),                                         # green
        _o(_c(_has("Scissors"), can_jump_high), can_fly),                            # blue
    ],
    "The Stagnant Swamp": [
        None,                                                                        # grey
        _has("Foot of Stone"),                                                       # red
        _c(_has("Foot of Stone"), _o(_c(has_grab_1, _has("High Jump Boots")), can_bounce)),# green
        _o(_has("Explosive Plunger Box"), can_fly),                                  # blue
    ],
    "The Frigid Sea": [
        None,                                                                        # grey
        _o(has_grab_1, can_fly),                                                     # red
        _c(_has("Scepter"), has_flippers_1),                                         # green
        _o(has_sun_medallion, has_flippers_2),                                       # blue
    ],
    "Castle of Illusions": [
        _o(has_grab_1, can_fly),                                                     # grey
        _o(_c(has_grab_2, _o(can_shake_screen, _has("High Jump Boots"))), can_bounce),# red
        _o(has_grab_2, can_bounce),                                                  # green
        _c(_has("Castle Brick"), can_pound_cracked_blocks, 
           _o(has_grab_1, can_fly)), # blue
    ],
    "The Colossal Hole": [
        None,                                                                        # grey
        _c(_has("Garlic"), _o(has_grab_1, _has("Zombie Form"))),                     # red
        _o(has_sun_medallion, can_jump_high),                                        # green
        _c(_has("Explosive Plunger Box"), can_jump_high),                            # blue
    ],
    "The Warped Void": [
        has_grab_1,                                                                  # grey
        _has("Warp Removal Apparatus"),                                              # red
        _c(_has("Warp Removal Apparatus"), _o(has_grab_1, can_bounce)),              # green
        _o(_c(has_key_cards, has_grab_1), _c(_has("Warp Removal Apparatus"),can_fly)),# blue
    ],
    "The East Crater": [
        _c(_o(has_grab_1, _has("Zombie Form")),
           _o(can_shake_screen, can_fly)),                                           # grey
        _c(_o(can_pass_through_fire), _o(_has("Zombie Form"), has_grab_1),
           _o(_c(has_grab_1, _o(can_pound_cracked_blocks)), _has("Zombie Form"))),   # red
        _c(has_grab_1, _o(_has("Jackhammer"), can_fly)),                             # green
        _c(_o(can_jump_high), _has("Pick Axe"), has_grab_1),                         # blue
    ],
    "Forest of Fear": [
        None,                                                                        # grey
        _c(_has("Mystery Handle"), _o(_c(has_grab_2, _has("High Jump Boots")),
                                      can_bounce)),                                  # red
        _c(_has("Mystery Handle"), has_grab_1),                                      # green
        _o(_has("Demon's Blood"), _has("Zombie Form")),                              # blue
    ],
}

# ---------------------------------------------------------------------------
# Per-coin access rules (additional requirements beyond the level unlock)
# Coins are 1-8, labeled in the Google Sheet
# ---------------------------------------------------------------------------

COIN_RULES: dict = {
    "Out of the Woods": [
        _o(_c(_has("High Jump Boots"), has_grab_1), _has("Puffy Form")),                #1
        None,                                                                           #2
        _o(can_shake_screen,can_fly),                                                   #3
        _o(has_flippers_2, _c(has_storm_pouch,_has("High Jump Boots")), can_fly),       #4
        can_jump_high,                                                                  #5
        None,                                                                           #6
        can_pound_cracked_blocks,                                                       #7
        _c(_has("Gold Magic"), _o(can_jump_high,_has("Fat Form"),_has("Zombie Form"))), #8
    ],
    "The Peaceful Village": [
        None,                                                                           #1
        _c(can_pound_large_solid_blocks,_has("Spiked Helmet")),                         #2
        None,                                                                           #3
        _c(_o(_has("Flute"),can_jump_high),has_flippers_1,
           _o(_has("Zombie Form"),can_pound_cracked_blocks)),                           #4
        _o(_has("Flute"),can_jump_high),                                                #5
        _o(can_pound_large_solid_blocks,
           _c(_o(_has("Flute"),can_jump_high),_has("Zombie Form"))),                    #6
        can_pound_large_solid_blocks,                                                   #7
        can_pound_large_solid_blocks,                                                   #8
    ],
    "The Vast Plain": [
        _o(_has("Magic Seeds"),_has("Puffy Form")),                                     #1
        None,                                                                           #2
        _o(has_chemicals, can_pass_spikes),                                             #3
        can_pound_cracked_blocks,                                                       #4
        _o(has_flippers_1,_has("Zombie Form")),                                         #5
        _o(_has("Magic Seeds"),can_fly),                                                #6
        has_chemicals,                                                                  #7
        _o(_has("Magic Seeds"),can_fly),                                                #8
    ],
    "Bank of the Wild River": [
        _o(has_flippers_1,can_fly),                                                     #1
        has_flippers_2,                                                                 #2
        has_flippers_2,                                                                 #3
        has_flippers_2,                                                                 #4
        _c(_o(_has("Air Pump"),can_fly),can_jump_high),                                 #5
        None,                                                                           #6
        _c(_has("Garlic"),has_grab_1),                                                  #7
        _o(_has("Air Pump"),can_fly),                                                   #8
    ],
    "The Tidal Coast": [
        None,                                                                           #1
        _o(_has("Garlic"),can_fly,_has("Flat Form")),                                   #2
        None,                                                                           #3
        None,                                                                           #4
        _c(has_grab_1,has_flippers_1),                                                  #5
        _c(_o(has_flippers_2,_c(has_flippers_1,_o(_has("Spiked Helmet"),_has("Zombie Form")))),
           has_grab_1),                                                                 #6
        _c(_has("Sapling of Growth"),_has("Garlic"),has_flippers_1),                    #7
        _c(_has("Sapling of Growth"),_has("Garlic"),has_flippers_1),                    #8
    ],
    "Sea Turtle Rocks": [
        _c(can_pound_cracked_blocks,_has("Spiked Helmet")),                             #1
        _c(can_pound_cracked_blocks,_has("Spiked Helmet")),                             #2
        can_pound_cracked_blocks,                                                       #3
        _c(can_pound_cracked_blocks,_has("Spiked Helmet"),has_flippers_1),              #4
        _c(can_pound_cracked_blocks,_has("Spiked Helmet"),has_flippers_1),              #5
        can_pound_solid_blocks,                                                         #6
        _c(can_pound_solid_blocks,_has("Night Vision Scope"),can_jump_high),            #7
        _c(can_pound_solid_blocks,_has("Night Vision Scope"),can_jump_high),            #8
    ],
    "Desert Ruins": [
        None,                                                                           #1
        _o(can_pound_cracked_blocks,_has("Garlic"),_has("Zombie Form")),                #2
        _c(_o(can_pound_solid_blocks, _has("Zombie Form")),
           _o(has_grab_1, can_bounce), has_overalls_1),                                 #3
        _c(_has("Spiked Helmet"),has_grab_1),                                           #4
        None,                                                                           #5
        can_pound_cracked_blocks,                                                       #6
        _c(can_pound_solid_blocks,has_grab_1),                                          #7
        _o(can_pound_solid_blocks,_has("Zombie Form")),                                 #8
    ],
    "The Volcano's Base": [
        None,                                                                           #1
        None,                                                                           #2
        None,                                                                           #3
        can_pound_cracked_blocks,                                                       #4
        _o(_has("Truck Wheel"),has_vampire_2),                                          #5
        _o(_has("Truck Wheel"),can_fly),                                                #6
        _o(_has("Truck Wheel"),can_fly),                                                #7
        _c(_has("Foot of Stone"),has_flippers_1),                                       #8
    ],
    "The Pool of Rain": [
        _o(_has("Magic Seeds"),_has("Puffy Form")),                                     #1
        has_flippers_1,                                                                 #2
        has_flippers_2,                                                                 #3
        _has("Magic Seeds"),                                                            #4
        has_flippers_1,                                                                 #5
        _c(has_flippers_2,_has("Spiked Helmet")),                                       #6
        _c(has_flippers_2,_has("Spiked Helmet")),                                       #7
        _c(has_flippers_1,_has("Air Pump")),                                            #8
    ],
    "A Town in Chaos": [
        None,                                                                           #1
        has_grab_1,                                                                     #2
        can_pound_solid_blocks,                                                         #3
        _o(_has("Spiked Helmet"),can_jump_high),                                        #4
        _c(_o(has_grab_2, can_kill_frogs), 
           _o(_c(can_shake_screen, _has("High Jump Boots"), has_grab_1),
              _c(_has("Bouncy Form"), has_grab_1), can_fly)),                           #5
        _o(_c(_has("Electric Fan Propeller"), has_grab_1), can_fly),                    #6
        _c(_o(has_grab_2, can_kill_frogs),has_grab_1),                                  #7
        _c(_o(_c(can_shake_screen,_has("High Jump Boots")),_has("Puffy Form"),_has("Bouncy Form")),
           _o(has_grab_2, can_kill_frogs),has_grab_1),                                  #8
    ],
    "Beneath the Waves": [
        _c(_o(can_fly,_has("High Jump Boots")),has_grab_1),                             #1
        has_flippers_1,                                                                 #2
        has_flippers_2,                                                                 #3
        _c(_has("Sapling of Growth"),has_flippers_2),                                   #4
        _c(has_chemicals,has_flippers_1,
           _o(_c(can_shake_screen,has_grab_1),has_grab_2,can_pass_spikes)),             #5
        _c(has_flippers_1,_o(_has("High Jump Boots"),can_bounce)),                      #6
        _c(has_flippers_2,has_grab_2,_has("Spiked Helmet")),                            #7
        _c(has_flippers_2,_has("Spiked Helmet")),                                       #8
    ],
    "The West Crater": [
        None,                                                                           #1
        _c(_has("Rust Spray"),can_pound_cracked_blocks),                                #2
        _c(_has("Rust Spray"),_o(has_grab_1,can_fly)),                                  #3
        _has("Rust Spray"),                                                             #4
        can_pound_large_solid_blocks,                                                   #5
        _o(_c(can_pass_through_fire, can_jump_high), can_fly),                          #6
        _o(_c(can_pass_through_fire, _has("High Jump Boots")), can_fly),                #7
        _c(_o(can_pound_cracked_blocks, _has("Yarn Form")), _o(has_grab_1, can_bounce)),#8
    ],
    "The Grasslands": [
        _o(_has("Flute"), can_fly),                                                     #1
        _has("Magic Seeds"),                                                            #2
        None,                                                                           #3
        _o(_c(_has("High Jump Boots"),has_grab_1),can_bounce),                          #4
        can_jump_high,                                                                  #5
        _o(_has("Flute"), can_fly),                                                     #6
        can_jump_high,                                                                  #7
        _has("Magic Seeds"),                                                            #8
    ],
    "The Big Bridge": [
        _o(has_grab_1,_c(has_flippers_1,can_bounce)),                                   #1
        _c(_o(can_pound_cracked_blocks,_has("Zombie Form")),
           _o(has_flippers_1,can_sink_in_water)),                                       #2
        _c(_o(can_pound_cracked_blocks,_has("Zombie Form")),has_flippers_1),            #3
        _c(_o(can_pound_cracked_blocks,_has("Zombie Form")),has_flippers_1),            #4
        _c(_has("Scepter"),has_flippers_1),                                             #5
        _c(_has("Scepter"),has_flippers_1,_o(_c(_has("Garlic"),_has("Spiked Helmet")),
                                             _has("Puffy Form"))),                      #6
        _c(has_flippers_1,_o(can_pound_cracked_blocks,_has("Zombie Form")),
           _o(can_shake_screen,can_fly)),                                               #7
        _c(has_flippers_1,_o(_c(can_shake_screen,_has("Garlic")),can_fly)),             #8
    ],
    "Tower of Revival": [
        _c(has_golden_eyes, _has("Garlic"), has_grab_2, _has("Spiked Helmet"),
           _has("Statue"), _has("High Jump Boots")),                                              #1
        _c(_has("Statue"), has_golden_eyes),                                            #2
        _has("Statue"),                                                                 #3
        _c(_has("Statue"), _has("Garlic")),                                             #4
        has_glass_eyes,                                                                 #5
        has_glass_eyes,                                                                 #6
        has_glass_eyes,                                                                 #7
        None,                                                                           #8
    ],
    "The Steep Canyon": [
        None,                                                                           #1
        None,                                                                           #2
        _has("Foot of Stone"),                                                          #3
        _c(_has("Foot of Stone"), has_flippers_2, _o(can_shake_screen, can_fly)),       #4
        _c(_has("Foot of Stone"), has_flippers_2, _o(can_shake_screen, can_fly)),       #5
        _c(_has("Foot of Stone"), has_flippers_2, _o(can_shake_screen, can_fly)),       #6
        _c(_has("Rust Spray"), _o(can_pound_cracked_blocks, _has("Zombie Form"))),      #7
        _c(_has("Rust Spray"), _o(can_pound_cracked_blocks, _has("Zombie Form"))),      #8
    ],
    "Cave of Flames": [
        can_jump_high,                                                                  #1
        can_jump_high,                                                                  #2
        _has("Explosive Plunger Box"),                                                  #3
        _o(can_bounce, _c(_has("High Jump Boots"), has_grab_1, can_shake_screen)),      #4
        _has("Spiked Helmet"),                                                          #5
        _c(_has("Rust Spray"),can_pound_cracked_blocks,has_grab_1,can_jump_high),       #6
        _c(_has("Rust Spray"),can_pound_cracked_blocks,has_grab_1,can_jump_high),       #7
        _c(_has("Rust Spray"), can_pound_cracked_blocks, 
           _o(_c(has_grab_1, _has("High Jump Boots")), can_bounce)),                    #8
    ],
    "Above the Clouds": [
        can_jump_high,                                                                  #1
        None,                                                                           #2
        None,                                                                           #3
        None,                                                                           #4
        can_jump_high,                                                                  #5
        _c(_has("Scissors"),can_jump_high),                                             #6
        _c(_has("Scissors"),can_jump_high),                                             #7
        _c(_has("Scissors"),can_jump_high,_has("Spiked Helmet")),                       #8
    ],
    "The Stagnant Swamp": [
        None,                                                                           #1
        None,                                                                           #2
        _c(_has("Foot of Stone"),_has("High Jump Boots")),                              #3
        _has("Foot of Stone"),                                                          #4
        _c(_has("Foot of Stone"),can_jump_high),                                        #5
        _has("Spiked Helmet"),                                                          #6
        _has("Explosive Plunger Box"),                                                  #7
        _c(_has("Foot of Stone"),_o(can_bounce,_c(_has("High Jump Boots"),has_grab_1))),#8
    ],
    "The Frigid Sea": [
        can_jump_high,                                                                  #1
        _o(has_sun_medallion,has_flippers_2),                                           #2
        _o(has_grab_1,can_fly),                                                         #3
        _o(has_grab_1,can_fly),                                                         #4
        _c(_has("Scepter"),has_flippers_1),                                             #5
        _c(_has("Scepter"),has_flippers_1,_has("Spiked Helmet"),_has("High Jump Boots")),#6
        _c(_has("Scepter"),has_flippers_1),                                             #7
        _o(has_sun_medallion,has_flippers_2),                                           #8
    ],
    "Castle of Illusions": [
        None,                                                                           #1
        _o(_c(has_grab_2,_has("High Jump Boots")),can_bounce),                          #2
        _o(_c(has_grab_2,_o(_has("High Jump Boots"),can_shake_screen)),can_bounce),     #3
        _o(_c(has_grab_2,_has("High Jump Boots")),can_bounce),                          #4
        _o(has_grab_2, can_bounce),                                                     #5
        _c(_has("Castle Brick"), _o(has_grab_1, can_fly)),                              #6
        _c(_has("Castle Brick"), _o(has_grab_1, can_fly)),                              #7
        _o(has_grab_2, can_bounce),                                                     #8
    ],
    "The Colossal Hole": [
        None,                                                                           #1
        _o(has_sun_medallion,can_jump_high),                                            #2
        None,                                                                           #3
        None,                                                                           #4
        None,                                                                           #5
        _c(_o(has_sun_medallion,can_fly),has_grab_1),                                   #6
        _c(_has("Explosive Plunger Box"),can_jump_high),                                #7
        _c(_has("Garlic"),_o(_c(_has("Spiked Helmet"),can_jump_high),can_fly)),         #8
    ],
    "The Warped Void": [
        _o(_c(has_key_cards,has_grab_1),_c(can_fly,_has("Warp Removal Apparatus"))),    #1
        _o(has_grab_1,can_bounce),                                                      #2
        has_grab_1,                                                                     #3
        _c(_has("Warp Removal Apparatus"), _o(has_grab_1, can_fly)),                    #4
        _has("Warp Removal Apparatus"),                                                 #5
        _has("Warp Removal Apparatus"),                                                 #6
        _o(_c(has_key_cards, has_grab_1,_has("High Jump Boots"),_has("Spiked Helmet")),
           _c(_has("Warp Removal Apparatus"), can_fly)),                                #7
        _o(_c(has_key_cards, has_grab_1,_has("High Jump Boots"),_has("Spiked Helmet")),
           _c(_has("Warp Removal Apparatus"), can_fly)),                                #8
    ],
    "The East Crater": [
        None,                                                                           #1
        has_grab_1,                                                                     #2
        _o(_has("Zombie Form"),has_grab_1),                                             #3
        _c(can_pass_through_fire,has_grab_1),                                           #4
        _c(_o(_has("Zombie Form"),has_grab_1),can_pass_through_fire),                   #5
        _c(has_grab_1,_o(can_fly,_has("Jackhammer"))),                                  #6
        _c(_has("Pick Axe"),has_grab_1,can_jump_high),                                  #7
        _c(_has("Pick Axe"),has_grab_1,can_jump_high),                                  #8
    ],
    "Forest of Fear": [
        _o(_has("High Jump Boots"),can_fly),                                            #1
        _c(_has("Mystery Handle"),
           _o(_c(has_grab_1,_has("High Jump Boots")),_has("Puffy Form"))),              #2
        _has("Mystery Handle"),                                                         #3
        _c(_has("Mystery Handle"), _o(_c(has_grab_2, _has("High Jump Boots")),
                                      can_bounce)),                                     #4
        None,                                                                           #5
        _c(_has("Mystery Handle"), _o(_c(has_grab_2, _has("High Jump Boots")),
                                      can_bounce)),                                     #6
        None,                                                                           #7
        None,                                                                           #8
    ],
}

# ---------------------------------------------------------------------------
# Main rule-setting function — called from WL3World.set_rules()
# ---------------------------------------------------------------------------

def set_rules(world: "WL3World") -> None:
    from .options import CombinedItems as _CI
    player  = world.player
    mw      = world.multiworld
    ci_mode = int(world.options.combined_items)
    combine_overworld = ci_mode in (_CI.option_overworld, _CI.option_both)
    # combine_in_level  = ci_mode in (_CI.option_in_level,  _CI.option_both) 
    combined = combine_overworld  # legacy alias for the overworld block below
    difficulty = int(world.options.difficulty)
    glitches = bool(world.options.minor_glitches)

    # Deep copies of the rules dicts for mutation
    chest_logic = {k: list(v) for k, v in CHEST_RULES.items()} 
    key_logic   = {k: list(v) for k, v in KEY_RULES.items()}
    coin_logic   = {k: list(v) for k, v in COIN_RULES.items()}
    
    # Difficulty Constants
    knowledge_checks = 1
    hard_logic = 2
    
    # Chest and Key Color Constants
    grey = 0
    red = 1
    green = 2
    blue = 3

    # Override some level requirements depending on difficulty
    if difficulty >= knowledge_checks:
        chest_logic["Out of the Woods"][red] = _o(can_pound_cracked_blocks, _has("Garlic"))
        chest_logic["Out of the Woods"][blue] = _c(_o(_c(has_grab_1, has_overalls_1, can_jump_high), can_fly), _has("Gold Magic"))
        chest_logic["The Peaceful Village"][red] = _o(_c(_o(can_shake_screen, _has("Zombie Form")), _has("Garlic")), _has("Flute"), can_jump_high)
        chest_logic["The Peaceful Village"][green] = _c(_o(_c(_o(can_shake_screen, _has("Zombie Form")), _has("Garlic")), _has("Flute"), can_jump_high), _o(can_pound_cracked_blocks, _has("Zombie Form")))
        chest_logic["The Vast Plain"][red] = _o(can_pound_cracked_blocks, _has("Zombie Form"))
        chest_logic["Desert Ruins"][blue] = _c(has_overalls_1, _o(can_jump_high, has_grab_1), _o(can_pound_solid_blocks, _has("Zombie Form")))
        chest_logic["Beneath the Waves"][green] = _c(has_flippers_1, _o(has_grab_1, _has("Yarn Form"), _c(_has("Flat Form"), _has("Spiked Helmet"))), _o(_has("High Jump Boots"), can_fly))
        chest_logic["The Grasslands"][red] = _c(_o(_has("Magic Seeds"), has_vampire_2), _o(can_pound_cracked_blocks, _has("Zombie Form")))
        chest_logic["The Grasslands"][green] = _c(_o(_has("Flute"), _has("High Jump Boots"), can_fly), has_flippers_1)
        chest_logic["Tower of Revival"][blue] = _c(has_golden_eyes, _has("Garlic"), has_grab_2, _has("Spiked Helmet"), _has("Statue"), can_jump_high)
        chest_logic["The Steep Canyon"][blue] = _c(_has("Rust Spray"), _o(can_pound_cracked_blocks, _has("Zombie Form"), _c(_has("Flat Form"), _has("Spiked Helmet"))))
        chest_logic["Above the Clouds"][red] = _o(_c(_has("High Jump Boots"), _has("Spiked Helmet")), can_bounce)
        chest_logic["Above the Clouds"][blue] = _o(_c(_has("Scissors"), _has("Full Moon Gong"), _has("High Jump Boots"), has_overalls_2, has_grab_1),_c(_has("Scissors"), _has("Full Moon Gong"), can_jump_high, _has("Flat Form"), _has("Spiked Helmet")))
        chest_logic["The East Crater"][blue] = _c(_has("Pick Axe"), has_grab_1)
        key_logic["Out of the Woods"][red] = _o(can_pound_cracked_blocks, _has("Garlic"))
        key_logic["The Peaceful Village"][red] = None
        key_logic["The Peaceful Village"][green] = _o(_c(_o(can_shake_screen, _has("Zombie Form")), _has("Garlic")), _has("Flute"), can_fly)
        key_logic["The Vast Plain"][red] = _o(can_pound_cracked_blocks, _has("Zombie Form"))
        key_logic["Desert Ruins"][green] = _o(_c(_has("Spiked Helmet"), _o(can_pound_cracked_blocks, _has("Flat Form"))), _has("Garlic"))
        key_logic["The Volcano's Base"][blue] = _c(_o(_has("Foot of Stone"),_c(_has("Flat Form"), _has("Spiked Helmet"))), _o(has_flippers_2, _c(has_flippers_1, _has("Spiked Helmet"))))
        key_logic["Beneath the Waves"][red] = _c(_o(has_flippers_2, can_sink_in_water), has_flippers_1)
        key_logic["The Grasslands"][green] = _o(_has("Flute"), _has("High Jump Boots"), can_fly)
        key_logic["The Big Bridge"][green] = _c(has_flippers_1, _o(can_pound_cracked_blocks, _has("Zombie Form")), _o(has_grab_1, can_shake_screen, can_fly))
        key_logic["The Big Bridge"][blue] = _c(_o(has_flippers_1, has_grab_1), _o(_has("Garlic"), can_fly))
        key_logic["The Steep Canyon"][blue] = _c(_has("Rust Spray"), _o(can_pound_cracked_blocks, _has("Zombie Form"), _c(_has("Flat Form"), _has("Spiked Helmet"))))
        key_logic["Cave of Flames"][grey] = _o(has_grab_1, _c(_has("Flat Form"), _has("Spiked Helmet")))
        key_logic["Castle of Illusions"][red] = _o(_c(_o(_c(has_grab_1, has_sun_medallion), has_grab_2), _o(can_shake_screen, _has("High Jump Boots"))), can_bounce)
        key_logic["Castle of Illusions"][blue] = _c(_o(_has("Castle Brick"), has_vampire_2), can_pound_cracked_blocks, _o(has_grab_1, can_fly, _has("Zombie Form")))
        key_logic["The East Crater"][red] = _c(_o(can_pass_through_fire), _o(_has("Zombie Form"), has_grab_1),_o(_c(has_grab_1, _o(can_pound_cracked_blocks)), _has("Zombie Form"), _c(_has("Flat Form"),_has("Spiked Helmet"))))
        key_logic["The East Crater"][blue] = _c(_has("Pick Axe"), has_grab_1)
        # Coins are 0 indexed, so one less than their counterparts on the level maps
        coin_logic["Out of the Woods"][0] = _o(_c(_has("High Jump Boots"), has_grab_1), can_fly)
        coin_logic["Out of the Woods"][3] = _o(has_flippers_2, has_storm_pouch, can_fly)
        coin_logic["Out of the Woods"][6] = _o(can_pound_cracked_blocks, _has("Garlic"))
        coin_logic["The Peaceful Village"][3] = _c(_o(_has("Flute"),can_jump_high),_o(_has("Zombie Form"),can_pound_cracked_blocks))
        coin_logic["The Vast Plain"][3] = _o(can_pound_cracked_blocks, _has("Zombie Form"))
        coin_logic["The Tidal Coast"][5] = _c(has_grab_1, _o(has_flippers_2, _c(has_flippers_1, _o(_has("Spiked Helmet"), _has("Zombie Form"))), _c(_has("Zombie Form"), can_sink_in_water)))
        coin_logic["Desert Ruins"][2] = _c(_o(can_pound_solid_blocks, _has("Zombie Form")), _o(has_grab_1, can_jump_high), has_overalls_1)
        coin_logic["The Volcano's Base"][4] = None
        coin_logic["A Town in Chaos"][2] = _o(can_pound_solid_blocks, _c(_has("Spiked Helmet"), can_pound_cracked_blocks))
        coin_logic["A Town in Chaos"][4] = _c(_o(has_grab_2, can_kill_frogs), _o(_c(can_shake_screen, _has("High Jump Boots")), can_bounce))
        coin_logic["A Town in Chaos"][7] = _c(_o(has_grab_2, can_kill_frogs), _o(_c(can_shake_screen, _has("High Jump Boots")), _has("Puffy Form"), _has("Bouncy Form")))
        coin_logic["Beneath the Waves"][6] = _c(has_flippers_2, _o(_c(has_grab_2, _has("Spiked Helmet")), can_bounce))
        coin_logic["The Grasslands"][0] = _o(_has("Flute"), can_fly, _has("High Jump Boots"))
        coin_logic["The Grasslands"][5] = _o(_has("Flute"), can_fly, _has("High Jump Boots"))
        coin_logic["Tower of Revival"][0] = _c(has_golden_eyes, _has("Garlic"), has_grab_2, _has("Spiked Helmet"), _has("Statue"), can_jump_high)
        coin_logic["The Steep Canyon"][6] = _c(_has("Rust Spray"), _o(can_pound_cracked_blocks, _has("Zombie Form"), _c(_has("Flat Form"), _has("Spiked Helmet"))))
        coin_logic["Castle of Illusions"][5] = _c(_o(_has("Castle Brick"), has_vampire_2), _o(has_grab_1, can_fly, _has("Zombie Form")))
        coin_logic["Castle of Illusions"][6] = _c(_o(_has("Castle Brick"), has_vampire_2), _o(has_grab_1, can_fly, _has("Zombie Form")))        

    if difficulty >= hard_logic:
        chest_logic["Out of the Woods"][green] = _o(has_storm_pouch,can_fly)
        chest_logic["Beneath the Waves"][red] = has_flippers_1
        chest_logic["Beneath the Waves"][green] = _c(has_flippers_1,_o(has_grab_1,_has("Yarn Form"),_c(_has("Flat Form"),_has("Spiked Helmet"))))
        chest_logic["Beneath the Waves"][blue] = _c(has_flippers_1,_o(has_grab_1,_has("Fat Form")))
        chest_logic["Above the Clouds"][blue] = _c(_has("Scissors"),_has("Full Moon Gong"),has_overalls_2,has_grab_1,can_jump_high)
        key_logic["The Volcano's Base"][red] = _o(_has("Truck Wheel"),_has("Flat Form"),can_fly)
        key_logic["A Town in Chaos"][green] = _c(can_kill_frogs,_o(can_shake_screen,can_fly))
        key_logic["Above the Clouds"][red] = _o(_c(_has("High Jump Boots"),has_grab_1),can_bounce)
        key_logic["The East Crater"][grey] = _o(has_grab_1,_has("Zombie Form"))
        key_logic["The Frigid Sea"][red] = _o(has_grab_1,can_bounce)
        # Coins are 0 indexed, so one less than their counterparts on the level maps
        coin_logic["The Pool of Rain"][5] = _c(has_flippers_1,_has("Spiked Helmet"))
        coin_logic["The Pool of Rain"][6] = _c(has_flippers_1,_has("Spiked Helmet"))
        coin_logic["The Frigid Sea"][3] = _o(has_grab_1,can_bounce)
        coin_logic["Castle of Illusions"][1] = _o(_c(_o(_c(has_grab_1,has_sun_medallion),has_grab_2),_has("High Jump Boots")), can_bounce)
        coin_logic["Castle of Illusions"][2] = _o(_c(_o(_c(has_grab_1,has_sun_medallion),has_grab_2),can_shake_screen,_has("High Jump Boots")), can_bounce)        

    # Override some level requirements if glitches are in logic (overwrites difficulty options, we assume glitched players can do most tricks)
    if glitches:
        chest_logic["The Peaceful Village"][red] = None
        chest_logic["The Peaceful Village"][green] = _o(can_pound_cracked_blocks,_has("Zombie Form"))
        chest_logic["The Tidal Coast"][green] = None
        chest_logic["The Grasslands"][blue] = None
        chest_logic["A Town in Chaos"][green] = _c(_o(has_grab_2,can_kill_frogs),_has("High Jump Boots"),_o(can_shake_screen,_has("Spiked Helmet"),can_bounce))
        chest_logic["Castle of Illusions"][grey] = None
        chest_logic["The East Crater"][red] = _c(can_pass_through_fire,_o(_c(has_grab_1,has_overalls_1),_has("Fire Form")))
        key_logic["Out of the Woods"][green] = None
        key_logic["The Peaceful Village"][red] = None
        key_logic["The Peaceful Village"][green] = None
        key_logic["The Grasslands"][blue] = None
        key_logic["A Town in Chaos"][green] = _c(_o(has_grab_2,can_kill_frogs),_o(can_shake_screen,_has("Spiked Helmet"),can_fly),_has("High Jump Boots"))
        key_logic["Cave of Flames"][red] = None
        key_logic["Castle of Illusions"][red] = _o(has_overalls_2,can_jump_high)
        key_logic["The East Crater"][red] = _c(can_pass_through_fire,_o(_c(has_grab_1,can_pound_cracked_blocks),_has("Zombie Form")))
        # Coins are 0 indexed, so one less than their counterparts on the level maps
        coin_logic["The Peaceful Village"][3] = _o(_has("Zombie Form"),can_pound_cracked_blocks)

    # Override multi-item unlock predicates when combined mode is on
    level_rules = dict(LEVEL_RULES)
    if combined:
        level_rules.update({
            "Desert Ruins":        unlock_w1c,
            "The Volcano's Base":  unlock_w2c,
            "The West Crater":     unlock_w6_e4c,
            "The Colossal Hole":   unlock_w6_e4c,
            "The Grasslands":      unlock_s1c,
            "Tower of Revival":    unlock_s3c,
            "The Steep Canyon":    unlock_s4c,
            "The Frigid Sea":      unlock_e2c,
            "Castle of Illusions": unlock_e3c,
        })

    ks = world.options.key_shuffle
    keysanity = (ks != KeyShuffle.option_vanilla)

    for loc_name, loc_data in LOCATION_TABLE.items():
        level_rule  = level_rules.get(loc_data.level_name)
        chest_rules = chest_logic.get(loc_data.level_name)
        chest_rule  = chest_rules[loc_data.color_index] if chest_rules else None

        if keysanity:
            # Keysanity: chests require the matching key item (separate from key access)
            # If the level is keyringed, a single Keyring item stands in for all 4 keys.
            key_item = f"{loc_data.level_name} {COLOR_NAMES[loc_data.color_index]} Key"
            keyringed = getattr(world, "keyringed_level_names", set())
            if loc_data.level_name in keyringed:
                keyring_item = f"{loc_data.level_name} Keyring"
                key_item_rule = _o(_has(key_item), _has(keyring_item))
            else:
                key_item_rule = _has(key_item)
            chest_rule = _c(chest_rule, key_item_rule) if chest_rule is not None else key_item_rule
        else:
            # Vanilla: combine key access + chest access (must reach both in same level)
            key_rules = key_logic.get(loc_data.level_name)
            key_rule = key_rules[loc_data.color_index] if key_rules else None
            if key_rule is not None:
                chest_rule = _c(chest_rule, key_rule) if chest_rule is not None else key_rule

        if level_rule is not None and chest_rule is not None:
            mw.get_location(loc_name, player).access_rule = \
                lambda state, lr=level_rule, cr=chest_rule: lr(state, player) and cr(state, player)
        elif level_rule is not None:
            mw.get_location(loc_name, player).access_rule = \
                lambda state, r=level_rule: r(state, player)
        elif chest_rule is not None:
            mw.get_location(loc_name, player).access_rule = \
                lambda state, r=chest_rule: r(state, player)

    # Key locations — excluded in vanilla, in logic for simple & full.
    if ks == KeyShuffle.option_vanilla:
        for loc_name in KEY_LOCATION_TABLE:
            mw.get_location(loc_name, player).progress_type = LocationProgressType.EXCLUDED
    else:
        for loc_name, loc_data in KEY_LOCATION_TABLE.items():
            level_rule = level_rules.get(loc_data.level_name)
            key_rules  = key_logic.get(loc_data.level_name)
            key_rule   = key_rules[loc_data.color_index] if key_rules else None

            if level_rule is not None and key_rule is not None:
                mw.get_location(loc_name, player).access_rule = \
                    lambda state, lr=level_rule, kr=key_rule: lr(state, player) and kr(state, player)
            elif level_rule is not None:
                mw.get_location(loc_name, player).access_rule = \
                    lambda state, r=level_rule: r(state, player)
            elif key_rule is not None:
                mw.get_location(loc_name, player).access_rule = \
                    lambda state, r=key_rule: r(state, player)

    # Coin locations (coinsanity) — gated by level entry AND any per-coin
    # ability requirements from COIN_RULES (e.g. flippers_2 for an underwater
    # coin). Coins don't need keys (they respawn each level visit), so we
    # combine just the two rule sources, mirroring the key location wiring.
    if world.options.bigcoinsanity:
        for loc_name, loc_data in COIN_LOCATION_TABLE.items():
            level_rule = level_rules.get(loc_data.level_name)
            coin_rules_for_level = coin_logic.get(loc_data.level_name)
            coin_rule = coin_rules_for_level[loc_data.coin_index] if coin_rules_for_level else None

            if level_rule is not None and coin_rule is not None:
                mw.get_location(loc_name, player).access_rule = \
                    lambda state, lr=level_rule, cr=coin_rule: lr(state, player) and cr(state, player)
            elif level_rule is not None:
                mw.get_location(loc_name, player).access_rule = \
                    lambda state, r=level_rule: r(state, player)
            elif coin_rule is not None:
                mw.get_location(loc_name, player).access_rule = \
                    lambda state, r=coin_rule: r(state, player)

    # Victory condition — collect required music boxes then beat the final boss.
    # Progressive Overalls x1 and Progressive Grab x2 are always required for the temple fight.
    required = int(world.options.music_boxes_required)
    mw.completion_condition[player] = \
        lambda state, n=required: (
            sum(state.has(mb, player) for mb in MUSIC_BOXES) >= n
            and has_overalls_1(state, player)
            and has_grab_2(state, player)
        )
