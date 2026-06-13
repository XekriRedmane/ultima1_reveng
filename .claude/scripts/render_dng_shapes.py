#!/usr/bin/env python3
"""Render the 25 DNG vector shapes to images/dng_monster_shapes.png.

MON_SHAPES ($A692) is a vector-stroke shape table consumed by
SHAPE_DRAW. It opens with 25 word pointers (offsets from $A692 to
each shape's stroke list), then the stroke lists themselves.

Each stroke list is a sequence of (x, y, flag) triples:
  x    -- signed offset from the screen-centre X origin ($80)
  y    -- signed offset from the shape's Y baseline
  flag -- 0 = move (pen up, reposition), nonzero = draw to here
A (0,0,*) triple terminates the shape.

SHAPE_DRAW scales x and y down by `depth` halvings before plotting;
here we render every shape at full size (scale 0) on its own tile.
Run from the project root.
"""
import sys
from PIL import Image, ImageDraw

DATA = open('reference/dng.bin', 'rb').read()
FBASE = 0x8956
MS = 0xA692
N_SHAPES = 25


def sbyte(b):
    return b - 256 if b >= 0x80 else b


def shape_strokes(idx):
    """Return a list of (x, y, draw) vertices for shape idx."""
    off = (MS - FBASE) + idx * 2
    ptr = DATA[off] | (DATA[off + 1] << 8)
    p = (MS - FBASE) + ptr  # file offset of the stroke list
    out = []
    while True:
        dx = sbyte(DATA[p]); dy = sbyte(DATA[p + 1]); flag = DATA[p + 2]
        p += 3
        if DATA[p - 3] == 0 and DATA[p - 2] == 0:
            break
        out.append((dx, dy, flag != 0))
    return out


def render_tile(idx, tw, th):
    """Render one shape centred on its own (tw x th) black tile."""
    tile = Image.new('RGB', (tw, th), (0, 0, 0))
    d = ImageDraw.Draw(tile)
    ox, oy = tw // 2, th // 2
    pen = None
    for (x, y, draw) in shape_strokes(idx):
        px, py = ox + x, oy + y
        if draw and pen is not None:
            d.line([pen[0], pen[1], px, py], fill=(0, 255, 0))
        pen = (px, py)
    d.text((2, 2), str(idx), fill=(120, 120, 120))
    return tile


def main():
    tile_w, tile_h = 130, 110
    cols, rows = 5, 5
    img = Image.new('RGB', (cols * tile_w, rows * tile_h), (0, 0, 0))
    for idx in range(N_SHAPES):
        c, r = idx % cols, idx // cols
        img.paste(render_tile(idx, tile_w, tile_h),
                  (c * tile_w, r * tile_h))
    img.resize((img.width * 2, img.height * 2),
               Image.NEAREST).save('images/dng_monster_shapes.png')
    print('wrote images/dng_monster_shapes.png')


if __name__ == '__main__':
    main()
