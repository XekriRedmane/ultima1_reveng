#!/usr/bin/env python3
"""Render the Ultima I glyph banks.

Bank A (text/overlay font), 128 glyphs of 1 byte x 8 scanlines:
    scanline s of glyph g lives at base + s*0x80 + g
    (planes of 128 bytes; FONT_DRAW at $1A1D walks $0800,$0880..$0B80).

Bank B (map tile set), 96 glyphs of 1 byte x 16 scanlines:
    scanline s of glyph g lives at base + s*0x60 + g
    (planes of 96 bytes; DRAW_MAP at $1C39 copies rows with stride $60).

Each glyph byte is 7 hi-res pixels, LSB leftmost; bit 7 is the
palette bit (ignored here for monochrome rendering).

Usage:
    render_font.py fontA <binfile> <offset> <out.png>
    render_font.py tilesB <binfile> <offset> <out.png>
"""
import sys
from PIL import Image

SCALE = 3


def glyph_rows(data, off, g, height, stride):
    return [data[off + s * stride + g] for s in range(height)]


def render(data, off, nglyphs, height, stride, per_row, pair=False):
    """Render a glyph sheet. pair=True draws glyphs in 2-wide pairs."""
    gw = 14 if pair else 7
    step = 2 if pair else 1
    cells = nglyphs // step
    rows = (cells + per_row - 1) // per_row
    pad = 2
    W = per_row * (gw + pad) + pad
    H = rows * (height + pad) + pad
    img = Image.new('RGB', (W, H), (40, 40, 60))
    px = img.load()
    for c in range(cells):
        g = c * step
        cx = pad + (c % per_row) * (gw + pad)
        cy = pad + (c // per_row) * (height + pad)
        for half in range(step):
            rowsdat = glyph_rows(data, off, g + half, height, stride)
            for s, byte in enumerate(rowsdat):
                for bit in range(7):
                    on = (byte >> bit) & 1
                    px[cx + half * 7 + bit, cy + s] = (
                        (235, 235, 235) if on else (0, 0, 0))
    return img.resize((W * SCALE, H * SCALE), Image.NEAREST)


def main():
    mode, path, off, out = sys.argv[1:5]
    data = open(path, 'rb').read()
    off = int(off, 16)
    if mode == 'fontA':
        # chars $00-$19 are pre-shifted even/odd pairs; show all 128 singly
        img = render(data, off, 128, 8, 0x80, per_row=16)
    elif mode == 'tilesB':
        # 96 chars = 48 two-char tiles, 16 scanlines tall
        img = render(data, off, 96, 16, 0x60, per_row=8, pair=True)
    else:
        raise SystemExit('mode must be fontA or tilesB')
    img.save(out)
    print('wrote', out, img.size)


if __name__ == '__main__':
    main()
