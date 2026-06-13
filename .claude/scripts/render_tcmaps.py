#!/usr/bin/env python3
"""Render the 10 TCMAPS town/castle maps to images/tcmaps_<n>.png and a
contact sheet images/tcmaps_all.png.

TCMAPS ($4000) opens with a 10-word directory of map pointers, then ten
764-byte maps. The displayed part of each map is a 38x19 grid of
MAPCHARS glyph codes (one byte per cell); the trailing 42 bytes are
per-map metadata. TWN/CAS draw a cell by printing its byte through the
MAPCHARS font (bank-A format: 128 glyphs x 8 scanlines, scanline s of
glyph g at base + s*0x80 + g).

Run from the project root.
"""
from PIL import Image

TCMAPS = open('reference/tcmaps.bin', 'rb').read()
FONT = open('reference/mapchars.bin', 'rb').read()

COLS, ROWS = 38, 19
CW, CH = 7, 8                 # Apple II character cell
N_MAPS = 10
DIR_BYTES = N_MAPS * 2


def glyph_rows(code):
    """Return 8 rows of 7 pixels for MAPCHARS glyph `code` (0-127)."""
    g = code & 0x7F
    rows = []
    for s in range(8):
        b = FONT[s * 0x80 + g]
        # Apple II: bit0 is leftmost pixel; high bit is the colour/hi
        # flag, not a pixel. Take 7 low bits, LSB first.
        rows.append([(b >> p) & 1 for p in range(7)])
    return rows


def render_map(idx):
    off = (TCMAPS[idx * 2] | (TCMAPS[idx * 2 + 1] << 8)) - 0x4000
    img = Image.new('RGB', (COLS * CW, ROWS * CH), (0, 0, 0))
    px = img.load()
    for r in range(ROWS):
        for c in range(COLS):
            code = TCMAPS[off + r * COLS + c]
            for s, bits in enumerate(glyph_rows(code)):
                for p, on in enumerate(bits):
                    if on:
                        px[c * CW + p, r * CH + s] = (255, 255, 255)
    return img


def main():
    maps = [render_map(i) for i in range(N_MAPS)]
    for i, m in enumerate(maps):
        m.resize((m.width * 2, m.height * 2),
                 Image.NEAREST).save(f'images/tcmaps_{i}.png')
    # contact sheet: 2 cols x 5 rows
    mw, mh = maps[0].width, maps[0].height
    gap = 8
    sheet = Image.new('RGB', (2 * mw + 3 * gap, 5 * mh + 6 * gap),
                      (40, 40, 40))
    for i, m in enumerate(maps):
        c, r = i % 2, i // 2
        sheet.paste(m, (gap + c * (mw + gap), gap + r * (mh + gap)))
    sheet.save('images/tcmaps_all.png')
    print(f'wrote images/tcmaps_0..{N_MAPS-1}.png and tcmaps_all.png')


if __name__ == '__main__':
    main()
