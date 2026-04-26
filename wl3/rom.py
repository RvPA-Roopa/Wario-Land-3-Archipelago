"""
WL3 patch class — builds the .apwl3 patch file using AP's APProcedurePatch system.

Procedure:
  1. apply_bsdiff4  — applies base ROM hack (original WL3 → hacked base)
  2. apply_tokens   — writes the randomized 100-byte chest table
"""
import colorsys
import os
import zipfile
from typing import TYPE_CHECKING

from settings import get_settings
from worlds.Files import APProcedurePatch, APTokenMixin, APTokenTypes

if TYPE_CHECKING:
    from . import WL3World

CHEST_TABLE_OFFSET               = 0x001AA2   # LevelTreasureIDs_WithoutTemple (100 bytes)
KEYSANITY_MODE_OFFSET            = 0x001B06   # KeysanityMode (1 byte: 0=vanilla, 1=simple, 2=full)
KEY_TABLE_OFFSET                 = 0x001B07   # LevelKeyPool (100 bytes; ITEM_KEY_BASE + index = vanilla)
CHEST_KEY_PAL_OFFSET             = 0x001B6B   # ChestKeyPalettes (100 bytes; $FF=not key, 4-7=palette)
KEY_PAL_OVERRIDE_OFFSET          = 0x001BCF   # KeyPaletteOverrides (100 bytes; $FF=default, else OBPAL)
CHEST_KEYRING_OFFSET             = 0x001C33   # ChestKeyringTargets (100 bytes; $FF=not keyring, 1-25=target owlevel)
KEY_KEYRING_OFFSET               = 0x001C97   # KeyKeyringTargets   (100 bytes; same format, but for key slots)
INITIAL_TREASURES_OFFSET         = 0x001CFB   # InitialTreasuresBits (13 bytes; OR'd into wTreasuresCollected at new-game init)
INITIAL_KEYS_OFFSET              = 0x001D08   # InitialKeysBits      (25 bytes; OR'd into wKeyInventory      at new-game init)
TRAP_CHEST_TABLE_OFFSET          = 0x001D21   # TrapChestTable (100 bytes; 0=no trap, 1-5=TRAP_* — offline trap dispatch from chests)
TRAP_KEY_TABLE_OFFSET            = 0x001D85   # TrapKeyTable   (100 bytes; same encoding — offline trap dispatch from key slots)
TREASURE_DUMMY_TILE_OFFSET       = 0x099940   # TreasureGfx[$65] — 64 bytes (4 tiles, 2bpp)
TREASURE_ZOMBIE_TILE_OFFSET      = 0x0999c0   # TreasureZombieFormGfx    — 64 bytes (4 tiles, 2bpp)
TREASURE_FIRE_TILE_OFFSET        = 0x099a00   # TreasureFireFormGfx      — 64 bytes (4 tiles, 2bpp)
TREASURE_BAT_TILE_OFFSET         = 0x099a40   # TreasureBatFormGfx       — 64 bytes (4 tiles, 2bpp)
TREASURE_INVISIBLE_TILE_OFFSET   = 0x099a80   # TreasureInvisibleFormGfx — 64 bytes (4 tiles, 2bpp)
TREASURE_FAT_TILE_OFFSET         = 0x099ac0   # TreasureFatFormGfx       — 64 bytes (4 tiles, 2bpp)
TREASURE_SNOWMAN_TILE_OFFSET     = 0x099b00   # TreasureSnowmanFormGfx   — 64 bytes (4 tiles, 2bpp)
TREASURE_BOUNCY_TILE_OFFSET      = 0x099b40   # TreasureBouncyFormGfx    — 64 bytes (4 tiles, 2bpp)
TREASURE_YARN_TILE_OFFSET        = 0x099b80   # TreasureYarnFormGfx      — 64 bytes (4 tiles, 2bpp)
TREASURE_ICE_SKATIN_TILE_OFFSET  = 0x099bc0   # TreasureIceSkatinFormGfx — 64 bytes (4 tiles, 2bpp)
TREASURE_FLAT_TILE_OFFSET        = 0x099c00   # TreasureFlatFormGfx      — 64 bytes (4 tiles, 2bpp)
TREASURE_PUFFY_TILE_OFFSET       = 0x099c40   # TreasurePuffyFormGfx     — 64 bytes (4 tiles, 2bpp)

# Vanilla Form icon extractions. Each entry:
#   (kind, offset, length, crop_x, crop_y, dest_offset)
# kind values:
#   "sprite":     RLE-compressed 8x16 sprite-pair sheet
#                 (src/gfx/enemies/*.2bpp.rle, src/gfx/cutscenes/*.2bpp.rle)
#   "sprite_raw": uncompressed 8x16 sprite-pair sheet
#                 (src/gfx/wario/*.2bpp — built with rgbgfx --interleave)
#   "tilemap":   uncompressed row-major 8x8 sheet
#                 (src/gfx/levels/main_tiles*.2bpp)
# Width is always 16 tiles; height is inferred from sheet size.
FORM_ICON_EXTRACTIONS = (
    ("sprite",     0x1a8a8a, 824,    96,  0, TREASURE_ZOMBIE_TILE_OFFSET),
    ("sprite",     0x1a945b, 544,    53,  0, TREASURE_BAT_TILE_OFFSET),
    ("sprite",     0x0a5ebd, 3175,   88,  0, TREASURE_INVISIBLE_TILE_OFFSET),
    ("sprite",     0x1a85b3, 854,    72, 16, TREASURE_FAT_TILE_OFFSET),
    ("sprite_raw", 0x1e8000, 2048,    1, 48, TREASURE_SNOWMAN_TILE_OFFSET),
    ("sprite",     0x0a5ebd, 3175,  108, 62, TREASURE_BOUNCY_TILE_OFFSET),
    ("sprite",     0x1a090d, 844,   108,  0, TREASURE_YARN_TILE_OFFSET),
    ("sprite_raw", 0x025000, 2048,  104,  0, TREASURE_FLAT_TILE_OFFSET),
    ("sprite_raw", 0x027000, 2048,   97, 33, TREASURE_PUFFY_TILE_OFFSET),
)

# Form icons built by horizontally mirroring a half-sprite into a full icon.
# Each entry: (kind, offset, length, crop_x, crop_y, half_w, half_h, dest_offset)
# Pipeline: decode source, crop a half_w x half_h region at (crop_x, crop_y),
# stitch it next to its horizontal flip to form a (2*half_w) x half_h full
# image, center-pad that onto a 16x16 white canvas, encode as 4 tiles.
FORM_ICON_MIRRORED_EXTRACTIONS = (
    # Ice Skatin' Form — half-snowflake from brrr_bear (game mirrors it at runtime too).
    ("sprite", 0x1ad4ea, 887, 122, 2, 6, 12, TREASURE_ICE_SKATIN_TILE_OFFSET),
    # Fire Form — half-flame from fire_bot, mirrored to form a full flame shape.
    ("sprite", 0x1ac234, 988,  97, 0, 7, 15, TREASURE_FIRE_TILE_OFFSET),
)
TREASURE_DUMMY_PAL_OFFSET        = 0x09AD1F   # TreasureOBPals[$65] — 1 byte (palette index)
TREASURE_GFX_BASE                = 0x098000   # TreasureGfx[0] — each entry 64 bytes
TREASURE_PAL_BASE                = 0x09AFBA   # TreasureOBPals[0] — each entry 1 byte
KEY_COLOR_PALS = [0x08, 0x05, 0x06, 0x07]    # OBPAL: grey, red, green, blue
OBPAL_TREASURE_PURPLE = 0x09                  # Combined unlock items

def _wl3_rle_decompress(src: bytes) -> bytes:
    """WL3 run-length encoding. Command byte: high bit set = copy N literal
    bytes; clear = repeat next byte N times. Terminates on end of input."""
    out = bytearray()
    pos = 0
    while pos < len(src):
        cmd = src[pos]
        pos += 1
        if pos >= len(src):
            break
        length = cmd & 0x7F
        if cmd & 0x80:
            out.extend(src[pos:pos + length])
            pos += length
        else:
            out.extend([src[pos]] * length)
            pos += 1
    return bytes(out)


def _decode_2bpp_tile(tile16: bytes):
    """Decode a 16-byte 2bpp tile into an 8x8 grid of palette indices (0-3)."""
    grid = [[0] * 8 for _ in range(8)]
    for y in range(8):
        lo, hi = tile16[y * 2], tile16[y * 2 + 1]
        for x in range(8):
            bit = 7 - x
            grid[y][x] = ((lo >> bit) & 1) | (((hi >> bit) & 1) << 1)
    return grid


def _decode_sprite_sheet(sheet_2bpp: bytes, width_tiles: int = 16):
    """Decode an rgbgfx --interleave sheet (8x16 sprite-pair tile order).
    Sprite (col, row) occupies tiles 2*(col+width*row) (top, y=0..7) and
    2*(col+width*row)+1 (bottom, y=8..15). Height is inferred from sheet size.
    Returns a pixel grid of shape (sprite_rows*16) x (width_tiles*8)."""
    num_tiles = len(sheet_2bpp) // 16
    sprite_rows = num_tiles // (width_tiles * 2)
    pixels = [[0] * (width_tiles * 8) for _ in range(sprite_rows * 16)]
    for row in range(sprite_rows):
        for col in range(width_tiles):
            base = 2 * (col + width_tiles * row)
            top = _decode_2bpp_tile(sheet_2bpp[base * 16:(base + 1) * 16])
            bot = _decode_2bpp_tile(sheet_2bpp[(base + 1) * 16:(base + 2) * 16])
            for yy in range(8):
                for xx in range(8):
                    pixels[row * 16 + yy][col * 8 + xx] = top[yy][xx]
                    pixels[row * 16 + 8 + yy][col * 8 + xx] = bot[yy][xx]
    return pixels


def _decode_tilemap(sheet_2bpp: bytes, width_tiles: int):
    """Decode a plain row-major 8x8 tile sheet (no --interleave). Returns a
    pixel grid sized (height * 8) x (width_tiles * 8), where height is derived
    from sheet size."""
    num_tiles = len(sheet_2bpp) // 16
    height_tiles = num_tiles // width_tiles
    pixels = [[0] * (width_tiles * 8) for _ in range(height_tiles * 8)]
    for ti in range(num_tiles):
        row, col = divmod(ti, width_tiles)
        tile = _decode_2bpp_tile(sheet_2bpp[ti * 16:(ti + 1) * 16])
        for yy in range(8):
            for xx in range(8):
                pixels[row * 8 + yy][col * 8 + xx] = tile[yy][xx]
    return pixels


def _encode_icon_from_pixels(pixels, crop_x: int, crop_y: int) -> bytes:
    """Crop a 16x16 region from a pixel grid and encode as 4 tiles of 2bpp
    in rgbgfx --interleave order (TL, BL, TR, BR). Returns 64 bytes."""
    def encode_tile(ty: int, tx: int) -> bytes:
        out = bytearray()
        for y in range(8):
            lo = hi = 0
            for x in range(8):
                v = pixels[crop_y + ty * 8 + y][crop_x + tx * 8 + x]
                bit = 7 - x
                lo |= (v & 1) << bit
                hi |= ((v >> 1) & 1) << bit
            out += bytes([lo, hi])
        return bytes(out)

    return encode_tile(0, 0) + encode_tile(1, 0) + encode_tile(0, 1) + encode_tile(1, 1)


def _build_mirrored_icon(pixels, crop_x: int, crop_y: int, half_w: int, half_h: int) -> bytes:
    """Build a 16x16 icon by horizontally mirroring a half-sprite:
      1. Take a half_w x half_h crop at (crop_x, crop_y) from the source grid.
      2. Produce its horizontal flip.
      3. Stitch the two halves into a (2*half_w) x half_h full image.
      4. Center-pad that onto a 16x16 canvas (palette index 0 = white).
      5. Encode as 4 tiles.
    Pal 0 is used for padding because our treasure icons treat it as the
    background/transparent color."""
    full_w = 2 * half_w
    assert full_w <= 16 and half_h <= 16, "mirrored icon must fit in 16x16"
    canvas = [[0] * 16 for _ in range(16)]
    offset_x = (16 - full_w) // 2
    offset_y = (16 - half_h) // 2
    for y in range(half_h):
        row = pixels[crop_y + y]
        for x in range(half_w):
            v = row[crop_x + x]
            canvas[offset_y + y][offset_x + x] = v
            canvas[offset_y + y][offset_x + full_w - 1 - x] = v
    return _encode_icon_from_pixels(canvas, 0, 0)


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
MUSIC_BOXES_REQUIRED_OFFSET      = 0x080F13   # MusicBoxesRequired byte in Bank 20
START_WITH_AXE_OFFSET            = 0x080F14   # StartWithAxeOpt byte in Bank 20
START_WITH_MAG_GLASS_OFFSET      = 0x080F15   # StartWithMagnifyingGlassOpt byte in Bank 20
GOLF_PRICE_OPT_OFFSET            = 0x003A00   # GolfPriceOpt byte in Home bank
GOLF_BUILDING_OPT_OFFSET         = 0x003A01   # GolfBuildingOpt byte in Home bank
DISABLE_PAL_CYCLE_OFFSET         = 0x003A02   # DisablePalCycleOpt byte in Home bank
I_HATE_GOLF_OFFSET               = 0x003A03   # AutoWinGolfOpt byte in Home bank
NON_STOP_CHESTS_OFFSET           = 0x003A04   # NonStopChestsOpt byte in Home bank
COMBINED_COMPANION_TABLE_OFFSET  = 0x003A05   # CombinedCompanionTable (101 bytes, home bank)
TRANSFORMS_REQUIRE_ITEMS_OFFSET  = 0x003A6A   # TransformsRequireItems byte in Home bank
TREASURE_OB_PALS_OFFSET          = 0x09AFBA   # TreasureOBPals table (indexed by treasure ID)

# Combined-item companion chains: collecting key → also grant value (chained).
# Tusk Set: $24→$25→$26 (two hops).
_COMPANION_PAIRS_OVERWORLD = {
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

# In-level combined pairs.
_COMPANION_PAIRS_IN_LEVEL = {
    0x49: 0x47,  # Pouch → Eye of the Storm
    0x27: 0x28,  # Blue Chemical → Red Chemical
    0x43: 0x42,  # Left Glass Eye → Right Glass Eye
    0x41: 0x40,  # Golden Left Eye → Golden Right Eye
    0x45: 0x46,  # Sun Medallion Top → Sun Medallion Bottom
    0x33: 0x34,  # Key Card Red → Key Card Blue
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

def _recolor_palette(data: bytes, rand, fixed_hue_rotate: float = None) -> bytes:
    """Recolor an 8-byte GBC palette.

    Near-grayscale colors (s < 0.25) each get an independent random hue at
    high saturation.  Saturated colors (s >= 0.25) are all hue-rotated by a
    single shared random offset so their relative color relationships are
    preserved.  Very dark colors (v < 0.15) are left unchanged.

    If `fixed_hue_rotate` is provided, it is used as the shared rotation
    instead of a fresh random value — this lets multiple palettes in a
    palette-cycle group share a hue so cycle frames stay coherent.
    """
    GRAY_THRESHOLD = 0.25
    grouped = fixed_hue_rotate is not None
    hue_rotate = fixed_hue_rotate if grouped else rand()
    out = bytearray(len(data))
    for i in range(len(data) // 2):
        color = data[i * 2] | (data[i * 2 + 1] << 8)
        r, g, b = _gbc_to_floats(color)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        if v < 0.15:
            pass  # dark/outline colors — leave unchanged
        elif s < GRAY_THRESHOLD:
            # near-white / light-gray: assign a hue at moderate saturation.
            # For grouped (palette-cycle) entries we derive the hue from the
            # group rotation + color slot so every cycle frame's grayscale
            # pixels share the same tint (no strobing on Above the Clouds day).
            if grouped:
                h = (hue_rotate + i * 0.13) % 1.0
            else:
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


def _recolor_palette_bg_simple(data: bytes, rand) -> bytes:
    """Apply a small, conservative hue shift to an 8-byte GBC palette.

    Very dark colors (v < 0.12) and near-gray colors (s < 0.25) are left
    unchanged to preserve outlines and subtle background tints. Saturated
    colors are hue-rotated by a small shared offset to keep scenes coherent.
    """
    # Make the simple mode extremely mild: very small hue adjustments.
    HUE_RANGE = 0.01  # maximum rotation in either direction (fraction of 1.0)
    hue_rotate = (rand() - 0.5) * (HUE_RANGE * 2)
    out = bytearray(len(data))
    # Use slightly stricter thresholds so fewer colors are modified.
    for i in range(len(data) // 2):
        color = data[i * 2] | (data[i * 2 + 1] << 8)
        r, g, b = _gbc_to_floats(color)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        if v < 0.18:
            # keep very dark (outlines)
            pass
        elif s < 0.35:
            # keep near-gray/background tints for consistency
            pass
        else:
            # apply only a very small hue rotation
            h = (h + hue_rotate) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        new = _floats_to_gbc(r, g, b)
        out[i * 2]     = new & 0xFF
        out[i * 2 + 1] = (new >> 8) & 0xFF
    return bytes(out)


def _shift_one_palette_color(chunk: bytes, rand) -> bytes:
    """Shift a single, non-dark, non-gray color within an 8-byte palette by a very small hue."""
    out = bytearray(chunk)
    # find a candidate color to shift: first color with v>=0.15 and s>=0.15
    target = None
    vals = []
    for i in range(4):
        color = chunk[i*2] | (chunk[i*2+1] << 8)
        r, g, b = _gbc_to_floats(color)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        vals.append((h, s, v, color))
        if target is None and v >= 0.15 and s >= 0.15:
            target = i
    if target is None:
        # fallback to second color (index 1) if no suitable candidate
        target = 1 if len(vals) > 1 else 0

    h, s, v, orig = vals[target]
    # very small hue shift
    HUE_RANGE = 0.005
    hue_rotate = (rand() - 0.5) * (HUE_RANGE * 2)
    h = (h + hue_rotate) % 1.0
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    new = _floats_to_gbc(r, g, b)
    out[target * 2] = new & 0xFF
    out[target * 2 + 1] = (new >> 8) & 0xFF
    return bytes(out)


def write_tokens(world: "WL3World", patch: WL3ProcedurePatch) -> None:
    """Write the randomized chest table, key pool, and options into the patch."""
    # Lazy loader for the user's vanilla ROM (shared across all features that
    # read original game bytes). Keeps vanilla data out of the apworld zip.
    _vanilla_rom_cache = [None]
    def _read_vanilla(offset: int, length: int) -> bytes:
        if _vanilla_rom_cache[0] is None:
            from settings import get_settings
            opts = get_settings().wl3_options
            rom_path = opts["rom_file"] if isinstance(opts, dict) else opts.rom_file
            with open(rom_path, "rb") as f:
                _vanilla_rom_cache[0] = f.read()
        return _vanilla_rom_cache[0][offset:offset + length]

    # Extract Form treasure icons from the user's vanilla ROM. Each icon is a
    # 16x16 pixel-crop, re-encoded as 4 tiles of 2bpp. No vanilla GFX ships in
    # the apworld — source bytes come from the user's own ROM.
    def _read_pixels(kind: str, src_offset: int, src_length: int):
        raw = _read_vanilla(src_offset, src_length)
        if kind == "sprite":
            return _decode_sprite_sheet(_wl3_rle_decompress(raw), width_tiles=16)
        elif kind == "sprite_raw":
            return _decode_sprite_sheet(raw, width_tiles=16)
        else:  # "tilemap"
            return _decode_tilemap(raw, width_tiles=16)

    for kind, src_offset, src_length, crop_x, crop_y, dest_offset in FORM_ICON_EXTRACTIONS:
        pixels = _read_pixels(kind, src_offset, src_length)
        patch.write_token(APTokenTypes.WRITE, dest_offset,
                          _encode_icon_from_pixels(pixels, crop_x, crop_y))

    for kind, src_offset, src_length, crop_x, crop_y, half_w, half_h, dest_offset in FORM_ICON_MIRRORED_EXTRACTIONS:
        pixels = _read_pixels(kind, src_offset, src_length)
        patch.write_token(APTokenTypes.WRITE, dest_offset,
                          _build_mirrored_icon(pixels, crop_x, crop_y, half_w, half_h))

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
    from .items import COMBINED_ITEMS, KEY_ITEM_TABLE, KEYRING_ITEM_TABLE
    from .locations import LOCATION_TABLE
    OBPAL_TREASURE_YELLOW = 4
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
        # Keyrings → force yellow (default TreasureOBPals already points here,
        # but explicit override ensures non-stop chest pop-up renders correctly).
        elif item.name in KEYRING_ITEM_TABLE:
            pal_overrides[idx] = OBPAL_TREASURE_YELLOW
    patch.write_token(APTokenTypes.WRITE, CHEST_KEY_PAL_OFFSET, bytes(pal_overrides))

    # Per-key palette overrides: in full keysanity, combined items at key
    # slots render with the purple palette (same as chest treatment). Index
    # into KeyPaletteOverrides = (owlevel-1)*4 + color_index (matches
    # LevelKeyPool layout). Values: 0xFF = default (use item's own palette),
    # else an OBPAL_TREASURE_* constant.
    from .locations import KEY_LOCATION_TABLE
    key_pal_overrides = bytearray([0xFF] * 100)
    if world.options.key_shuffle == KeyShuffle.option_full:
        for loc_name, loc_data in KEY_LOCATION_TABLE.items():
            location = world.multiworld.get_location(loc_name, world.player)
            item = location.item
            if item is None or item.player != world.player:
                continue
            if item.name in COMBINED_ITEMS:
                idx = (loc_data.owlevel - 1) * 4 + loc_data.color_index
                key_pal_overrides[idx] = OBPAL_TREASURE_PURPLE
    patch.write_token(APTokenTypes.WRITE, KEY_PAL_OVERRIDE_OFFSET, bytes(key_pal_overrides))

    # --- chest + key slot keyring targets ---
    # When a slot holds a keyring (treasure ID $66), the ROM needs to know
    # which level's 4 keys to grant. Two parallel 100-byte tables: one indexed
    # by chest slot, one by key slot (both (owlevel-1)*4 + color). Lets the
    # ROM grant keyring items locally without the AP client, in either
    # location type.
    chest_keyring_targets = bytearray([0xFF] * 100)
    for loc_name, loc_data in LOCATION_TABLE.items():
        location = world.multiworld.get_location(loc_name, world.player)
        item = location.item
        if item is None or item.player != world.player:
            continue
        if item.name in KEYRING_ITEM_TABLE:
            chest_keyring_targets[loc_data.loc_index] = KEYRING_ITEM_TABLE[item.name].owlevel
    patch.write_token(APTokenTypes.WRITE, CHEST_KEYRING_OFFSET, bytes(chest_keyring_targets))

    key_keyring_targets = bytearray([0xFF] * 100)
    if world.options.key_shuffle == KeyShuffle.option_full:
        for loc_name, loc_data in KEY_LOCATION_TABLE.items():
            location = world.multiworld.get_location(loc_name, world.player)
            item = location.item
            if item is None or item.player != world.player:
                continue
            if item.name in KEYRING_ITEM_TABLE:
                idx = (loc_data.owlevel - 1) * 4 + loc_data.color_index
                key_keyring_targets[idx] = KEYRING_ITEM_TABLE[item.name].owlevel
    patch.write_token(APTokenTypes.WRITE, KEY_KEYRING_OFFSET, bytes(key_keyring_targets))

    # --- initial inventory bits ---
    # Precollected items (start_with_axe, random_level_starts, etc.) are usually
    # delivered by the AP client on connect. Bake them into ROM tables too so a
    # seed plays standalone without the client ever running — also lets a fresh
    # save boot on real hardware / flashcart. The ROM new-game init OR's these
    # into wTreasuresCollected / wKeyInventory.
    from .items import (
        COMBINED_COMPONENTS as _CC,
        KEY_ITEM_TABLE as _KIT,
        KEYRING_ITEM_TABLE as _KRT,
        PROGRESSIVE_ITEMS as _PI,
        ITEM_TABLE as _IT,
    )
    initial_treasures = bytearray((0x65 // 8) + 1)  # 13 bytes, matches wTreasuresCollected
    initial_keys = bytearray(25)                    # matches wKeyInventory
    for pre_item in world.multiworld.precollected_items[world.player]:
        name = pre_item.name
        if name in _KRT:
            owlevel = _KRT[name].owlevel
            initial_keys[owlevel - 1] |= 0x0F   # grant all 4 keys for that level
        elif name in _KIT:
            kd = _KIT[name]
            initial_keys[kd.owlevel - 1] |= 1 << kd.color_index
        elif name in _CC:
            for tid in _CC[name]:
                if 0 <= tid < 0x65:
                    initial_treasures[tid >> 3] |= 1 << (tid & 7)
        elif name in _PI:
            # Progressive start: grant tier 1 (matches AP "one precollected = first tier").
            tid = _PI[name].tier_ids[0]
            initial_treasures[tid >> 3] |= 1 << (tid & 7)
        elif name in _IT:
            tid = _IT[name].tier_ids[0]
            if 0 <= tid < 0x65:
                initial_treasures[tid >> 3] |= 1 << (tid & 7)
    patch.write_token(APTokenTypes.WRITE, INITIAL_TREASURES_OFFSET, bytes(initial_treasures))
    patch.write_token(APTokenTypes.WRITE, INITIAL_KEYS_OFFSET, bytes(initial_keys))

    patch.write_token(APTokenTypes.WRITE, CHEST_TABLE_OFFSET, bytes(chest_assignments))

    # Trap dispatch table (offline). Chest table holds Red Gem ($4E) for trap
    # slots so the popup graphic stays consistent; this parallel table tells
    # the ROM "this slot is actually trap N (1-5)" so SetTreasureTransitionParam
    # can queue the trap into wPendingTrap and skip the gem grant.
    trap_chest_table = list(world._build_trap_chest_table())
    patch.write_token(APTokenTypes.WRITE, TRAP_CHEST_TABLE_OFFSET, bytes(trap_chest_table))

    # Same dispatch for traps placed at key locations (Full keysanity).
    # SaveKeyToInventory reads TrapKeyTable; LevelKeyPool keeps a gem
    # placeholder so the visual pickup still works.
    trap_key_table = list(world._build_trap_key_table())
    patch.write_token(APTokenTypes.WRITE, TRAP_KEY_TABLE_OFFSET, bytes(trap_key_table))

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

    i_hate_golf = int(world.options.i_hate_golf)
    patch.write_token(APTokenTypes.WRITE, I_HATE_GOLF_OFFSET,
                      bytes([i_hate_golf]))

    non_stop_chests = int(world.options.non_stop_chests)
    patch.write_token(APTokenTypes.WRITE, NON_STOP_CHESTS_OFFSET,
                      bytes([non_stop_chests]))

    transformation_shuffle = int(world.options.transformation_shuffle)
    patch.write_token(APTokenTypes.WRITE, TRANSFORMS_REQUIRE_ITEMS_OFFSET,
                      bytes([transformation_shuffle]))

    # --- combined item companion table ---
    from .options import CombinedItems as _CI
    ci_mode = int(world.options.combined_items)
    combine_overworld = ci_mode in (_CI.option_overworld, _CI.option_both)
    combine_in_level  = ci_mode in (_CI.option_in_level,  _CI.option_both)

    if combine_overworld or combine_in_level:
        companion_table = bytearray(101)
        if combine_overworld:
            for trigger, companion in _COMPANION_PAIRS_OVERWORLD.items():
                companion_table[trigger] = companion
        if combine_in_level:
            for trigger, companion in _COMPANION_PAIRS_IN_LEVEL.items():
                companion_table[trigger] = companion
        patch.write_token(APTokenTypes.WRITE, COMBINED_COMPANION_TABLE_OFFSET,
                          bytes(companion_table))

    # --- combined item palette overrides ---
    if combine_overworld:
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

    # --- disable palette cycling when any palette shuffle or reduce flashing is active ---
    if (world.options.reduce_flashing or
            world.options.enemy_palette_shuffle or
            world.options.level_bg_palette_shuffle or
            world.options.wario_overalls_shuffle or
            world.options.wario_shirt_shuffle):
        patch.write_token(APTokenTypes.WRITE, DISABLE_PAL_CYCLE_OFFSET, bytes([1]))

    # --- palette shuffle ---
    # Vanilla palette bytes are NOT stored in the apworld. Offsets are inlined
    # in palette_offsets.py; actual bytes are read from the user's own vanilla
    # ROM here at generation time (via _read_vanilla defined at top of this fn).
    from .palette_offsets import ENEMY_PALETTES, LEVEL_BG_PALETTES

    if world.options.enemy_palette_shuffle:
        for offset, length, _group in ENEMY_PALETTES:
            data = _read_vanilla(offset, length)
            result = bytearray()
            for i in range(len(data) // 8):
                chunk = data[i * 8 : (i + 1) * 8]
                result.extend(_recolor_palette(chunk, world.random.random))
            patch.write_token(APTokenTypes.WRITE, offset, bytes(result))

    # --- level / room BG palette shuffle (simple or full) ---
    level_bg_mode = int(world.options.level_bg_palette_shuffle)
    if level_bg_mode != 0:
        # Per-cycle-group shared hue rotation: palettes that belong to the
        # same room palette cycle (e.g. Above the Clouds lightning flash) all
        # get the same hue offset so cycle frames don't strobe random colors.
        group_hue_cache: dict = {}

        # Normal per-block processing (simple or full recolors applied per-palette)
        for offset, length, group in LEVEL_BG_PALETTES:
            data = _read_vanilla(offset, length)
            result = bytearray()
            count = len(data) // 8
            if level_bg_mode == 1:
                num = min(count, 2)
                chosen = set(world.random.sample(range(count), num))
            else:
                chosen = None

            if group is not None:
                if group not in group_hue_cache:
                    group_hue_cache[group] = world.random.random()
                group_hue = group_hue_cache[group]
            else:
                group_hue = None

            for i in range(count):
                chunk = data[i * 8 : (i + 1) * 8]
                if level_bg_mode == 2:
                    result.extend(_recolor_palette(chunk, world.random.random, fixed_hue_rotate=group_hue))
                elif level_bg_mode == 1 and (i in chosen):
                    # instead of recoloring entire palette, shift one color slightly
                    result.extend(_shift_one_palette_color(chunk, world.random.random))
                else:
                    result.extend(chunk)
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
