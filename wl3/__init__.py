"""
Wario Land 3 Archipelago World definition.

Randomizes all 100 treasure chests across 25 levels.
Output: a .apwl3 patch file — double-click it in the BizHawk client to auto-patch.
"""

import os
from typing import Any, ClassVar, Dict, List

import settings as ap_settings
from BaseClasses import Item, ItemClassification, Location, Tutorial

from worlds.AutoWorld import WebWorld, World
from worlds.LauncherComponents import Component, SuffixIdentifier, Type, components, launch_subprocess

from .items import (
    BASE_ITEM_ID,
    COMBINED_ITEMS,
    CREST_DEFAULT_EXTRA_COUNTS,
    CREST_EXTRA_COUNTS,
    INDIVIDUAL_MULTI_ITEM_NAMES,
    ITEM_TABLE,
    PROGRESSIVE_COUNTS,
    PROGRESSIVE_ITEMS,
    TREASURE_TABLE,
    WL3ItemData,
)
from .locations import BASE_LOC_ID, LOCATION_TABLE, WL3LocationData
from Options import OptionGroup
from .options import (WL3Options, MusicBoxShuffle,
                      GolfPrice, GolfBuilding, StartWithMagnifyingGlass,
                      MusicShuffle, PaletteShuffle)
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
        OptionGroup("Quality of Life", [GolfPrice, GolfBuilding, StartWithMagnifyingGlass]),
        OptionGroup("Cosmetics", [MusicShuffle, PaletteShuffle]),
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

    item_name_to_id      = {name: data.ap_id for name, data in ITEM_TABLE.items()}
    location_name_to_id  = {name: data.ap_id for name, data in LOCATION_TABLE.items()}

    item_name_groups = {
        "Grab":     {"Progressive Grab"},
        "Flippers": {"Progressive Flippers"},
        "Overalls": {"Progressive Overalls"},
    }

    # ------------------------------------------------------------------
    # Item creation
    # ------------------------------------------------------------------

    def create_item(self, name: str) -> WL3Item:
        data = ITEM_TABLE[name]
        return WL3Item(name, data.classification, data.ap_id, self.player)

    def create_items(self) -> None:
        items: List[WL3Item] = []
        skip_items = set()

        if self.options.start_with_axe:
            skip_items.add("Axe")
            self.multiworld.push_precollected(self.create_item("Axe"))

        random_starts = int(self.options.random_level_starts)
        if random_starts > 0:
            eligible = RANDOM_START_ELIGIBLE_COMBINED if self.options.combined_level_unlocks else RANDOM_START_ELIGIBLE
            count = min(random_starts, len(eligible))
            picks = self.random.sample(eligible, count)
            for group in picks:
                for name in group:
                    skip_items.add(name)
                    self.multiworld.push_precollected(self.create_item(name))

        if self.options.combined_level_unlocks:
            # Skip the 17 individual multi-item unlocks; add 8 combined items instead
            for name in TREASURE_TABLE:
                if name not in INDIVIDUAL_MULTI_ITEM_NAMES and name not in skip_items:
                    items.append(self.create_item(name))
            for name in COMBINED_ITEMS:
                if name not in skip_items:
                    items.append(self.create_item(name))
            # Fill freed slots with extra crest copies (9 + 1 if axe removed)
            extra = len(skip_items)
            counts = dict(CREST_EXTRA_COUNTS)
            counts["Clubs Crest (1 Coin)"] = counts.get("Clubs Crest (1 Coin)", 0) + extra
            for name, count in counts.items():
                for _ in range(count):
                    items.append(self.create_item(name))
        else:
            # Default: one copy of every regular item
            for name in TREASURE_TABLE:
                if name not in skip_items:
                    items.append(self.create_item(name))
            # Extra crest copies to fill gem-freed slots
            for name, count in CREST_DEFAULT_EXTRA_COUNTS.items():
                for _ in range(count):
                    items.append(self.create_item(name))
            # Replace removed items (e.g. level_start_mode) with crests
            for _ in range(len(skip_items)):
                items.append(self.create_item("Clubs Crest (1 Coin)"))

        # Progressive items (same in both modes)
        for name, count in PROGRESSIVE_COUNTS.items():
            for _ in range(count):
                items.append(self.create_item(name))

        assert len(items) == 100, f"Expected 100 items, got {len(items)}"
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
        mode = self.options.music_box_shuffle
        if mode == MusicBoxShuffle.option_any_boss:
            allowed = BOSS_CHEST_LOCATIONS

            pool = self.multiworld.itempool
            music_box_items = [item for item in pool
                               if item.player == self.player and item.name in MUSIC_BOXES]
            for item in music_box_items:
                pool.remove(item)

            target_locs = [self.multiworld.get_location(name, self.player) for name in allowed]

            from Fill import fill_restrictive
            fill_restrictive(
                self.multiworld,
                self.multiworld.get_all_state(use_cache=False),
                target_locs,
                music_box_items,
                single_player_placement=True,
                lock=True,
            )

        if self.options.combined_level_unlocks:
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

    # ------------------------------------------------------------------
    # Slot data
    # ------------------------------------------------------------------

    def fill_slot_data(self) -> Dict[str, Any]:
        return {
            "death_link":            False,
            "combined_level_unlocks": int(self.options.combined_level_unlocks),
        }
