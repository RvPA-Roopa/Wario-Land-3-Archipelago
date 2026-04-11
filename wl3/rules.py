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

from .locations import COLOR_NAMES, KEY_LOCATION_TABLE, LOCATION_TABLE
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

CHEST_RULES: dict = {
    "Out of the Woods": [
        None,                                                                        # grey
        has_overalls_1,                                          # red
        _c(_has("Pouch"), _has("Eye of the Storm")),                                 # green
        _c(_has("Gold Magic"), _has("High Jump Boots"), has_grab_1, has_overalls_1), # blue
    ],
    "The Peaceful Village": [
        None,                                                                        # grey
        _o(_has("Flute"), _has("High Jump Boots")),                                  # red
        _c(_o(_has("Flute"), _has("High Jump Boots")), has_overalls_1),              # green
        _c(has_overalls_2, _has("Garlic")),                                          # blue
    ],
    "The Vast Plain": [
        None,                                                                        # grey
        has_overalls_1,                                                              # red
        _has("Magic Seeds"),                                                         # green
        _c(_has("Blue Chemical"), _has("Red Chemical")),                             # blue
    ],
    "Bank of the Wild River": [
        None,                                                                        # grey
        _has("Garlic"),                                                              # red
        has_flippers_2,                                                              # green
        _c(_has("Air Pump"), has_grab_1),                                            # blue
    ],
    "The Tidal Coast": [
        None,                                                                        # grey
        _c(has_flippers_1, has_grab_1),                                              # red
        _has("Statue"),                                                              # green
        _c(_has("Sapling of Growth"), has_flippers_1, _has("Garlic")),               # blue
    ],
    "Sea Turtle Rocks": [
        _c(_has("Spiked Helmet"), has_overalls_1, has_flippers_1),                   # grey
        _c(_has("Scepter"), has_overalls_1, has_flippers_1),                         # red
        has_overalls_2,                                                              # green
        _c(_has("Night Vision Scope"), has_overalls_2, _has("High Jump Boots")),     # blue
    ],
    "Desert Ruins": [
        None,                                                                        # grey
        None,                                                                        # red
        _has("Spiked Helmet"),                                                       # green
        _c(has_overalls_2, has_grab_1),                                              # blue
    ],
    "The Volcano's Base": [
        None,                                                                        # grey
        _has("Truck Wheel"),                                                         # red
        _c(_has("Flute"), _has("Truck Wheel")),                                      # green
        _has("Foot of Stone"),                                                       # blue
    ],
    "The Pool of Rain": [
        has_overalls_1,                                                              # grey
        _has("Magic Seeds"),                                                         # red
        has_flippers_1,                                                              # green
        _c(_has("Air Pump"), has_flippers_1),                                        # blue
    ],
    "A Town in Chaos": [
        None,                                                                        # grey
        _has("Spiked Helmet"),                                                       # red
        _c(has_grab_2, has_overalls_2, _has("High Jump Boots")),                     # green
        None,                                                                        # blue
    ],
    "Beneath the Waves": [
        has_flippers_1,                                                              # grey
        _c(has_flippers_1, _has("High Jump Boots")),                                 # red
        _c(has_flippers_1, has_grab_1, _has("High Jump Boots")),                     # green
        _c(has_flippers_1, has_grab_1, _has("High Jump Boots")),                     # blue
    ],
    "The West Crater": [
        has_overalls_1,                                                              # grey
        _c(has_overalls_2, _has("Garlic")),                                          # red
        _c(_has("Fire Drencher"), _has("High Jump Boots")),                          # green
        _has("Rust Spray"),                                                          # blue
    ],
    "The Grasslands": [
        has_overalls_1,                                                              # grey
        _c(_has("Magic Seeds"), has_overalls_1),                                     # red
        _c(_o(_has("Flute"), _has("High Jump Boots")), has_flippers_1),              # green
        _has("High Jump Boots"),                                                     # blue
    ],
    "The Big Bridge": [
        None,                                                                        # grey
        _c(has_flippers_1, has_overalls_1),                                          # red
        has_grab_1,                                                                  # green
        _c(_has("Scepter"), has_flippers_1, _has("Garlic"), _has("Spiked Helmet")),  # blue
    ],
    "Tower of Revival": [
        None,                                                                        # grey
        _c(_has("Left Glass Eye"), _has("Right Glass Eye")),                         # red
        _c(_has("Statue"), _has("High Jump Boots")),                                 # green
        _c(_has("Golden Left Eye"), _has("Golden Right Eye"), _has("Statue"),
           _has("Garlic"), has_grab_2, _has("High Jump Boots")),                     # blue
    ],
    "The Steep Canyon": [
        None,                                                                        # grey
        _has("Foot of Stone"),                                                       # red
        _c(_has("Foot of Stone"), has_flippers_2, has_overalls_2),                   # green
        _c(_has("Rust Spray"), has_overalls_1),                                      # blue
    ],
    "Cave of Flames": [
        None,                                                                        # grey
        _c(has_grab_1, _has("High Jump Boots"), has_overalls_2),                     # red
        _has("Explosive Plunger Box"),                                               # green
        _c(_has("Rust Spray"), has_overalls_1, has_grab_1, _has("High Jump Boots")), # blue
    ],
    "Above the Clouds": [
        None,                                                                        # grey
        _c(_has("High Jump Boots"), has_grab_1, _has("Spiked Helmet")),              # red
        _c(_has("Scissors"), _has("High Jump Boots")),                               # green
        _c(_has("Scissors"), _has("Full Moon Gong"), _has("High Jump Boots"),
           has_overalls_2, has_grab_1),                                              # blue
    ],
    "The Stagnant Swamp": [
        None,                                                                        # grey
        _c(_has("Foot of Stone"),
           _o(has_overalls_1, _c(has_flippers_2, _has("High Jump Boots")))),         # red
        _c(_has("Foot of Stone"), _has("High Jump Boots")),                          # green
        _has("Explosive Plunger Box"),                                               # blue
    ],
    "The Frigid Sea": [
        None,                                                                        # grey
        has_grab_1,                                                                  # red
        _c(_has("Scepter"), has_flippers_1),                                         # green
        _o(_c(_has("Sun Medallion Top"), _has("Sun Medallion Bottom")),
           has_flippers_2),                                                          # blue
    ],
    "Castle of Illusions": [
        has_overalls_1,                                                              # grey
        has_grab_1,                                                                  # red
        has_grab_1,                                                                  # green
        has_grab_1,                                                                  # blue
    ],
    "The Colossal Hole": [
        None,                                                                        # grey
        _has("Garlic"),                                                              # red
        _o(_c(_has("Sun Medallion Top"), _has("Sun Medallion Bottom")),
           _has("High Jump Boots")),                                                 # green
        _c(_has("Explosive Plunger Box"), _has("High Jump Boots")),                  # blue
    ],
    "The Warped Void": [
        None,                                                                        # grey
        _has("Warp Removal Apparatus"),                                              # red
        _c(_has("Warp Removal Apparatus"), has_grab_1),                              # green
        _c(_has("Key Card Red"), _has("Key Card Blue"), has_grab_1),                 # blue
    ],
    "The East Crater": [
        has_grab_1,                                                                  # grey
        _c(_has("Fire Drencher"), has_grab_1, has_overalls_1),                       # red
        _c(_has("Jackhammer"), has_grab_1),                                          # green
        _c(_has("Pick Axe"), has_grab_1, _has("High Jump Boots")),                   # blue
    ],
    "Forest of Fear": [
        None,                                                                        # grey
        _c(_has("Mystery Handle"), has_grab_2),                                      # red
        _c(_has("Mystery Handle"), has_grab_1),                                      # green
        _has("Demon's Blood"),                                                       # blue
    ],
}


# ---------------------------------------------------------------------------
# Per-key access rules (additional requirements beyond the level unlock)
# Each entry: [grey_rule, red_rule, green_rule, blue_rule]
# ---------------------------------------------------------------------------

KEY_RULES: dict = {
    "Out of the Woods": [
        None,                                                                        # grey
        has_overalls_1,                                                          # red
        _has("High Jump Boots"),                                                     # green
        _c(_has("Gold Magic"), _has("High Jump Boots")),                             # blue
    ],
    "The Peaceful Village": [
        None,                                                                        # grey
        _o(_has("Flute"), _has("High Jump Boots")),                                  # red
        _o(_has("Flute"), _has("High Jump Boots")),                                  # green
        _c(has_overalls_2, _has("Garlic")),                                          # blue
    ],
    "The Vast Plain": [
        None,                                                                        # grey
        has_overalls_1,                                                              # red
        _has("Magic Seeds"),                                                         # green
        _c(_has("Blue Chemical"), _has("Red Chemical")),                             # blue
    ],
    "Bank of the Wild River": [
        None,                                                                        # grey
        _has("Garlic"),                                                              # red
        has_flippers_2,                                                              # green
        _has("Air Pump"),                                                            # blue
    ],
    "The Tidal Coast": [
        None,                                                                        # grey
        _c(has_grab_1, _o(has_flippers_2, _c(has_flippers_1, 
           _has("Spiked Helmet")))),                                                 # red
        _has("Garlic"),                                                              # green
        _c(has_flippers_1, _has("Garlic"), _has("Sapling of Growth")),               # blue
    ],
    "Sea Turtle Rocks": [
        _c(_has("Spiked Helmet"), has_overalls_1, has_flippers_1),                   # grey
        _c(_has("Scepter"), has_overalls_1, has_flippers_1),                         # red
        has_overalls_2,                                                              # green
        _c(has_overalls_2, _has("High Jump Boots"), _has("Night Vision Scope")),     # blue
    ],
    "Desert Ruins": [
        None,                                                                        # grey
        None,                                                                        # red
        _c(_has("Spiked Helmet"), has_overalls_1),                                   # green
        has_overalls_2,                                                              # blue
    ],
    "The Volcano's Base": [
        None,                                                                        # grey
        _has("Truck Wheel"),                                                         # red
        _c(_has("Truck Wheel"), has_flippers_1),                                     # green
        _c(_has("Foot of Stone"), _o(has_flippers_2, _c(has_flippers_1, 
           _has("Spiked Helmet")))),                                                 # blue
    ],
    "The Pool of Rain": [
        has_overalls_1,                                                              # grey
        _has("Magic Seeds"),                                                         # red
        has_flippers_1,                                                              # green
        _c(_has("Air Pump"), has_flippers_1),                                        # blue
    ],
    "A Town in Chaos": [
        None,                                                                        # grey
        None,                                                                        # red
        _c(has_grab_2, has_overalls_2, _has("High Jump Boots")),                     # green
        _c(_has("Electric Fan Propeller"), has_grab_1),                              # blue
    ],
    "Beneath the Waves": [
        _has("High Jump Boots"),                                                     # grey
        has_flippers_2,                                                              # red
        _c(has_flippers_1, _has("Sapling of Growth")),                               # green
        _c(has_flippers_1, _has("Red Chemical"), _has("Blue Chemical")),             # blue
    ],
    "The West Crater": [
        None,                                                                        # grey
        _c(has_overalls_1, has_grab_1),                                              # red
        _c(_has("Fire Drencher"), _has("High Jump Boots")),                          # green
        _c(_has("Rust Spray"), has_grab_1),                                          # blue
    ],
    "The Grasslands": [
        None,                                                                        # grey
        None,                                                                        # red
        _o(_has("Flute"), _has("High Jump Boots")),                                  # green
        _has("High Jump Boots"),                                                     # blue
    ],
    "The Big Bridge": [
        None,                                                                        # grey
        _c(has_overalls_1, has_flippers_1),                                          # red
        _c(has_flippers_1, has_overalls_1, has_grab_1),                              # green
        _c(has_flippers_1, _has("Garlic")),                                          # blue
    ],
    "Tower of Revival": [
        None,                                                                        # grey
        _c(_has("Left Glass Eye"), _has("Right Glass Eye")),                         # red
        _has("Statue"),                                                              # green
        _c(_has("Statue"), _has("Golden Left Eye"), _has("Golden Right Eye")),       # blue
    ],
    "The Steep Canyon": [
        None,                                                                        # grey
        _has("Foot of Stone"),                                                       # red
        _c(_has("Foot of Stone"), has_flippers_2, has_overalls_2),                   # green
        _c(_has("Rust Spray"), has_overalls_1),                                      # blue
    ],
    "Cave of Flames": [
        has_grab_1,                                                                  # grey
        _has("High Jump Boots"),                                                     # red
        _has("Explosive Plunger Box"),                                               # green
        _c(_has("Rust Spray"), has_overalls_1, has_grab_1, _has("High Jump Boots")), # blue
    ],
    "Above the Clouds": [
        None,                                                                        # grey
        _c(_has("High Jump Boots"), has_grab_1, _has("Spiked Helmet")),              # red
        _c(_has("Scissors"), _has("High Jump Boots")),                               # green
        _c(_has("Scissors"), _has("High Jump Boots")),                               # blue
    ],
    "The Stagnant Swamp": [
        None,                                                                        # grey
        _has("Foot of Stone"),                                                       # red
        _c(_has("Foot of Stone"), has_grab_1, _has("High Jump Boots")),              # green
        _has("Explosive Plunger Box"),                                               # blue
    ],
    "The Frigid Sea": [
        None,                                                                        # grey
        has_grab_1,                                                                  # red
        _c(_has("Scepter"), has_flippers_1),                                         # green
        _o(_c(_has("Sun Medallion Top"), _has("Sun Medallion Bottom")), 
           has_flippers_2),                                                          # blue
    ],
    "Castle of Illusions": [
        has_grab_1,                                                                  # grey
        _c(_o(_c(has_grab_1, _has("Sun Medallion Top"), _has("Sun Medallion Bottom")),
           has_grab_2), _o(has_overalls_2, _has("High Jump Boots"))),                # red
        has_grab_2,                                                                  # green
        _c(_has("Castle Brick"), has_overalls_1, has_grab_1),                        # blue
    ],
    "The Colossal Hole": [
        None,                                                                        # grey
        _c(_has("Garlic"), has_grab_1),                                              # red
        _o(_c(_has("Sun Medallion Top"), _has("Sun Medallion Bottom")), 
           _has("High Jump Boots")),                                                 # green
        _c(_has("Explosive Plunger Box"), _has("High Jump Boots")),                  # blue
    ],
    "The Warped Void": [
        has_grab_1,                                                                  # grey
        _has("Warp Removal Apparatus"),                                              # red
        _c(_has("Warp Removal Apparatus"), has_grab_1),                              # green
        _c(_has("Key Card Red"), _has("Key Card Blue"), has_grab_1),                 # blue
    ],
    "The East Crater": [
        _c(has_grab_1, has_overalls_2),                                              # grey
        _c(_has("Fire Drencher"), has_grab_1, has_overalls_1),                       # red
        _c(_has("Jackhammer"), has_grab_1),                                          # green
        _c(_has("Pick Axe"), has_grab_1, _has("High Jump Boots")),                   # blue
    ],
    "Forest of Fear": [
        None,                                                                        # grey
        _c(_has("Mystery Handle"), has_grab_2, _has("High Jump Boots")),             # red
        _c(_has("Mystery Handle"), has_grab_1),                                      # green
        _has("Demon's Blood"),                                                       # blue
    ],
}

NoRule = object()

CHEST_RULES_KNOWLEDGE: dict = {
    "Out of the Woods": [
        None,                                                                        # grey
        _o(has_overalls_1, _has("Garlic")),                                          # red
        None,                                                                        # green
        None,                                                                        # blue
    ],
    "The Peaceful Village": [
        None,                                                                        # grey
        _o(_c(has_overalls_2, _has("Garlic")),_has("Flute"),_has("High Jump Boots")),# red
        _o(_c(has_overalls_2, _has("Garlic")),_has("Flute"),_has("High Jump Boots")),# green
        None,                                                                        # blue
    ],
    "Desert Ruins": [
        None,                                                                        # grey
        None,                                                                        # red
        None,                                                                        # green
        _o(_c(has_grab_1,has_overalls_2),_c(has_overalls_2,_has("High Jump Boots"))),# blue
    ],
    "Above the Clouds": [
        None,                                                                        # grey
        _c(_has("High Jump Boots"), _has("Spiked Helmet")),                          # red
        None,                                                                        # green
        None,                                                                        # blue
    ]
}

CHEST_RULES_HARD: dict = {
    "Beneath the Waves": [
        None,                                                                        # grey
        has_flippers_1,                                                              # red
        _c(has_flippers_1, has_grab_1),                                              # green
        _c(has_flippers_1, has_grab_1),                                              # blue
    ]
}

CHEST_RULES_GLITCHED: dict = {
    "The Peaceful Village": [
        None,                                                                        # grey
        NoRule,                                                                      # red
        has_overalls_1,                                                              # green
        None,                                                                        # blue
    ],
    "The Tidal Coast": [
        None,                                                                        # grey
        None,                                                                        # red
        NoRule,                                                                      # green
        None,                                                                        # blue
    ],
    "The Grasslands": [
        None,                                                                        # grey
        None,                                                                        # red
        None,                                                                      # green
        NoRule,                                                                        # blue
    ]
}

KEY_RULES_KNOWLEDGE: dict = {
    "Out of the Woods": [
        None,                                                                        # grey
        _o(has_overalls_1, _has("Garlic")),                                          # red
        None,                                                                        # green
        None,                                                                        # blue
    ],
    "The Peaceful Village": [
        None,                                                                        # grey
        NoRule,                                                                      # red
        _o(_c(has_overalls_2, _has("Garlic")),_has("Flute"),_has("High Jump Boots")),# green
        None,                                                                        # blue
    ],
    "Desert Ruins": [
        None,                                                                        # grey
        None,                                                                        # red
        _o(_c(_has("Spiked Helmet"), has_overalls_1),_has("Garlic")),                # green
        None,                                                                        # blue
    ],
        "Beneath the Waves": [
        None,                                                                        # grey
        has_flippers_2,                                                              # red
        None,                                                                        # green
        None,                                                                        # blue
    ],
        "The Big Bridge": [
        None,                                                                        # grey
        None,                                                                        # red
        _c(has_flippers_1, _o(_c(has_overalls_1, has_grab_1), has_overalls_2)),      # green
        None,                                                                        # blue
    ],
    
}

KEY_RULES_HARD: dict = {
    "A Town in Chaos": [
        None,                                                                        # grey
        None,                                                                        # red
        _c(has_grab_2, has_overalls_2),                                              # green
        None,                                                                        # blue
    ],
    "Above the Clouds": [
        None,                                                                        # grey
        _c(_has("High Jump Boots"), has_grab_1),                                     # red
        None,                                                                        # green
        None,                                                                        # blue
    ],
    "The East Crater": [
        has_grab_1,                                                                  # grey
        None,                                                                        # red
        None,                                                                        # green
        None,                                                                        # blue
    ],

}

KEY_RULES_GLITCHED: dict = {
    "Out of the Woods": [
        None,                                                                        # grey
        None,                                                                        # red
        NoRule,                                                                      # green
        None,                                                                        # blue
    ],
    "The Peaceful Village": [
        None,                                                                        # grey
        NoRule,                                                                      # red
        NoRule,                                                                      # green
        None,                                                                        # blue
    ],
    "The Grasslands": [
        None,                                                                        # grey
        None,                                                                        # red
        None,                                                                        # green
        NoRule,                                                                      # blue
    ],
    "Cave of Flames": [
        None,                                                                        # grey
        NoRule,                                                                      # red
        None,                                                                        # green
        None,                                                                        # blue
    ],
    "Castle of Illusions": [
        None,                                                                        # grey
        _o(has_overalls_2, _has("High Jump Boots")),                                 # red
        None,                                                                        # green
        None,                                                                        # blue
    ]
}


# ---------------------------------------------------------------------------
# Main rule-setting function — called from WL3World.set_rules()
# ---------------------------------------------------------------------------

def set_rules(world: "WL3World") -> None:
    player  = world.player
    mw      = world.multiworld
    combined = bool(world.options.combined_level_unlocks)
    difficulty = int(world.options.difficulty_option)
    glitches = bool(world.options.minor_glitches)
    chest_logic = dict(CHEST_RULES)
    key_logic = dict(KEY_RULES)


    # Override certain level requirements depending on difficulty
    if difficulty > 0:
        for level, rules in CHEST_RULES_KNOWLEDGE.items():
            for i, rule in enumerate(rules):
                if not rule:
                    continue
                if rule is NoRule:  #Erase current rules, can't use None because that means no changes
                    chest_logic[level][i] = None                        
                else:
                    chest_logic[level][i] = rule
        for level, rules in KEY_RULES_KNOWLEDGE.items():
            for i, rule in enumerate(rules):
                if not rule:
                    continue
                if rule is NoRule:  #Erase current rules, can't use None because that means no changes
                    key_logic[level][i] = None                        
                else:
                    key_logic[level][i] = rule
    if difficulty > 1:
        for level, rules in CHEST_RULES_HARD.items():
            for i, rule in enumerate(rules):
                if not rule:
                    continue
                if rule is NoRule:  #Erase current rules, can't use None because that means no changes
                    chest_logic[level][i] = None                        
                else:
                    chest_logic[level][i] = rule
        for level, rules in KEY_RULES_HARD.items():
            for i, rule in enumerate(rules):
                if not rule:
                    continue
                if rule is NoRule:  #Erase current rules, can't use None because that means no changes
                    key_logic[level][i] = None                        
                else:
                    key_logic[level][i] = rule


    # Override certain level requirements if glitches are in logic
    if glitches:
        for level, rules in CHEST_RULES_GLITCHED.items():
            for i, rule in enumerate(rules):
                if not rule:
                    continue
                if rule is NoRule:  #Erase current rules, can't use None because that means no changes
                    chest_logic[level][i] = None                        
                else:
                    chest_logic[level][i] = rule
        for level, rules in KEY_RULES_GLITCHED.items():
            for i, rule in enumerate(rules):
                if not rule:
                    continue
                if rule is NoRule:  #Erase current rules, can't use None because that means no changes
                    key_logic[level][i] = None                        
                else:
                    key_logic[level][i] = rule


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
            key_item = f"{loc_data.level_name} {COLOR_NAMES[loc_data.color_index]} Key"
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

    # Victory condition — collect required music boxes then beat the final boss.
    # Progressive Overalls x1 and Progressive Grab x2 are always required for the temple fight.
    required = int(world.options.music_boxes_required)
    mw.completion_condition[player] = \
        lambda state, n=required: (
            sum(state.has(mb, player) for mb in MUSIC_BOXES) >= n
            and has_overalls_1(state, player)
            and has_grab_2(state, player)
        )
