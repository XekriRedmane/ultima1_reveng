#!/usr/bin/env python3
"""Render the SPA (space overlay) enemy-ship sprite atlas.

The overlay stores 36 sprite descriptors in six parallel 36-entry tables at
the file tail:

  SHAPE_PTR_LO  $A1CF  low byte of the shape's pixel pointer
  SHAPE_PTR_HI  $A1F3  high byte
  SHAPE_XOFF    $A217  screen-x centring offset for this scale
  SHAPE_YOFF    $A23B  screen-y centring offset
  SHAPE_WID     $A25F  width in bytes (7-pixel columns)
  SHAPE_DX      $A283  per-row stride helper
  SHAPE_HGT     $A2A7  height in rows

Shapes 0..8 are the enemy craft drawn at nine increasing scales (a 1x1 dot at
the farthest range up to a 3-byte-wide, 45-row craft at closest range); the
draw routine ($9DE1) reads WID bytes per row for HGT rows, XOR-blitting the
7-bit pixel data into the hi-res view window through the engine's row-address
tables. Shapes 9..35 are 4-byte-wide windows into the shared docking/planet
bitmap.

We render each shape as an Apple II hi-res mono image (each data byte = 7
pixels, low bit first; the high "palette" bit is masked off by the blitter at
$9F60 so we treat bit7 as ignored). Output: images/spa_ships.png (the 9 ship
scales in a row) and images/spa_shapes_all.png (the full 36-entry atlas grid).
"""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
BASE = 0x8956
DATA = (ROOT / 'reference/spa.bin').read_bytes()

def b(addr):
    return DATA[addr - BASE]

N = 36
LO  = [b(0xA1CF + i) for i in range(N)]
HI  = [b(0xA1F3 + i) for i in range(N)]
WID = [b(0xA25F + i) for i in range(N)]
HGT = [b(0xA2A7 + i) for i in range(N)]
PTR = [(HI[i] << 8) | LO[i] for i in range(N)]


def shape_rows(i):
    """Return list of rows; each row is a list of 7-pixel bools left->right."""
    rows = []
    p = PTR[i] - BASE
    for _ in range(HGT[i]):
        bits = []
        for col in range(WID[i]):
            byte = DATA[p] if 0 <= p < len(DATA) else 0
            p += 1
            for k in range(7):           # low bit is leftmost pixel
                bits.append((byte >> k) & 1)
        rows.append(bits)
    return rows


def render_shape(i, scale=3, pad=1):
    rows = shape_rows(i)
    h = len(rows)
    w = max((len(r) for r in rows), default=1)
    img = Image.new('RGB', ((w + 2 * pad) * scale, (h + 2 * pad) * scale), (0, 0, 0))
    px = img.load()
    for y, row in enumerate(rows):
        for x, on in enumerate(row):
            if on:
                for dy in range(scale):
                    for dx in range(scale):
                        px[(x + pad) * scale + dx, (y + pad) * scale + dy] = (255, 255, 255)
    return img


def grid(indices, cols, scale, cell_pad=4, label=False):
    imgs = [render_shape(i, scale) for i in indices]
    cw = max(im.width for im in imgs) + cell_pad
    ch = max(im.height for im in imgs) + cell_pad
    rows = (len(imgs) + cols - 1) // cols
    out = Image.new('RGB', (cols * cw, rows * ch), (24, 24, 40))
    for n, im in enumerate(imgs):
        r, c = divmod(n, cols)
        ox = c * cw + (cw - im.width) // 2
        oy = r * ch + (ch - im.height) // 2
        out.paste(im, (ox, oy))
    return out


if __name__ == '__main__':
    outdir = ROOT / 'images'
    outdir.mkdir(exist_ok=True)
    # The nine enemy-ship scales, big, in one row.
    ships = grid(range(9), cols=9, scale=4)
    ships.save(outdir / 'spa_ships.png')
    # The full 36-entry atlas (ships + the 4x80 docking/planet windows).
    allg = grid(range(N), cols=9, scale=2)
    allg.save(outdir / 'spa_shapes_all.png')
    print('wrote images/spa_ships.png', ships.size)
    print('wrote images/spa_shapes_all.png', allg.size)
    for i in range(9):
        print(f'  ship scale {i}: {WID[i]}x{HGT[i]} @ ${PTR[i]:04X}')
