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

from BaseClasses import CollectionState

from .locations import LOCATION_TABLE

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
        None,
        has_overalls_1,
        _c(_has("High Jump Boots"), _has("Pouch"), _has("Eye of the Storm")),
        _c(_has("Gold Magic"), _has("High Jump Boots"), has_grab_1, has_overalls_1),
    ],
    "The Peaceful Village": [
        None,
        _o(_has("Flute"), _has("High Jump Boots")),
        _c(_o(_has("Flute"), _has("High Jump Boots")), has_overalls_1),
        _c(has_overalls_2, _has("Garlic")),
    ],
    "The Vast Plain": [
        None,
        has_overalls_1,
        _has("Magic Seeds"),
        _c(_has("Blue Chemical"), _has("Red Chemical")),
    ],
    "Bank of the Wild River": [
        has_flippers_1,
        _has("Garlic"),
        has_flippers_2,
        _c(_has("Air Pump"), has_grab_1),
    ],
    "The Tidal Coast": [
        None,
        _c(has_flippers_1, has_grab_1),
        _has("Statue"),
        _c(_has("Sapling of Growth"), has_flippers_1, _has("Garlic")),
    ],
    "Sea Turtle Rocks": [
        _c(_has("Garlic"), _has("Spiked Helmet"), has_overalls_1, has_flippers_1),
        _c(_has("Scepter"), _has("Garlic"), has_overalls_1, has_flippers_1),
        has_overalls_2,
        _c(_has("Night Vision Scope"), has_overalls_2, _has("High Jump Boots")),
    ],
    "Desert Ruins": [
        None,
        None,
        _c(_has("Spiked Helmet"), has_overalls_1),
        _c(has_grab_1, has_overalls_2, _has("High Jump Boots")),
    ],
    "The Volcano's Base": [
        None,
        _has("Truck Wheel"),
        _c(_has("Flute"), _has("Truck Wheel")),
        _c(_has("Foot of Stone"), has_flippers_1, _has("Spiked Helmet")),
    ],
    "The Pool of Rain": [
        has_overalls_1,
        _has("Magic Seeds"),
        has_flippers_1,
        _c(_has("Air Pump"), has_flippers_1),
    ],
    "A Town in Chaos": [
        None,
        _has("Spiked Helmet"),
        _c(has_grab_2, _has("High Jump Boots")),
        _c(_has("Electric Fan Propeller"), has_grab_1),
    ],
    "Beneath the Waves": [
        _c(has_flippers_1, _has("High Jump Boots")),
        _c(has_flippers_1, has_grab_2),
        _c(has_flippers_1, _has("Sapling of Growth")),
        _c(has_flippers_1, has_grab_1, _has("Blue Chemical"), _has("Red Chemical")),
    ],
    "The West Crater": [
        has_overalls_1,
        _c(has_overalls_2, _has("Garlic")),
        _c(_has("Fire Drencher"), _has("High Jump Boots")),
        _c(_has("Rust Spray"), has_grab_1),
    ],
    "The Grasslands": [
        has_overalls_1,
        _c(_has("Magic Seeds"), has_overalls_1),
        _c(_has("Flute"), has_flippers_1),
        _c(has_flippers_1, _has("High Jump Boots")),
    ],
    "The Big Bridge": [
        None,
        _c(has_flippers_1, has_overalls_1),
        _c(has_flippers_1, has_grab_1, has_overalls_1),
        _c(_has("Scepter"), has_flippers_1, _has("Garlic"), _has("Spiked Helmet")),
    ],
    "Tower of Revival": [
        None,
        _c(_has("Left Glass Eye"), _has("Right Glass Eye")),
        _c(_has("Statue"), _has("High Jump Boots")),
        _c(_has("Golden Left Eye"), _has("Golden Right Eye"), _has("Statue"),
           _has("Spiked Helmet"), _has("Garlic"), has_grab_2, _has("High Jump Boots")),
    ],
    "The Steep Canyon": [
        None,
        _has("Foot of Stone"),
        _c(_has("Foot of Stone"), has_flippers_2, has_overalls_2, _has("High Jump Boots")),
        _c(_has("Rust Spray"), has_overalls_1),
    ],
    "Cave of Flames": [
        has_grab_1,
        _c(has_grab_1, _has("High Jump Boots"), has_overalls_2),
        _has("Explosive Plunger Box"),
        _c(_has("Rust Spray"), has_overalls_1, has_grab_1, _has("High Jump Boots")),
    ],
    "Above the Clouds": [
        None,
        _c(_has("High Jump Boots"), has_grab_1, _has("Spiked Helmet")),
        _c(_has("Scissors"), _has("High Jump Boots")),
        _c(_has("Scissors"), _has("Full Moon Gong"), _has("High Jump Boots"), has_overalls_2, has_grab_1),
    ],
    "The Stagnant Swamp": [
        None,
        _c(_has("Foot of Stone"), has_overalls_1),
        _c(_has("Foot of Stone"), _has("High Jump Boots"), has_grab_1),
        _has("Explosive Plunger Box"),
    ],
    "The Frigid Sea": [
        None,
        has_grab_1,
        _c(_has("Scepter"), has_flippers_1),
        _c(_has("Sun Medallion Top"), _has("Sun Medallion Bottom"), has_flippers_2),
    ],
    "Castle of Illusions": [
        has_overalls_1,
        _o(has_grab_2, _c(_has("Sun Medallion Top"), _has("Sun Medallion Bottom"))),
        _o(has_grab_2, _c(_has("Sun Medallion Top"), _has("Sun Medallion Bottom"))),
        _c(_has("Castle Brick"), has_grab_1),
    ],
    "The Colossal Hole": [
        None,
        _has("Garlic"),
        _o(_c(_has("Sun Medallion Top"), _has("Sun Medallion Bottom")), _has("High Jump Boots")),
        _c(_has("Explosive Plunger Box"), _has("High Jump Boots")),
    ],
    "The Warped Void": [
        has_grab_1,
        _has("Warp Removal Apparatus"),
        _c(_has("Warp Removal Apparatus"), has_grab_1),
        _c(_has("Key Card Red"), _has("Key Card Blue"), has_grab_1),
    ],
    "The East Crater": [
        _c(has_grab_1, has_overalls_2),
        None,
        _c(_has("Jackhammer"), has_grab_1),
        _c(_has("Pick Axe"), has_grab_1, _has("High Jump Boots")),
    ],
    "Forest of Fear": [
        None,
        _c(_has("Mystery Handle"), has_grab_2),
        _c(_has("Mystery Handle"), has_grab_1),
        _has("Demon's Blood"),
    ],
}


# ---------------------------------------------------------------------------
# Main rule-setting function — called from WL3World.set_rules()
# ---------------------------------------------------------------------------

def set_rules(world: "WL3World") -> None:
    player  = world.player
    mw      = world.multiworld
    combined = bool(world.options.combined_level_unlocks)

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

    for loc_name, loc_data in LOCATION_TABLE.items():
        level_rule  = level_rules.get(loc_data.level_name)
        chest_rules = CHEST_RULES.get(loc_data.level_name)
        chest_rule  = chest_rules[loc_data.color_index] if chest_rules else None

        if level_rule is not None and chest_rule is not None:
            mw.get_location(loc_name, player).access_rule = \
                lambda state, lr=level_rule, cr=chest_rule: lr(state, player) and cr(state, player)
        elif level_rule is not None:
            mw.get_location(loc_name, player).access_rule = \
                lambda state, r=level_rule: r(state, player)
        elif chest_rule is not None:
            mw.get_location(loc_name, player).access_rule = \
                lambda state, r=chest_rule: r(state, player)

    # Victory condition — collect required music boxes then beat the final boss.
    # Progressive Overalls x1 and Progressive Grab x2 are always required for the temple fight.
    required = int(world.options.music_boxes_required)
    mw.completion_condition[player] = \
        lambda state, n=required: (
            sum(state.has(mb, player) for mb in MUSIC_BOXES) >= n
            and has_overalls_1(state, player)
            and has_grab_2(state, player)
        )
