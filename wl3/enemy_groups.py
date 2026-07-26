"""Enemy home-category and substitution-pool data for the 'grouped'
enemy randomization mode. Consumed by enemizer.py when
slot_data['enemy_grouping'] is set to 'grouped'.

Two concepts:

  ENEMY_HOME[enemy_name] = category
      The enemy's VANILLA habitat — where it naturally lives in the
      un-randomized game. Used to determine which pool a slot draws
      from: a slot whose vanilla enemy has HOME 'water' picks a
      substitute from SUBSTITUTION_POOLS['water'].

  SUBSTITUTION_POOLS[category] = frozenset(enemy_names)
      Enemies safe to place INTO a slot of that category. An enemy
      may appear in multiple pools (e.g. Snake in water/flying/ground)
      even though it has a single HOME.

Not all randomizable enemies have entries — enemies missing from
ENEMY_HOME fall back to the unrestricted "any" pool even in grouped
mode. Enemies explicitly excluded from randomization live in
NEVER_RANDOMIZE and are never picked as substitutes regardless of
mode.
"""

# Each enemy's vanilla home category. Missing labels = "any" fallback.
ENEMY_HOME: dict[str, str] = {
    "Appleby": "flying",
    "BeamBot": "ground",
    "BigOctohon": "water",
    "Bird": "flying",
    "BlueBird": "flying",
    "BrrrBear": "ground",
    "CountRichtertoffen": "ground",
    "Doughnuteer": "ground",
    "Dragonfly": "flying",
    "Dragonfly2": "flying",
    "Fire": "ground",
    "FireBot": "ground",
    "HammerBot": "ground",
    "Hand": "ground",
    "Haridama": "water",
    "Hebarii": "flying",
    "Kobatto": "flying",
    "Kushimushi": "flying",
    "MadScienstein": "ground",
    "Mizuuo": "water",
    "Moon": "flying",
    "Moon1": "flying",
    "Moon2": "flying",
    "Nobiiru": "flying",
    "Octohon": "water",
    "Omodonmeka": "flying",
    "OrangeBird": "flying",
    "ParaGoom": "ground",
    "Pneumo": "flying",
    "Silky": "ground",
    "SmallOctohon": "water",
    "Snake": "ground",
    "SpearBot": "ground",
    "Spearhead": "ground",
    "Sun": "flying",
    "Sun1": "flying",
    "Sun2": "flying",
    "Tadpole": "water",
    "Teruteru": "flying",
    "Torch": "flying",
    "WaterDrop": "flying",
    "Webber": "flying",
    "Zombie": "ground",
}

# Enemies safe to place in a slot of each category.
SUBSTITUTION_POOLS: dict[str, frozenset[str]] = {
    "water": frozenset({
        "Appleby", "Tadpole", "Snake", "Haridama", "Mizuuo",
        "Kushimushi", "Pneumo", "Webber", "Fire", "Hand", "Hebarii",
        "Kobatto", "Zombie", "Nobiiru", "Torch", "WaterDrop",
    }),
    "flying": frozenset({
        "Tadpole", "Appleby", "Bird", "Haridama", "Hebarii", "Kobatto",
        "Kushimushi", "Mizuuo", "Nobiiru", "ParaGoom", "Pneumo",
        "Snake", "Teruteru", "Webber", "Omodonmeka",
    }),
    "ground": frozenset({
        "BeamBot", "BrrrBear", "CountRichtertoffen", "Doughnuteer",
        "FireBot", "HammerBot", "MadScienstein", "ParaGoom", "Snake",
        "SpearBot", "Spearhead", "Zombie", "Fire", "Hand", "Silky",
    }),
}

# Enemies excluded from randomization entirely — never used as a
# substitute, and their vanilla slots are left vanilla. These are
# either mechanically-required (Omodonmeka companions), buggy
# (Togeba / RoboMouse combos), or per-location gated (Bubble spawner).
NEVER_RANDOMIZE: frozenset[str] = frozenset({
    "Bubble",                       # bubble spawner — location-gated
    "Omodon",                       # Omodonmeka's companion
    "OmodonmekaWithOmodon1",        # combined pre-Omodon variant
    "OmodonmekaWithOmodon2",        # combined pre-Omodon variant
    "RoboMouse",                    # crashes when substituted
    "Togeba",                       # crashes when substituted
})
