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

from .locations import BOSS_DEFEAT_LOCATION_TABLE, COIN_LOCATION_TABLE, COLOR_NAMES, KEY_LOCATION_TABLE, LOCATION_TABLE
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

def add_tf(location_dict, rule_id, *fns) -> None:
    new = _o(*fns)
    existing = location_dict[rule_id]
    location_dict[rule_id] = new if existing is None else _c(existing, new)

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
can_pass_spikes = _o(_has("Zombie Form"),has_vampire_1,_has("Fire Form"),_has("Snowman Form"),_has("Flat Form"),_has("Ice Skatin' Form"))

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
        _o(can_pound_large_solid_blocks,
           _c(_o(can_shake_screen,_has("Zombie Form")),_has("Garlic"))),             # blue
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
        _c(has_flippers_1, _o(has_grab_1, _has("Yarn Form"), _has("Roll Form")), 
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
        _c(_has("Magic Seeds"), _o(can_pound_cracked_blocks, _has("Zombie Form"))),  # red
        _c(_o(_has("Flute"), _has("Puffy Form")), has_flippers_1),                   # green
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
        _o(_has("Statue"),can_fly),                                                  # green
        _c(_c(has_golden_eyes, _o(_has("Statue"),can_fly)), 
           _o(_c(_has("Garlic"), has_grab_2, _has("Spiked Helmet"), _has("High Jump Boots")),
              _c(_has("Yarn Form"), can_jump_high))),                                # blue
    ],
    "The Steep Canyon": [
        None,                                                                        # grey
        _has("Foot of Stone"),                                                       # red
        _c(_has("Foot of Stone"), has_flippers_2, _o(can_shake_screen, can_fly)),    # green
        _c(_has("Rust Spray"), 
           _o(can_pound_cracked_blocks, _has("Zombie Form"), _has("Roll Form"))),    # blue
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
        _o(_c(_has("High Jump Boots"), _o(_c(has_grab_1, _has("Spiked Helmet")), 
                                          _has("Roll Form"))), can_bounce),          # red
        _c(_has("Scissors"), can_jump_high),                                         # green
        _c(_has("Scissors"), _has("Full Moon Gong"), can_jump_high,
           _o(_c(_has("High Jump Boots"), has_overalls_2, has_grab_1)), _has("Roll Form")),# blue
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
        _c(can_pass_through_fire, 
           _o(_c(has_grab_1, _o(can_pound_cracked_blocks,_has("Roll Form"))), 
              _has("Fire Form")), _o(_has("Zombie Form"), has_grab_1)),              # red
        _c(_o(_has("Jackhammer"), can_fly), has_grab_1),                             # green
        _c(_has("Pick Axe"), has_grab_1, can_jump_high),                             # blue
    ],
    "Forest of Fear": [
        None,                                                                        # grey
        _c(_has("Mystery Handle"), _o(has_grab_2, can_bounce)),                      # red
        _c(_has("Mystery Handle"), has_grab_1),                                      # green
        _o(_has("Demon's Blood"), _has("Zombie Form")),                              # blue
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
        _o(can_pound_large_solid_blocks,
           _c(_o(can_shake_screen,_has("Zombie Form")),_has("Garlic"))),             # blue
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
        _c(_o(_has("Foot of Stone"), _has("Roll Form")), 
           _o(has_flippers_2, _c(has_flippers_1, _has("Spiked Helmet")))),           # blue
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
        _c(_o(can_pound_cracked_blocks, _has("Yarn Form")), _o(has_grab_1, can_fly)),# red
        _o(_c(can_pass_through_fire, can_jump_high), can_fly),                       # green
        _c(_has("Rust Spray"), has_grab_1),                                          # blue
    ],
    "The Grasslands": [
        None,                                                                        # grey
        None,                                                                        # red
        _o(_has("Flute"), _has("Puffy Form")),                                       # green
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
        _o(_has("Statue"),can_fly),                                                  # green
        _c(_o(_has("Statue"),can_fly), has_golden_eyes),                             # blue
    ],
    "The Steep Canyon": [
        None,                                                                        # grey
        _has("Foot of Stone"),                                                       # red
        _c(_has("Foot of Stone"), has_flippers_2, _o(can_shake_screen, can_fly)),    # green
        _c(_has("Rust Spray"), 
           _o(can_pound_cracked_blocks, _has("Zombie Form"), _has("Roll Form"))),    # blue
    ],
    "Cave of Flames": [
        _o(has_grab_1, _has("Roll Form")),                                           # grey
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
        _o(_has("Explosive Plunger Box"), can_bounce),                               # blue
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
        _c(_o(can_pass_through_fire), 
           _o(_c(has_grab_1, can_pound_cracked_blocks), 
              _has("Zombie Form"), _has("Roll Form"))),                              # red
        _c(has_grab_1, _o(_has("Jackhammer"), can_fly)),                             # green
        _c(_o(can_jump_high), _has("Pick Axe"), has_grab_1),                         # blue
    ],
    "Forest of Fear": [
        None,                                                                        # grey
        _c(_has("Mystery Handle"), _o(_c(has_grab_2, _has("High Jump Boots")),
                                      can_bounce)),                                  # red
        _c(_has("Mystery Handle"), has_grab_1),                                      # green
        _o(_has("Demon's Blood"), can_pass_spikes),                                  # blue
    ],
}

# ---------------------------------------------------------------------------
# Per-coin access rules (additional requirements beyond the level unlock)
# Coins are 1-8, labeled on maps in the the docs
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
        _c(_o(can_shake_screen,_has("Zombie Form")),_has("Garlic")),                    #6
        _o(can_pound_large_solid_blocks,
           _c(_o(can_shake_screen,_has("Zombie Form")),_has("Garlic"))),                #7
        _o(can_pound_large_solid_blocks,
           _c(_o(can_shake_screen,_has("Zombie Form")),_has("Garlic"))),                #8
    ],
    "The Vast Plain": [
        _o(_has("Magic Seeds"),_has("Puffy Form")),                                     #1
        None,                                                                           #2
        _o(has_chemicals, can_pass_spikes),                                             #3
        can_pound_cracked_blocks,                                                       #4
        _o(has_flippers_1,_has("Zombie Form")),                                         #5
        _o(_has("Magic Seeds"),_c(can_fly,has_chemicals)),                              #6
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
        _c(can_pound_solid_blocks,_has("Night Vision Scope"),can_jump_high),            #6
        can_pound_solid_blocks,                                                         #7
        _c(can_pound_solid_blocks,_has("Night Vision Scope"),can_jump_high),            #8
    ],
    "Desert Ruins": [
        None,                                                                           #1
        _o(can_pound_cracked_blocks,_has("Garlic")),                                    #2
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
        _c(_o(_has("Foot of Stone"),_has("Roll Form")),has_flippers_1),                                       #8
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
        _c(has_chemicals,has_flippers_1,_o(has_grab_2,can_pass_spikes,can_fly)),        #5
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
        _c(_o(can_pound_cracked_blocks, _has("Yarn Form")), _o(has_grab_1, can_fly)),   #8
    ],
    "The Grasslands": [
        _o(_has("Flute"), _has("Puffy Form")),                                          #1
        _has("Magic Seeds"),                                                            #2
        None,                                                                           #3
        _o(_c(_has("High Jump Boots"),has_grab_1),can_bounce),                          #4
        can_jump_high,                                                                  #5
        _o(_has("Flute"), _has("Puffy Form")),                                          #6
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
        _c(has_flippers_1,_o(_c(_has("Garlic"),_o(can_shake_screen,can_bounce)),can_fly)),#8
    ],
    "Tower of Revival": [
        _c(has_golden_eyes, _has("Garlic"), has_grab_2, _has("Spiked Helmet"),
           _o(_has("Statue"),can_fly), _has("High Jump Boots")),                        #1
        _c(_o(_has("Statue"),can_fly), has_golden_eyes),                                #2
        _o(_has("Statue"),can_fly),                                                     #3
        _c(_o(_has("Statue"),can_fly), _has("Garlic")),                                 #4
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
        _c(_has("Rust Spray"), 
           _o(can_pound_cracked_blocks, _has("Zombie Form"), _has("Roll Form"))),       #7
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
        _has("Foot of Stone"),                                                          #3
        _has("Foot of Stone"),                                                          #4
        _has("Foot of Stone"),                                                          #5
        _has("Spiked Helmet"),                                                          #6
        _o(_has("Explosive Plunger Box"),_has("Zombie Form")),                          #7
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
        _c(_o(_c(has_key_cards,has_grab_1),can_fly),_has("Warp Removal Apparatus")),    #1
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
        _c(_has("Pick Axe"),can_jump_high,_o(has_grab_1,can_fly)),                      #7
        _c(_has("Pick Axe"),has_grab_1,can_jump_high),                                  #8
    ],
    "Forest of Fear": [
        _o(_has("High Jump Boots"),can_fly),                                            #1
        _c(_has("Mystery Handle"),
           _o(_c(has_grab_1,_has("High Jump Boots")),_has("Puffy Form"))),              #2
        _has("Mystery Handle"),                                                         #3
        _c(_has("Mystery Handle"), _o(has_grab_2,can_bounce)),                          #4
        None,                                                                           #5
        _c(_has("Mystery Handle"), _o(_c(has_grab_2, _has("High Jump Boots")),
                                      can_bounce)),                                     #6
        None,                                                                           #7
        None,                                                                           #8
    ],
}

# ---------------------------------------------------------------------------
# Per-boss access rules (additional requirements beyond the level unlock)
# Bosses are each their own single location
# ---------------------------------------------------------------------------

BOSS_RULES: dict = {
    "Wormwould":  has_overalls_1,
    "Shoot":      _o(_has("Spiked Helmet"), can_bounce),
    "Scowler":    _c(_has("Spiked Helmet"), has_flippers_1, can_pound_cracked_blocks),
    "Jamano":     _c(_has("Foot of Stone"), can_jump_high),
    "Anonster":   _c(_has("Gold Magic"), has_grab_1, has_overalls_1, can_jump_high),
    "Wolfenboss": has_flippers_1,
    "Pesce":      has_flippers_2,
    "Muddee":     _c(_has("Foot of Stone"), has_overalls_1),
    "Doll Boy":   None,
    "Yellow Belly": _c(_o(can_pound_solid_blocks, _has("Zombie Form")), _o(has_grab_1, can_bounce), has_overalls_1),
}

able_to_beat_rudy = _c(has_grab_2,_o(has_overalls_1,has_vampire_1,_has("Zombie Form"),_has("Fat Form"),_has("Fire Form")))

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

DOOR_RULES: dict = {
    # N1 Out of the Woods
    "Out of the Woods - Green Chest":         _has("N1 - Door A Key"),
    "Out of the Woods - Big Coin 4":          _has("N1 - Door A Key"),
    "Out of the Woods - Grey Chest":          _has("N1 - Door B Key"),
    # N2 The Peaceful Village
    "The Peaceful Village - Big Coin 3":      _has("N2 - Door A Key"),
    # B room is also reachable from the roof via pipe F (Flute / high jump)
    "The Peaceful Village - Red Key":         _o(_has("N2 - Door B Key"), _has("Flute"), can_jump_high),
    "The Peaceful Village - Coin Block 3":    _o(_has("N2 - Door B Key"), _has("Flute"), can_jump_high),
    "The Peaceful Village - Grey Chest":      _has("N2 - Door C Key"),
    "The Peaceful Village - Red Chest":       _has("N2 - Door D Key"),
    "The Peaceful Village - Green Key":       _has("N2 - Door J Key"),
    "The Peaceful Village - Big Coin 4":      _has("N2 - Door J Key"),
    # N3 The Vast Plain
    "The Vast Plain - Green Chest":           _has("N3 - Door H Key"),
    "The Vast Plain - Blue Chest":            _has("N3 - Door J Key"),
    # N4 Bank of the Wild River. A-D: river bank doors behind breakable
    # blocks; F: river side -> Green Chest Room; G: Green Chest Room ->
    # Pesce room (green key); H: river lobby -> the big lower room.
    "Bank of the Wild River - Red Chest":     _has("N4 - Door A Key"),
    "Bank of the Wild River - Big Coin 7":    _has("N4 - Door B Key"),
    "Bank of the Wild River - Big Coin 6":    _has("N4 - Door C Key"),
    "Bank of the Wild River - Red Key":       _has("N4 - Door D Key"),
    "Bank of the Wild River - Green Chest":   _has("N4 - Door F Key"),
    "Bank of the Wild River - Green Key":     _c(_has("N4 - Door F Key"), _has("N4 - Door G Key")),
    "Bank of the Wild River - Blue Key":      _has("N4 - Door H Key"),
    "Bank of the Wild River - Blue Chest":    _has("N4 - Door H Key"),
    "Bank of the Wild River - Big Coin 8":    _has("N4 - Door H Key"),
    "Pesce - Defeated":                       _c(_has("N4 - Door F Key"), _has("N4 - Door G Key")),
    # N5 The Tidal Coast. A: outside -> the octopi room (and the blue chest
    # room past it); D: outside -> the vine rooms; E: outside -> the green
    # key room; F / I: vine rooms -> green chest room (either will do);
    # H only leads back up from it. Underwater doors: C, from the tall water
    # room -> the red chest room; J, from the octopi room -> the blue chest
    # room.
    "The Tidal Coast - Blue Key":             _has("N5 - Door A Key"),
    "The Tidal Coast - Big Coin 7":           _has("N5 - Door A Key"),
    "The Tidal Coast - Big Coin 8":           _has("N5 - Door A Key"),
    "The Tidal Coast - Blue Chest":           _c(_has("N5 - Door A Key"), _has("N5 - Door J Key")),
    "The Tidal Coast - Red Chest":            _has("N5 - Door C Key"),
    "The Tidal Coast - Big Coin 5":           _has("N5 - Door C Key"),
    # N6 Sea Turtle Rocks, from the lobby: A -> Scowler's room (also reached
    # from the pipe room's lower pipes, past C); B -> the minigame / red
    # chest room; C -> the pipe room (green), whose pipe F leads to the dark
    # room, where G -> the blue chest room.
    "Sea Turtle Rocks - Grey Chest":          _o(_has("N6 - Door A Key"), _has("N6 - Door C Key")),
    "Sea Turtle Rocks - Big Coin 5":          _o(_has("N6 - Door A Key"), _has("N6 - Door C Key")),
    "Sea Turtle Rocks - Red Key":             _has("N6 - Door B Key"),
    "Sea Turtle Rocks - Red Chest":           _has("N6 - Door B Key"),
    "Sea Turtle Rocks - Green Key":           _has("N6 - Door C Key"),
    "Sea Turtle Rocks - Green Chest":         _has("N6 - Door C Key"),
    "Sea Turtle Rocks - Big Coin 7":          _has("N6 - Door C Key"),
    "Sea Turtle Rocks - Blue Key":            _c(_has("N6 - Door C Key"), _has("N6 - Door G Key")),
    "Sea Turtle Rocks - Blue Chest":          _c(_has("N6 - Door C Key"), _has("N6 - Door G Key")),
    "Sea Turtle Rocks - Big Coin 6":          _c(_has("N6 - Door C Key"), _has("N6 - Door G Key")),
    "Sea Turtle Rocks - Big Coin 8":          _c(_has("N6 - Door C Key"), _has("N6 - Door G Key")),
    "Scowler - Defeated":                     _o(_has("N6 - Door A Key"), _has("N6 - Door C Key")),
    # W1 Desert Ruins, from the lobby: A -> grey key room; B -> right hub
    # (coins 4-6), whose E -> grey chest room; C -> red key room; D -> left
    # hub (green key/chest, coin 7), whose F -> red chest room and G -> the
    # switch room (coin 3); its H -> the stair room (blue key, coin 8), whose
    # I -> the Yellow Belly room (blue chest). Strict: the stair room may be
    # reachable without H.
    "Desert Ruins - Grey Key":                _has("W1 - Door A Key"),
    "Desert Ruins - Big Coin 4":              _has("W1 - Door B Key"),
    "Desert Ruins - Big Coin 5":              _has("W1 - Door B Key"),
    "Desert Ruins - Big Coin 6":              _has("W1 - Door B Key"),
    "Desert Ruins - Grey Chest":              _c(_has("W1 - Door B Key"), _has("W1 - Door E Key")),
    "Desert Ruins - Red Key":                 _has("W1 - Door C Key"),
    "Desert Ruins - Green Key":               _has("W1 - Door D Key"),
    "Desert Ruins - Green Chest":             _has("W1 - Door D Key"),
    "Desert Ruins - Big Coin 7":              _has("W1 - Door D Key"),
    "Desert Ruins - Red Chest":               _c(_has("W1 - Door D Key"), _has("W1 - Door F Key")),
    "Desert Ruins - Big Coin 3":              _c(_has("W1 - Door D Key"), _has("W1 - Door G Key")),
    "Desert Ruins - Blue Key":                _c(_has("W1 - Door D Key"), _has("W1 - Door G Key"), _has("W1 - Door H Key")),
    "Desert Ruins - Big Coin 8":              _c(_has("W1 - Door D Key"), _has("W1 - Door G Key"), _has("W1 - Door H Key")),
    "Desert Ruins - Blue Chest":              _c(_c(_has("W1 - Door D Key"), _has("W1 - Door G Key"), _has("W1 - Door H Key")), _has("W1 - Door I Key")),
    # W2 The Volcano's Base: E (lobby) -> the ladder room (coin 4), whose
    # pipe F -> the cloud room (red key / chest, coins 5, 6), whose G -> the
    # green key room (coin 7) and H -> the green chest room; I (lobby, above
    # the rock pile) -> the blue chest room; C (Doll Boy's room) -> the grey
    # chest room; K (J's water room) -> L's room (coin 8). Strict: the cloud
    # room and the grey chest may have other ways in.
    "The Volcano's Base - Big Coin 4":        _has("W2 - Door E Key"),
    "The Volcano's Base - Red Key":           _has("W2 - Door E Key"),
    "The Volcano's Base - Red Chest":         _has("W2 - Door E Key"),
    "The Volcano's Base - Big Coin 5":        _has("W2 - Door E Key"),
    "The Volcano's Base - Big Coin 6":        _has("W2 - Door E Key"),
    "The Volcano's Base - Green Key":         _c(_has("W2 - Door E Key"), _has("W2 - Door G Key")),
    "The Volcano's Base - Big Coin 7":        _c(_has("W2 - Door E Key"), _has("W2 - Door G Key")),
    "The Volcano's Base - Green Chest":       _c(_has("W2 - Door E Key"), _has("W2 - Door H Key")),
    "The Volcano's Base - Blue Chest":        _has("W2 - Door I Key"),
    "The Volcano's Base - Grey Chest":        _has("W2 - Door C Key"),
    "The Volcano's Base - Big Coin 8":        _has("W2 - Door K Key"),
    # W3 The Pool of Rain: A (lobby) -> the grey chest room; D (the pool,
    # underwater) -> the currents (green key, coins 5-7), whose F
    # (underwater) -> Wolfenboss's room (green chest below him). Strict: G
    # (unlocked) also reaches Wolfenboss's room from the currents.
    "The Pool of Rain - Grey Chest":          _has("W3 - Door A Key"),
    "The Pool of Rain - Green Key":           _has("W3 - Door D Key"),
    "The Pool of Rain - Big Coin 5":          _has("W3 - Door D Key"),
    "The Pool of Rain - Big Coin 6":          _has("W3 - Door D Key"),
    "The Pool of Rain - Big Coin 7":          _has("W3 - Door D Key"),
    "The Pool of Rain - Green Chest":         _c(_has("W3 - Door D Key"), _has("W3 - Door F Key")),
    "Wolfenboss - Defeated":                  _c(_has("W3 - Door D Key"), _has("W3 - Door F Key")),
    # W4 A Town in Chaos, from the lobby: A -> the red key room (coin 3),
    # whose K -> the pipe water room (blue key, coin 6), whose L -> the blue
    # chest room; B -> the grey key room (coin 2), whose C -> the sunlight
    # room (coin 4), whose E -> Shoot's room (red chest); G -> the hub (green
    # chest, coin 5), whose H / I -> the coin 7 / 8 switch rooms. Strict: D
    # and F (unlocked) also reach the sunlight room and Shoot's room.
    "A Town in Chaos - Red Key":              _has("W4 - Door A Key"),
    "A Town in Chaos - Big Coin 3":           _has("W4 - Door A Key"),
    "A Town in Chaos - Grey Key":             _has("W4 - Door B Key"),
    "A Town in Chaos - Big Coin 2":           _has("W4 - Door B Key"),
    "A Town in Chaos - Big Coin 4":           _c(_has("W4 - Door B Key"), _has("W4 - Door C Key")),
    "A Town in Chaos - Red Chest":            _c(_has("W4 - Door B Key"), _has("W4 - Door C Key"), _has("W4 - Door E Key")),
    "Shoot - Defeated":                       _c(_has("W4 - Door B Key"), _has("W4 - Door C Key"), _has("W4 - Door E Key")),
    "A Town in Chaos - Green Chest":          _has("W4 - Door G Key"),
    "A Town in Chaos - Big Coin 5":           _has("W4 - Door G Key"),
    "A Town in Chaos - Big Coin 7":           _c(_has("W4 - Door G Key"), _has("W4 - Door H Key")),
    "A Town in Chaos - Big Coin 8":           _c(_has("W4 - Door G Key"), _has("W4 - Door I Key")),
    "A Town in Chaos - Blue Key":             _c(_has("W4 - Door A Key"), _has("W4 - Door K Key")),
    "A Town in Chaos - Big Coin 6":           _c(_has("W4 - Door A Key"), _has("W4 - Door K Key")),
    "A Town in Chaos - Blue Chest":           _c(_has("W4 - Door A Key"), _has("W4 - Door K Key"), _has("W4 - Door L Key")),
    # W5 Beneath the Waves, from the lobby: A -> the grey key room (coin 1);
    # B (the island, underwater) -> the zipline hub (coin 2, grey chest),
    # whose E / F / G -> the red / green / blue chest rooms (G's has coin 6);
    # from the arrow water room, I -> the red key room's left half (red key,
    # coin 7), H -> its right half (coin 8).
    "Beneath the Waves - Grey Key":             _has("W5 - Door A Key"),
    "Beneath the Waves - Big Coin 1":           _has("W5 - Door A Key"),
    "Beneath the Waves - Big Coin 2":           _has("W5 - Door B Key"),
    "Beneath the Waves - Grey Chest":           _has("W5 - Door B Key"),
    "Beneath the Waves - Red Chest":            _c(_has("W5 - Door B Key"), _has("W5 - Door E Key")),
    "Beneath the Waves - Green Chest":          _c(_has("W5 - Door B Key"), _has("W5 - Door F Key")),
    "Beneath the Waves - Blue Chest":           _c(_has("W5 - Door B Key"), _has("W5 - Door G Key")),
    "Beneath the Waves - Big Coin 6":           _c(_has("W5 - Door B Key"), _has("W5 - Door G Key")),
    "Beneath the Waves - Red Key":              _has("W5 - Door I Key"),
    "Beneath the Waves - Big Coin 7":           _has("W5 - Door I Key"),
    "Beneath the Waves - Big Coin 8":           _has("W5 - Door H Key"),
    # W6 The West Crater, from the lobby: A -> the red key room (coin 8); C
    # (past the flames) -> the green chest room (green key, coins 6, 7); D
    # (past the gate) -> the windy hub (blue key / chest, coins 3, 4).
    "The West Crater - Red Key":              _has("W6 - Door A Key"),
    "The West Crater - Big Coin 8":           _has("W6 - Door A Key"),
    "The West Crater - Green Key":            _has("W6 - Door C Key"),
    "The West Crater - Green Chest":          _has("W6 - Door C Key"),
    "The West Crater - Big Coin 6":           _has("W6 - Door C Key"),
    "The West Crater - Big Coin 7":           _has("W6 - Door C Key"),
    "The West Crater - Blue Key":             _has("W6 - Door D Key"),
    "The West Crater - Blue Chest":           _has("W6 - Door D Key"),
    "The West Crater - Big Coin 3":           _has("W6 - Door D Key"),
    "The West Crater - Big Coin 4":           _has("W6 - Door D Key"),
    # S1 The Grasslands, from the lobby: A / B -> Wormwould's room (bottom /
    # top; grey chest); C -> the grey key room (coin 3); D / E -> the tree
    # trunk (green key, coin 6), whose H (underwater) -> the green chest
    # room; F -> the red chest room (coin 8); G -> the vertical hub (and the
    # blue chest room past J: coins 4, 5), whose I -> the blue key room
    # (coin 7). Wormwould's room: B (the usual way in) or A with Puffy Form.
    "The Grasslands - Grey Chest":           _o(_has("S1 - Door B Key"), _c(_has("S1 - Door A Key"), _has("Puffy Form"))),
    "Wormwould - Defeated":                   _o(_has("S1 - Door B Key"), _c(_has("S1 - Door A Key"), _has("Puffy Form"))),
    "The Grasslands - Grey Key":             _has("S1 - Door C Key"),
    "The Grasslands - Big Coin 3":           _has("S1 - Door C Key"),
    "The Grasslands - Green Key":            _o(_has("S1 - Door D Key"), _has("S1 - Door E Key")),
    "The Grasslands - Big Coin 6":           _o(_has("S1 - Door D Key"), _has("S1 - Door E Key")),
    "The Grasslands - Green Chest":          _c(_o(_has("S1 - Door D Key"), _has("S1 - Door E Key")), _has("S1 - Door H Key")),
    "The Grasslands - Red Chest":            _has("S1 - Door F Key"),
    "The Grasslands - Big Coin 8":           _has("S1 - Door F Key"),
    "The Grasslands - Blue Chest":           _has("S1 - Door G Key"),
    "The Grasslands - Big Coin 4":           _has("S1 - Door G Key"),
    "The Grasslands - Big Coin 5":           _has("S1 - Door G Key"),
    "The Grasslands - Blue Key":             _c(_has("S1 - Door G Key"), _has("S1 - Door I Key")),
    "The Grasslands - Big Coin 7":           _c(_has("S1 - Door G Key"), _has("S1 - Door I Key")),
    # S2 The Big Bridge, from the lobby: A -> the green key room (coin 7);
    # B (underwater) -> the red chest room (red key, coins 3, 4); C -> the
    # green chest room; D (past the lake) -> the blue key room (coin 8); E
    # (underwater) -> the blue chest room (coins 5, 6).
    "The Big Bridge - Green Key":            _has("S2 - Door A Key"),
    "The Big Bridge - Big Coin 7":           _has("S2 - Door A Key"),
    "The Big Bridge - Red Key":              _has("S2 - Door B Key"),
    "The Big Bridge - Red Chest":            _has("S2 - Door B Key"),
    "The Big Bridge - Big Coin 3":           _has("S2 - Door B Key"),
    "The Big Bridge - Big Coin 4":           _has("S2 - Door B Key"),
    "The Big Bridge - Green Chest":          _has("S2 - Door C Key"),
    "The Big Bridge - Blue Key":             _has("S2 - Door D Key"),
    "The Big Bridge - Big Coin 8":           _has("S2 - Door D Key"),
    "The Big Bridge - Blue Chest":           _has("S2 - Door E Key"),
    "The Big Bridge - Big Coin 5":           _has("S2 - Door E Key"),
    "The Big Bridge - Big Coin 6":           _has("S2 - Door E Key"),
    # S3 Tower of Revival: D (the lobby tower's top) -> the blue chest room
    "Tower of Revival - Blue Chest":          _has("S3 - Door D Key"),
    "Tower of Revival - Big Coin 1":          _has("S3 - Door D Key"),
    # S5 Cave of Flames, from the lobby: A -> the red chest room (red key,
    # coin 2; coin 4's room past B); E (past the rust blocks) -> the blue
    # chest room (blue key, coin 6), whose G -> the vertical room (coin 7;
    # coin 8 past F); H -> the stay-down room (coin 5).
    "Cave of Flames - Red Key":              _has("S5 - Door A Key"),
    "Cave of Flames - Red Chest":            _has("S5 - Door A Key"),
    "Cave of Flames - Big Coin 2":           _has("S5 - Door A Key"),
    "Cave of Flames - Big Coin 4":           _has("S5 - Door A Key"),
    "Cave of Flames - Blue Key":             _has("S5 - Door E Key"),
    "Cave of Flames - Blue Chest":           _has("S5 - Door E Key"),
    "Cave of Flames - Big Coin 6":           _has("S5 - Door E Key"),
    "Cave of Flames - Big Coin 7":           _c(_has("S5 - Door E Key"), _has("S5 - Door G Key")),
    "Cave of Flames - Big Coin 8":           _c(_has("S5 - Door E Key"), _has("S5 - Door G Key")),
    "Cave of Flames - Big Coin 5":           _has("S5 - Door H Key"),
    # S6 Above the Clouds: A -> the grey key cave (coins 3, 4); B / C -> the
    # red chest room's left (red chest, coin 5) / right (red key) parts; D
    # (balloon) -> the green chest room (green key, coins 6-8); F (from E's
    # temple room, night) -> the blue chest room. Strict: B and C's parts may
    # connect.
    "Above the Clouds - Grey Key":             _has("S6 - Door A Key"),
    "Above the Clouds - Big Coin 3":           _has("S6 - Door A Key"),
    "Above the Clouds - Big Coin 4":           _has("S6 - Door A Key"),
    "Above the Clouds - Red Chest":            _has("S6 - Door B Key"),
    "Above the Clouds - Big Coin 5":           _has("S6 - Door B Key"),
    "Above the Clouds - Red Key":              _has("S6 - Door C Key"),
    "Above the Clouds - Green Chest":          _has("S6 - Door D Key"),
    "Above the Clouds - Green Key":            _has("S6 - Door D Key"),
    "Above the Clouds - Big Coin 6":           _has("S6 - Door D Key"),
    "Above the Clouds - Big Coin 7":           _has("S6 - Door D Key"),
    "Above the Clouds - Big Coin 8":           _has("S6 - Door D Key"),
    "Above the Clouds - Blue Chest":           _has("S6 - Door F Key"),
    # E1 The Stagnant Swamp, from the lobby: C / D -> the wood hub (bottom /
    # top; red key, coins 4, 5; Jamano and the green chest past pipes G/F),
    # whose E -> the green key room (coin 8); H -> the blue chest room (blue
    # key, coins 6, 7).
    "The Stagnant Swamp - Red Key":              _o(_has("E1 - Door C Key"), _has("E1 - Door D Key")),
    "The Stagnant Swamp - Big Coin 4":           _o(_has("E1 - Door C Key"), _has("E1 - Door D Key")),
    "The Stagnant Swamp - Big Coin 5":           _o(_has("E1 - Door C Key"), _has("E1 - Door D Key")),
    "The Stagnant Swamp - Green Chest":          _o(_has("E1 - Door C Key"), _has("E1 - Door D Key")),
    "Jamano - Defeated":                      _o(_has("E1 - Door C Key"), _has("E1 - Door D Key")),
    "The Stagnant Swamp - Green Key":            _c(_o(_has("E1 - Door C Key"), _has("E1 - Door D Key")), _has("E1 - Door E Key")),
    "The Stagnant Swamp - Big Coin 8":           _c(_o(_has("E1 - Door C Key"), _has("E1 - Door D Key")), _has("E1 - Door E Key")),
    "The Stagnant Swamp - Blue Chest":           _has("E1 - Door H Key"),
    "The Stagnant Swamp - Blue Key":             _has("E1 - Door H Key"),
    "The Stagnant Swamp - Big Coin 6":           _has("E1 - Door H Key"),
    "The Stagnant Swamp - Big Coin 7":           _has("E1 - Door H Key"),
    # E2 The Frigid Sea, from the lobby: A -> the red chest room (coin 3);
    # B -> the red key room (coin 4); C (underwater) -> the green chest hub
    # (green key, coin 5), whose E (underwater) -> the pipe passthrough
    # (coins 6, 7); D -> the blue chest room (blue key, coin 8).
    "The Frigid Sea - Red Chest":            _has("E2 - Door A Key"),
    "The Frigid Sea - Big Coin 3":           _has("E2 - Door A Key"),
    "The Frigid Sea - Red Key":              _has("E2 - Door B Key"),
    "The Frigid Sea - Big Coin 4":           _has("E2 - Door B Key"),
    "The Frigid Sea - Green Chest":          _has("E2 - Door C Key"),
    "The Frigid Sea - Green Key":            _has("E2 - Door C Key"),
    "The Frigid Sea - Big Coin 5":           _has("E2 - Door C Key"),
    "The Frigid Sea - Big Coin 6":           _c(_has("E2 - Door C Key"), _has("E2 - Door E Key")),
    "The Frigid Sea - Big Coin 7":           _c(_has("E2 - Door C Key"), _has("E2 - Door E Key")),
    "The Frigid Sea - Blue Chest":           _has("E2 - Door D Key"),
    "The Frigid Sea - Blue Key":             _has("E2 - Door D Key"),
    "The Frigid Sea - Big Coin 8":           _has("E2 - Door D Key"),
    # E3 Castle of Illusions, from the lobby: A / B / C / D -> the grey /
    # red / green / blue chest rooms; from the green / blue chest rooms, I /
    # J -> the blue key room's left / right (blue key, coins 6, 7; strict:
    # both, until that room's switch/platform logic is redone); G (F/G
    # room) -> the switch room.
    "Castle of Illusions - Grey Chest":           _has("E3 - Door A Key"),
    "Castle of Illusions - Red Chest":            _has("E3 - Door B Key"),
    "Castle of Illusions - Green Chest":          _has("E3 - Door C Key"),
    "Castle of Illusions - Blue Chest":           _has("E3 - Door D Key"),
    "Castle of Illusions - Blue Key":             _c(_has("E3 - Door C Key"), _has("E3 - Door I Key"), _has("E3 - Door D Key"), _has("E3 - Door J Key")),
    "Castle of Illusions - Big Coin 6":           _c(_has("E3 - Door C Key"), _has("E3 - Door I Key"), _has("E3 - Door D Key"), _has("E3 - Door J Key")),
    "Castle of Illusions - Big Coin 7":           _c(_has("E3 - Door C Key"), _has("E3 - Door I Key"), _has("E3 - Door D Key"), _has("E3 - Door J Key")),
    # E4 The Colossal Hole, from the hole: A -> the red key room; B -> the
    # red chest room (coin 8); C -> the green chest room (coin 6); D (past
    # the falling blocks) -> the blue chest room (blue key, coin 7).
    "The Colossal Hole - Red Key":              _has("E4 - Door A Key"),
    "The Colossal Hole - Red Chest":            _has("E4 - Door B Key"),
    "The Colossal Hole - Big Coin 8":           _has("E4 - Door B Key"),
    "The Colossal Hole - Green Chest":          _has("E4 - Door C Key"),
    "The Colossal Hole - Big Coin 6":           _has("E4 - Door C Key"),
    "The Colossal Hole - Blue Chest":           _has("E4 - Door D Key"),
    "The Colossal Hole - Blue Key":             _has("E4 - Door D Key"),
    "The Colossal Hole - Big Coin 7":           _has("E4 - Door D Key"),
    # E6 The East Crater: B (crater) -> the green chest room (green key,
    # coin 6); C (red chest room) -> the Omodon room (coin 5), whose D -> the
    # red chest room's right part (red chest).
    "The East Crater - Green Chest":          _has("E6 - Door B Key"),
    "The East Crater - Green Key":            _has("E6 - Door B Key"),
    "The East Crater - Big Coin 6":           _has("E6 - Door B Key"),
    "The East Crater - Big Coin 5":           _has("E6 - Door C Key"),
    "The East Crater - Red Chest":            _c(_has("E6 - Door C Key"), _has("E6 - Door D Key")),
    # E7 Forest of Fear: E (lobby) -> the blue chest room (blue key, coin
    # 5); D (green chest room) -> the red chest room (coins 3, 4), whose F ->
    # the red key room (coin 6).
    "Forest of Fear - Blue Chest":           _has("E7 - Door E Key"),
    "Forest of Fear - Blue Key":             _has("E7 - Door E Key"),
    "Forest of Fear - Big Coin 5":           _has("E7 - Door E Key"),
    "Forest of Fear - Red Chest":            _has("E7 - Door D Key"),
    "Forest of Fear - Big Coin 3":           _has("E7 - Door D Key"),
    "Forest of Fear - Big Coin 4":           _has("E7 - Door D Key"),
    "Forest of Fear - Red Key":              _c(_has("E7 - Door D Key"), _has("E7 - Door F Key")),
    "Forest of Fear - Big Coin 6":           _c(_has("E7 - Door D Key"), _has("E7 - Door F Key")),
    "Yellow Belly - Defeated":                _c(_c(_has("W1 - Door D Key"), _has("W1 - Door G Key"), _has("W1 - Door H Key")), _has("W1 - Door I Key")),
    "The Tidal Coast - Green Key":            _has("N5 - Door E Key"),
    "The Tidal Coast - Green Chest":          _c(_has("N5 - Door D Key"),
                                                 _o(_has("N5 - Door F Key"), _has("N5 - Door I Key"))),
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
    glitches = int(world.options.minor_glitches)

    # Copies of the rules dicts for mutation, deep copies for chests, keys, and coins
    chest_logic = {k: list(v) for k, v in CHEST_RULES.items()} 
    key_logic   = {k: list(v) for k, v in KEY_RULES.items()}
    coin_logic   = {k: list(v) for k, v in COIN_RULES.items()}
    boss_logic = BOSS_RULES.copy()
    
    # Difficulty Constants
    knowledge_checks = 1
    hard_logic = 2
    easy_glitches = 1
    all_glitches = 2
    
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
        chest_logic["The Grasslands"][red] = _c(_o(_has("Magic Seeds"), has_vampire_2), _o(can_pound_cracked_blocks, _has("Zombie Form")))
        chest_logic["The Grasslands"][green] = _c(_o(_has("Flute"), _has("High Jump Boots"), can_fly), has_flippers_1)
        chest_logic["Tower of Revival"][blue] = _c(_c(has_golden_eyes, _has("Statue"), can_jump_high), _o(_c(_has("Garlic"), has_grab_2, _has("Spiked Helmet")),_has("Yarn Form")))
        chest_logic["Above the Clouds"][red] = _o(_c(_has("High Jump Boots"), _has("Spiked Helmet")), can_bounce)
        chest_logic["Castle of Illusions"][green] = _o(has_grab_1, can_bounce)
        chest_logic["Castle of Illusions"][blue] = _o(has_grab_1, can_bounce)
        chest_logic["The Warped Void"][green] = _o(_c(_has("Warp Removal Apparatus"),_o(has_grab_1,can_fly)),_c(has_key_cards,has_grab_1))
        chest_logic["The East Crater"][blue] = _c(_has("Pick Axe"), has_grab_1)
        key_logic["Out of the Woods"][red] = _o(can_pound_cracked_blocks, _has("Garlic"))
        key_logic["The Peaceful Village"][red] = None
        key_logic["The Peaceful Village"][green] = _o(_c(_o(can_shake_screen, _has("Zombie Form")), _has("Garlic")), _has("Flute"), can_jump_high)
        key_logic["The Vast Plain"][red] = _o(can_pound_cracked_blocks, _has("Zombie Form"))
        key_logic["Desert Ruins"][green] = _o(_c(_has("Spiked Helmet"),can_pound_cracked_blocks), _has("Garlic"), _has("Roll Form"))
        key_logic["Beneath the Waves"][red] = _c(_o(has_flippers_2, can_sink_in_water), has_flippers_1)
        key_logic["The Grasslands"][green] = _o(_has("Flute"), _has("High Jump Boots"), can_fly)
        key_logic["The Big Bridge"][green] = _c(has_flippers_1, _o(can_pound_cracked_blocks, _has("Zombie Form")), _o(has_grab_1, can_shake_screen, can_fly, _has("Roll Form")))
        key_logic["The Big Bridge"][blue] = _c(_o(has_flippers_1, has_grab_1), _o(_has("Garlic"), can_fly))
        key_logic["Castle of Illusions"][red] = _o(_c(_o(_c(has_grab_1, has_sun_medallion), has_grab_2), _o(can_shake_screen, _has("High Jump Boots"))), can_bounce)
        key_logic["Castle of Illusions"][blue] = _c(_o(_has("Castle Brick"), has_vampire_2), can_pound_cracked_blocks, _o(has_grab_1, can_fly, _c(_has("Zombie Form"),can_bounce)))
        key_logic["The Warped Void"][green] = _o(_c(_has("Warp Removal Apparatus"),_o(has_grab_1,can_bounce)),_c(has_key_cards,has_grab_1))
        key_logic["The East Crater"][blue] = _c(_has("Pick Axe"), has_grab_1)
        # Coins are 0 indexed, so one less than their counterparts on the level maps
        coin_logic["Out of the Woods"][0] = _o(_c(_has("High Jump Boots"), has_grab_1), can_fly)
        coin_logic["Out of the Woods"][6] = _o(can_pound_cracked_blocks, _has("Garlic"))
        coin_logic["The Peaceful Village"][3] = _c(_o(_has("Flute"),can_jump_high),_o(_has("Zombie Form"),can_pound_cracked_blocks))
        coin_logic["The Vast Plain"][3] = _o(can_pound_cracked_blocks, _has("Zombie Form"))
        coin_logic["Bank of the Wild River"][4] = _o(_has("Air Pump"),can_fly)
        coin_logic["The Tidal Coast"][5] = _c(has_grab_1, _o(has_flippers_2, _c(has_flippers_1, _o(_has("Spiked Helmet"), _has("Zombie Form"))), _c(_has("Zombie Form"), can_sink_in_water)))
        coin_logic["Desert Ruins"][1] = _o(can_pound_cracked_blocks,_has("Garlic"),_c(_has("Zombie Form"),can_jump_high))
        coin_logic["Desert Ruins"][2] = _c(_o(can_pound_solid_blocks, _has("Zombie Form")), _o(has_grab_1, can_jump_high), has_overalls_1)
        coin_logic["The Volcano's Base"][4] = None
        coin_logic["A Town in Chaos"][2] = _o(can_pound_solid_blocks, _c(_has("Spiked Helmet"), can_pound_cracked_blocks))
        coin_logic["A Town in Chaos"][4] = _c(_o(has_grab_2, can_kill_frogs), _o(_c(can_shake_screen, _has("High Jump Boots")), can_bounce))
        coin_logic["A Town in Chaos"][7] = _c(_o(has_grab_2, can_kill_frogs), _o(_c(can_shake_screen, _has("High Jump Boots")), _has("Puffy Form"), _has("Bouncy Form")))
        coin_logic["Beneath the Waves"][4] = _c(has_chemicals,has_flippers_1,_o(_c(can_shake_screen,has_grab_1),has_grab_2,can_pass_spikes,can_fly))
        coin_logic["Beneath the Waves"][6] = _c(_o(has_flippers_2, _c(has_flippers_1, can_sink_in_water)), _o(_c(has_grab_2, _has("Spiked Helmet")), can_bounce))
        coin_logic["The West Crater"][1] = _o(_c(_has("Rust Spray"),can_pound_cracked_blocks),_c(_has("Bouncy Form"),_has("Spiked Helmet"),can_fly))
        coin_logic["The Grasslands"][0] = _o(_has("Flute"), can_fly, _has("High Jump Boots"))
        coin_logic["The Grasslands"][5] = _o(_has("Flute"), can_fly, _has("High Jump Boots"))
        coin_logic["The Big Bridge"][7] = _c(_o(has_flippers_1,has_grab_1),_o(_c(_has("Garlic"),_o(can_shake_screen,can_bounce)),can_fly))
        coin_logic["Tower of Revival"][0] = _c(has_golden_eyes, _has("Garlic"), has_grab_2, _has("Spiked Helmet"), _has("Statue"), can_jump_high)
        coin_logic["Castle of Illusions"][1] = _o(_c(_o(_c(has_grab_1,has_sun_medallion),has_grab_2),_has("High Jump Boots")), can_bounce)
        coin_logic["Castle of Illusions"][2] = _o(_c(_o(_c(has_grab_1,has_sun_medallion),has_grab_2),can_shake_screen,_has("High Jump Boots")), can_bounce)  
        coin_logic["Castle of Illusions"][3] = _o(has_grab_2,can_bounce)
        coin_logic["Castle of Illusions"][5] = _c(_o(_has("Castle Brick"), has_vampire_2), _o(has_grab_1, can_fly, _has("Zombie Form")))
        coin_logic["Castle of Illusions"][6] = _c(_o(_has("Castle Brick"), has_vampire_2), _o(has_grab_1, can_fly, _has("Zombie Form")))        
        coin_logic["The Warped Void"][0] = _o(_c(has_key_cards,has_grab_1),_c(can_fly,_has("Warp Removal Apparatus")))
        coin_logic["The Warped Void"][3] = _o(_c(_has("Warp Removal Apparatus"),_o(has_grab_1,can_fly)),_c(has_key_cards,has_grab_1))
        coin_logic["The East Crater"][6] = _c(_has("Pick Axe"))
        coin_logic["The East Crater"][7] = _c(_has("Pick Axe"), has_grab_1)
        boss_logic["Yellow Belly"] = _c(_o(can_pound_solid_blocks, _has("Zombie Form")), _o(has_grab_1, can_jump_high), has_overalls_1)

    if difficulty >= hard_logic:
        chest_logic["Out of the Woods"][green] = _o(has_storm_pouch,can_fly)
        chest_logic["Beneath the Waves"][red] = has_flippers_1
        chest_logic["Beneath the Waves"][green] = _c(has_flippers_1,_o(has_grab_1,_has("Yarn Form"),_has("Roll Form")))
        chest_logic["Beneath the Waves"][blue] = _c(has_flippers_1,_o(has_grab_1,_has("Fat Form")))
        key_logic["The Volcano's Base"][red] = _o(_has("Truck Wheel"),_has("Flat Form"),can_fly)
        key_logic["A Town in Chaos"][green] = _c(_o(can_kill_frogs,has_grab_2),_o(_c(can_shake_screen, can_jump_high),can_bounce))
        key_logic["Above the Clouds"][red] = _o(_c(_has("High Jump Boots"),has_grab_1),can_bounce)
        key_logic["The East Crater"][grey] = _o(has_grab_1,_has("Zombie Form"))
        key_logic["The Frigid Sea"][red] = _o(has_grab_1,can_bounce)
        # Coins are 0 indexed, so one less than their counterparts on the level maps
        coin_logic["Out of the Woods"][3] = _o(has_flippers_2, has_storm_pouch, can_fly)
        coin_logic["The Pool of Rain"][5] = _c(has_flippers_1,_has("Spiked Helmet"))
        coin_logic["The Pool of Rain"][6] = _c(has_flippers_1,_has("Spiked Helmet"))
        coin_logic["The Frigid Sea"][3] = _o(has_grab_1,can_bounce)      
        coin_logic["The Frigid Sea"][5] = _c(_has("Scepter"),has_flippers_1,_has("Spiked Helmet"))    
        coin_logic["The Warped Void"][6] = _o(_c(has_key_cards, has_grab_1,_has("Spiked Helmet")),_c(_has("Warp Removal Apparatus"), can_fly))
        coin_logic["The Warped Void"][7] = _o(_c(has_key_cards, has_grab_1,_has("Spiked Helmet")),_c(_has("Warp Removal Apparatus"), can_fly))

    # Override some level requirements if glitches are in logic (overwrites difficulty options, we assume glitched players can do most tricks)
    if glitches >= easy_glitches:
        chest_logic["Bank of the Wild River"][green] = _o(has_flippers_2,_has("Flat Form"),_c(has_flippers_1,_has("Roll Form")))
        chest_logic["The Tidal Coast"][red] = _c(_o(has_flippers_1,_has("Flat Form")), has_grab_1)
        chest_logic["The Tidal Coast"][blue] = _c(_has("Garlic"),_o(_c(has_flippers_1,_has("Sapling of Growth")),_has("Flat Form")))
        chest_logic["Sea Turtle Rocks"][grey] = _c(can_pound_cracked_blocks,_has("Spiked Helmet"),_o(has_flippers_1,_c(can_fly,_has("Flat Form"))))
        chest_logic["Sea Turtle Rocks"][red] = _c(_has("Scepter"), can_pound_cracked_blocks, _o(has_flippers_1,_has("Flat Form")))
        chest_logic["The Pool of Rain"][blue] = _c(_o(has_flippers_1,_has("Flat Form")),_has("Air Pump"))
        chest_logic["Beneath the Waves"][grey] = _o(has_flippers_1,_has("Flat Form"))
        chest_logic["Beneath the Waves"][red] = _c(_o(has_flippers_1,_has("Flat Form")),_o(_has("High Jump Boots"),can_fly))
        chest_logic["Beneath the Waves"][green] = _c(_o(has_flippers_1,_has("Flat Form")),_o(has_grab_1,_has("Yarn Form"),_c(_has("Flat Form"),_has("Spiked Helmet"))),_o(_has("High Jump Boots"),can_fly))
        chest_logic["Beneath the Waves"][blue] = _c(_o(has_flippers_1,_has("Flat Form")),_o(has_grab_1,_has("Fat Form")),_o(_has("High Jump Boots"),can_fly))
        chest_logic["The Grasslands"][green] = _o(_c(_o(_has("Flute"),can_fly,_has("High Jump Boots")),_o(has_flippers_1,_c(_has("Flat Form"),_has("Puffy Form")))))
        chest_logic["The Big Bridge"][red] = _c(_o(has_flippers_1,_has("Flat Form")),_o(can_pound_cracked_blocks,_has("Zombie Form")))
        chest_logic["The Big Bridge"][blue] = _c(_has("Scepter"),_o(_has("Flat Form"),has_flippers_1),_o(_c(_has("Garlic"),_has("Spiked Helmet")),_has("Puffy Form")))
        chest_logic["The Steep Canyon"][green] = _c(_has("Foot of Stone"),_o(has_flippers_2,_has("Flat Form"),_c(_has("Roll Form"),has_flippers_1)),_o(can_shake_screen,can_fly))
        chest_logic["The Steep Canyon"][blue] = _c(_has("Rust Spray"), _o(can_pound_cracked_blocks, _has("Zombie Form"), _c(_has("Flat Form"), _has("Spiked Helmet"))))
        chest_logic["Cave of Flames"][blue] = _c(_o(_has("Rust Spray"),_c(_has("Flat Form"),_has("Bouncy Form"))),_o(_c(has_grab_1,_has("High Jump Boots")),can_bounce))
        chest_logic["Above the Clouds"][blue] = _c(_has("Scissors"),_has("Full Moon Gong"),_o(_c(_has("High Jump Boots"),can_shake_screen,has_grab_1),_c(can_jump_high,_has("Flat Form"),_has("Spiked Helmet"))))
        chest_logic["The Stagnant Swamp"][red] = _c(_has("Foot of Stone"),_o(has_overalls_1,has_vampire_2,_c(has_flippers_2, _has("High Jump Boots")),_c(_has("Flat Form"),_has("Puffy Form"))))
        chest_logic["The Frigid Sea"][green] = _c(_has("Scepter"),_o(has_flippers_1,_has("Flat Form")))
        chest_logic["The Frigid Sea"][blue] = _o(has_sun_medallion,has_flippers_2,_has("Flat Form"))
        key_logic["Desert Ruins"][green] = _o(_c(_has("Spiked Helmet"), _o(can_pound_cracked_blocks, _has("Flat Form"))))
        key_logic["Bank of the Wild River"][green] = _o(has_flippers_2,_has("Flat Form"),_c(has_flippers_1,_has("Roll Form")))
        key_logic["The Tidal Coast"][blue] = _c(_has("Garlic"),_o(_c(has_flippers_1,_has("Sapling of Growth")),_has("Flat Form")))
        key_logic["Sea Turtle Rocks"][red] = _c(_has("Scepter"), can_pound_cracked_blocks, _o(has_flippers_1,_has("Flat Form")))
        key_logic["The Volcano's Base"][green] = _c(_o(_has("Truck Wheel"), can_fly), _o(has_flippers_1,_has("Flat Form")))
        key_logic["The Volcano's Base"][blue] = _c(_o(_has("Foot of Stone"),_has("Roll Form"),_c(_has("Flat Form"),_has("Spiked Helmet"))),_o(_has("Flat Form"),has_flippers_2,_c(has_flippers_1,_o(_has("Spiked Helmet"),_has("Roll Form")))))
        key_logic["The Pool of Rain"][blue] = _c(_o(has_flippers_1,_has("Flat Form")),_has("Air Pump"))
        key_logic["Beneath the Waves"][blue] = _c(_o(has_flippers_1,_has("Flat Form")), has_chemicals)
        key_logic["The Big Bridge"][red] = _c(_o(has_flippers_1,_has("Flat Form")),_o(can_pound_cracked_blocks,_has("Zombie Form")))
        key_logic["The Big Bridge"][green] = _c(_o(has_flippers_1,_has("Flat Form")),has_grab_1,_o(can_pound_cracked_blocks,_has("Zombie Form")))
        key_logic["The Big Bridge"][blue] = _c(_o(has_flippers_1,_has("Flat Form")), _o(_has("Garlic"), can_fly))
        key_logic["The Steep Canyon"][green] = _c(_has("Foot of Stone"),_o(has_flippers_2,_has("Flat Form"),_c(_has("Roll Form"),has_flippers_1)),_o(can_shake_screen,can_fly))
        key_logic["The Steep Canyon"][blue] = _c(_has("Rust Spray"), _o(can_pound_cracked_blocks, _has("Zombie Form"), _c(_has("Flat Form"), _has("Spiked Helmet"))))
        key_logic["Cave of Flames"][grey] = _o(has_grab_1, _has("Roll Form"),_c(_has("Flat Form"), _has("Spiked Helmet")))
        key_logic["Cave of Flames"][blue] = _c(_o(_has("Rust Spray"),_c(_has("Flat Form"),_has("Bouncy Form"))),_o(_c(has_grab_1,_has("High Jump Boots")),can_bounce))
        key_logic["The Frigid Sea"][green] = _c(_has("Scepter"),_o(has_flippers_1,_has("Flat Form")))
        key_logic["The Frigid Sea"][blue] = _o(has_sun_medallion,has_flippers_2,_has("Flat Form"))
        key_logic["The East Crater"][red] = _c(_o(can_pass_through_fire), _o(_has("Zombie Form"), has_grab_1),_o(_c(has_grab_1, _o(can_pound_cracked_blocks)), _has("Zombie Form"), _c(_has("Flat Form"),_has("Spiked Helmet"))))
        # Coins are 0 indexed, so one less than their counterparts on the level maps
        coin_logic["Out of the Woods"][3] = _o(has_flippers_2,_c(has_storm_pouch,_has("High Jump Boots")),can_fly,_has("Flat Form"))
        coin_logic["The Peaceful Village"][1] = _o(_c(can_pound_large_solid_blocks,_has("Spiked Helmet")),_c(_has("Roll Form"),_o(_has("Fat Form"),_has("Snowman Form"))))
        coin_logic["The Vast Plain"][4] = _o(has_flippers_1,_has("Zombie Form"),_has("Flat Form"))
        coin_logic["Bank of the Wild River"][0] = _o(has_flippers_1,can_fly,_has("Flat Form"))
        coin_logic["Bank of the Wild River"][1] = _o(has_flippers_2,_has("Flat Form"),_c(has_flippers_1,_has("Roll Form")))
        coin_logic["Bank of the Wild River"][2] = _o(has_flippers_2,_has("Flat Form"),_c(has_flippers_1,_has("Roll Form")))
        coin_logic["Bank of the Wild River"][3] = _o(has_flippers_2,_has("Flat Form"),_c(has_flippers_1,_has("Roll Form")))
        coin_logic["The Tidal Coast"][4] = _c(_o(has_flippers_1,_has("Flat Form")), has_grab_1)
        coin_logic["The Tidal Coast"][5] = _c(_o(_c(has_flippers_1,_o(_has("Spiked Helmet"),_has("Roll Form"))),_has("Flat Form")),has_grab_1)
        coin_logic["The Tidal Coast"][6] = _c(_has("Garlic"),_o(_c(has_flippers_1,_has("Sapling of Growth")),_has("Flat Form")))
        coin_logic["The Tidal Coast"][7] = _c(_has("Garlic"),_o(_c(has_flippers_1,_has("Sapling of Growth")),_has("Flat Form")))
        coin_logic["Desert Ruins"][2] = _c(_o(can_pound_solid_blocks, _has("Zombie Form")), _o(has_grab_1, can_bounce), _o(has_overalls_1,_c(_has("Spiked Helmet"), _has("Flat Form"))))
        coin_logic["The Volcano's Base"][7] = _c(_o(_has("Foot of Stone"),_has("Roll Form"),_c(_has("Flat Form"),_has("Spiked Helmet"))),_o(_has("Flat Form"),has_flippers_1))
        coin_logic["The Pool of Rain"][1] = _o(has_flippers_1,_has("Flat Form"))
        coin_logic["The Pool of Rain"][2] = _o(has_flippers_2,_has("Flat Form"),_c(_has("Roll Form"),has_flippers_1))
        coin_logic["The Pool of Rain"][7] = _c(_o(has_flippers_1,_has("Flat Form")),_has("Air Pump"))
        coin_logic["Beneath the Waves"][4] = _c(has_chemicals,_o(has_flippers_1,_has("Flat Form")),_o(has_grab_2,can_pass_spikes,can_fly))
        coin_logic["Sea Turtle Rocks"][4] = _c(can_pound_cracked_blocks,_has("Spiked Helmet"),_o(has_flippers_1,_c(can_fly,_has("Flat Form"))))
        coin_logic["The Big Bridge"][0] = _o(has_grab_1,_c(_o(has_flippers_1,_has("Flat Form")),can_bounce))
        coin_logic["The Big Bridge"][2] = _c(_o(can_pound_cracked_blocks,_has("Zombie Form")),_o(has_flippers_1,_has("Flat Form")))
        coin_logic["The Big Bridge"][3] = _c(_o(can_pound_cracked_blocks,_has("Zombie Form")),_o(has_flippers_1,_has("Flat Form")))
        coin_logic["The Big Bridge"][4] = _c(_has("Scepter"),_o(has_flippers_1,_has("Flat Form")))
        coin_logic["The Big Bridge"][5] = _c(_has("Scepter"),_o(_has("Flat Form"),has_flippers_1),_o(_c(_has("Garlic"),_has("Spiked Helmet")),_has("Puffy Form")))
        coin_logic["The Big Bridge"][6] = _c(_o(has_flippers_1,_has("Flat Form")),_o(can_pound_cracked_blocks,_has("Zombie Form")),_o(can_shake_screen,can_fly))
        coin_logic["The Big Bridge"][7] = _c(_o(has_flippers_1,_has("Flat Form")),_o(_c(_has("Garlic"),_o(can_shake_screen,can_bounce)),can_fly))
        coin_logic["The Steep Canyon"][3] = _c(_has("Foot of Stone"),_o(has_flippers_2,_has("Flat Form"),_c(_has("Roll Form"),has_flippers_1)),_o(can_shake_screen,can_fly))
        coin_logic["The Steep Canyon"][4] = _c(_has("Foot of Stone"),_o(has_flippers_2,_has("Flat Form"),_c(_has("Roll Form"),has_flippers_1)),_o(can_shake_screen,can_fly))
        coin_logic["The Steep Canyon"][5] = _c(_has("Foot of Stone"),_o(has_flippers_2,_has("Flat Form"),_c(_has("Roll Form"),has_flippers_1)),_o(can_shake_screen,can_fly))
        coin_logic["The Steep Canyon"][6] = _c(_has("Rust Spray"), _o(can_pound_cracked_blocks, _has("Zombie Form"), _c(_has("Flat Form"), _has("Spiked Helmet"))))
        coin_logic["Cave of Flames"][5] = _c(_o(_has("Rust Spray"),_c(_has("Flat Form"),_has("Bouncy Form"))),can_pound_cracked_blocks,has_grab_1,can_jump_high)
        coin_logic["Cave of Flames"][6] = _c(_o(_has("Rust Spray"),_c(_has("Flat Form"),_has("Bouncy Form"))),can_pound_cracked_blocks,has_grab_1,can_jump_high)
        coin_logic["Cave of Flames"][7] = _c(_o(_has("Rust Spray"),_c(_has("Flat Form"),_has("Bouncy Form"))),can_pound_cracked_blocks,_o(_c(has_grab_1,_has("High Jump Boots")),can_bounce))
        coin_logic["The Frigid Sea"][1] = _o(has_sun_medallion,has_flippers_2,_has("Flat Form"),_c(_has("Roll Form"),has_flippers_1))
        coin_logic["The Frigid Sea"][4] = _c(_has("Scepter"),_o(has_flippers_1,_has("Flat Form")))
        coin_logic["The Frigid Sea"][5] = _c(_has("Scepter"),_o(has_flippers_1,_has("Flat Form")),_has("Spiked Helmet"),_has("High Jump Boots"))
        coin_logic["The Frigid Sea"][6] = _c(_has("Scepter"),_o(has_flippers_1,_has("Flat Form")))
        coin_logic["The Frigid Sea"][7] = _o(has_sun_medallion,has_flippers_2,_has("Flat Form"))
    if glitches >= all_glitches:
        chest_logic["The Peaceful Village"][red] = None
        chest_logic["The Peaceful Village"][green] = _o(can_pound_cracked_blocks,_has("Zombie Form"))
        chest_logic["The Tidal Coast"][green] = None
        chest_logic["The Grasslands"][blue] = None
        chest_logic["A Town in Chaos"][green] = _c(_o(has_grab_2,can_kill_frogs),_o(can_shake_screen,can_bounce))
        chest_logic["Castle of Illusions"][grey] = None
        chest_logic["The East Crater"][red] = _c(can_pass_through_fire,_o(_c(has_grab_1,has_overalls_1),_has("Fire Form")))
        key_logic["Out of the Woods"][green] = None
        key_logic["The Peaceful Village"][red] = None
        key_logic["The Peaceful Village"][green] = None
        key_logic["The Grasslands"][blue] = None
        key_logic["A Town in Chaos"][green] = _c(_o(has_grab_2,can_kill_frogs),_o(can_shake_screen,_has("Spiked Helmet"),can_fly),_has("High Jump Boots"))
        key_logic["Cave of Flames"][red] = None
        key_logic["Castle of Illusions"][red] = _o(can_shake_screen,can_jump_high)
        # Coins are 0 indexed, so one less than their counterparts on the level maps
        coin_logic["The Peaceful Village"][3] = _o(_has("Zombie Form"),can_pound_cracked_blocks)
        coin_logic["The Peaceful Village"][4] = None
        coin_logic["The Peaceful Village"][3] = _o(_has("Zombie Form"),can_pound_cracked_blocks)
        coin_logic["Castle of Illusions"][1] = can_jump_high
        coin_logic["Castle of Illusions"][2] = _o(can_jump_high,can_shake_screen)
    if glitches >= easy_glitches and difficulty >= knowledge_checks:
        key_logic["Desert Ruins"][green] = _o(_c(_has("Spiked Helmet"), _o(can_pound_cracked_blocks, _has("Flat Form"))), _has("Garlic"), _has("Roll Form"))
        chest_logic["The Big Bridge"][green] = _c(_o(has_flippers_1,_has("Flat Form")),_o(has_grab_1,can_fly,can_shake_screen),_o(can_pound_cracked_blocks,_has("Zombie Form")))
        key_logic["The Big Bridge"][blue] = _c(_o(has_flippers_1,_has("Flat Form"),has_grab_1), _o(_has("Garlic"), can_fly))
        coin_logic["The Big Bridge"][7] = _c(_o(has_flippers_1,_has("Flat Form"),has_grab_1),_o(_c(_has("Garlic"),_o(can_shake_screen,can_bounce)),can_fly))
        coin_logic["Beneath the Waves"][4] = _c(has_chemicals,_o(has_flippers_1,_has("Flat Form")),_o(_c(can_shake_screen,has_grab_1),has_grab_2,can_pass_spikes,can_fly))
    if glitches >= easy_glitches and difficulty >= hard_logic:
        coin_logic["Out of the Woods"][3] = _o(has_flippers_2,has_storm_pouch,can_fly,_has("Flat Form"))
        chest_logic["Beneath the Waves"][red] = _c(_o(has_flippers_1,_has("Flat Form")))
        chest_logic["Beneath the Waves"][green] = _c(_o(has_flippers_1,_has("Flat Form")),_o(has_grab_1,_has("Yarn Form"),_c(_has("Flat Form"),_has("Spiked Helmet"))))
        chest_logic["Beneath the Waves"][blue] = _c(_o(has_flippers_1,_has("Flat Form")),_o(has_grab_1,_has("Fat Form")))
        
    if world.options.enemizer:
        add_tf(coin_logic["Out of the Woods"], 1, _has("Fire Form"), can_pound_solid_blocks)
        add_tf(coin_logic["Out of the Woods"], 2, _has("Puffy Form"))
        add_tf(coin_logic["Out of the Woods"], 4, can_bounce)
        add_tf(coin_logic["Out of the Woods"], 6, _has("Flat Form"), _has("Roll Form"))
        add_tf(coin_logic["Out of the Woods"], 7, _has("Fat Form"), _has("Zombie Form"))
        add_tf(chest_logic["The Peaceful Village"], red, _has("Fat Form"), _has("Zombie Form"))
        add_tf(chest_logic["The Peaceful Village"], green, _has("Invisible Form"), can_fly)
        add_tf(key_logic["The Peaceful Village"], grey, can_pound_solid_blocks, _has("Zombie Form"))
        add_tf(key_logic["The Peaceful Village"], red, can_pound_solid_blocks, _has("Zombie Form"))
        add_tf(coin_logic["The Peaceful Village"], 0, _has("Zombie Form"))
        add_tf(coin_logic["The Peaceful Village"], 2, can_bounce)
        add_tf(chest_logic["The Vast Plain"], grey, _has("Invisible Form"))
        add_tf(chest_logic["The Vast Plain"], red, _has("Puffy Form"))
        add_tf(chest_logic["The Vast Plain"], green, _has("Invisible Form"))
        add_tf(chest_logic["The Vast Plain"], blue, _has("Invisible Form"))
        add_tf(key_logic["The Vast Plain"], grey, _has("Invisible Form"))
        add_tf(key_logic["The Vast Plain"], green, _has("Invisible Form"))
        add_tf(key_logic["The Vast Plain"], blue, _has("Invisible Form"))
        add_tf(coin_logic["The Vast Plain"], 1, _has("Invisible Form"))
        add_tf(coin_logic["The Vast Plain"], 2, _c(_has("Invisible Form"), can_pass_spikes))
        add_tf(coin_logic["The Vast Plain"], 3, _has("Puffy Form"))
        add_tf(coin_logic["The Vast Plain"], 4, _has("Invisible Form"))
        add_tf(coin_logic["The Vast Plain"], 5, _has("Invisible Form"))
        add_tf(coin_logic["The Vast Plain"], 6, _c(_has("Invisible Form"), _o(_has("Zombie Form"), can_fly)))
        add_tf(coin_logic["The Vast Plain"], 7, _c(_has("Invisible Form"), can_fly))
        add_tf(chest_logic["Bank of the Wild River"], blue, _has("Fire Form"))
        add_tf(key_logic["Bank of the Wild River"], blue, can_fly)
        add_tf(coin_logic["Bank of the Wild River"], 0, can_fly)
        add_tf(coin_logic["Bank of the Wild River"], 4, can_kill_frogs)
        add_tf(coin_logic["Bank of the Wild River"], 5, _has("Fire Form"))
        add_tf(coin_logic["Bank of the Wild River"], 7, _c(can_kill_frogs, _o(can_fly,_has("High Jump Boots"))))
        add_tf(chest_logic["The Tidal Coast"], grey, _has("Fire Form"))
        add_tf(coin_logic["The Tidal Coast"], 0, can_bounce)
        # add_tf(coin_logic["The Tidal Coast"], 1, can_fly, _has("Flat Form")) # uncomment if omodonmeka are randomized
        add_tf(coin_logic["The Tidal Coast"], 3, can_bounce)
        add_tf(chest_logic["Sea Turtle Rocks"], red, _has("Fat Form"))
        add_tf(key_logic["Sea Turtle Rocks"], red, _has("Fat Form"))
        add_tf(chest_logic["Desert Ruins"], green, _has("Yarn Form"))
        add_tf(chest_logic["Desert Ruins"], blue, can_fly) 
        add_tf(key_logic["Desert Ruins"], blue, can_fly) 
        add_tf(coin_logic["Desert Ruins"], 2, can_bounce) 
        add_tf(coin_logic["Desert Ruins"], 3, _has("Bouncy Form"), _has("High Jump Boots")) 
        add_tf(coin_logic["The Volcano's Base"], 6, can_fly) 
        add_tf(coin_logic["The Volcano's Base"], 7, can_fly) 
        add_tf(coin_logic["The Pool of Rain"], 7, can_fly)
        add_tf(chest_logic["The Pool of Rain"], blue, can_fly)
        add_tf(chest_logic["A Town in Chaos"], red, _has("Zombie Form")) 
        add_tf(chest_logic["A Town in Chaos"], green, can_fly) 
        add_tf(key_logic["A Town in Chaos"], green, _has("Fat Form"))
        coin_logic["A Town in Chaos"][3] = _c(_has("Zombie Form"), _o(can_bounce, _has("Spiked Helmet")))
        add_tf(coin_logic["A Town in Chaos"], 7, _has("Bouncy Form"), _has("Puffy Form"))
        add_tf(chest_logic["Beneath the Waves"], green, _has("Yarn Form"), _has("Roll Form"))
        add_tf(chest_logic["Beneath the Waves"], blue, _has("Fat Form"))
        add_tf(coin_logic["Beneath the Waves"], 4, can_pass_spikes, can_fly)
        add_tf(coin_logic["Beneath the Waves"], 5, can_bounce)
        add_tf(coin_logic["Beneath the Waves"], 6, can_bounce)
        add_tf(coin_logic["Beneath the Waves"], 7, can_bounce)
        add_tf(chest_logic["The West Crater"], grey, _has("Yarn Form"), _c(_has("Rust Spray"), can_pound_cracked_blocks))
        add_tf(coin_logic["The West Crater"], 0, can_bounce)
        add_tf(coin_logic["The West Crater"], 1, _has("Yarn Form"), _c(_has("Rust Spray"), can_pound_cracked_blocks))
        add_tf(coin_logic["The West Crater"], 3, _has("Fat Form"))
        add_tf(key_logic["The Grasslands"], grey, _has("Flat Form"), can_bounce)
        add_tf(chest_logic["The Grasslands"], blue, _has("Yarn Form"))
        add_tf(key_logic["The Grasslands"], blue, can_bounce)
        add_tf(coin_logic["The Grasslands"], 2, _has("Zombie Form"), can_fly) 
        add_tf(coin_logic["The Grasslands"], 3, _c(can_bounce,_has("Yarn Form")))
        add_tf(coin_logic["The Grasslands"], 4, _c(can_bounce,_has("Yarn Form")))
        add_tf(coin_logic["The Grasslands"], 6, can_bounce)
        add_tf(coin_logic["The Big Bridge"], 6, can_fly) 
        add_tf(coin_logic["The Big Bridge"], 7, can_fly) 
        add_tf(chest_logic["The Steep Canyon"], red, can_fly)
        add_tf(chest_logic["The Steep Canyon"], green, can_fly)
        add_tf(key_logic["The Steep Canyon"], red, can_fly)
        add_tf(key_logic["The Steep Canyon"], green, can_fly)
        add_tf(coin_logic["The Steep Canyon"], 2, can_fly)
        add_tf(coin_logic["The Steep Canyon"], 3, can_fly)
        add_tf(coin_logic["The Steep Canyon"], 4, can_fly)
        add_tf(coin_logic["The Steep Canyon"], 5, can_fly)
        add_tf(chest_logic["Cave of Flames"], red, _c(can_bounce, _o(_has("Flat Form"), has_flippers_2, _has("Roll Form")), _has("Fat Form")))
        add_tf(chest_logic["Cave of Flames"], green, _has("Invisible Form"), _has("Zombie Form"))
        add_tf(chest_logic["Cave of Flames"], blue, can_bounce)
        add_tf(key_logic["Cave of Flames"], red, can_bounce)
        add_tf(key_logic["Cave of Flames"], green, _has("Invisible Form"))
        add_tf(key_logic["Cave of Flames"], blue, can_bounce)
        add_tf(coin_logic["Cave of Flames"], 0, can_bounce)
        add_tf(coin_logic["Cave of Flames"], 1, can_bounce)
        add_tf(coin_logic["Cave of Flames"], 3, _c(can_bounce, _o(has_flippers_2, _has("Flat Form"), _has("Roll Form"))))
        add_tf(coin_logic["Cave of Flames"], 4, _has("Bouncy Form"))
        add_tf(coin_logic["Cave of Flames"], 5, can_bounce)
        add_tf(coin_logic["Cave of Flames"], 6, can_bounce)
        add_tf(coin_logic["Cave of Flames"], 7, can_bounce)
        add_tf(chest_logic["Above the Clouds"], blue, can_bounce, _has ("Roll Form"))
        add_tf(key_logic["Above the Clouds"], green, _has("Zombie Form"))
        add_tf(coin_logic["Above the Clouds"], 6, _has("Zombie Form"))
        add_tf(coin_logic["Above the Clouds"], 7, _has("Zombie Form"))
        add_tf(chest_logic["The Stagnant Swamp"], blue, can_fly)
        add_tf(key_logic["The Stagnant Swamp"], green, can_bounce)
        add_tf(key_logic["The Stagnant Swamp"], blue, can_fly)
        add_tf(coin_logic["The Stagnant Swamp"], 6, can_fly)
        add_tf(coin_logic["The Stagnant Swamp"], 7, can_bounce)
        add_tf(chest_logic["The Frigid Sea"], red, _has("Snowman Form")) # remove if snow drops aren't randomized
        add_tf(key_logic["The Frigid Sea"], blue, _has("Snowman Form")) # remove if snow drops aren't randomized
        add_tf(coin_logic["The Frigid Sea"], 2, _has("Snowman Form")) # remove if snow drops aren't randomized
        add_tf(coin_logic["The Frigid Sea"], 7, _has("Snowman Form")) # remove if snow drops aren't randomized
        add_tf(key_logic["Castle of Illusions"], red, can_bounce)
        add_tf(key_logic["Castle of Illusions"], green, can_bounce)
        add_tf(coin_logic["Castle of Illusions"], 0, _has("Zombie Form"), can_fly)
        add_tf(coin_logic["Castle of Illusions"], 1, can_bounce)
        add_tf(coin_logic["Castle of Illusions"], 2, can_bounce)
        add_tf(coin_logic["Castle of Illusions"], 3, can_bounce)
        add_tf(coin_logic["Castle of Illusions"], 4, can_bounce)
        add_tf(coin_logic["Castle of Illusions"], 7, can_bounce)
        add_tf(chest_logic["The Colossal Hole"], grey, can_jump_high, has_sun_medallion)
        add_tf(chest_logic["The Colossal Hole"], green, _has("Fire Form"), _has("Zombie Form"))
        add_tf(chest_logic["The Colossal Hole"], blue, can_jump_high, has_sun_medallion)
        add_tf(key_logic["The Colossal Hole"], grey, can_jump_high, has_sun_medallion)
        add_tf(key_logic["The Colossal Hole"], green,  _has("Fire Form")) 
        add_tf(key_logic["The Colossal Hole"], blue, can_jump_high, has_sun_medallion)
        add_tf(coin_logic["The Colossal Hole"], 0, can_jump_high, has_sun_medallion) 
        add_tf(coin_logic["The Colossal Hole"], 1, can_jump_high, has_sun_medallion) 
        add_tf(coin_logic["The Colossal Hole"], 2, can_jump_high, has_sun_medallion) 
        # add_tf(coin_logic["The Colossal Hole"], 3, _has("Flat Form"), _has("Roll Form")) # uncomment if omodonmeka are randomized
        add_tf(coin_logic["The Colossal Hole"], 4, can_jump_high, has_sun_medallion) 
        add_tf(coin_logic["The Colossal Hole"], 6, can_jump_high, has_sun_medallion) 
        add_tf(key_logic["The Warped Void"], blue, _has("Fat Form"))
        # add_tf(key_logic["The Warped Void"], blue, _c(_has("Fat Form"), _has("Flat Form"))) # uncomment if omodonmeka are randomized
        add_tf(coin_logic["The Warped Void"], 1, can_bounce)
        # add_tf(coin_logic["The Warped Void"], 4, _has("Flat Form", has_vampire_2)) # uncomment if omodonmeka are randomized
        add_tf(key_logic["The East Crater"], green, can_fly)
        add_tf(chest_logic["The East Crater"], blue, can_jump_high) # could have been removed by knowledge check
        add_tf(key_logic["The East Crater"], blue, can_jump_high) # could have been removed by knowledge check
        add_tf(coin_logic["The East Crater"], 0, can_fly)
        add_tf(coin_logic["The East Crater"], 1, can_fly)
        add_tf(coin_logic["The East Crater"], 4, _has("Flat Form"), _has("Roll Form")) # uncomment if omodonmeka are randomized
        add_tf(coin_logic["The East Crater"], 6, _c(can_jump_high, has_grab_1)) # could have been removed by knowledge check
        add_tf(coin_logic["The East Crater"], 7, can_jump_high) # could have been removed by knowledge check
        add_tf(chest_logic["Forest of Fear"], red, can_bounce)
        add_tf(chest_logic["Forest of Fear"], blue, _has("Zombie Form"))
        add_tf(key_logic["Forest of Fear"], red, can_bounce)
        add_tf(key_logic["Forest of Fear"], green, can_fly)
        add_tf(key_logic["Forest of Fear"], blue, can_pass_spikes)
        add_tf(coin_logic["Forest of Fear"], 2, can_bounce)
        add_tf(coin_logic["Forest of Fear"], 3, can_bounce)
        add_tf(coin_logic["Forest of Fear"], 7, can_pass_spikes)
        add_tf(boss_logic, "Shoot", _has("Zombie Form")) # Shoot
        add_tf(boss_logic, "Anonster", can_bounce) # Anonster
        add_tf(boss_logic, "Yellow Belly", can_fly) # Yellow Belly

        # Certain spots need to be changed different ways depending on the player's logic options
        if difficulty < knowledge_checks:
            add_tf(key_logic["The Tidal Coast"], grey, can_bounce) # garlic if knowledge checks
            add_tf(key_logic["The Tidal Coast"], green, can_bounce) # garlic if knowledge checks
            add_tf(key_logic["The Vast Plain"], red, _has("Puffy Form")) # roll form if knowledge checks, spiked helmet + flat form if knowledge checks plus easy glitches
            add_tf(coin_logic["Desert Ruins"], 7, can_fly)
            # Knowledge: Flying to get around fire for Red Room, bat or flat to get further
            add_tf(chest_logic["Tower of Revival"], red, _c(_has("Fire Form"), _has("Fat Form"), _has("Zombie Form"))) # knowledge: Garlic and Fire
            add_tf(chest_logic["Tower of Revival"], green, _has("Fire Form"))
            add_tf(chest_logic["Tower of Revival"], blue, _c(_has("Fire Form"), _has("Yarn Form"), _has("Flat Form"))) # knowledge: Bat instead of Flat
            add_tf(key_logic["Tower of Revival"], grey, _c(can_fly, _has("Fire Form")))
            add_tf(key_logic["Tower of Revival"], red, _c(_has("Fire Form"), _has("Fat Form"), _has("Zombie Form"))) # knowledge: Garlic and Fire
            add_tf(key_logic["Tower of Revival"], green, _c(_has("Fire Form"),_has("Fat Form")))
            add_tf(key_logic["Tower of Revival"], blue, _has("Fire Form"))
            add_tf(coin_logic["Tower of Revival"], 0, _c(_has("Fire Form"),_has("Flat Form"))) # knowledge: Bat instead of Flat
            add_tf(coin_logic["Tower of Revival"], 1, _has("Fire Form"))
            add_tf(coin_logic["Tower of Revival"], 2, _has("Fire Form"))
            add_tf(coin_logic["Tower of Revival"], 3, _c(_has("Fire Form"),_has("Fat Form")))
            add_tf(coin_logic["Tower of Revival"], 4, _has("Fire Form"))
            add_tf(coin_logic["Tower of Revival"], 5, _c(_has("Fire Form"),_has("Fat Form")))
            add_tf(coin_logic["Tower of Revival"], 6, _c(_has("Fat Form"), _has("Fire Form"), _has("Zombie Form")))
            add_tf(coin_logic["Tower of Revival"], 7, _c(_has("Fire Form"),can_fly))
            # add_tf(chest_logic["The Colossal Hole"], red, _has("Flat Form")) # uncomment if omodonmeka are randomized
            # add_tf(coin_logic["The Colossal Hole"], 7, _has("Flat Form")) # uncomment if omodonmeka are randomized
            add_tf(key_logic["The Colossal Hole"], grey, can_jump_high, has_sun_medallion)
            add_tf(coin_logic["The Colossal Hole"], 2, can_jump_high, has_sun_medallion, _has("Zombie Form")) 
            add_tf(coin_logic["The Colossal Hole"], 4, can_jump_high, has_sun_medallion) 
            add_tf(coin_logic["The East Crater"], 2, can_kill_frogs)

        if difficulty >= knowledge_checks:
            key_logic["The Peaceful Village"][grey] = _o(can_pound_solid_blocks, _has("Zombie Form"), _has("Garlic"))
            coin_logic["The Peaceful Village"][0] = _o(_has("Zombie Form"), _has("Garlic"))
            add_tf(key_logic["The Tidal Coast"], grey, can_bounce, _has("Garlic")) 
            add_tf(key_logic["The Tidal Coast"], green, can_bounce, _has("Garlic"))
            add_tf(chest_logic["Tower of Revival"], red, _c(_o(_has("Fire Form"),can_fly), _o(_c(_has("Fat Form"), _has("Zombie Form"), _has("Fire Form")),_has("Garlic")))) # knowledge: Garlic and Fire
            add_tf(chest_logic["Tower of Revival"], green, _o(_has("Fire Form"),_c(_o(_has("Flat Form"),has_vampire_2,_has("Roll Form")),can_fly)))
            add_tf(chest_logic["Tower of Revival"], blue, _c(_o(_has("Fire Form"),_c(_o(_has("Flat Form"),has_vampire_2,_has("Roll Form")),can_fly)), _has("Yarn Form"), _o(_has("Flat Form"),_has("Roll Form"),has_vampire_2))) # knowledge: Bat instead of Flat
            add_tf(key_logic["Tower of Revival"], grey, _c(_o(_has("Fire Form"),_c(_o(_has("Flat Form"),has_vampire_2,_has("Roll Form")),can_fly)),can_fly))
            add_tf(key_logic["Tower of Revival"], red, _c(_o(_has("Fire Form"),can_fly), _o(_c(_has("Fat Form"), _has("Zombie Form"), _has("Fire Form")),_has("Garlic")))) # knowledge: Garlic and Fire
            add_tf(key_logic["Tower of Revival"], green, _c(_o(_has("Fire Form"),_c(_o(_has("Flat Form"),has_vampire_2,_has("Roll Form")),can_fly)),_has("Fat Form")))
            add_tf(key_logic["Tower of Revival"], blue, _o(_has("Fire Form"),_c(_o(_has("Flat Form"),has_vampire_2,_has("Roll Form")),can_fly)))
            add_tf(coin_logic["Tower of Revival"], 0, _c(_o(_has("Fire Form"),_c(_o(_has("Flat Form"),has_vampire_2,_has("Roll Form")),can_fly)),_o(_has("Flat Form"),_has("Roll Form"),has_vampire_2))) # knowledge: Bat instead of Flat
            add_tf(coin_logic["Tower of Revival"], 1, _o(_has("Fire Form"),_c(_o(_has("Flat Form"),has_vampire_2,_has("Roll Form")),can_fly)))
            add_tf(coin_logic["Tower of Revival"], 2, _o(_has("Fire Form"),_c(_o(_has("Flat Form"),has_vampire_2,_has("Roll Form")),can_fly)))
            add_tf(coin_logic["Tower of Revival"], 3, _c(_o(_has("Fire Form"),_c(_o(_has("Flat Form"),has_vampire_2,_has("Roll Form")),can_fly)),_has("Fat Form")))
            add_tf(coin_logic["Tower of Revival"], 4, _o(_has("Fire Form"),_c(_o(_has("Flat Form"),has_vampire_2,_has("Roll Form")),can_fly)))
            add_tf(coin_logic["Tower of Revival"], 5, _c(_o(_has("Fire Form"),_c(_o(_has("Flat Form"),has_vampire_2,_has("Roll Form")),can_fly)),_has("Fat Form")))
            add_tf(coin_logic["Tower of Revival"], 6, _c(_o(_has("Fire Form"),_c(_o(_has("Flat Form"),has_vampire_2,_has("Roll Form")),can_fly)), _o(_c(_has("Fat Form"), _has("Zombie Form"), _has("Fire Form")),_has("Garlic"))))
            add_tf(coin_logic["Tower of Revival"], 7, _c(_o(_has("Fire Form"),_c(_o(_has("Flat Form"),has_vampire_2,_has("Roll Form")),can_fly)),can_fly))

        if glitches < easy_glitches:
            add_tf(chest_logic["The Steep Canyon"], blue, _has("Fire Form"), _has("Roll Form"))
            add_tf(key_logic["The Steep Canyon"], blue, _has("Fire Form"), _has("Roll Form"))
            add_tf(coin_logic["The Steep Canyon"], 6, _has("Fire Form"), _has("Roll Form"))
            add_tf(coin_logic["The Steep Canyon"], 7, _has("Fire Form"), _has("Roll Form"))

        if glitches >= easy_glitches:
            add_tf(chest_logic["The Steep Canyon"], blue, _has("Fire Form"), _has("Roll Form"), _c(_has("Spiked Helmet"),_has("Flat Form")))
            add_tf(key_logic["The Steep Canyon"], blue, _has("Fire Form"), _has("Roll Form"), _c(_has("Spiked Helmet"),_has("Flat Form")))
            add_tf(coin_logic["The Steep Canyon"], 6, _has("Fire Form"), _has("Roll Form"), _c(_has("Spiked Helmet"),_has("Flat Form")))
            add_tf(coin_logic["The Steep Canyon"], 7, _has("Fire Form"), _has("Roll Form"), _c(_has("Spiked Helmet"),_has("Flat Form")))

        if glitches < all_glitches:
            key_logic["Out of the Woods"][green] = can_bounce

        if difficulty >= knowledge_checks and glitches < easy_glitches:
            add_tf(key_logic["The Vast Plain"], red, _has("Puffy Form"), _has("Roll Form"))
        if difficulty >= knowledge_checks and glitches >= easy_glitches:
            add_tf(key_logic["The Vast Plain"], red, _has("Puffy Form"), _c(_has("Spiked Helmet"),_has("Flat Form")), _has("Roll Form")) 
        
    # Builds position-indexed predicate list, then route each level's rule
    # through the entrance-shuffle map. LEVEL_RULES is already ordered by
    # vanilla owlevel (0..24) so `list(LEVEL_RULES.values())[pos]` is the
    # predicate for position. Append None at index 25 for the
    # Temple slot (unlocked from the start).

    position_predicates = list(LEVEL_RULES.values()) + [None]
    if combined:
        # Combined-mode overrides apply POSITION-first
        for pos_idx, combined_pred in (
            (6, unlock_w1c), (7, unlock_w2c),
            (11, unlock_w6_e4c), (12, unlock_s1c),
            (14, unlock_s3c), (15, unlock_s4c),
            (19, unlock_e2c), (20, unlock_e3c),
            (21, unlock_w6_e4c),
        ):
            position_predicates[pos_idx] = combined_pred

    # For each level (by its vanilla owlevel index), find the position
    # that shuffles TO it and inherit that position's predicate. Identity
    # entrance_map (when shuffle is off) reproduces vanilla LEVEL_RULES.
    level_names = list(LEVEL_RULES.keys())
    entrance_map = getattr(world, "entrance_map", list(range(26)))
    level_rules = {}
    for target_idx, level_name in enumerate(level_names):
        pos = entrance_map.index(target_idx)
        level_rules[level_name] = position_predicates[pos]

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

    # Coin Blocksanity — gated by level entry only for now. Each of the 44
    # blocks' exact in-room reachability (whether it needs a specific
    # breaking ability, flight, swimming, etc. beyond "the level is
    # accessible") is left to logic refinement later — same deferred
    # split as the rest of this project's detailed per-location rules.
    if world.options.coin_blocksanity:
        from .locations import COIN_BLOCK_LOCATION_TABLE
        for loc_name, loc_data in COIN_BLOCK_LOCATION_TABLE.items():
            level_rule = level_rules.get(loc_data.level_name)
            if level_rule is not None:
                mw.get_location(loc_name, player).access_rule = \
                    lambda state, r=level_rule: r(state, player)

    # Door signposts stand outside their door: reachable with the level,
    # unless the door is deeper in, where its sign takes the rule of a
    # location behind that door (set above; the door rules come below), or
    # the level's plus the chest logic of the chest behind it (not its key)
    # and any door key on the way there.
    from .locations import DOOR_SIGN_LOCATION_TABLE
    sign_rule_from = {
        "The Peaceful Village - Door J Sign": "The Peaceful Village - Green Key",
    }
    sign_chest_area = {
        "The Vast Plain - Door H Sign": (green, None),
        "The Vast Plain - Door J Sign": (blue, None),
        "Bank of the Wild River - Door F Sign": (green, None),
        "Bank of the Wild River - Door G Sign": (green, "N4 - Door F Key"),
        "Forest of Fear - Door D Sign": (green, None),
        "Forest of Fear - Door F Sign": (red, "E7 - Door D Key"),
        "Castle of Illusions - Door I Sign": (green, "E3 - Door C Key"),
        "Castle of Illusions - Door J Sign": (blue, "E3 - Door D Key"),
        "The Frigid Sea - Door C Sign": (green, None),
        "The Frigid Sea - Door E Sign": (green, "E2 - Door C Key"),
        # in the water before their doors: the swim there is the chest's
        "The Tidal Coast - Door C Sign": (red, None),
        "The Tidal Coast - Door J Sign": (blue, "N5 - Door A Key"),
    }
    # A-D's signposts are out when their door is: breaking in is what their
    # room's own logic asks for first.
    # signposts past another locked door: the level plus those keys
    sign_needs_keys = {
        "The Tidal Coast - Door F Sign": _has("N5 - Door D Key"),
        "The Tidal Coast - Door I Sign": _has("N5 - Door D Key"),
        # B's door is only there once the Scepter clears the water; G's
        # signpost is in the dark room, past C, where the door wants the scope
        "Sea Turtle Rocks - Door B Sign": _has("Scepter"),
        "The Volcano's Base - Door G Sign": _has("W2 - Door E Key"),
        "The Volcano's Base - Door H Sign": _has("W2 - Door E Key"),
        "The Pool of Rain - Door D Sign": has_flippers_1,
        "The Pool of Rain - Door F Sign": _c(_has("W3 - Door D Key"), has_flippers_1),
        "A Town in Chaos - Door C Sign": _has("W4 - Door B Key"),
        "A Town in Chaos - Door E Sign": _c(_has("W4 - Door B Key"), _has("W4 - Door C Key")),
        "A Town in Chaos - Door H Sign": _has("W4 - Door G Key"),
        "A Town in Chaos - Door I Sign": _has("W4 - Door G Key"),
        "A Town in Chaos - Door J Sign": _has("W4 - Door G Key"),
        "A Town in Chaos - Door K Sign": _has("W4 - Door A Key"),
        "A Town in Chaos - Door L Sign": _c(_has("W4 - Door A Key"), _has("W4 - Door K Key")),
        "Beneath the Waves - Door E Sign": _has("W5 - Door B Key"),
        "Beneath the Waves - Door F Sign": _has("W5 - Door B Key"),
        "Beneath the Waves - Door G Sign": _has("W5 - Door B Key"),
        "The Grasslands - Door H Sign": _o(_has("S1 - Door D Key"), _has("S1 - Door E Key")),
        "The Grasslands - Door I Sign": _has("S1 - Door G Key"),
        "Cave of Flames - Door G Sign": _c(_has("S5 - Door E Key"), _has("Rust Spray")),
        "The Stagnant Swamp - Door E Sign": _o(_has("E1 - Door C Key"), _has("E1 - Door D Key")),
        "The East Crater - Door D Sign": _has("E6 - Door C Key"),
        "Desert Ruins - Door E Sign": _has("W1 - Door B Key"),
        "Desert Ruins - Door F Sign": _has("W1 - Door D Key"),
        "Desert Ruins - Door G Sign": _has("W1 - Door D Key"),
        "Desert Ruins - Door H Sign": _c(_has("W1 - Door D Key"), _has("W1 - Door G Key")),
        "Desert Ruins - Door I Sign": _c(_has("W1 - Door D Key"), _has("W1 - Door G Key"), _has("W1 - Door H Key")),
        "Sea Turtle Rocks - Door G Sign": _c(_has("N6 - Door C Key"), _has("Night Vision Scope")),
        "The Tidal Coast - Door H Sign": _c(_has("N5 - Door D Key"),
                                            _o(_has("N5 - Door F Key"), _has("N5 - Door I Key"))),
    }
    sign_logic_from = {
        "Bank of the Wild River - Door A Sign": (chest_logic, red),
        "Bank of the Wild River - Door B Sign": (coin_logic, 6),
        "Bank of the Wild River - Door C Sign": (coin_logic, 5),
        "Bank of the Wild River - Door D Sign": (key_logic, red),
        "Beneath the Waves - Door H Sign": (coin_logic, 2),
        "Beneath the Waves - Door I Sign": (coin_logic, 2),
        "The West Crater - Door C Sign": (chest_logic, green),
        "The West Crater - Door D Sign": (chest_logic, blue),
        "The Big Bridge - Door D Sign": (key_logic, blue),
        "The Big Bridge - Door E Sign": (chest_logic, blue),
        "Cave of Flames - Door E Sign": (chest_logic, blue),
        "Above the Clouds - Door D Sign": (chest_logic, green),
        "Above the Clouds - Door F Sign": (chest_logic, blue),
        "Castle of Illusions - Door G Sign": (coin_logic, 3),
        "The Colossal Hole - Door D Sign": (chest_logic, blue),
        "The Volcano's Base - Door I Sign": (chest_logic, blue),
        "The Volcano's Base - Door K Sign": (key_logic, blue),
    }
    for loc_name, loc_data in DOOR_SIGN_LOCATION_TABLE.items():
        if loc_name in sign_rule_from:
            mw.get_location(loc_name, player).access_rule = \
                mw.get_location(sign_rule_from[loc_name], player).access_rule
            continue
        level_rule = level_rules.get(loc_data.level_name)
        if loc_name in sign_needs_keys:
            mw.get_location(loc_name, player).access_rule = \
                lambda state, r=level_rule, k=sign_needs_keys[loc_name]: \
                (r is None or r(state, player)) and k(state, player)
            continue
        if loc_name in sign_logic_from:
            table, index = sign_logic_from[loc_name]
            area = table[loc_data.level_name][index]
            mw.get_location(loc_name, player).access_rule = \
                lambda state, r=level_rule, a=area: \
                (r is None or r(state, player)) and (a is None or a(state, player))
            continue
        if loc_name in sign_chest_area:
            colour, door_key = sign_chest_area[loc_name]
            area = chest_logic[loc_data.level_name][colour]
            mw.get_location(loc_name, player).access_rule = \
                lambda state, r=level_rule, a=area, k=door_key: \
                (r is None or r(state, player)) and (a is None or a(state, player)) \
                and (k is None or state.has(k, player))
            continue
        if level_rule is not None:
            mw.get_location(loc_name, player).access_rule = \
                lambda state, r=level_rule: r(state, player)

    # Boss defeats — reuse each boss's existing chest access rule. Boss chest
    # locations always live in LOCATION_TABLE (they're regular chest slots
    # from the level's grey/red/green/blue set), so we can look up the
    # already-configured access rule and copy it onto the "Boss - Defeated"
    # location. Mapping mirrors _BOSSES in locations.py.
    if world.options.boss_defeats:
        for loc_name, loc_data in BOSS_DEFEAT_LOCATION_TABLE.items():
            level_rule = level_rules.get(loc_data.level_name)
            boss_rule = boss_logic.get(loc_data.boss_name)            
            if level_rule is not None and boss_rule is not None:
                mw.get_location(loc_name, player).access_rule = \
                    lambda state, lr=level_rule, cr=boss_rule: lr(state, player) and cr(state, player)
            elif level_rule is not None:
                mw.get_location(loc_name, player).access_rule = \
                    lambda state, r=level_rule: r(state, player)
            elif boss_rule is not None:
                mw.get_location(loc_name, player).access_rule = \
                    lambda state, r=boss_rule: r(state, player)

    # Locked doors — AND each door rule onto whatever rule the location has.
    # With vanilla keys a chest's rule includes reaching its key, so a key
    # location's door rule carries over to the same-colour chest.
    door_rules = dict(DOOR_RULES)
    if not keysanity:
        for loc_name, rule in DOOR_RULES.items():
            if loc_name.endswith(" Key"):
                chest = loc_name[:-len(" Key")] + " Chest"
                old_rule = door_rules.get(chest)
                door_rules[chest] = _c(old_rule, rule) if old_rule else rule
    for loc_name, door_rule in door_rules.items():
        try:
            loc = mw.get_location(loc_name, player)
        except KeyError:
            continue
        loc.access_rule = (lambda state, old=loc.access_rule, dr=door_rule:
                           old(state) and dr(state, player))

    # Shop item filter — reject coin bundles (ex-crests). No point
    # spending coins to buy more coins.
    if world.options.shopsanity:
        from .locations import SHOP_LOCATION_TABLE
        _COIN_NAMES = {
            "1 Coin",
            "10 Coins",
            "25 Coins",
            "50 Coins",
        }
        for loc_name in SHOP_LOCATION_TABLE:
            mw.get_location(loc_name, player).item_rule = \
                lambda item, coins=_COIN_NAMES: item.name not in coins

    # Victory condition — either the music-box threshold OR the bosses
    # threshold (per VictoryCondition option). Rudy fight always requires
    # Progressive Overalls x1 and Progressive Grab x2 on top of the wincon.
    from .options import VictoryCondition
    victory = int(world.options.victory_condition)
    if victory == VictoryCondition.option_bosses:
        # Bosses wincon — require N bosses defeated. Uses the 10 BOSS
        # CHEST locations for reachability
        from . import BOSS_CHEST_LOCATIONS
        bosses_needed = int(world.options.bosses_required)
        mw.completion_condition[player] = \
            lambda state, n=bosses_needed, names=BOSS_CHEST_LOCATIONS: (
                sum(state.can_reach_location(name, player) for name in names) >= n
                and able_to_beat_rudy(state, player)
            )
    else:
        required = int(world.options.music_boxes_required)
        mw.completion_condition[player] = \
            lambda state, n=required: (
                sum(state.has(mb, player) for mb in MUSIC_BOXES) >= n
                and able_to_beat_rudy(state, player)
            )
