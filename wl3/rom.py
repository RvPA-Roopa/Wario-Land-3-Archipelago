"""
WL3 patch class — builds the .apwl3 patch file using AP's APProcedurePatch system.

Procedure:
  1. apply_bsdiff4  — applies base ROM hack (original WL3 → hacked base)
  2. apply_tokens   — writes the randomized 100-byte chest table
"""
import base64
import colorsys
import json
import os
import zipfile
from typing import TYPE_CHECKING

from settings import get_settings
from worlds.Files import APProcedurePatch, APTokenMixin, APTokenTypes

if TYPE_CHECKING:
    from . import WL3World

CHEST_TABLE_OFFSET               = 0x001A84   # LevelTreasureIDs_WithoutTemple (100 bytes)
KEYSANITY_MODE_OFFSET            = 0x001AE8   # KeysanityMode (1 byte: 0=vanilla, 1=simple, 2=full)
KEY_TABLE_OFFSET                 = 0x001AE9   # LevelKeyPool (100 bytes; ITEM_KEY_BASE + index = vanilla)
CHEST_KEY_PAL_OFFSET             = 0x001B4D   # ChestKeyPalettes (100 bytes; $FF=not key, 4-7=palette)
TREASURE_DUMMY_TILE_OFFSET       = 0x099940   # TreasureGfx[$65] — 64 bytes (4 tiles, 2bpp)
TREASURE_DUMMY_PAL_OFFSET        = 0x09AD1F   # TreasureOBPals[$65] — 1 byte (palette index)
TREASURE_GFX_BASE                = 0x098000   # TreasureGfx[0] — each entry 64 bytes
TREASURE_PAL_BASE                = 0x09ACBA   # TreasureOBPals[0] — each entry 1 byte
KEY_COLOR_PALS = [0x08, 0x05, 0x06, 0x07]    # OBPAL: grey, red, green, blue
OBPAL_TREASURE_PURPLE = 0x09                  # Combined unlock items

def _build_key_portrait() -> bytes:
    """Generate 16x16 key icon portrait (4 tiles, 2bpp) programmatically.
    Color 1=highlight, 2=fill (themed), 3=outline. No embedded game assets."""
    # 16x16 pixel grid: 0=transparent, 1=highlight, 2=fill, 3=outline
    rows = [
        "00000333" "33300000",  # row 0
        "00033112" "22233000",  # row 1
        "00311222" "22222300",  # row 2
        "00312333" "33322300",  # row 3
        "00322333" "33322300",  # row 4
        "00322222" "22222300",  # row 5
        "00033222" "22233000",  # row 6
        "00000333" "33300000",  # row 7
        "00000031" "23000000",  # row 8
        "00000003" "30000000",  # row 9
        "00000031" "23330000",  # row 10
        "00000032" "22213000",  # row 11
        "00000032" "23330000",  # row 12
        "00000032" "23330000",  # row 13
        "00000032" "22213000",  # row 14
        "00000003" "33330000",  # row 15
    ]
    # Convert to 4 tiles (top-left, bottom-left, top-right, bottom-right)
    out = bytearray()
    for ty, tx in [(0, 0), (8, 0), (0, 8), (8, 8)]:
        for y in range(8):
            lo = hi = 0
            for x in range(8):
                px = int(rows[ty + y][tx + x])
                bit = 7 - x
                lo |= (px & 1) << bit
                hi |= ((px >> 1) & 1) << bit
            out.append(lo)
            out.append(hi)
    return bytes(out)

KEY_PORTRAIT_TILES = _build_key_portrait()
LEVEL_MUSIC_OFFSET               = 0x03FE40   # LevelMusic table (25 levels × 16 bytes = 400 bytes)
MUSIC_BOXES_REQUIRED_OFFSET      = 0x080EEB   # MusicBoxesRequired byte in Bank 20
START_WITH_AXE_OFFSET            = 0x080ED4   # StartWithAxeOpt byte in Bank 20
START_WITH_MAG_GLASS_OFFSET      = 0x080ED5   # StartWithMagnifyingGlassOpt byte in Bank 20
GOLF_PRICE_OPT_OFFSET            = 0x003A00   # GolfPriceOpt byte in Home bank
GOLF_BUILDING_OPT_OFFSET         = 0x003A01   # GolfBuildingOpt byte in Home bank
COMBINED_COMPANION_TABLE_OFFSET  = 0x003A02   # CombinedCompanionTable (101 bytes, home bank)
TREASURE_OB_PALS_OFFSET          = 0x09ACBA   # TreasureOBPals table (indexed by treasure ID)

# Combined-item companion chains: collecting key → also grant value (chained).
# Tusk Set: $24→$25→$26 (two hops).
_COMPANION_PAIRS = {
    0x0F: 0x10,  # Lantern → Magical Flame
    0x12: 0x13,  # Gear 1 → Gear 2
    0x17: 0x1C,  # Blue Book → Magic Wand
    0x1A: 0x19,  # Trident → Yellow Book
    0x1D: 0x1E,  # Skull Ring Blue → Skull Ring Red
    0x1F: 0x20,  # Blue Tablet → Green Tablet
    0x22: 0x23,  # Top Half of Scroll → Bottom Half of Scroll
    0x24: 0x25,  # Tusk Blue → Tusk Red
    0x25: 0x26,  # Tusk Red → Green Flower (chain)
}

# OBPAL constants: YELLOW=4, RED=5, GREEN=6, BLUE=7
_OBPAL_YELLOW = 4
_OBPAL_RED    = 5
_OBPAL_GREEN  = 6
_OBPAL_BLUE   = 7

# Palette overrides for combined items (applied only when combined_level_unlocks is on).
# Each entry: (treasure_id, new_palette_byte)
# Chosen to be visually distinct from the vanilla palette for that treasure.
_COMBINED_PAL_OVERRIDES = [
    (0x0F, _OBPAL_RED),    # Lantern         (vanilla: YELLOW) → RED
    (0x12, _OBPAL_GREEN),  # Gear 1          (vanilla: BLUE)   → GREEN
    (0x17, _OBPAL_RED),    # Blue Book       (vanilla: BLUE)   → RED
    (0x1A, _OBPAL_BLUE),   # Trident         (vanilla: GREEN)  → BLUE
    (0x1D, _OBPAL_RED),    # Skull Ring Blue (vanilla: BLUE)   → RED
    (0x1F, _OBPAL_GREEN),  # Blue Tablet     (vanilla: BLUE)   → GREEN
    (0x22, _OBPAL_BLUE),   # Top Half Scroll (vanilla: YELLOW) → BLUE
    (0x24, _OBPAL_YELLOW), # Tusk Blue       (vanilla: GREEN)  → YELLOW
]

# Vanilla (day_id, night_id) music pairs for each of the 25 levels, in level order.
_LEVEL_MUSIC = [
    (0x01, 0x02),  # Out of the Woods
    (0x07, 0x08),  # The Peaceful Village
    (0x0e, 0x0f),  # The Vast Plain
    (0x10, 0x10),  # Bank of the Wild River
    (0x11, 0x11),  # The Tidal Coast
    (0x11, 0x11),  # Sea Turtle Rocks
    (0x05, 0x05),  # Desert Ruins
    (0x0c, 0x0b),  # The Volcano's Base
    (0x13, 0x14),  # The Pool of Rain
    (0x07, 0x08),  # A Town in Chaos
    (0x11, 0x11),  # Beneath the Waves
    (0x0d, 0x0d),  # The West Crater
    (0x0e, 0x0f),  # The Grasslands
    (0x10, 0x10),  # The Big Bridge
    (0x05, 0x05),  # Tower of Revival
    (0x10, 0x10),  # The Steep Canyon
    (0x12, 0x12),  # Cave of Flames
    (0x09, 0x0a),  # Above the Clouds
    (0x13, 0x14),  # The Stagnant Swamp
    (0x06, 0x06),  # The Frigid Sea
    (0x0c, 0x0b),  # Castle of Illusions
    (0x12, 0x12),  # The Colossal Hole
    (0x04, 0x04),  # The Warped Void
    (0x0d, 0x0d),  # The East Crater
    (0x03, 0x03),  # Forest of Fear
]

def _build_level_music_table(pairs) -> bytes:
    """Encode (day_id, night_id) pairs into the LevelMusic table format.
    Each entry = 4×dw day_id + 4×dw night_id (16 bytes, little-endian)."""
    out = bytearray()
    for day_id, night_id in pairs:
        for _ in range(4):
            out.append(day_id & 0xFF)
            out.append(0x00)
        for _ in range(4):
            out.append(night_id & 0xFF)
            out.append(0x00)
    return bytes(out)


class WL3ProcedurePatch(APProcedurePatch, APTokenMixin):
    game                = "Wario Land 3"
    hash                = None   # no hash check — any WL3 ROM version accepted
    patch_file_ending   = ".apwl3"
    result_file_ending  = ".gbc"

    procedure = [
        ("apply_bsdiff4", ["base_patch.bsdiff4"]),
        ("apply_tokens",  ["token_data.bin"]),
    ]

    @classmethod
    def get_source_data(cls) -> bytes:
        opts = get_settings().wl3_options
        # In the patching context WL3World may not be loaded yet,
        # so opts may be a plain dict rather than a WL3Settings Group.
        rom_path = opts["rom_file"] if isinstance(opts, dict) else opts.rom_file
        with open(rom_path, "rb") as f:
            return f.read()


# --- palette helpers ---

def _gbc_to_floats(color: int):
    """15-bit GBC color → (r, g, b) as 0.0–1.0 floats."""
    r = (color & 0x1F) / 31.0
    g = ((color >> 5) & 0x1F) / 31.0
    b = ((color >> 10) & 0x1F) / 31.0
    return r, g, b

def _floats_to_gbc(r: float, g: float, b: float) -> int:
    """(r, g, b) 0.0–1.0 floats → 15-bit GBC color."""
    return round(r * 31) | (round(g * 31) << 5) | (round(b * 31) << 10)

def _recolor_palette(data: bytes, rand) -> bytes:
    """Recolor an 8-byte GBC palette.

    Near-grayscale colors (s < 0.25) each get an independent random hue at
    high saturation.  Saturated colors (s >= 0.25) are all hue-rotated by a
    single shared random offset so their relative color relationships are
    preserved.  Very dark colors (v < 0.15) are left unchanged.
    """
    GRAY_THRESHOLD = 0.25
    hue_rotate = rand()  # one shared rotation for saturated colors in this palette
    out = bytearray(len(data))
    for i in range(len(data) // 2):
        color = data[i * 2] | (data[i * 2 + 1] << 8)
        r, g, b = _gbc_to_floats(color)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        if v < 0.15:
            pass  # dark/outline colors — leave unchanged
        elif s < GRAY_THRESHOLD:
            # near-white / light-gray: assign a random hue at moderate saturation
            # (toned down to avoid intense hue shifts on glow effects sharing palette 0)
            h = rand()
            s = 0.45
        else:
            # saturated colors: rotate hue by shared offset
            h = (h + hue_rotate) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        new = _floats_to_gbc(r, g, b)
        out[i * 2]     = new & 0xFF
        out[i * 2 + 1] = (new >> 8) & 0xFF
    return bytes(out)


def write_tokens(world: "WL3World", patch: WL3ProcedurePatch) -> None:
    """Write the randomized chest table, key pool, and options into the patch."""
    chest_assignments = list(world._build_chest_assignments())

    key_assignments = world._build_key_assignments()
    patch.write_token(APTokenTypes.WRITE, KEY_TABLE_OFFSET, bytes(key_assignments))

    # Write keysanity mode flag (0=vanilla, 1=simple, 2=full)
    from .options import KeyShuffle
    patch.write_token(APTokenTypes.WRITE, KEYSANITY_MODE_OFFSET,
                      bytes([int(world.options.key_shuffle)]))

    # Patch TREASURE_DUMMY ($65) tile graphics with key icon.
    patch.write_token(APTokenTypes.WRITE, TREASURE_DUMMY_TILE_OFFSET, KEY_PORTRAIT_TILES)

    # Build per-chest palette override table: $FF = use default, 4-9 = override palette.
    from .items import COMBINED_ITEMS, KEY_ITEM_TABLE
    from .locations import LOCATION_TABLE
    pal_overrides = bytearray([0xFF] * 100)
    for loc_name, loc_data in LOCATION_TABLE.items():
        idx = loc_data.loc_index
        location = world.multiworld.get_location(loc_name, world.player)
        item = location.item
        if item is None or item.player != world.player:
            continue
        # Key items at chests → key color palette
        if chest_assignments[idx] == 0x65 and item.name in KEY_ITEM_TABLE:
            color = KEY_ITEM_TABLE[item.name].color_index
            pal_overrides[idx] = KEY_COLOR_PALS[color]
        # Combined items → purple palette
        elif item.name in COMBINED_ITEMS:
            pal_overrides[idx] = OBPAL_TREASURE_PURPLE
    patch.write_token(APTokenTypes.WRITE, CHEST_KEY_PAL_OFFSET, bytes(pal_overrides))

    patch.write_token(APTokenTypes.WRITE, CHEST_TABLE_OFFSET, bytes(chest_assignments))

    music_boxes_required = int(world.options.music_boxes_required)
    patch.write_token(APTokenTypes.WRITE, MUSIC_BOXES_REQUIRED_OFFSET,
                      bytes([music_boxes_required]))

    start_with_axe = int(world.options.start_with_axe)
    patch.write_token(APTokenTypes.WRITE, START_WITH_AXE_OFFSET,
                      bytes([start_with_axe]))

    start_with_mag_glass = int(world.options.start_with_magnifying_glass)
    patch.write_token(APTokenTypes.WRITE, START_WITH_MAG_GLASS_OFFSET,
                      bytes([start_with_mag_glass]))

    golf_price = int(world.options.golf_price)
    patch.write_token(APTokenTypes.WRITE, GOLF_PRICE_OPT_OFFSET,
                      bytes([golf_price]))

    golf_building = int(world.options.golf_building)
    patch.write_token(APTokenTypes.WRITE, GOLF_BUILDING_OPT_OFFSET,
                      bytes([golf_building]))

    # --- combined item companion table ---
    if int(world.options.combined_level_unlocks):
        companion_table = bytearray(101)
        for trigger, companion in _COMPANION_PAIRS.items():
            companion_table[trigger] = companion
        patch.write_token(APTokenTypes.WRITE, COMBINED_COMPANION_TABLE_OFFSET,
                          bytes(companion_table))

    # --- combined item palette overrides ---
    if int(world.options.combined_level_unlocks):
        for tid, pal in _COMBINED_PAL_OVERRIDES:
            patch.write_token(APTokenTypes.WRITE, TREASURE_OB_PALS_OFFSET + tid, bytes([pal]))

    # --- music shuffle ---
    music_shuffle = int(world.options.music_shuffle)
    if music_shuffle == 1:  # split: day with day, night with night
        days   = [d for d, _ in _LEVEL_MUSIC]
        nights = [n for _, n in _LEVEL_MUSIC]
        world.random.shuffle(days)
        world.random.shuffle(nights)
        patch.write_token(APTokenTypes.WRITE, LEVEL_MUSIC_OFFSET,
                          _build_level_music_table(zip(days, nights)))
    elif music_shuffle == 2:  # full: all 50 track slots shuffled freely
        pool = [d for d, _ in _LEVEL_MUSIC] + [n for _, n in _LEVEL_MUSIC]
        world.random.shuffle(pool)
        patch.write_token(APTokenTypes.WRITE, LEVEL_MUSIC_OFFSET,
                          _build_level_music_table(zip(pool[:25], pool[25:])))

    # --- palette shuffle ---
    if world.options.enemy_palette_shuffle:
        here = os.path.dirname(os.path.abspath(__file__))
        table_path = os.path.join(here, "data", "palette_table.json")
        if os.path.exists(table_path):
            with open(table_path) as f:
                palette_table = json.load(f)
        else:
            archive = getattr(__loader__, "archive", None)
            if archive is None:
                raise FileNotFoundError("Cannot locate palette_table.json")
            with zipfile.ZipFile(archive) as zf:
                palette_table = json.loads(zf.read("wl3/data/palette_table.json"))

        for entry in palette_table:
            offset = entry["offset"]
            data   = base64.b64decode(entry["data"])
            result = bytearray()
            for i in range(len(data) // 8):
                chunk = data[i * 8 : (i + 1) * 8]
                result.extend(_recolor_palette(chunk, world.random.random))
            patch.write_token(APTokenTypes.WRITE, offset, bytes(result))

    # Wario palette offsets (color 3 = overalls/outline in each variant)
    WARIO_OVERALLS_OFFSETS = [
        0xc806, 0xc812, 0xc826, 0xc82e, 0xc836, 0xc83e, 0xc846, 0xc84e,
        0xc856, 0xc85a, 0xc85e, 0xc866, 0xc86e, 0xc876, 0xc87e, 0xc886,
        0xc89e, 0xc8ae, 0xc8be, 0xc8c6, 0xc8ce, 0xc8d6, 0xc8de, 0xc8ee,
        0xc8fe, 0xc90e, 0xc916, 0xc936, 0xc942, 0xc956, 0xc95e, 0xc96e,
        0xc97e, 0xc996, 0xc99e, 0xc9a6, 0xc9ae, 0xc9c6, 0xc9d6, 0xc9e6,
    ]
    WARIO_SHIRT_OFFSETS = [off - 4 for off in WARIO_OVERALLS_OFFSETS]
    if world.options.wario_overalls_shuffle:
        r = world.random.randint(0, 23)
        g = world.random.randint(0, 23)
        b = world.random.randint(0, 23)
        gbc_color = (b << 10) | (g << 5) | r
        color_bytes = bytes([gbc_color & 0xFF, (gbc_color >> 8) & 0xFF])
        for off in WARIO_OVERALLS_OFFSETS:
            patch.write_token(APTokenTypes.WRITE, off, color_bytes)

    if world.options.wario_shirt_shuffle:
        r = world.random.randint(8, 31)
        g = world.random.randint(8, 31)
        b = world.random.randint(8, 31)
        gbc_color = (b << 10) | (g << 5) | r
        color_bytes = bytes([gbc_color & 0xFF, (gbc_color >> 8) & 0xFF])
        for off in WARIO_SHIRT_OFFSETS:
            patch.write_token(APTokenTypes.WRITE, off, color_bytes)

    # Embed the base bsdiff4 patch and token data into self.files so
    # APProcedurePatch.write_contents() includes them in the output zip.
    here = os.path.dirname(os.path.abspath(__file__))
    bsdiff4_path = os.path.join(here, "data", "base_patch.bsdiff4")
    if os.path.exists(bsdiff4_path):
        with open(bsdiff4_path, "rb") as f:
            bsdiff4_data = f.read()
    else:
        # Loaded from inside an apworld zip — read via the zip archive
        archive = getattr(__loader__, "archive", None)
        if archive is None:
            raise FileNotFoundError("Cannot locate base_patch.bsdiff4")
        with zipfile.ZipFile(archive) as zf:
            bsdiff4_data = zf.read("wl3/data/base_patch.bsdiff4")
    patch.write_file("base_patch.bsdiff4", bsdiff4_data)
    patch.write_file("token_data.bin", patch.get_token_binary())
