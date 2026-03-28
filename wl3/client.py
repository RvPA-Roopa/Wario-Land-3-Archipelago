"""
Wario Land 3 — Archipelago BizHawk Client

Works with connector_bizhawkclient_mgba.lua loaded in mGBA.

Setup:
  1. Patch your ROM:   python3 patch_wl3_rando.py original.gbc seed.apwl3
  2. Open the patched .gbc in mGBA
  3. In mGBA: Tools → Scripting → Load Script → connector_bizhawkclient_mgba.lua
  4. Launch ArchipelagoBizHawkClient.exe and connect to your AP server
"""

import logging
from typing import TYPE_CHECKING

from NetUtils import ClientStatus
from worlds._bizhawk import read, write, RequestFailedError
from worlds._bizhawk.client import BizHawkClient

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

logger = logging.getLogger("Client")

# AP ID bases (must match items.py / locations.py)
BASE_LOC_ID  = 7770300
BASE_ITEM_ID = 7770000

# Progressive item AP IDs → tier treasure IDs (in order: tier1, tier2)
PROGRESSIVE_ITEMS = {
    BASE_ITEM_ID + 200: [0x0C, 0x0D],  # Progressive Overalls: Lead → Super Jump Slam
    BASE_ITEM_ID + 201: [0x0B, 0x09],  # Progressive Grab:     Grab Glove → Super Grab
    BASE_ITEM_ID + 202: [0x07, 0x06],  # Progressive Flippers: Swimming → Prince Frog's
}

def _i(tid: int) -> int:
    return BASE_ITEM_ID + tid


# Combined unlock item AP IDs → all component treasure IDs to grant
# (active when slot_data["combined_level_unlocks"] is truthy)
COMBINED_GRANTS = {
    BASE_ITEM_ID + 203: [0x0F, 0x10],        # Lantern & Magical Flame
    BASE_ITEM_ID + 204: [0x12, 0x13],        # Gears
    BASE_ITEM_ID + 205: [0x17, 0x1C],        # Blue Book & Magic Wand
    BASE_ITEM_ID + 206: [0x1A, 0x19],        # Trident & Yellow Book
    BASE_ITEM_ID + 207: [0x1D, 0x1E],        # Skull Ring
    BASE_ITEM_ID + 208: [0x1F, 0x20],        # Tablets
    BASE_ITEM_ID + 209: [0x22, 0x23],        # Scroll
    BASE_ITEM_ID + 210: [0x24, 0x25, 0x26],  # Tusk Set
}

# Level unlock table for combined mode (single item per level)
COMBINED_LEVEL_UNLOCK_ITEMS: dict[int, list[int]] = {
    2:  [_i(0x1b)],              # Peaceful Village — Axe
    3:  [_i(0x1b)],              # Vast Plain — Axe
    4:  [_i(0x02)],              # Bank of Wild River — Blue Music Box
    5:  [_i(0x02)],              # Tidal Coast — Blue Music Box
    6:  [_i(0x0a)],              # Sea Turtle Rocks — Garlic
    7:  [BASE_ITEM_ID + 208],    # Desert Ruins — Tablets
    8:  [BASE_ITEM_ID + 209],    # Volcano's Base — Scroll
    9:  [_i(0x15)],              # Pool of Rain — Jar
    10: [_i(0x15)],              # Town in Chaos — Jar
    11: [_i(0x04)],              # Beneath the Waves — Red Music Box
    12: [BASE_ITEM_ID + 210],    # West Crater — Tusk Set
    13: [BASE_ITEM_ID + 204],    # Grasslands — Gears
    14: [_i(0x01)],              # Big Bridge — Yellow Music Box
    15: [BASE_ITEM_ID + 207],    # Tower of Revival — Skull Ring
    16: [BASE_ITEM_ID + 206],    # Steep Canyon — Trident & Yellow Book
    17: [_i(0x03)],              # Cave of Flames — Green Music Box
    18: [_i(0x18)],              # Above the Clouds — Sky Key
    19: [_i(0x21)],              # Stagnant Swamp — Ornamental Fan
    20: [BASE_ITEM_ID + 205],    # Frigid Sea — Blue Book & Magic Wand
    21: [BASE_ITEM_ID + 203],    # Castle of Illusions — Lantern & Magical Flame
    22: [BASE_ITEM_ID + 210],    # Colossal Hole — Tusk Set
    23: [_i(0x14)],              # Warped Void — Warp Compact
    24: [_i(0x16)],              # East Crater — Treasure Map
    25: [_i(0x11)],              # Forest of Fear — Torch
}

# WRAM0 addresses — always accessible via System Bus (0xC000–0xCFFF)
ADDR_LEVEL          = 0xCA0B   # wLevel:         (owlevel-1)*8 + state
ADDR_END_SCREEN     = 0xCED4   # wLevelEndScreen: 0=idle, 0x81–0x84=chest collecting
ADDR_GAME_MODE      = 0xCA44   # wGameModeFlags:  bit 0 = MODE_GAME_CLEARED (final boss defeated)
ADDR_CHEST_AP_KEY   = 0x2E58   # wChestAPKey (WRAM domain, bank 2 $DE58): chest-gave-key signal (1-4)

# wTreasuresCollected and wUnlockedLevels are in WRAMX bank 2.
# Use the "WRAM" domain (all 32 KB across all banks) for reliable bank-2 access.
# GBC WRAM layout: bank 0 at offset 0x0000, bank 1 at 0x1000, bank 2 at 0x2000, …
ADDR_TREASURES_WRAM     = 0x2000   # WRAM domain offset for wTreasuresCollected (bank 2, 0xD000)
ADDR_UNLOCKED_LEVELS_WRAM = 0x2E00 # WRAM domain offset for wUnlockedLevels    (bank 2, 0xDE00)
ADDR_OPENED_CHESTS_WRAM   = 0x2E19 # WRAM domain offset for wOpenedChests      (bank 2, 0xDE19)
ADDR_LEVEL_KEYS_WRAM      = 0x2E26 # WRAM domain offset for wLevelKeys         (bank 2, 0xDE26)
ADDR_KEY_INVENTORY_WRAM   = 0x2E3F # WRAM domain offset for wKeyInventory      (bank 2, 0xDE3F)

KEY_BASE_LOC_ID  = 7_770_400        # AP location ID = KEY_BASE_LOC_ID + (owlevel-1)*4 + color
KEY_BASE_ITEM_ID = BASE_ITEM_ID + 300  # 7_770_300


LEVEL_NAMES: dict[int, str] = {
     1: "N1 Out of the Woods",
     2: "N2 The Peaceful Village",
     3: "N3 The Vast Plain",
     4: "N4 Bank of the Wild River",
     5: "N5 The Tidal Coast",
     6: "N6 Sea Turtle Rocks",
     7: "W1 Desert Ruins",
     8: "W2 The Volcano's Base",
     9: "W3 The Pool of Rain",
    10: "W4 A Town in Chaos",
    11: "W5 Beneath the Waves",
    12: "W6 The West Crater",
    13: "S1 The Grasslands",
    14: "S2 The Big Bridge",
    15: "S3 Tower of Revival",
    16: "S4 The Steep Canyon",
    17: "S5 Cave of Flames",
    18: "S6 Above the Clouds",
    19: "E1 The Stagnant Swamp",
    20: "E2 The Frigid Sea",
    21: "E3 Castle of Illusions",
    22: "E4 The Colossal Hole",
    23: "E5 The Warped Void",
    24: "E6 The East Crater",
    25: "E7 Forest of Fear",
}

# Level unlock conditions: level (1-25) → set of AP item IDs all required
LEVEL_UNLOCK_ITEMS: dict[int, list[int]] = {
    2:  [_i(0x1b)],                              # Peaceful Village — Axe
    3:  [_i(0x1b)],                              # Vast Plain — Axe
    4:  [_i(0x02)],                              # Bank of Wild River — Blue Music Box
    5:  [_i(0x02)],                              # Tidal Coast — Blue Music Box
    6:  [_i(0x0a)],                              # Sea Turtle Rocks — Garlic
    7:  [_i(0x1f), _i(0x20)],                   # Desert Ruins — Blue+Green Tablet
    8:  [_i(0x22), _i(0x23)],                   # Volcano's Base — Top+Bottom Scroll
    9:  [_i(0x15)],                              # Pool of Rain — Jar
    10: [_i(0x15)],                              # Town in Chaos — Jar
    11: [_i(0x04)],                              # Beneath the Waves — Red Music Box
    12: [_i(0x24), _i(0x25), _i(0x26)],         # West Crater — Tusk B+R + Green Flower
    13: [_i(0x12), _i(0x13)],                   # Grasslands — Gear 1+2
    14: [_i(0x01)],                              # Big Bridge — Yellow Music Box
    15: [_i(0x1e), _i(0x1d)],                   # Tower of Revival — Skull Ring B+R
    16: [_i(0x1a), _i(0x19)],                   # Steep Canyon — Trident + Yellow Book
    17: [_i(0x03)],                              # Cave of Flames — Green Music Box
    18: [_i(0x18)],                              # Above the Clouds — Sky Key
    19: [_i(0x21)],                              # Stagnant Swamp — Ornamental Fan
    20: [_i(0x17), _i(0x1c)],                   # Frigid Sea — Blue Book + Magic Wand
    21: [_i(0x0f), _i(0x10)],                   # Castle of Illusions — Lantern + Magical Flame
    22: [_i(0x24), _i(0x25), _i(0x26)],         # Colossal Hole — Tusk B+R + Green Flower
    23: [_i(0x14)],                              # Warped Void — Warp Compact
    24: [_i(0x16)],                              # East Crater — Treasure Map
    25: [_i(0x11)],                              # Forest of Fear — Torch
}

class WL3Client(BizHawkClient):
    """Wario Land 3 game client for the Archipelago BizHawk Client / mGBA."""

    game          = "Wario Land 3"
    system        = "GBC"
    patch_suffix  = ".apwl3"

    def __init__(self) -> None:
        super().__init__()
        self._prev_end_screen:  int   = 0
        self._prev_level_keys:  bytes = bytes(25)
        self._checked_locs:     set   = set()
        self._items_handled:    int  = 0
        self._cached_received:  set  = set()   # AP IDs received; kept between disconnects
        self._prog_counts:      dict = {}       # ap_id → count received (for progressive tiers)
        self._combined_unlocks: bool = False
        self._seeded_from_wram: bool = False    # True after wOpenedChests read into _checked_locs
        self._goal_sent:        bool = False    # True after CLIENT_GOAL sent to server
        self._cmd_registered:   bool = False    # True after /levels command registered
        self._levels_shown:     bool = False    # True after auto-print on first connect

    # ------------------------------------------------------------------
    # validate_rom — called every poll cycle until it returns True
    # ------------------------------------------------------------------

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        """Return True if a patched WL3 ROM is loaded in mGBA."""
        try:
            rom_title_bytes = (await read(ctx.bizhawk_ctx, [(0x0134, 10, "ROM")]))[0]
            rom_title = bytes(b for b in rom_title_bytes if b != 0).decode("ascii", errors="ignore")
        except RequestFailedError:
            return False

        if "WARIO" not in rom_title:
            return False

        ctx.game            = self.game
        ctx.items_handling  = 0b111   # receive all items (own world + multiworld)
        ctx.want_slot_data  = True
        ctx.watcher_timeout = 0.125   # poll ~8x per second
        return True

    # ------------------------------------------------------------------
    # game_watcher — main poll loop
    # ------------------------------------------------------------------

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        # Always read game state so we can detect chests even when disconnected.
        try:
            read_result = await read(ctx.bizhawk_ctx, [
                (ADDR_LEVEL,      1, "System Bus"),   # wLevel
                (ADDR_END_SCREEN, 1, "System Bus"),   # wLevelEndScreen
            ])
        except RequestFailedError:
            return

        w_level    = read_result[0][0]
        end_screen = read_result[1][0]

        # Bit 7 is set immediately after the color byte is written (set 7, [wLevelEndScreen]),
        # so the live value is 0x81–0x84, not 0x01–0x04.  Mask it off for comparison.
        color_byte = end_screen & 0x7F

        # ---- Detect chest opening: rising edge 0 → {1,2,3,4} (ignoring bit 7) ----
        # Always accumulate into _checked_locs even if not connected — sent on reconnect.
        if self._prev_end_screen == 0 and 1 <= color_byte <= 4:
            owlevel     = (w_level >> 3) + 1          # floor(wLevel / 8) + 1
            color_index = color_byte - 1              # 0=grey, 1=red, 2=green, 3=blue
            loc_id      = BASE_LOC_ID + (owlevel - 1) * 4 + color_index

            if loc_id not in self._checked_locs:
                self._checked_locs.add(loc_id)
                color_name = ("Grey", "Red", "Green", "Blue")[color_index]
                logger.debug(f"[WL3] Chest opened — level {owlevel} {color_name} → AP loc {loc_id}")

        self._prev_end_screen = end_screen

        # ---- Detect key pickups: new bits set in wLevelKeys ----
        try:
            lk_raw = (await read(ctx.bizhawk_ctx, [(ADDR_LEVEL_KEYS_WRAM, 25, "WRAM")]))[0]
            for byte_idx in range(25):
                new_bits = (~self._prev_level_keys[byte_idx]) & lk_raw[byte_idx] & 0x0F
                for bit in range(4):
                    if new_bits & (1 << bit):
                        loc_id = KEY_BASE_LOC_ID + byte_idx * 4 + bit
                        if loc_id not in self._checked_locs:
                            self._checked_locs.add(loc_id)
                            color_name = ("Grey", "Red", "Green", "Blue")[bit]
                            logger.debug(f"[WL3] Key pickup — L{byte_idx+1} {color_name} → AP loc {loc_id}")
            self._prev_level_keys = bytes(lk_raw)
        except RequestFailedError:
            pass

        # Refresh unlock flags from cache if we have any received items.
        # If cache is empty (never connected this session) the ROM handles it from SRAM.
        if self._cached_received:
            await self._update_level_unlocks_cached(ctx)

        # ---- Restore wLevelKeys from checked locations (works offline too) ----
        await self._update_level_keys(ctx)

        if ctx.server is None or ctx.slot is None:
            return

        # Register /levels command once
        if not self._cmd_registered and hasattr(ctx, "command_processor"):
            ctx.command_processor.commands["levels"] = lambda *_: self._show_unlocked_levels(ctx)
            self._cmd_registered = True

        # ---- Seed _checked_locs from wOpenedChests on first server connection ----
        # The ROM now writes wOpenedChests on every chest open and it's saved to SRAM,
        # so it accurately reflects ALL offline checks including gem/crest placeholders.
        if not self._seeded_from_wram:
            try:
                oc_raw = (await read(ctx.bizhawk_ctx, [(ADDR_OPENED_CHESTS_WRAM, 13, "WRAM")]))[0]
                for loc_index in range(100):
                    if oc_raw[loc_index >> 3] & (1 << (loc_index & 7)):
                        self._checked_locs.add(BASE_LOC_ID + loc_index)
                self._seeded_from_wram = True
                logger.debug(f"[WL3] Seeded {len(self._checked_locs)} offline checks from wOpenedChests")
                self._levels_shown = False  # trigger auto-print after items are processed
            except RequestFailedError:
                pass  # retry next poll

        # ---- Send any pending location checks (including those collected offline) ----
        server_checked = set(getattr(ctx, "checked_locations", None) or set())
        pending = self._checked_locs - server_checked
        if pending:
            await ctx.send_msgs([{"cmd": "LocationChecks", "locations": list(pending)}])

        # Track combined mode from slot data
        self._combined_unlocks = bool((ctx.slot_data or {}).get("combined_level_unlocks", 0))

        # If AP server reset the items list, sync handler index down to match.
        # _update_level_unlocks_cached restores all treasure bits from _cached_received.
        if len(ctx.items_received) < self._items_handled:
            self._items_handled = len(ctx.items_received)
            # Recount progressive items from scratch after a server reset.
            self._prog_counts = {}
            for net_item in ctx.items_received:
                if net_item.item in PROGRESSIVE_ITEMS:
                    self._prog_counts[net_item.item] = self._prog_counts.get(net_item.item, 0) + 1

        # ---- Grant any newly received items ----
        while self._items_handled < len(ctx.items_received):
            ap_id = ctx.items_received[self._items_handled].item
            self._cached_received.add(ap_id)
            if ap_id in PROGRESSIVE_ITEMS:
                self._prog_counts[ap_id] = self._prog_counts.get(ap_id, 0) + 1
            await self._grant_item(ctx, ap_id)
            self._items_handled += 1

        # Keep cache in sync with full server list (covers reconnect/reset cases)
        for net_item in ctx.items_received:
            self._cached_received.add(net_item.item)

        # Auto-print unlocked levels once after first connect + items processed
        if not self._levels_shown and self._seeded_from_wram:
            self._show_unlocked_levels(ctx)
            self._levels_shown = True

        # ---- Victory detection: wGameModeFlags bit 0 = MODE_GAME_CLEARED ----
        if not self._goal_sent:
            try:
                mode_byte = (await read(ctx.bizhawk_ctx, [(ADDR_GAME_MODE, 1, "System Bus")]))[0][0]
                if mode_byte & 0x01:  # MODE_GAME_CLEARED
                    await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
                    self._goal_sent = True
                    logger.info("[WL3] Goal achieved — final boss defeated!")
            except RequestFailedError:
                pass

        # ---- Update opened-chest bitmask in WRAM ----
        await self._update_opened_chests(ctx)

    # ------------------------------------------------------------------
    # Item granting helpers
    # ------------------------------------------------------------------

    async def _grant_item(self, ctx: "BizHawkClientContext", ap_id: int) -> None:
        """Resolve an AP item ID to treasure ID(s) and apply them to the game."""
        if ap_id in PROGRESSIVE_ITEMS:
            # ROM fully handles progressive ability progression via treasure_clear.asm.
            # Client must not write these bits — doing so before a chest is opened
            # would cause the ROM's upgrade logic to fire prematurely.
            pass
        elif ap_id in COMBINED_GRANTS:
            for tid in COMBINED_GRANTS[ap_id]:
                logger.debug(f"[WL3] Combined AP {ap_id} → treasure 0x{tid:02X}")
                await self._apply_treasure(ctx, tid)
        elif BASE_ITEM_ID < ap_id <= BASE_ITEM_ID + 100:
            tid = ap_id - BASE_ITEM_ID
            logger.debug(f"[WL3] Item AP {ap_id} → treasure 0x{tid:02X}")
            await self._apply_treasure(ctx, tid)
        elif KEY_BASE_ITEM_ID <= ap_id < KEY_BASE_ITEM_ID + 100:
            key_index = ap_id - KEY_BASE_ITEM_ID
            owlevel_minus1 = key_index >> 2   # // 4
            color = key_index & 3
            color_name = ("Grey", "Red", "Green", "Blue")[color]
            logger.debug(f"[WL3] Key item AP {ap_id} → L{owlevel_minus1+1} {color_name} key")
            await self._set_key_bit(ctx, owlevel_minus1, color)
            # Signal ROM to show key portrait on clear screen if a chest is active
            try:
                cur_end = (await read(ctx.bizhawk_ctx, [(ADDR_END_SCREEN, 1, "System Bus")]))[0][0]
                chest_color = cur_end & 0x7F  # strip bit 7
                if 1 <= chest_color <= 4:
                    await write(ctx.bizhawk_ctx, [(ADDR_CHEST_AP_KEY, bytes([chest_color]), "WRAM")])
                    logger.debug(f"[WL3] wChestAPKey={chest_color} (key portrait for chest color {chest_color})")
            except RequestFailedError:
                pass

    async def _apply_treasure(self, ctx: "BizHawkClientContext", tid: int) -> None:
        """Set wTreasuresCollected bit. The ROM derives all ability vars from
        wTreasuresCollected every frame via UpdateAbilitiesFromTreasures."""
        await self._set_treasure_bit(ctx, tid)

    async def _set_key_bit(self, ctx: "BizHawkClientContext", owlevel_minus1: int, color: int) -> None:
        """Set a key bit in wKeyInventory (WRAMX bank 2) — key item received from AP."""
        addr = ADDR_KEY_INVENTORY_WRAM + owlevel_minus1
        bit_mask = 1 << color
        try:
            cur = (await read(ctx.bizhawk_ctx, [(addr, 1, "WRAM")]))[0][0]
            new_val = cur | bit_mask
            await write(ctx.bizhawk_ctx, [(addr, bytes([new_val]), "WRAM")])
        except RequestFailedError as e:
            logger.warning(f"[WL3] Failed to set key L{owlevel_minus1+1} color {color}: {e}")

    async def _set_treasure_bit(self, ctx: "BizHawkClientContext", treasure_id: int) -> None:
        """Set the collected bit for treasure_id in wTreasuresCollected (WRAMX bank 2)."""
        if not (1 <= treasure_id <= 100):
            return
        byte_idx = treasure_id >> 3        # matches IsTreasureCollected: tid / 8
        bit_mask = 1 << (treasure_id & 7)  # matches IsTreasureCollected: tid % 8
        addr     = ADDR_TREASURES_WRAM + byte_idx
        try:
            cur = (await read(ctx.bizhawk_ctx, [(addr, 1, "WRAM")]))[0][0]
            new_val = cur | bit_mask
            await write(ctx.bizhawk_ctx, [(addr, bytes([new_val]), "WRAM")])
            logger.debug(f"[WL3] Set treasure 0x{treasure_id:02X}: WRAM[0x{addr:04X}] 0x{cur:02X}→0x{new_val:02X}")
        except RequestFailedError as e:
            logger.warning(f"[WL3] Failed to set treasure 0x{treasure_id:02X}: {e}")

    async def _update_opened_chests(self, ctx: "BizHawkClientContext") -> None:
        """Write wOpenedChests (13 bytes) based on which AP locations are checked.

        loc_index = (owlevel - 1) * 4 + color_index  (matches ROM chest table layout)
        Bit (loc_index & 7) of byte (loc_index >> 3) is set for each checked chest.
        The ROM reads this for gem/crest placeholder IDs ($4E-$54) to decide whether
        a chest should appear pre-opened on level entry.
        """
        # Combine all available sources of checked locations:
        #   ctx.locations_checked  — AP framework set (current session RoomUpdates)
        #   self._checked_locs     — our own tracking (current session sends)
        #   ctx.checked_locations  — server record from Connected message (includes prior sessions)
        all_checked = set(ctx.locations_checked or set())
        all_checked |= self._checked_locs
        all_checked |= set(getattr(ctx, "checked_locations", None) or set())
        opened = bytearray(13)
        for loc_id in all_checked:
            loc_index = loc_id - BASE_LOC_ID
            if 0 <= loc_index < 100:
                opened[loc_index >> 3] |= 1 << (loc_index & 7)
        try:
            await write(ctx.bizhawk_ctx, [(ADDR_OPENED_CHESTS_WRAM, bytes(opened), "WRAM")])
        except RequestFailedError:
            pass

    async def _update_level_keys(self, ctx: "BizHawkClientContext") -> None:
        """Write wLevelKeys (visited slots) and wKeyInventory (held keys) each poll.
        Mirrors _update_opened_chests — self-healing if WRAM is cleared on level load.
        wLevelKeys  ← which key LOCATIONS have been checked (suppresses key objects).
        wKeyInventory ← which key ITEMS have been received (grants chest access)."""
        # wLevelKeys: set from visited key locations (object suppression)
        level_keys = bytearray(25)
        all_checked = set(ctx.locations_checked or set())
        all_checked |= self._checked_locs
        all_checked |= set(getattr(ctx, "checked_locations", None) or set())
        for loc_id in all_checked:
            key_index = loc_id - KEY_BASE_LOC_ID
            if 0 <= key_index < 100:
                level_keys[key_index >> 2] |= 1 << (key_index & 3)
        # wKeyInventory: set from received key items (held keys for chest access)
        key_inventory = bytearray(25)
        for ap_id in self._cached_received:
            if KEY_BASE_ITEM_ID <= ap_id < KEY_BASE_ITEM_ID + 100:
                key_index = ap_id - KEY_BASE_ITEM_ID
                key_inventory[key_index >> 2] |= 1 << (key_index & 3)
        try:
            # OR with current WRAM to preserve ROM-written bits not yet detected
            cur = (await read(ctx.bizhawk_ctx, [
                (ADDR_LEVEL_KEYS_WRAM, 25, "WRAM"),
                (ADDR_KEY_INVENTORY_WRAM, 25, "WRAM"),
            ]))
            for i in range(25):
                level_keys[i] |= cur[0][i]
                key_inventory[i] |= cur[1][i]
        except RequestFailedError:
            pass
        try:
            await write(ctx.bizhawk_ctx, [
                (ADDR_LEVEL_KEYS_WRAM,    bytes(level_keys),    "WRAM"),
                (ADDR_KEY_INVENTORY_WRAM, bytes(key_inventory), "WRAM"),
            ])
        except RequestFailedError:
            pass

    def _show_unlocked_levels(self, ctx: "BizHawkClientContext") -> None:
        """Print which levels are currently unlocked based on received items."""
        unlock_table = COMBINED_LEVEL_UNLOCK_ITEMS if self._combined_unlocks else LEVEL_UNLOCK_ITEMS
        unlocked = []
        for level in range(1, 26):
            name = LEVEL_NAMES[level]
            required = unlock_table.get(level)
            if required is None or all(item in self._cached_received for item in required):
                unlocked.append(name)
        logger.info("=== Unlocked Levels ===")
        for name in unlocked:
            logger.info(f"  {name}")

    async def _update_level_unlocks_cached(self, ctx: "BizHawkClientContext") -> None:
        """Stamp AP-received treasure IDs into wTreasuresCollected (OR-merge) so the
        ROM's UpdateLevelUnlocks (which reads wTreasuresCollected) correctly computes
        wUnlockedLevels on every map transition. wTreasuresCollected is SRAM-saved, so
        this persists across reloads without the client. wUnlockedLevels is intentionally
        NOT written here — the ROM is the sole authority on that derived array."""
        # Build the treasure-bit mask for every AP item received and OR it into
        # wTreasuresCollected so the ROM can recompute unlocks from the save alone.
        ap_bits = bytearray(13)
        for ap_id in self._cached_received:
            tid = ap_id - BASE_ITEM_ID
            if 0 <= tid < 0x65:                          # regular treasure ID
                ap_bits[tid >> 3] |= 1 << (tid & 7)
            elif ap_id in COMBINED_GRANTS:               # combined item — expand
                for tid2 in COMBINED_GRANTS[ap_id]:
                    ap_bits[tid2 >> 3] |= 1 << (tid2 & 7)
        # Progressive abilities: set tier bits based on how many have been received.
        # count >= 1 → tier 1 bit; count >= 2 → tier 2 bit.
        # Skip during chest animation (wLevelEndScreen != 0) — the ROM owns the upgrade
        # logic in .do_collect and must see the pre-chest WRAM state unmodified.
        # After the animation ends (_prev_end_screen returns to 0), we write the bits;
        # by then the ROM has already set them so the write is a no-op.
        if self._prev_end_screen == 0:
            for ap_id, count in self._prog_counts.items():
                tier_ids = PROGRESSIVE_ITEMS[ap_id]
                if count >= 1:
                    t = tier_ids[0]
                    ap_bits[t >> 3] |= 1 << (t & 7)
                if count >= 2:
                    t = tier_ids[1]
                    ap_bits[t >> 3] |= 1 << (t & 7)
        try:
            cur = (await read(ctx.bizhawk_ctx, [(ADDR_TREASURES_WRAM, 13, "WRAM")]))[0]
            merged = bytes(a | b for a, b in zip(cur, ap_bits))
            # Only write bytes where we're adding new bits.
            # Writing bytes unchanged would race against the ROM setting progressive
            # ability bits (e.g., Swimming Flippers) in the same byte — a stale read
            # followed by a write-back would clear the ROM's freshly-set bit.
            writes = [(ADDR_TREASURES_WRAM + i, bytes([merged[i]]), "WRAM")
                      for i in range(13) if merged[i] != cur[i]]
            if writes:
                await write(ctx.bizhawk_ctx, writes)
        except RequestFailedError:
            pass
