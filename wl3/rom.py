"""
WL3 patch class — builds the .apwl3 patch file using AP's APProcedurePatch system.

Procedure (runs at patch-application time, not generation):
  1. capture_vanilla        — snapshot vanilla ROM on self for steps 4-5
  2. apply_bsdiff4          — vanilla → hacked base
  3. apply_tokens           — write seeded tables (chest, key, options, wario palettes, …)
  4. apply_form_icons       — extract Form icons from snapshot, encode, write
  5. apply_palette_shuffle  — recolor enemy/level-bg palettes from snapshot using
                              per-palette seeds bundled in palette_params.json

Form icon extraction and palette shuffle are deferred so generation never reads
the user's vanilla ROM. Hosts can produce multiworld zips for upload without
owning the ROM; the player applying the .apwl3 supplies their own.
"""
import colorsys
import os
import zipfile
from typing import TYPE_CHECKING

from settings import get_settings
from worlds.Files import APProcedurePatch, APPatchExtension, APTokenMixin, APTokenTypes

if TYPE_CHECKING:
    from . import WL3World

CHEST_TABLE_OFFSET = 0x001B16   # LevelTreasureIDs_WithoutTemple (100 bytes)
KEYSANITY_MODE_OFFSET = 0x001B7A   # KeysanityMode (1 byte: 0=vanilla, 1=simple, 2=full)
KEY_TABLE_OFFSET = 0x001B7B   # LevelKeyPool (100 bytes; ITEM_KEY_BASE + index = vanilla)
CHEST_KEY_PAL_OFFSET = 0x001BDF   # ChestKeyPalettes (100 bytes; $FF=not key, 4-7=palette)
LEVEL_ENTRANCE_MAP_OFFSET = 0x001C43   # LevelEntranceMap (26 bytes; entries 0-24 are regular positions, entry 25 is the Temple slot; identity default)
KEY_PAL_OVERRIDE_OFFSET = 0x001C5D   # KeyPaletteOverrides (100 bytes; $FF=default, else OBPAL) — shifted +26 by LevelEntranceMap
CHEST_KEYRING_OFFSET = 0x001CC1   # ChestKeyringTargets (100 bytes; $FF=not keyring, 1-25=target owlevel) — shifted +26
KEY_KEYRING_OFFSET = 0x001D25   # KeyKeyringTargets   (100 bytes; same format, but for key slots) — shifted +26
INITIAL_TREASURES_OFFSET = 0x001D89   # InitialTreasuresBits (13 bytes; OR'd into wTreasuresCollected at new-game init) — shifted +26
INITIAL_KEYS_OFFSET = 0x001D96   # InitialKeysBits      (25 bytes; OR'd into wKeyInventory      at new-game init) — shifted +26
INITIAL_TRANSFORM_UNLOCKS_OFFSET = 0x001DAF   # InitialTransformUnlocks  (1 byte; OR'd into wTransformUnlocks  at new-game init) — shifted +26
INITIAL_TRANSFORM_UNLOCKS2_OFFSET = 0x001DB0   # InitialTransformUnlocks2 (1 byte; OR'd into wTransformUnlocks2 at new-game init) — shifted +26
TRAP_CHEST_TABLE_OFFSET = 0x001DB1   # TrapChestTable (100 bytes; 0=no trap, 1-5=TRAP_* — offline trap dispatch from chests) — shifted +26
TRAP_KEY_TABLE_OFFSET = 0x001E15   # TrapKeyTable   (100 bytes; same encoding — offline trap dispatch from key slots) — shifted +26
LEVEL_COIN_ITEMS_OFFSET          = 0x05836C   # LevelCoinItems       (200 bytes; bank $16 — display treasure ID per coin slot, $FF=plain)
COIN_PAL_OVERRIDE_OFFSET         = 0x058434   # CoinPaletteOverrides (200 bytes; bank $16 — OBPAL per coin, $FF=default)
TRAP_COIN_TABLE_OFFSET           = 0x0584FC   # TrapCoinTable        (200 bytes; bank $16 — 0=no trap, 1-5=TRAP_* — offline trap dispatch from coins)
COIN_KEYRING_TARGETS_OFFSET      = 0x0585C4   # CoinKeyringTargets   (200 bytes; bank $16 — $FF=not keyring, 1-25=target owlevel)
LEVEL_BOSS_ITEMS_OFFSET          = 0x05868C   # LevelBossItems       (10 bytes;  bank $16 — same encoding as LevelCoinItems)
TRAP_BOSS_TABLE_OFFSET           = 0x058696   # TrapBossTable        (10 bytes;  bank $16 — 0=no trap, 1-5=TRAP_*)
BOSS_KEYRING_TARGETS_OFFSET      = 0x0586A0   # BossKeyringTargets   (10 bytes;  bank $16 — $FF=not keyring, 1-25=target owlevel)
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
TREASURE_ROLL_TILE_OFFSET        = 0x099c80   # TreasureRollFormGfx      — 64 bytes (4 tiles, 2bpp)

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

# Form icons built by cropping a full 16x16 region and horizontally flipping
# it. Same shape as FORM_ICON_EXTRACTIONS but the encoder mirrors the pixels
# left-to-right before encoding as tiles.
FORM_ICON_FLIPPED_EXTRACTIONS = (
    # Roll Form — Wario face-rolling frame from the slide sheet, mirrored so
    # motion trail is on the right (matches rolling right visually).
    ("sprite_raw", 0x025000, 2048, 112, 32, TREASURE_ROLL_TILE_OFFSET),
)
TREASURE_DUMMY_PAL_OFFSET        = 0x09B462   # TreasureOBPals[$65] — 1 byte (palette index)
TREASURE_GFX_BASE                = 0x098000   # TreasureGfx[0] — each entry 64 bytes
TREASURE_PAL_BASE                = 0x09B3FD   # TreasureOBPals[0] — each entry 1 byte
KEY_COLOR_PALS = [0x08, 0x05, 0x06, 0x07]    # OBPAL: grey, red, green, blue
OBPAL_TREASURE_PURPLE = 0x09                  # Combined unlock items

# Coin-bundle items (repurposed crest treasure IDs $51-$54). Each gets its
# own OBPAL_TREASURE_* so wherever the coin bundle lands (chest / key /
# coin slot) the ROM's palette override system renders the sprite in the
# denomination's intended color instead of whatever the slot's default
# palette holds (usually the slot color = grey/red/green/blue).
COIN_BUNDLE_PALS = {
    "1 Coin":    0x04,   # OBPAL_TREASURE_YELLOW
    "10 Coins":  0x05,   # OBPAL_TREASURE_RED
    "25 Coins":  0x06,   # OBPAL_TREASURE_GREEN
    "50 Coins":  0x08,   # OBPAL_TREASURE_GREY (silver)
}

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


def _encode_icon_from_pixels(pixels, crop_x: int, crop_y: int,
                             flip_h: bool = False) -> bytes:
    """Crop a 16x16 region from a pixel grid and encode as 4 tiles of 2bpp
    in rgbgfx --interleave order (TL, BL, TR, BR). Returns 64 bytes.
    When flip_h is True, the 16x16 region is horizontally mirrored before
    encoding (so an icon designed as "facing right" becomes "facing left")."""
    def px(y: int, x: int) -> int:
        if flip_h:
            return pixels[crop_y + y][crop_x + 15 - x]
        return pixels[crop_y + y][crop_x + x]
    def encode_tile(ty: int, tx: int) -> bytes:
        out = bytearray()
        for y in range(8):
            lo = hi = 0
            for x in range(8):
                v = px(ty * 8 + y, tx * 8 + x)
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
MUSIC_BOXES_REQUIRED_OFFSET      = 0x080F81   # MusicBoxesRequired byte in Bank 20
START_WITH_AXE_OFFSET            = 0x080F82   # StartWithAxeOpt byte in Bank 20
START_WITH_MAG_GLASS_OFFSET      = 0x080F83   # StartWithMagnifyingGlassOpt byte in Bank 20
ENTRANCE_SHUFFLE_OPT_OFFSET      = 0x080F84   # EntranceShuffleOpt byte in Bank 20 (0 = off, non-zero = on; gates the "?????" reveal system)
SHOP_PRICES_OFFSET               = 0x080F85   # ShopPrices table in Bank 20 (10 slots × 2 bytes BCD = 20 bytes)
SHOPSANITY_MODE_OFFSET           = 0x080F99   # ShopsanityModeOpt byte in Bank 20 (0 = off → shop tile hidden; 1 = on)
SHOP_SLOT_ITEMS_OFFSET           = 0x080F9A   # ShopSlotItems table in Bank 20 (10 bytes = treasure ID per shop slot)
SHOP_SLOT_NAMES_OFFSET           = 0x080FA4   # ShopSlotNamesTable in Bank 20 (10 slots × 20 bytes = 200 bytes, msg-font encoded)
HIDDEN_PASSAGES_REVEALED_OFFSET = 0x00FF80  # HiddenPassagesRevealedOpt byte in Bank 3
GOLF_PRICE_OPT_OFFSET            = 0x003A00   # GolfPriceOpt byte in Home bank
GOLF_BUILDING_OPT_OFFSET         = 0x003A01   # GolfBuildingOpt byte in Home bank
DISABLE_PAL_CYCLE_OFFSET         = 0x003A02   # DisablePalCycleOpt byte in Home bank
I_HATE_GOLF_OFFSET               = 0x003A03   # AutoWinGolfOpt byte in Home bank
NON_STOP_CHESTS_OFFSET           = 0x003A04   # NonStopChestsOpt byte in Home bank
COMBINED_COMPANION_TABLE_OFFSET  = 0x003A05   # CombinedCompanionTable (101 bytes, home bank)
TRANSFORMS_REQUIRE_ITEMS_OFFSET  = 0x003A6A   # TransformsRequireItems byte in Home bank
DEATH_MODE_OPT_OFFSET            = 0x003A6B   # DeathModeOpt byte in Home bank (0=none, 1=grabs, 2=grabs+golf)
BIG_COINSANITY_OPT_OFFSET        = 0x003A6C   # BigCoinsanityOpt byte in Home bank (0=vanilla coins, 1=portrait/suppress/AP-dispatch)
GOLF_PAR_HINT_FREQ_OFFSET        = 0x003A6E   # GolfParHintFrequencyOpt byte in Home bank (0=per_hole, 1=per_course)
# Rudy hit count: `ld a, $XX` immediate byte at HiddenFigureFunc+20.
# HiddenFigureFunc lives at bank 13 offset $4C80 (13:4c80), and the target
# immediate byte is 20 bytes into the function (right after the second `ld hl`).
# Vanilla source is `$04`; the AP option lets the player pick 1-10 without
# touching the ROM layout. Re-audit if hidden_figure.asm changes above line 15.
RUDY_HIT_POINTS_OFFSET           = 0x04CC94
TREASURE_OB_PALS_OFFSET          = 0x09B3FD   # TreasureOBPals table (indexed by treasure ID)

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

    # Procedure order matters:
    #   1. capture_vanilla        — snapshot unmodified rom on self for later steps
    #   2. apply_bsdiff4          — vanilla → hacked base
    #   3. apply_tokens           — write seeded tables (chest/key/options/wario palettes)
    #   4. apply_form_icons       — read vanilla pixels from snapshot, re-encode, write
    #   5. apply_palette_shuffle  — read vanilla palette bytes, recolor with stored seed
    # Steps 4-5 are deferred to patch time so generation never reads the user's
    # vanilla ROM. Hosts can produce multiworld zips for upload without owning
    # the ROM; only the player applying the .apwl3 needs it.
    procedure = [
        ("capture_vanilla",       []),
        ("apply_bsdiff4",         ["base_patch.bsdiff4"]),
        ("apply_tokens",          ["token_data.bin"]),
        ("apply_form_icons",      []),
        ("apply_palette_shuffle", ["palette_params.json"]),
        # enemizer runs last so it can reuse palette_params (same seeds
        # as apply_palette_shuffle) to keep enemizer slot palettes
        # color-consistent with the vanilla rooms. enemizer_params.json
        # is only included in the .apwl3 if the Enemizer option is on.
        ("apply_enemizer",        ["enemizer_params.json", "palette_params.json"]),
    ]

    @classmethod
    def get_source_data(cls) -> bytes:
        opts = get_settings().wl3_options
        # In the patching context WL3World may not be loaded yet,
        # so opts may be a plain dict rather than a WL3Settings Group.
        rom_path = opts["rom_file"] if isinstance(opts, dict) else opts.rom_file
        with open(rom_path, "rb") as f:
            return f.read()


# Custom procedure steps for our patch. Procedure dispatch goes through
# AutoPatchExtensionRegister.get_handler(game), which finds the APPatchExtension
# subclass with matching `game`. Methods receive (caller, rom, *args) — `caller`
# is the WL3ProcedurePatch instance, used for self.get_file() and stashing
# vanilla bytes between steps.
class WL3PatchExtension(APPatchExtension):
    game = "Wario Land 3"

    @staticmethod
    def capture_vanilla(caller, rom: bytes) -> bytes:
        # Snapshot for apply_form_icons / apply_palette_shuffle, which run after
        # bsdiff has modified rom and need original bytes.
        caller._wl3_vanilla = bytes(rom)
        return rom

    @staticmethod
    def apply_form_icons(caller, rom: bytes) -> bytes:
        rom = bytearray(rom)
        vanilla = caller._wl3_vanilla
        for kind, src_offset, src_length, crop_x, crop_y, dest_offset in FORM_ICON_EXTRACTIONS:
            raw = vanilla[src_offset:src_offset + src_length]
            if kind == "sprite":
                pixels = _decode_sprite_sheet(_wl3_rle_decompress(raw), width_tiles=16)
            elif kind == "sprite_raw":
                pixels = _decode_sprite_sheet(raw, width_tiles=16)
            else:
                pixels = _decode_tilemap(raw, width_tiles=16)
            encoded = _encode_icon_from_pixels(pixels, crop_x, crop_y)
            rom[dest_offset:dest_offset + len(encoded)] = encoded
        for kind, src_offset, src_length, crop_x, crop_y, half_w, half_h, dest_offset in FORM_ICON_MIRRORED_EXTRACTIONS:
            raw = vanilla[src_offset:src_offset + src_length]
            if kind == "sprite":
                pixels = _decode_sprite_sheet(_wl3_rle_decompress(raw), width_tiles=16)
            elif kind == "sprite_raw":
                pixels = _decode_sprite_sheet(raw, width_tiles=16)
            else:
                pixels = _decode_tilemap(raw, width_tiles=16)
            encoded = _build_mirrored_icon(pixels, crop_x, crop_y, half_w, half_h)
            rom[dest_offset:dest_offset + len(encoded)] = encoded
        for kind, src_offset, src_length, crop_x, crop_y, dest_offset in FORM_ICON_FLIPPED_EXTRACTIONS:
            raw = vanilla[src_offset:src_offset + src_length]
            if kind == "sprite":
                pixels = _decode_sprite_sheet(_wl3_rle_decompress(raw), width_tiles=16)
            elif kind == "sprite_raw":
                pixels = _decode_sprite_sheet(raw, width_tiles=16)
            else:
                pixels = _decode_tilemap(raw, width_tiles=16)
            encoded = _encode_icon_from_pixels(pixels, crop_x, crop_y, flip_h=True)
            rom[dest_offset:dest_offset + len(encoded)] = encoded
        return bytes(rom)

    @staticmethod
    def apply_enemizer(caller, rom: bytes, params_filename: str,
                       palette_params_filename: str) -> bytes:
        """Generate enemizer EnemizerGroups table + room patches using
        vanilla palette bytes read from the snapshot. Skipped silently
        when enemizer_params.json isn't shipped (option off)."""
        import json
        import random as _random
        raw = caller.get_file(params_filename)
        if not raw:
            return rom
        params = json.loads(raw.decode("utf-8"))
        if not params.get("enabled"):
            return rom   # Enemizer option off — skip silently
        rom = bytearray(rom)
        # CRITICAL: read palettes from the POST-BSDIFF rom (hacked layout),
        # NOT from caller._wl3_vanilla. enemizer_data.py stores HACKED-ROM
        # palette offsets — bsdiff has already relocated each vanilla
        # palette by ENEMIZER_SLOT_COUNT*4 bytes (the dispatch-table growth
        # in bank $19). Reading from the vanilla snapshot at those offsets
        # would pull non-palette bytes; rom[off] reads the correct relocated
        # palette bytes.
        # Build (offset → shuffled bytes) lookup if enemy_palette_shuffle
        # is also on. Mirrors apply_palette_shuffle's enemy loop using
        # the same per-entry seeds so colors match.
        palette_overrides: dict[int, bytes] = {}
        if params.get("use_palette_overrides"):
            pp_raw = caller.get_file(palette_params_filename)
            if pp_raw:
                pp = json.loads(pp_raw.decode("utf-8"))
                for entry in pp.get("enemy", []):
                    rng = _random.Random(entry["seed"])
                    base = entry["offset"]
                    for i in range(entry["length"] // 8):
                        sub = base + i * 8
                        src = bytes(rom[sub:sub + 8])  # hacked offset
                        palette_overrides[sub] = _recolor_palette(src, rng.random)

        def palette_lookup(off: int) -> bytes:
            ov = palette_overrides.get(off)
            # When override is absent, pull from the hacked-layout rom so
            # enemizer_data.py's hacked offsets resolve to the actual
            # vanilla palette bytes (relocated by bsdiff).
            return ov if ov is not None else bytes(rom[off:off + 8])

        from . import enemizer as _enemizer
        rng = _random.Random(params["seed"])
        mode = int(params.get("mode", 1))   # default 1=full for old params.json
        grouped = (mode == 2)
        for off, data in _enemizer.generate_patch_writes(
                rng, palette_lookup, grouped=grouped):
            rom[off:off + len(data)] = data

        # After all enemizer writes are applied, dump a per-level report
        # of what enemies ended up in which rooms — helps players preview
        # their seed and helps diagnose "why did that room look weird"
        # feedback. Writes to enemizer_room_map.txt in cwd (usually the
        # seed's output folder); errors go to a sibling .error.txt.
        try:
            WL3PatchExtension._write_enemizer_room_map(bytes(rom))
        except Exception:
            import os as _os, traceback as _tb
            try:
                with open(_os.path.abspath("enemizer_room_map.error.txt"),
                          "w", encoding="utf-8") as f:
                    f.write(_tb.format_exc())
            except Exception:
                pass
        return bytes(rom)

    @staticmethod
    def _write_enemizer_room_map(rom: bytes) -> None:
        """Decode each wgid's final dispatch entry and write a per-level
        report to enemizer_room_map.txt in the current working directory."""
        import os as _os
        from . import enemizer_data as _ed
        from .level_room_wgids import LEVEL_ROOM_WGIDS
        try:
            from .slot_gfx_names import SLOT_GFX_NAMES
        except Exception:
            SLOT_GFX_NAMES = {i: {} for i in range(4)}

        OG_TABLE = 0x65062  # ObjectGroups[] ROM offset
        # Enemizer composed-slot region (bank-19 relative and ROM absolute)
        ENEMIZER_SLOT_BASE_BANK19 = 0x6B58
        ENEMIZER_ROM_BASE = 0x66B58
        SLOT_SIZE = 64

        def _decode_dispatch(wgid: int) -> "list[str]":
            entry_off = OG_TABLE + wgid * 4
            og_ptr = rom[entry_off + 2] | (rom[entry_off + 3] << 8)
            # Enemizer custom slot?
            if ENEMIZER_SLOT_BASE_BANK19 <= og_ptr < (
                    ENEMIZER_SLOT_BASE_BANK19 + 82 * SLOT_SIZE):
                slot_offset = og_ptr - ENEMIZER_SLOT_BASE_BANK19
                rom_off = ENEMIZER_ROM_BASE + slot_offset
                names = []
                for i in range(4):
                    lo = rom[rom_off + 1 + i * 2]
                    hi = rom[rom_off + 2 + i * 2]
                    enc = lo | (hi << 8)
                    if enc & 0x8000:
                        # cross-slot encoded gfx ptr — source slot in bits 13-14
                        source_slot = (enc >> 13) & 3
                        real_addr = ((enc & 0x1FFF) | 0x4000)
                        name = SLOT_GFX_NAMES.get(source_slot, {}).get(
                            real_addr, f"?@0x{real_addr:04X}")
                        names.append(f"{name}*")
                    else:
                        name = SLOT_GFX_NAMES.get(i, {}).get(
                            enc, f"?@0x{enc:04X}")
                        names.append(name)
                return names
            # Fallback: vanilla ObjectGroup in bank 19
            rom_off = 0x64000 + (og_ptr - 0x4000)
            names = []
            for i in range(4):
                enc = rom[rom_off + 1 + i * 2] | (rom[rom_off + 2 + i * 2] << 8)
                name = SLOT_GFX_NAMES.get(i, {}).get(enc, f"?@0x{enc:04X}")
                names.append(name)
            return names

        lines = []
        lines.append("Enemizer room map — generated at patch time")
        lines.append("=" * 60)
        lines.append("")
        lines.append("Legend: each row shows a room's 4 VRAM slot enemies.")
        lines.append("        * = cross-slotted (enemy's native slot != VRAM slot)")
        lines.append("")
        for ow in sorted(LEVEL_ROOM_WGIDS):
            display, rows = LEVEL_ROOM_WGIDS[ow]
            lines.append(f"=== {ow:2d}. {display} ===")
            # Collect wRooms per wgid so we can inline them (multiple rooms
            # sharing a wgid all get the identical enemy composition).
            per_wgid: "dict[int, list[int]]" = {}
            wgid_order = []
            for _lbl, wr, wgid in rows:
                if wgid not in per_wgid:
                    per_wgid[wgid] = []
                    wgid_order.append(wgid)
                if wr not in per_wgid[wgid]:
                    per_wgid[wgid].append(wr)
            for wgid in wgid_order:
                slots = _decode_dispatch(wgid)
                slots_str = " / ".join(
                    f"[{i}]{s}" for i, s in enumerate(slots))
                wrooms = per_wgid[wgid]
                wrooms_str = ",".join(f"0x{w:02X}" for w in wrooms)
                lines.append(
                    f"  wgid 0x{wgid:02X}  wRoom={wrooms_str:20s}  "
                    f"{slots_str}")
            lines.append("")

        path = _os.path.abspath("enemizer_room_map.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    @staticmethod
    def apply_palette_shuffle(caller, rom: bytes, params_filename: str) -> bytes:
        import json
        import random as _random
        params_raw = caller.get_file(params_filename)
        if not params_raw:
            return rom
        params = json.loads(params_raw.decode("utf-8"))
        rom = bytearray(rom)
        vanilla = caller._wl3_vanilla

        # ENEMY palette entries in palette_offsets.py use HACKED-ROM offsets
        # (generated by gen_palette_table.py against warioland3.sym), so read
        # source bytes from the post-bsdiff `rom` and write recolored bytes
        # back to the same offset.
        for entry in params.get("enemy", []):
            rng = _random.Random(entry["seed"])
            offset = entry["offset"]
            length = entry["length"]
            data = bytes(rom[offset:offset + length])
            result = bytearray()
            for i in range(length // 8):
                chunk = data[i * 8:(i + 1) * 8]
                result.extend(_recolor_palette(chunk, rng.random))
            rom[offset:offset + len(result)] = bytes(result)

        # level_bg + overworld_bg share the exact same per-entry shape, so
        # process them in one loop. Each entry: offset, length, group_hue,
        # optional "source" ("vanilla" default; "rom" when the entry's
        # offsets are HACKED-ROM offsets, e.g. title palettes shifted by
        # the bank-1 growth and only present at their hacked location in
        # the post-bsdiff rom).
        for kind in ("level_bg", "overworld_bg"):
            for entry in params.get(kind, []):
                offset = entry["offset"]
                length = entry["length"]
                group_hue = entry["group_hue"]
                src = rom if entry.get("source") == "rom" else vanilla
                data = src[offset:offset + length]
                result = bytearray()
                for i in range(length // 8):
                    chunk = data[i * 8:(i + 1) * 8]
                    # rng arg is unused when fixed_hue_rotate is supplied
                    result.extend(_recolor_palette(chunk, None, fixed_hue_rotate=group_hue))
                rom[offset:offset + len(result)] = bytes(result)

        return bytes(rom)


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

    Every color (near-gray and saturated alike) rotates by the same hue
    offset — preserves both the within-palette relationships AND the
    "shadow / edge / highlight" tones' low-saturation neutrality, so
    edges between tiles don't get jagged hue jumps.  Very dark colors
    (v < 0.15) are left unchanged so outlines stay outlines.

    If `fixed_hue_rotate` is provided, it is used as the shared rotation
    instead of a fresh random value — this lets multiple palettes in a
    palette-cycle group share a hue so cycle frames stay coherent.
    """
    grouped = fixed_hue_rotate is not None
    # Hue wraps, so rand()s near 0 or 1 produce near-vanilla shifts. Clamp the
    # rolled value to [0.1, 0.9] so enemy_palette_shuffle always reads as a
    # real recolor.
    hue_rotate = fixed_hue_rotate if grouped else (0.1 + rand() * 0.8)
    out = bytearray(len(data))
    for i in range(len(data) // 2):
        color = data[i * 2] | (data[i * 2 + 1] << 8)
        r, g, b = _gbc_to_floats(color)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        if v >= 0.15:
            h = (h + hue_rotate) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        new = _floats_to_gbc(r, g, b)
        out[i * 2]     = new & 0xFF
        out[i * 2 + 1] = (new >> 8) & 0xFF
    return bytes(out)


def write_tokens(world: "WL3World", patch: WL3ProcedurePatch) -> None:
    """Write the randomized chest table, key pool, and options into the patch.

    Operations that need vanilla ROM bytes (Form icon extraction, palette
    shuffle) are NOT performed here — they're deferred to patch-application
    time via the apply_form_icons / apply_palette_shuffle procedure steps.
    This lets generation run without the user's vanilla ROM."""
    chest_assignments = list(world._build_chest_assignments())

    key_assignments = world._build_key_assignments()
    patch.write_token(APTokenTypes.WRITE, KEY_TABLE_OFFSET, bytes(key_assignments))

    # Coinsanity per-coin item + palette tables (200 bytes each, bank $16).
    # Same encoding as LevelKeyPool / KeyPaletteOverrides. Used by
    # LoadCoinTreasureTiles to load portrait tiles into VRAM at room entry.
    coin_items, coin_pals = world._build_coin_assignments()
    patch.write_token(APTokenTypes.WRITE, LEVEL_COIN_ITEMS_OFFSET,  bytes(coin_items))
    patch.write_token(APTokenTypes.WRITE, COIN_PAL_OVERRIDE_OFFSET, bytes(coin_pals))

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
        # Key items at chests → key color palette. The chest table now
        # stores AP-encoded key ids ($80+x); item.name lookup is the
        # source of truth for "is this a key".
        if item.name in KEY_ITEM_TABLE:
            color = KEY_ITEM_TABLE[item.name].color_index
            pal_overrides[idx] = KEY_COLOR_PALS[color]
        # Combined items → purple palette
        elif item.name in COMBINED_ITEMS:
            pal_overrides[idx] = OBPAL_TREASURE_PURPLE
        # Keyrings → force yellow (default TreasureOBPals already points here,
        # but explicit override ensures non-stop chest pop-up renders correctly).
        elif item.name in KEYRING_ITEM_TABLE:
            pal_overrides[idx] = OBPAL_TREASURE_YELLOW
        # Coin bundles → force the denomination's own palette so the sprite
        # renders in its intended color regardless of which slot it lands at.
        elif item.name in COIN_BUNDLE_PALS:
            pal_overrides[idx] = COIN_BUNDLE_PALS[item.name]
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
            elif item.name in COIN_BUNDLE_PALS:
                idx = (loc_data.owlevel - 1) * 4 + loc_data.color_index
                key_pal_overrides[idx] = COIN_BUNDLE_PALS[item.name]
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

    # Coin slot keyring targets (mirror of ChestKeyringTargets / KeyKeyringTargets
    # but for coin slots — 200 bytes, indexed by (owlevel-1)*8 + coin_idx).
    coin_keyring_targets = bytearray([0xFF] * 200)
    if world.options.bigcoinsanity:
        from .locations import COIN_LOCATION_TABLE as _CLT
        for loc_name, loc_data in _CLT.items():
            location = world.multiworld.get_location(loc_name, world.player)
            item = location.item
            if item is None or item.player != world.player:
                continue
            if item.name in KEYRING_ITEM_TABLE:
                coin_keyring_targets[loc_data.loc_index] = KEYRING_ITEM_TABLE[item.name].owlevel
    patch.write_token(APTokenTypes.WRITE, COIN_KEYRING_TARGETS_OFFSET, bytes(coin_keyring_targets))

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
        TRANSFORM_UNLOCK_ITEMS as _TUI,
        ITEM_TABLE as _IT,
    )
    initial_treasures = bytearray((0x65 // 8) + 1)  # 13 bytes, matches wTreasuresCollected
    initial_keys = bytearray(25)                    # matches wKeyInventory
    initial_form_unlocks  = 0                       # OR'd into wTransformUnlocks
    initial_form_unlocks2 = 0                       # OR'd into wTransformUnlocks2
    for pre_item in world.multiworld.precollected_items[world.player]:
        name = pre_item.name
        if name in _KRT:
            owlevel = _KRT[name].owlevel
            initial_keys[owlevel - 1] |= 0x0F   # grant all 4 keys for that level
        elif name in _KIT:
            kd = _KIT[name]
            initial_keys[kd.owlevel - 1] |= 1 << kd.color_index
        elif name in _TUI:
            # Form item: tier_ids = [byte_idx, bit_idx] (and possibly more
            # entries for progressive Vampire — first pair is the tier-1 bit).
            byte_idx, bit_idx = _TUI[name].tier_ids[0:2]
            if byte_idx == 0:
                initial_form_unlocks  |= 1 << bit_idx
            else:
                initial_form_unlocks2 |= 1 << bit_idx
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
    patch.write_token(APTokenTypes.WRITE, INITIAL_TRANSFORM_UNLOCKS_OFFSET,  bytes([initial_form_unlocks]))
    patch.write_token(APTokenTypes.WRITE, INITIAL_TRANSFORM_UNLOCKS2_OFFSET, bytes([initial_form_unlocks2]))

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

    # Same dispatch for traps placed at coin locations (bigcoinsanity).
    # GrantCoinItem reads TrapCoinTable; LevelCoinItems keeps a gem
    # placeholder so the portrait/popup stays consistent.
    trap_coin_table = list(world._build_trap_coin_table())
    patch.write_token(APTokenTypes.WRITE, TRAP_COIN_TABLE_OFFSET, bytes(trap_coin_table))

    # Boss-defeat item tables (offline grant). Only populated when the
    # boss_defeats option is on; otherwise all three tables ship as
    # defaults ($FF / $00 / $FF) and GrantBossItem's ret-on-$FF path
    # makes it a no-op.
    boss_items, boss_keyring_targets, boss_traps = world._build_boss_item_assignments()
    patch.write_token(APTokenTypes.WRITE, LEVEL_BOSS_ITEMS_OFFSET,     bytes(boss_items))
    patch.write_token(APTokenTypes.WRITE, BOSS_KEYRING_TARGETS_OFFSET, bytes(boss_keyring_targets))
    patch.write_token(APTokenTypes.WRITE, TRAP_BOSS_TABLE_OFFSET,      bytes(boss_traps))

    music_boxes_required = int(world.options.music_boxes_required)
    patch.write_token(APTokenTypes.WRITE, MUSIC_BOXES_REQUIRED_OFFSET,
                      bytes([music_boxes_required]))

    # -----------------------------------------------------------------
    # Entrance Shuffle (EXPERIMENTAL — Phase A: ROM plumbing only).
    #
    # LevelEntranceMap is a 26-byte table in the home bank. Entries
    # 0-24 correspond to overworld positions 1-25 (regular levels);
    # entry 25 is the Temple slot (wOWLevel = 0). Each byte holds the
    # target owlevel index:
    #     0-24 → run the regular level with that 0-indexed owlevel
    #     25   → route to the Temple (SelectLevel jumps to .the_temple)
    #
    # Default (option off) leaves the identity map already built into
    # the ROM: entry[i] = i. Options "on" and "with_temple" replace it
    # with a random permutation. Rules.py is NOT yet aware of the
    # shuffle — this seed will likely not be beatable when the option
    # is on. Phase B will thread the shuffle through rules.
    # Entrance Shuffle — read the permutation generated in generate_early
    # (world.entrance_map) so rules.py and the ROM patch are in perfect
    # sync. Both the LevelEntranceMap bytes and the option flag get
    # patched only when the option is non-off.
    entrance_shuffle_opt = int(world.options.entrance_shuffle)
    if entrance_shuffle_opt != 0:
        patch.write_token(APTokenTypes.WRITE, LEVEL_ENTRANCE_MAP_OFFSET,
                          bytes(world.entrance_map))
        # Flip the ROM's EntranceShuffleOpt flag so LoadLevelNameIfValid
        # activates the "?????" reveal system. When the option is off,
        # the flag stays 0 (default) and level labels render vanilla.
        patch.write_token(APTokenTypes.WRITE, ENTRANCE_SHUFFLE_OPT_OFFSET,
                          bytes([entrance_shuffle_opt]))

    # -----------------------------------------------------------------
    # Shopsanity — 10 slot prices, 2 bytes each (2-byte BCD, big-endian
    # matching wNumCoins layout). All ladders cap at 500 coins so the
    # player always has spending headroom under the 999-coin wallet cap
    # (MAX_NUM_COINS = $999). A price at the wallet cap would mean the
    # player can never buy AND save for the next slot at the same time.
    #   cheap:     20, 40, ..., 200          (20×N — affordable early)
    #   normal:    50, 100, ..., 500         (50×N — default)
    #   expensive: 100, 150, ..., 500, 500   (steep front-load, top-slot
    #              flat at cap so it feels like a splurge)
    def _to_bcd_2byte(v: int) -> tuple[int, int]:
        v = max(0, min(999, int(v)))
        hi = v // 100                          # 0-9
        mid = (v // 10) % 10                   # 0-9
        lo = v % 10                            # 0-9
        return hi, (mid << 4) | lo             # matches wNumCoins big-endian BCD

    shop_tier = int(world.options.shop_price_tier)
    if shop_tier == 0:   # cheap
        price_ladder = [20 * (i + 1) for i in range(10)]
    elif shop_tier == 2: # expensive
        price_ladder = [100, 150, 200, 250, 300, 350, 400, 450, 500, 500]
    else:                # normal (default)
        price_ladder = [50 * (i + 1) for i in range(10)]

    price_bytes = bytearray()
    for coins in price_ladder:
        hi, lo = _to_bcd_2byte(coins)
        price_bytes.append(hi)
        price_bytes.append(lo)
    patch.write_token(APTokenTypes.WRITE, SHOP_PRICES_OFFSET, bytes(price_bytes))

    # Shopsanity mode flag. Off → InitNorthMapSide skips the shop tile +
    # traversal arrows so the tile is invisible AND unwalkable, and
    # .shop_entry silently no-ops as defense. On → shop is drawn and
    # A-press launches the shop scene.
    shopsanity_on = 1 if bool(world.options.shopsanity) else 0
    patch.write_token(APTokenTypes.WRITE, SHOPSANITY_MODE_OFFSET,
                      bytes([shopsanity_on]))

    # Shopsanity per-slot treasure IDs — 10 bytes, one per shop slot.
    # ROM reads this at shop init to render a treasure icon per window.
    # Mirrors _build_chest_assignments: own placement → real treasure id;
    # foreign item → gem placeholder ($4E-$50) based on classification;
    # anything else (key, keyring, form, trap) → sensible fallback icon.
    # Default $65 (TREASURE_DUMMY) when shopsanity is off or the location
    # somehow has no item.
    from BaseClasses import ItemClassification
    from .locations import SHOP_LOCATION_TABLE, NUM_SHOP_SLOTS
    from .items import ITEM_TABLE, KEY_ITEM_TABLE

    # msg-font charmap (matches src/data/msg_names.asm): A..Z = 0..25,
    # 0..9 = 26..35, space = 36, dash = 37, ampersand = 38, period = 39.
    # Encode a plain ASCII string as msg-font bytes for the shop name
    # cache. Anything not in this map falls back to space so we never
    # write a byte that would decode as garbage in the sprite tile.
    def _encode_msgfont(text: str) -> bytes:
        out = bytearray()
        for ch in text.upper():
            if 'A' <= ch <= 'Z':
                out.append(ord(ch) - ord('A'))
            elif '0' <= ch <= '9':
                out.append(0x1A + (ord(ch) - ord('0')))
            elif ch == ' ':
                out.append(0x24)
            elif ch == '-':
                out.append(0x25)
            elif ch == '&':
                out.append(0x26)
            elif ch == '.':
                out.append(0x27)
            else:
                out.append(0x24)   # unknown → blank
        return bytes(out)

    # Compact per-item shop labels. Anything not listed here uses its
    # AP item name, uppercased and truncated to 10 chars.
    _SHOP_SHORT = {
        # Combined items (when combined_items option is on, the AP pool
        # uses the combined name — NOT the component names below).
        "Lantern & Magical Flame": "LTRN+FLAME",
        "Gears":                   "GEARS",
        "Blue Book & Magic Wand":  "BOOK+WAND",
        "Trident & Yellow Book":   "TRD+BOOK",
        "Skull Ring":              "SKULL RING",
        "Tablets":                 "TABLETS",
        "Scroll":                  "SCROLL",
        "Tusk Set":                "TUSK SET",
        "Storm Pouch":             "STRM POUCH",
        "Chemicals":               "CHEMICALS",
        "Glass Eyes":              "GLASS EYES",
        "Golden Eyes":             "GOLDEN EYE",
        "Sun Medallion":           "MEDALLION",
        "Key Cards":               "KEY CARDS",
        # Uncombined (one component per AP item)
        "Yellow Music Box":  "YEL M. BOX",
        "Blue Music Box":    "BLU M. BOX",
        "Green Music Box":   "GRN M. BOX",
        "Red Music Box":     "RED M. BOX",
        "Gold Music Box":    "GLD M. BOX",
        "Progressive Flippers": "FLIPPERS",
        "Progressive Grab":  "GRAB",
        "Progressive Overalls": "OVERALLS",
        "High Jump Boots":   "BOOTS",
        "Spiked Helmet":     "HELMET",
        "Magical Flame":     "FLAME",
        "Warp Compact":      "COMPACT",
        "Treasure Map":      "MAP",
        "Yellow Book":       "Y. BOOK",
        "Blue Tablet":       "B. TABLET",
        "Green Tablet":      "G. TABLET",
        "Ornamental Fan":    "FAN",
        "Top Half of Scroll": "HALFSCROLL",
        "Bottom Half of Scroll": "HALFSCROLL",
        "Green Flower":      "FLOWER",
        "Blue Chemical":     "CHEMICAL",
        "Red Chemical":      "CHEMICAL",
        "Sapling of Growth": "SAPLING",
        "Night Vision Scope": "NIGHTSCOPE",
        "Electric Fan Propeller": "PROPELLER",
        "Explosive Plunger Box": "PLUNGER",
        "Castle Brick":      "BRICK",
        "Warp Removal Apparatus": "W. REMOVAL",
        "Red Key Card":      "KEY CARD",
        "Blue Key Card":     "KEY CARD",
        "Mystery Handle":    "HANDLE",
        "Demon's Blood":     "DMON BLOOD",
        "Fighter Mannequin": "MANNEQUIN",
        "Truck Wheel":       "WHEEL",
        "Foot of Stone":     "STONE FOOT",
        "Golden Right Eye":  "GOLDEN EYE",
        "Golden Left Eye":   "GOLDEN EYE",
        "Right Glass Eye":   "GLASS EYE",
        "Left Glass Eye":    "GLASS EYE",
        "Sun Medallion Top": "MEDALLION",
        "Sun Medallion Bottom": "MEDALLION",
        "Eye of the Storm":  "STORM EYE",
        "Magic Seeds":       "MAGIC SEED",
        "Full Moon Gong":    "GONG",
        "Day or Night Spell": "DAY SPELL",
        "Earthen Figure":    "FIGURE",
        "Magnifying Glass":  "MAGNIFIER",
        "Fire Drencher":     "DRENCHER",
        "Red Crayon":        "CRAYON",
        "Brown Crayon":      "CRAYON",
        "Yellow Crayon":     "CRAYON",
        "Green Crayon":      "CRAYON",
        "Cyan Crayon":       "CRAYON",
        "Blue Crayon":       "CRAYON",
        "Pink Crayon":       "CRAYON",
        # Coin bundles (repurposed crest slots)
        "1 Coin":    "1 COIN",
        "10 Coins":  "10 COINS",
        "25 Coins":  "25 COINS",
        "50 Coins":  "50 COINS",
    }

    # Map owlevel index (1-25) → 2-char abbreviation for shop labels
    # (level_id + 1..6/7 within its map side, matches the LevelAbbrevs
    # table used by the in-level KEYRING message).
    _OW_ABBREV = (
        ["N1", "N2", "N3", "N4", "N5", "N6"] +
        ["W1", "W2", "W3", "W4", "W5", "W6"] +
        ["S1", "S2", "S3", "S4", "S5", "S6"] +
        ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]
    )
    _COLOR_ABBREV = ["GRY", "RED", "GRN", "BLU"]  # color_index 0..3

    def _shop_label_for(item) -> str:
        """Return the ≤10-char label to display in the shop for `item`
        (from the same player). Falls back to the item name uppercased +
        truncated when we don't have a canonical short form."""
        # Level keys aren't in ITEM_TABLE — format as "N1 GRY KEY".
        key_data = KEY_ITEM_TABLE.get(item.name)
        if key_data is not None:
            ow = _OW_ABBREV[key_data.owlevel - 1]
            col = _COLOR_ABBREV[key_data.color_index]
            return f"{ow} {col} KEY"
        short = _SHOP_SHORT.get(item.name)
        if short is not None:
            return short
        # Anything else: uppercase + truncate. Better than a blank slot.
        return item.name.upper()[:10]

    def _center_pad(label: str) -> bytes:
        """Encode label to msg-font, then centre-pad to 20 bytes with
        msg-font spaces. Matches how TreasureMsgNames entries are laid
        out so the ROM's draw code can share code paths."""
        label = label[:20]
        enc = _encode_msgfont(label)
        pad = 20 - len(enc)
        lead = pad // 2
        trail = pad - lead
        return b'\x24' * lead + enc + b'\x24' * trail

    shop_slot_items = bytearray([0x65] * NUM_SHOP_SLOTS)
    shop_slot_names = bytearray(b'\x24' * (NUM_SHOP_SLOTS * 20))
    if shopsanity_on:
        for loc_name, loc_data in SHOP_LOCATION_TABLE.items():
            try:
                location = world.multiworld.get_location(loc_name, world.player)
            except KeyError:
                continue
            item = location.item
            if item is None:
                continue
            slot = loc_data.slot_index
            if item.player != world.player:
                cls = item.classification
                if cls in (ItemClassification.progression,
                           ItemClassification.progression_skip_balancing):
                    shop_slot_items[slot] = 0x4E  # Red Gem
                elif cls == ItemClassification.useful:
                    shop_slot_items[slot] = 0x50  # Blue Gem
                else:
                    shop_slot_items[slot] = 0x4F  # Green Gem
                shop_slot_names[slot*20:slot*20+20] = _center_pad("AP ITEM")
                continue
            # Same-player item — pick tile ID + short label.
            item_data = ITEM_TABLE.get(item.name)
            if item_data is not None:
                tid = item_data.tier_ids[0]
                shop_slot_items[slot] = tid if 0 < tid < 0x65 else 0x65
            else:
                # Not in ITEM_TABLE — likely a level key. $65 = DUMMY
                # renders the key portrait art.
                shop_slot_items[slot] = 0x65
            shop_slot_names[slot*20:slot*20+20] = _center_pad(_shop_label_for(item))
    patch.write_token(APTokenTypes.WRITE, SHOP_SLOT_ITEMS_OFFSET,
                      bytes(shop_slot_items))
    patch.write_token(APTokenTypes.WRITE, SHOP_SLOT_NAMES_OFFSET,
                      bytes(shop_slot_names))

    # Rudy (Hidden Figure) hit points — patch the immediate byte in
    # HiddenFigureFunc's initializer so a player-chosen 1-10 controls
    # how many hits Wario needs to land. ROM layout unchanged.
    rudy_hit_points = int(world.options.rudy_hit_points)
    patch.write_token(APTokenTypes.WRITE, RUDY_HIT_POINTS_OFFSET,
                      bytes([rudy_hit_points]))

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

    # DeathMode drives the ROM-side intercepts (Jamano grab / golf bogey).
    # The DeathLink Toggle is purely client-side; this byte controls what
    # the ROM treats as a local death.
    death_mode = int(world.options.death_mode)
    patch.write_token(APTokenTypes.WRITE, DEATH_MODE_OPT_OFFSET,
                      bytes([death_mode]))

    # Big Coinsanity flag — gates MusicalCoinFunc's portrait/suppression
    # logic. Off (0) = vanilla coin sprite, no AP item dispatch.
    bigcoinsanity = int(world.options.bigcoinsanity)
    patch.write_token(APTokenTypes.WRITE, BIG_COINSANITY_OPT_OFFSET,
                      bytes([bigcoinsanity]))

    # Golf Building par-hint frequency (0=per_hole, 1=per_course).
    # Controls when the ROM sets wParHintRequest in GolfHoleState_Cleared.
    # The hint MODE (nothing / music_boxes / progressive / anything) is
    # client-side only, dispatched from the GolfParHints option.
    golf_par_hint_freq = int(world.options.golf_par_hint_frequency)
    patch.write_token(APTokenTypes.WRITE, GOLF_PAR_HINT_FREQ_OFFSET,
                      bytes([golf_par_hint_freq]))

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
            world.options.wario_palette_shuffle):
        # NOTE: overworld_bg_palette_shuffle intentionally NOT here. The
        # DisablePalCycleOpt flag gates the in-level palette tick. Including
        # it for the overworld shuffle was causing a freeze on day/night
        # transitions even though the cycle code only affects level rooms —
        # likely an indirect interaction. Re-enable only with a repro.
        patch.write_token(APTokenTypes.WRITE, DISABLE_PAL_CYCLE_OFFSET, bytes([1]))

    # --- palette shuffle: deferred to patch time ---
    # Per-palette seeds are rolled here (consumes world.random deterministically),
    # then bundled into palette_params.json. apply_palette_shuffle reads vanilla
    # palette bytes from the snapshot at patch time and runs the recolors with
    # these seeds. Vanilla palette bytes are NOT stored in the apworld.
    import json as _json
    from .palette_offsets import (ENEMY_PALETTES, LEVEL_BG_PALETTES,
                                    OVERWORLD_BG_PALETTES)

    palette_params: dict = {"enemy": [], "level_bg": [], "overworld_bg": []}

    if world.options.enemy_palette_shuffle:
        for offset, length, _group in ENEMY_PALETTES:
            palette_params["enemy"].append({
                "offset": offset,
                "length": length,
                "seed":   world.random.getrandbits(32),
            })

    if world.options.level_bg_palette_shuffle:
        # Same shared-hue trick as the overworld: rotate every level BG
        # palette by ONE seed-rolled hue so adjacent palette regions within
        # a level/room don't get independently rotated and produce jagged
        # color edges. Trade-off: all levels become tinted the same family,
        # but within each level everything stays coherent.
        # Clamp away from 0/1 — hue wraps, so values near either end produce
        # near-vanilla rotations. [0.1, 0.9] guarantees a visible shift.
        shared_level_hue = world.random.uniform(0.1, 0.9)
        for offset, length, _group in LEVEL_BG_PALETTES:
            palette_params["level_bg"].append({
                "offset": offset,
                "length": length,
                "group_hue": shared_level_hue,
            })

    if world.options.overworld_bg_palette_shuffle:
        # All overworld palettes share ONE hue rotation so adjacent terrain
        # types (mountain / ground / grass / etc — each in its own palette
        # entry) stay thematically related instead of rotating independently
        # and clashing at tile borders. Whole map gets uniformly tinted.
        shared_ow_hue = world.random.uniform(0.1, 0.9)
        # OVERWORLD_BG_PALETTES includes labels that the engine ALSO uses as
        # OBJ palette sources (loaded into wTempPals2). Recoloring those
        # corrupts overworld OBJ palettes (star indicator, map-side OBJ
        # tints) and softlocks the day/night transition — keep them vanilla.
        # Sourced by grepping `ld hl, Pals_84xxx` followed by wTempPals2 /
        # OBPI / rOBPI in src/engine/overworld/*.asm.
        OW_OBJ_PALETTE_OFFSETS = {0x848e0, 0x84900, 0x84980, 0x84a20}
        sorted_entries = sorted(OVERWORLD_BG_PALETTES, key=lambda e: e[0])
        for i, (offset, length, _group) in enumerate(sorted_entries):
            if offset in OW_OBJ_PALETTE_OFFSETS:
                continue
            if i + 1 < len(sorted_entries):
                next_off = sorted_entries[i + 1][0]
                length = min(length, next_off - offset)
            palette_params["overworld_bg"].append({
                "offset": offset,
                "length": length,
                "group_hue": shared_ow_hue,
            })
        # Title screen palettes — 4 × 64-byte sets (Pals_4f82/_4fc2/_5002/
        # _5042). 4f82+5002 feed wTempPals1 (BG); 4fc2+5042 feed wTempPals2
        # (OBJ). Including all 4 gives a coherent title recolor that matches
        # the overworld's hue shift. Offsets are HACKED-ROM positions (bank
        # 1 grew ~542 bytes vs vanilla), so they're flagged source="rom" to
        # tell apply_palette_shuffle to read from the post-bsdiff rom.
        # UPDATE THESE any time bank-1 layout shifts (grep warioland3.sym
        # for Pals_4f82 / Pals_4fc2 / Pals_5002 / Pals_5042). The old
        # offsets 0x51a0/0x51e0/0x5220/0x5260 collided with
        # LevelTreasureRequirements after a section shift — writing here
        # smashed the treasure requirements table for owlevels 22-25
        # (Colossal Hole, Warped Void, East Crater, Forest of Fear),
        # forcing every high-level variant to fail its treasure check.
        TITLE_PALETTE_OFFSETS = [0x5209, 0x5249, 0x5289, 0x52c9]
        for offset in TITLE_PALETTE_OFFSETS:
            palette_params["overworld_bg"].append({
                "offset": offset,
                "length": 64,
                "group_hue": shared_ow_hue,
                "source": "rom",
            })

    # Always write the file (even if both shuffles disabled) so apply_palette_shuffle
    # can self.get_file() without erroring.
    patch.write_file("palette_params.json",
                     _json.dumps(palette_params).encode("utf-8"))

    # Wario palette offsets — hand-curated list of positions in each
    # WarioXxxPal palette that contain visually-impactful colors.
    # OVERALLS_OFFSETS points at black/dark outline slots; SHIRT_OFFSETS at
    # white/highlight slots. These are the ONLY positions that demonstrably
    # affect Wario's rendered sprite — sub-palette B positions (where
    # logical "shirt yellow" and "overalls purple" live in vanilla) appear
    # to be loaded but unused by Wario's sprite tiles.
    # NOTE: This means changing "shirt" affects eye whites + gloves; changing
    # "overalls" affects the outline.
    WARIO_OVERALLS_OFFSETS = [
        0xc806, 0xc812, 0xc826, 0xc82e, 0xc836, 0xc83e, 0xc846, 0xc84e,
        0xc856, 0xc85a, 0xc85e, 0xc866, 0xc86e, 0xc876, 0xc87e, 0xc886,
        0xc89e, 0xc8ae, 0xc8be, 0xc8c6, 0xc8ce, 0xc8d6, 0xc8de, 0xc8ee,
        0xc8fe, 0xc90e, 0xc916, 0xc936, 0xc942, 0xc956, 0xc95e, 0xc96e,
        0xc97e, 0xc996, 0xc99e, 0xc9a6, 0xc9ae, 0xc9c6, 0xc9d6, 0xc9e6,
    ]
    WARIO_SHIRT_OFFSETS = [off - 4 for off in WARIO_OVERALLS_OFFSETS]

    def _hex_to_gbc_bytes(s):
        """Parse #RRGGBB / RRGGBB / #RGB / RGB into 2 bytes of GBC BGR555,
        snapping each 8-bit channel to the nearest 5-bit value. Returns None
        if the string is empty / malformed."""
        s = s.strip().lstrip('#')
        if not s:
            return None
        if len(s) == 3:
            # Short form: each char expands to two (e.g. #f80 -> #ff8800)
            s = s[0]*2 + s[1]*2 + s[2]*2
        if len(s) != 6:
            return None
        try:
            r8, g8, b8 = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
        except ValueError:
            return None
        # Quantize 0-255 -> 0-31 with rounding to nearest.
        r5 = (r8 * 31 + 127) // 255
        g5 = (g8 * 31 + 127) // 255
        b5 = (b8 * 31 + 127) // 255
        gbc = (b5 << 10) | (g5 << 5) | r5
        return bytes([gbc & 0xFF, (gbc >> 8) & 0xFF])

    # WarioPaletteShuffle: 0 off, 1 shirt, 2 overalls, 3 both.
    # Color priority per slot (highest first):
    #   custom hex (wario_colors dict) > shuffle > vanilla (no write).
    wario_pal = int(world.options.wario_palette_shuffle)

    wc = world.options.wario_colors.value or {}
    custom_overalls = _hex_to_gbc_bytes(str(wc.get("overalls", "")))
    custom_shirt    = _hex_to_gbc_bytes(str(wc.get("shirt", "")))

    # Overalls slot.
    if custom_overalls is not None:
        overalls_bytes = custom_overalls
    elif wario_pal in (2, 3):  # overalls or both shuffle
        r = world.random.randint(0, 23)
        g = world.random.randint(0, 23)
        b = world.random.randint(0, 23)
        overalls_bytes = bytes([((b << 10) | (g << 5) | r) & 0xFF,
                                (((b << 10) | (g << 5) | r) >> 8) & 0xFF])
    else:
        overalls_bytes = None
    if overalls_bytes is not None:
        for off in WARIO_OVERALLS_OFFSETS:
            patch.write_token(APTokenTypes.WRITE, off, overalls_bytes)

    # Shirt slot.
    if custom_shirt is not None:
        shirt_bytes = custom_shirt
    elif wario_pal in (1, 3):  # shirt or both shuffle
        r = world.random.randint(8, 31)
        g = world.random.randint(8, 31)
        b = world.random.randint(8, 31)
        shirt_bytes = bytes([((b << 10) | (g << 5) | r) & 0xFF,
                             (((b << 10) | (g << 5) | r) >> 8) & 0xFF])
    else:
        shirt_bytes = None
    if shirt_bytes is not None:
        for off in WARIO_SHIRT_OFFSETS:
            patch.write_token(APTokenTypes.WRITE, off, shirt_bytes)

    # Hidden Passages Revealed — flip the ROM flag byte; the in-ROM
    # RevealHiddenBlocksInRoom routine runs at room load and overlays
    # cracked-block tile indices onto hidden block slots in
    # wRoomBlockTiles. Behavior/IDs unchanged, only the rendered tiles.
    patch.write_token(APTokenTypes.WRITE, HIDDEN_PASSAGES_REVEALED_OFFSET,
                      bytes([1 if world.options.hidden_passages_revealed else 0]))

    # --- Random dialog text variants ---
    # tools/build_text_variants.py bundles all compiled RLE blobs from
    # src/text/en/*_variants/ into text_variants.py. We pick one per
    # seed and write it over the vanilla blob at its ROM offset. The
    # RLE decompressor stops on the first $00 byte, so shorter variants
    # naturally ignore trailing bytes from the vanilla slot.
    try:
        from . import text_variants as _tv
        if getattr(_tv, "RUDY_PRE_FIGHT", None):
            chosen = world.random.choice(_tv.RUDY_PRE_FIGHT)
            # ROM offset for TextEN_HiddenFigureReplenishPower (bank $2c addr $6424).
            patch.write_token(APTokenTypes.WRITE, 0x0B2424, chosen)
        if getattr(_tv, "OLD_MAN_THANK_YOU", None):
            chosen = world.random.choice(_tv.OLD_MAN_THANK_YOU)
            # ROM offset for TextEN_OldManThankYou (bank $57 addr $6225).
            patch.write_token(APTokenTypes.WRITE, 0x15E225, chosen)
    except ImportError:
        # text_variants.py hasn't been generated (run tools/build_text_variants.py
        # after `make`). Fall back to vanilla text silently.
        pass

    # Enemizer — deferred to patch-apply time so vanilla palette bytes
    # never ship in the apworld. Gen-time only rolls the seed; the
    # deferred apply_enemizer step does composition using vanilla bytes
    # read from the ROM snapshot. The file is always written so the
    # procedure step always has its input — `enabled: false` skips work.
    # bool() on an AP Toggle returns True/False based on its value; using
    # `Toggle and X` short-circuits to the Toggle object itself when the
    # value is falsy, which then explodes the JSON encoder.
    # Enemizer is a Choice: 0 off / 1 full / 2 grouped. Any non-zero
    # value enables randomization; the specific value is passed through
    # so generate_patch_writes can restrict substitution pools when
    # grouping is on.
    enemizer_mode = int(getattr(world.options, "enemizer", 0))
    enemizer_on = enemizer_mode != 0
    enemizer_params = {
        "enabled": enemizer_on,
        "mode": enemizer_mode,   # 0=off / 1=full / 2=grouped
        "seed": world.random.getrandbits(32) if enemizer_on else 0,
        "use_palette_overrides": enemizer_on and bool(world.options.enemy_palette_shuffle),
    }
    patch.write_file("enemizer_params.json",
                     _json.dumps(enemizer_params).encode("utf-8"))

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
