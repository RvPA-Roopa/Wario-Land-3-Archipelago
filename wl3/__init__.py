"""
Wario Land 3 Archipelago World definition.

Randomizes all 100 treasure chests across 25 levels.
Output: a .apwl3 patch file — double-click it in the BizHawk client to auto-patch.
"""

import os
from typing import Any, ClassVar, Dict, List

import settings as ap_settings
from BaseClasses import Item, ItemClassification, Location, Tutorial
from Fill import fill_restrictive

from worlds.AutoWorld import WebWorld, World
from worlds.LauncherComponents import Component, SuffixIdentifier, Type, components, launch_subprocess

from .items import (
    BASE_ITEM_ID,
    COMBINED_ITEMS,
    COMBINED_ITEMS_OVERWORLD,
    COMBINED_ITEMS_IN_LEVEL,
    CREST_DEFAULT_EXTRA_COUNTS,
    CREST_EXTRA_COUNTS,
    INDIVIDUAL_OVERWORLD_NAMES,
    INDIVIDUAL_IN_LEVEL_NAMES,
    INDIVIDUAL_MULTI_ITEM_NAMES,
    ITEM_TABLE,
    KEY_BASE_ITEM_ID,
    KEY_ITEM_TABLE,
    KEYRING_BASE_ITEM_ID,
    KEYRING_ITEM_TABLE,
    PROGRESSIVE_COUNTS,
    PROGRESSIVE_ITEMS,
    TRAP_AP_IDS_SET,
    TRAP_ITEMS,
    FORM_DISPLAY_TREASURE,
    TRANSFORM_SACRIFICED_TREASURES,
    TRANSFORM_UNLOCK_ITEMS,
    TRANSFORM_UNLOCK_PROGRESSIVE_COUNTS,
    TREASURE_TABLE,
    WL3ItemData,
)
from .locations import BASE_LOC_ID, KEY_LOCATION_TABLE, LOCATION_TABLE, WL3LocationData
from Options import OptionGroup
from .options import (WL3Options, MusicBoxShuffle, KeyShuffle, CombinedItems,
                      GolfPrice, GolfBuilding, IHateGolf,
                      StartWithMagnifyingGlass, ReduceFlashing, NonStopChests, TrapFill,
                      MusicShuffle, EnemyPaletteShuffle, LevelBGPaletteShuffle,
                      WarioOverallsShuffle, WarioShirtShuffle, DifficultyOptions, MinorGlitches)
from .regions import create_regions
from .rom import WL3ProcedurePatch, write_tokens
from .rules import MUSIC_BOXES, set_rules
from . import client as _client  # noqa: F401 — registers WL3Client with AutoBizHawkClientRegister


def _do_patch(*args):
    import Patch
    import logging
    import shlex
    import subprocess
    import sys
    import os
    logger = logging.getLogger("WL3")
    if not args:
        logger.error("No patch file provided.")
        return
    patch_file = args[0]
    logger.info(f"Patching {patch_file} ...")
    _, rom_file = Patch.create_rom_file(patch_file)
    logger.info(f"Patched ROM written to: {rom_file}")
    from settings import get_settings
    settings = get_settings()
    opts = settings.wl3_options
    rom_start = opts.get("rom_start", False) if isinstance(opts, dict) else getattr(opts, "rom_start", False)
    if rom_start is True:
        # Auto-build command from bizhawkclient_options
        bzhawk_opts = settings.bizhawkclient_options
        emuhawk = bzhawk_opts.get("emuhawk_path", "") if isinstance(bzhawk_opts, dict) else getattr(bzhawk_opts, "emuhawk_path", "")
        if emuhawk and os.path.isfile(emuhawk):
            rom_start = f'"{emuhawk}" --lua=data/lua/connector_bizhawk_generic.lua'
        else:
            rom_start = False
    if isinstance(rom_start, str) and rom_start:
        cmd_args = shlex.split(rom_start)
        cmd_args.append(os.path.realpath(rom_file))
        script_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.realpath(__file__))
        subprocess.Popen(cmd_args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=script_dir)
        logger.info(f"Launched: {cmd_args[0]}")
    bizhawk_client = os.path.join(os.path.dirname(sys.executable), "ArchipelagoBizHawkClient.exe")
    if os.path.isfile(bizhawk_client):
        subprocess.Popen([bizhawk_client])


def _launch_patch(*args):
    launch_subprocess(_do_patch, name="Wario Land 3 Patcher", args=args)


components.append(Component(
    "Wario Land 3 Patcher",
    func=_launch_patch,
    component_type=Type.CLIENT,
    file_identifier=SuffixIdentifier(".apwl3"),
))

# Level unlock groups eligible for random starts.
# Each tuple unlocks a level with a sphere-0 grey chest; music box unlocks excluded.
RANDOM_START_ELIGIBLE = [
    ("Blue Tablet", "Green Tablet"),                 # Desert Ruins
    ("Top Half of Scroll", "Bottom Half of Scroll"), # The Volcano's Base
    ("Skull Ring Red", "Skull Ring Blue"),            # Tower of Revival
    ("Trident", "Yellow Book"),                      # The Steep Canyon
    ("Sky Key",),                                    # Above the Clouds
    ("Ornamental Fan",),                             # The Stagnant Swamp
    ("Blue Book", "Magic Wand"),                     # The Frigid Sea
    ("Torch",),                                      # Forest of Fear
]
RANDOM_START_ELIGIBLE_COMBINED = [
    ("Tablets",),
    ("Scroll",),
    ("Skull Ring",),
    ("Trident & Yellow Book",),
    ("Sky Key",),
    ("Ornamental Fan",),
    ("Blue Book & Magic Wand",),
    ("Torch",),
]

# The 5 vanilla music box chest locations (original game placements)
VANILLA_MUSIC_BOX_LOCATIONS = [
    "Out of the Woods - Blue Chest",       # Gold Music Box
    "Sea Turtle Rocks - Grey Chest",       # Green Music Box
    "A Town in Chaos - Red Chest",         # Blue Music Box
    "The Grasslands - Grey Chest",         # Yellow Music Box
    "The Stagnant Swamp - Green Chest",    # Red Music Box
]

# All 10 boss chest locations
BOSS_CHEST_LOCATIONS = [
    "The Grasslands - Grey Chest",         # Wormwould
    "A Town in Chaos - Red Chest",         # Shoot
    "Sea Turtle Rocks - Grey Chest",       # Scowler
    "The Stagnant Swamp - Green Chest",    # Jamano
    "Out of the Woods - Blue Chest",       # Anonster
    "The Pool of Rain - Green Chest",      # Wolfenboss
    "Bank of the Wild River - Green Chest", # Pesce
    "The Stagnant Swamp - Red Chest",      # Muddee
    "The Volcano's Base - Grey Chest",     # Doll Boy
    "Desert Ruins - Blue Chest",           # Helio
]


class WL3Item(Item):
    game = "Wario Land 3"


class WL3Location(Location):
    game = "Wario Land 3"

    def __init__(self, player: int, name: str, address: int,
                 loc_data: WL3LocationData, parent=None):
        super().__init__(player, name, address, parent)
        self.loc_data = loc_data


class WL3WebWorld(WebWorld):
    theme = "ocean"
    tutorials = [
        Tutorial(
            tutorial_name="Setup Guide",
            description="How to set up Wario Land 3 Randomizer with Archipelago",
            language="English",
            file_name="setup_en.md",
            link="setup/en",
            authors=["RVPA"],
        )
    ]
    option_groups = [
        OptionGroup("Quality of Life", [GolfPrice, GolfBuilding, IHateGolf,
                                       StartWithMagnifyingGlass, ReduceFlashing,
                                       NonStopChests, TrapFill]),
        OptionGroup("Cosmetics", [MusicShuffle, EnemyPaletteShuffle,
                                  LevelBGPaletteShuffle,
                                   WarioOverallsShuffle, WarioShirtShuffle]),
    ]


class WL3Settings(ap_settings.Group):
    class RomFile(ap_settings.UserFilePath):
        """Path to the unmodified Wario Land 3 (USA/EUR) GBC ROM."""
        copy_to   = "warioland3.gbc"
        description = "Wario Land 3 ROM File"
        md5s      = []

    rom_file:  RomFile = RomFile(RomFile.copy_to)
    # Auto-launches BizHawk using bizhawkclient_options.emuhawk_path with the connector script.
    # Set to a custom string command to override, or false to disable.
    rom_start: bool = True


class WL3World(World):
    """Wario Land 3 — randomizes all 100 treasure chests."""

    game                 = "Wario Land 3"
    options_dataclass    = WL3Options
    topology_present     = True
    web                  = WL3WebWorld()
    settings:            ClassVar[WL3Settings]

    item_name_to_id      = {
        **{name: data.ap_id for name, data in ITEM_TABLE.items()},
        **{name: data.ap_id for name, data in KEY_ITEM_TABLE.items()},
        **{name: data.ap_id for name, data in KEYRING_ITEM_TABLE.items()},
    }
    location_name_to_id  = {
        **{name: data.ap_id for name, data in LOCATION_TABLE.items()},
        **{name: data.ap_id for name, data in KEY_LOCATION_TABLE.items()},
    }

    item_name_groups = {
        "Grab":      {"Progressive Grab"},
        "Flippers":  {"Progressive Flippers"},
        "Overalls":  {"Progressive Overalls"},
        "Music Box": {"Red Music Box", "Blue Music Box", "Yellow Music Box", "Green Music Box", "Gold Music Box"},
    }

    # ------------------------------------------------------------------
    # Item creation
    # ------------------------------------------------------------------

    def create_item(self, name: str) -> WL3Item:
        if name in KEY_ITEM_TABLE:
            data = KEY_ITEM_TABLE[name]
            return WL3Item(name, ItemClassification.progression, data.ap_id, self.player)
        if name in KEYRING_ITEM_TABLE:
            data = KEYRING_ITEM_TABLE[name]
            return WL3Item(name, ItemClassification.progression, data.ap_id, self.player)
        data = ITEM_TABLE[name]
        return WL3Item(name, data.classification, data.ap_id, self.player)

    def generate_early(self) -> None:
        # Pick which levels get Keyring treatment. If keyring_count > 0, force
        # key_shuffle to Full so the non-keyringed levels' keys are still in
        # the pool and shuffled.
        count = int(self.options.keyring_count)
        self.keyringed_level_names: set = set()
        if count > 0:
            if self.options.key_shuffle == KeyShuffle.option_vanilla:
                self.options.key_shuffle.value = KeyShuffle.option_full
            level_names = [data.level_name for data in KEYRING_ITEM_TABLE.values()]
            n = min(count, len(level_names))
            self.keyringed_level_names = set(self.random.sample(level_names, n))

    def create_items(self) -> None:
        items: List[WL3Item] = []
        skip_items = set()

        if self.options.start_with_axe:
            skip_items.add("Axe")
            self.multiworld.push_precollected(self.create_item("Axe"))

        # Transformation Shuffle: 12 filler treasures are replaced by Form items.
        if self.options.transformation_shuffle:
            skip_items |= TRANSFORM_SACRIFICED_TREASURES

        ci_mode = int(self.options.combined_items)
        combine_overworld = ci_mode in (CombinedItems.option_overworld, CombinedItems.option_both)
        combine_in_level  = ci_mode in (CombinedItems.option_in_level,  CombinedItems.option_both)

        random_starts = int(self.options.random_level_starts)
        if random_starts > 0:
            eligible = RANDOM_START_ELIGIBLE_COMBINED if combine_overworld else RANDOM_START_ELIGIBLE
            count = min(random_starts, len(eligible))
            picks = self.random.sample(eligible, count)
            for group in picks:
                for name in group:
                    skip_items.add(name)
                    self.multiworld.push_precollected(self.create_item(name))

        # Determine which individuals to skip and which combineds to add.
        skip_individuals: set = set()
        add_combined: dict = {}
        if combine_overworld:
            skip_individuals |= INDIVIDUAL_OVERWORLD_NAMES
            add_combined.update(COMBINED_ITEMS_OVERWORLD)
        if combine_in_level:
            skip_individuals |= INDIVIDUAL_IN_LEVEL_NAMES
            add_combined.update(COMBINED_ITEMS_IN_LEVEL)

        # Base pool: regular treasures minus anything absorbed by combines.
        for name in TREASURE_TABLE:
            if name in skip_individuals or name in skip_items:
                continue
            items.append(self.create_item(name))

        # Add combined items.
        for name in add_combined:
            if name not in skip_items:
                items.append(self.create_item(name))

        # Progressive items (always added)
        for name, count in PROGRESSIVE_COUNTS.items():
            for _ in range(count):
                items.append(self.create_item(name))

        # Transform unlock items — player-activated abilities (Select+button).
        # All are progression; placed in logic by rules.py.
        # When on, 12 filler treasures are removed from the pool (see
        # TRANSFORM_SACRIFICED_TREASURES in items.py) and replaced by Forms.
        # Progressive Vampire has 2 copies (tier 1 = Vampire, tier 2 = Bat).
        if self.options.transformation_shuffle:
            for name in TRANSFORM_UNLOCK_ITEMS:
                count = TRANSFORM_UNLOCK_PROGRESSIVE_COUNTS.get(name, 1)
                for _ in range(count):
                    items.append(self.create_item(name))

        # Fill remaining slots to reach 100 using crests. Use the existing crest
        # distribution tables as the starting point, then top up with Clubs Crests.
        if combine_overworld:
            base_counts = dict(CREST_EXTRA_COUNTS)
        else:
            base_counts = dict(CREST_DEFAULT_EXTRA_COUNTS)
        base_total = sum(base_counts.values())
        slots_remaining = 100 - len(items)
        if slots_remaining >= base_total:
            # Use the full distribution table; top up with extra Clubs Crests.
            for name, count in base_counts.items():
                for _ in range(count):
                    items.append(self.create_item(name))
            for _ in range(slots_remaining - base_total):
                items.append(self.create_item("Clubs Crest (1 Coin)"))
        else:
            # Less slots than the table wants — just fill with Clubs Crests.
            for _ in range(slots_remaining):
                items.append(self.create_item("Clubs Crest (1 Coin)"))

        assert len(items) == 100, f"Expected 100 items, got {len(items)}"

        # Key shuffle: add all 100 key items to the pool
        # Full: pool is 200 with free placement across all locations
        # Keyring levels: skip 4 individual keys, add 1 Keyring + 3 filler instead.
        if self.options.key_shuffle != KeyShuffle.option_vanilla:
            for name, data in KEY_ITEM_TABLE.items():
                if data.level_name in self.keyringed_level_names:
                    continue
                items.append(self.create_item(name))
            for level_name in self.keyringed_level_names:
                items.append(self.create_item(f"{level_name} Keyring"))
                # 3 filler items to preserve pool size (keyring replaces 4 keys)
                for _ in range(3):
                    items.append(self.create_item("Clubs Crest (1 Coin)"))

        # Trap replacement: swap a % of filler items for random trap items.
        # Runs after key shuffle so keyring-padding fillers are also candidates.
        trap_pct = int(self.options.trap_fill)
        if trap_pct > 0 and TRAP_ITEMS:
            filler_indices = [
                i for i, it in enumerate(items)
                if it.classification == ItemClassification.filler
            ]
            num_traps = (len(filler_indices) * trap_pct + 50) // 100
            if num_traps > 0:
                victim_indices = self.random.sample(filler_indices, num_traps)
                trap_names = list(TRAP_ITEMS.keys())
                for idx in victim_indices:
                    trap_name = self.random.choice(trap_names)
                    items[idx] = self.create_item(trap_name)

        self.multiworld.itempool += items

    # ------------------------------------------------------------------
    # Region / location creation
    # ------------------------------------------------------------------

    def create_regions(self) -> None:
        regions = create_regions(self)
        self.multiworld.regions += list(regions.values())

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------

    def set_rules(self) -> None:
        set_rules(self)

    # ------------------------------------------------------------------
    # Pre-fill — restrict music box placement if requested
    # ------------------------------------------------------------------

    def pre_fill(self) -> None:
        ks = self.options.key_shuffle
        if ks == KeyShuffle.option_vanilla:
            # Lock each key item to its own location (not in item pool).
            for loc_name, loc_data in KEY_LOCATION_TABLE.items():
                loc = self.multiworld.get_location(loc_name, self.player)
                key_item_name = f"{loc_data.level_name} {loc_data.color_name} Key"
                item = WL3Item(key_item_name, ItemClassification.progression,
                               KEY_ITEM_TABLE[key_item_name].ap_id, self.player)
                loc.place_locked_item(item)
        # Full: keys are in the pool and placed freely by AP.

        mode = self.options.music_box_shuffle
        if mode == MusicBoxShuffle.option_any_boss:
            allowed = BOSS_CHEST_LOCATIONS

            pool = self.multiworld.itempool
            music_box_items = [item for item in pool
                               if item.player == self.player and item.name in MUSIC_BOXES]
            for item in music_box_items:
                pool.remove(item)

            target_locs = [self.multiworld.get_location(name, self.player) for name in allowed]

            fill_restrictive(
                self.multiworld,
                self.multiworld.get_all_state(use_cache=False),
                target_locs,
                music_box_items,
                single_player_placement=True,
                lock=True,
            )

        # Overworld combines make pre-fill unnecessary (combined items naturally open
        # progression without needing a hand-placed chain).
        if int(self.options.combined_items) in (CombinedItems.option_overworld, CombinedItems.option_both):
            return

        # Bootstrap the opening chain.
        # Out of the Woods Grey is the only sphere-0 location.  Pre-fill a
        # chain through free chests so the main fill starts with a rich
        # collected-items state.
        #
        # Phase 1: level-unlock keys → free grey chests they open
        # Phase 2: key ability items → sphere-1 locations opened by Phase 1
        #
        # Each entry: item name → locations it directly unlocks (single-gated).
        _LEVEL_KEY_MAP: Dict[str, List[str]] = {
            "Axe":            ["The Peaceful Village - Grey Chest",
                               "The Vast Plain - Grey Chest"],
            "Ornamental Fan": ["The Stagnant Swamp - Grey Chest"],
            "Sky Key":        ["Above the Clouds - Grey Chest"],
            "Torch":          ["Forest of Fear - Grey Chest"],
            "Jar":            ["A Town in Chaos - Grey Chest"],
        }
        _ABILITY_MAP: Dict[str, List[str]] = {
            "Progressive Overalls": ["The Vast Plain - Red Chest",
                                     "The Pool of Rain - Grey Chest"],
            "Spiked Helmet":        ["A Town in Chaos - Red Chest"],
            "Progressive Flippers": ["The Pool of Rain - Green Chest"],
        }

        pool    = self.multiworld.itempool
        rng     = self.multiworld.random
        to_fill = ["Out of the Woods - Grey Chest"]

        for phase_map in (_LEVEL_KEY_MAP, _ABILITY_MAP):
            remaining = list(to_fill)
            to_fill = []
            while remaining:
                loc_name = remaining.pop(0)
                loc = self.multiworld.get_location(loc_name, self.player)
                if loc.item is not None:
                    continue  # already filled (e.g., by music-box pre-fill)

                candidates = [item for item in pool
                              if item.player == self.player
                              and item.name in phase_map]
                if not candidates:
                    # No items left for this phase; carry location to next phase
                    to_fill.append(loc_name)
                    continue

                chosen = rng.choice(candidates)
                pool.remove(chosen)
                loc.place_locked_item(chosen)

                # Queue the locations this item now unlocks
                for next_loc_name in phase_map[chosen.name]:
                    nxt = self.multiworld.get_location(next_loc_name, self.player)
                    if nxt.item is None:
                        remaining.append(next_loc_name)

    # ------------------------------------------------------------------
    # Output — produce a .apwl3 patch file
    # ------------------------------------------------------------------

    def generate_output(self, output_directory: str) -> None:
        patch = WL3ProcedurePatch(
            player=self.player,
            player_name=self.multiworld.player_name[self.player],
        )
        write_tokens(self, patch)
        out_name = self.multiworld.get_out_file_name_base(self.player)
        patch.write(os.path.join(output_directory,
                                 f"{out_name}{WL3ProcedurePatch.patch_file_ending}"))

    def _build_chest_assignments(self) -> List[int]:
        """Return a 100-element list of in-game treasure IDs.

        Index: (owlevel - 1) * 4 + color_index  (matches CHEST_TABLE_OFFSET layout)
        For progressive items, tier is determined by which copy of the item
        this is (sorted by location index so tier 1 lands in the earlier chest).
        """
        chest_table = [0] * 100

        # Collect progressive item placements: name → sorted list of loc_index
        progressive_placements: Dict[str, List[int]] = {
            name: [] for name in PROGRESSIVE_ITEMS
        }

        for loc_name, loc_data in LOCATION_TABLE.items():
            location = self.multiworld.get_location(loc_name, self.player)
            item = location.item
            if item is None or item.player != self.player:
                # Foreign item — show a gem so the player sees what they're sending
                if item is not None:
                    cls = item.classification
                    if cls in (ItemClassification.progression,
                               ItemClassification.progression_skip_balancing):
                        chest_table[loc_data.loc_index] = 0x4E  # Red Gem
                    elif cls == ItemClassification.useful:
                        chest_table[loc_data.loc_index] = 0x50  # Blue Gem
                    else:
                        chest_table[loc_data.loc_index] = 0x4F  # Green Gem
                continue

            item_data = ITEM_TABLE.get(item.name)
            if item_data is None:
                # Key items (keysanity): show key icon via TREASURE_DUMMY ($65)
                # whose tile graphics are patched with a key portrait by write_tokens.
                if item.name in KEY_ITEM_TABLE:
                    chest_table[loc_data.loc_index] = 0x65  # TREASURE_DUMMY → key icon
                # Keyring items: show the 4-keys "keyring" icon (TREASURE_KEYRING $66).
                elif item.name in KEYRING_ITEM_TABLE:
                    chest_table[loc_data.loc_index] = 0x66  # TREASURE_KEYRING
                continue

            # Trap items: show as red gem. tier_ids[0] is a TRAP_* constant,
            # NOT a treasure ID, so we must never write it to the chest table.
            if item_data.ap_id in TRAP_AP_IDS_SET:
                chest_table[loc_data.loc_index] = 0x4E  # Red Gem
                continue

            # Transform unlock items: tier_ids are (byte_idx, bit_idx) pairs,
            # NOT treasure IDs. Show as the sacrificed treasure's icon so each
            # Form has a unique visual (see FORM_DISPLAY_TREASURE).
            if item.name in TRANSFORM_UNLOCK_ITEMS:
                chest_table[loc_data.loc_index] = FORM_DISPLAY_TREASURE[item.name]
                continue

            if item.name in PROGRESSIVE_ITEMS:
                progressive_placements[item.name].append(loc_data.loc_index)
            else:
                chest_table[loc_data.loc_index] = item_data.tier_ids[0]

        # Progressive ability chests always use tier 1 ID in ROM.
        # Tier 2 is granted exclusively by the AP client when the 2nd progressive
        # item is received — enforcing strict tier 1 → tier 2 progression regardless
        # of which physical chest the player opens first.
        for prog_name, loc_indices in progressive_placements.items():
            tier_ids = PROGRESSIVE_ITEMS[prog_name].tier_ids
            for loc_idx in loc_indices:
                chest_table[loc_idx] = tier_ids[0]

        return chest_table

    def _build_key_assignments(self) -> List[int]:
        """Return a 100-element list of in-game item IDs for the LevelKeyPool table.

        Index: (owlevel - 1) * 4 + color_index  (matches KEY_TABLE_OFFSET layout)

        Vanilla: identity mapping (each key location gives its own key).
        Simple/Full keysanity:
          - Own WL3 key item   → ROM key ID (0x80 + pool_index); ROM sets key inventory.
          - Own WL3 treasure   → ROM treasure ID; ROM skips key inventory (bit-7 check).
          - Foreign/empty      → Red Gem placeholder (0x4E); ROM skips, AP client delivers.
        """
        if self.options.key_shuffle == KeyShuffle.option_vanilla:
            return [0x80 + i for i in range(100)]

        key_table = [0] * 100
        for loc_name, loc_data in KEY_LOCATION_TABLE.items():
            location = self.multiworld.get_location(loc_name, self.player)
            item = location.item
            idx = (loc_data.owlevel - 1) * 4 + loc_data.color_index

            if item is None or item.player != self.player:
                # Foreign item — AP client delivers it; give ROM a safe no-op gem
                if item is not None:
                    cls = item.classification
                    if cls in (ItemClassification.progression,
                               ItemClassification.progression_skip_balancing):
                        key_table[idx] = 0x4E  # Red Gem
                    elif cls == ItemClassification.useful:
                        key_table[idx] = 0x50  # Blue Gem
                    else:
                        key_table[idx] = 0x4F  # Green Gem
                else:
                    key_table[idx] = 0x4F
                continue

            if item.name in KEY_ITEM_TABLE:
                key_item_data = KEY_ITEM_TABLE[item.name]
                key_table[idx] = 0x80 + (key_item_data.owlevel - 1) * 4 + key_item_data.color_index
            elif item.name in KEYRING_ITEM_TABLE:
                # Keyring at a key location → show 4-keys portrait (TREASURE_KEYRING $66)
                key_table[idx] = 0x66
            elif item.name in TRANSFORM_UNLOCK_ITEMS:
                # Form at a key location → use the sacrificed treasure's icon.
                # tier_ids are (byte_idx, bit_idx), NOT a treasure ID, so we
                # must never write tier_ids[0] for Forms.
                key_table[idx] = FORM_DISPLAY_TREASURE[item.name]
            else:
                item_data = ITEM_TABLE.get(item.name)
                if item_data is None:
                    key_table[idx] = 0x4F
                elif item_data.ap_id in TRAP_AP_IDS_SET:
                    # Trap at a key location → red gem (tier_ids[0] is a TRAP_*
                    # constant, not a treasure ID).
                    key_table[idx] = 0x4E
                else:
                    # Own treasure at key location — ROM safely skips inventory update
                    key_table[idx] = item_data.tier_ids[0]

        return key_table

    # ------------------------------------------------------------------
    # Slot data
    # ------------------------------------------------------------------

    def fill_slot_data(self) -> Dict[str, Any]:
        loc_items = {}
        all_locs = {**LOCATION_TABLE, **KEY_LOCATION_TABLE}
        for loc_name, loc_data in all_locs.items():
            loc = self.multiworld.get_location(loc_name, self.player)
            if loc.item is not None:
                loc_items[str(loc_data.ap_id)] = {
                    "item": loc.item.name,
                    "player": loc.item.player,
                }
        return {
            "death_link":            False,
            "combined_items":        int(self.options.combined_items),
            "loc_items":             loc_items,
        }
