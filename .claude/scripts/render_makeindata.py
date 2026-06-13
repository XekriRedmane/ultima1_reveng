#!/usr/bin/env python3
"""Render the MAKE.INDATA title image recovered by the decompressor.

MAKE.INDATA's build driver decompresses the packed stream at $49EC straight
into hi-res page 1 ($2000-$3FFF) using the standard interleaved Apple II row
layout, then dissolves it onto the screen. We replay the decompressor
(makeindata_emu) to recover the page-1 image, de-interleave it into 192
line-sequential rows of 40 bytes, and save a PNG.
"""
import sys
sys.path.insert(0, '.claude/scripts')
from render_hires import render_rows, save_png
from makeindata_emu import decompress_at


def rowaddr(r):
    a = 0x2000
    a += (r & 0x07) << 10
    a += ((r >> 3) & 0x07) << 7
    a += (r >> 6) * 0x28
    return a


def page1_to_rows(page):
    """De-interleave a $2000-$3FFF page-1 image (0x2000 bytes) into 192
    line-sequential rows of 40 bytes each."""
    rows = []
    for r in range(192):
        off = rowaddr(r) - 0x2000
        rows.append(page[off:off + 40])
    return rows


def build_logo():
    """Run the $8700 payload to recover the ORIGIN logo at $9600 (interleaved
    page image), then de-interleave it. Returns 192 line-sequential rows."""
    from makeindata_emu import CPU, load_ref
    data = load_ref()
    mem = bytearray(0x10000)
    mem[0x1E00:0x1E00 + len(data)] = data
    src = 0x2000 - 0x1E00
    mem[0x8700:0x8700 + 0x800] = data[src:src + 0x800]
    cpu = CPU(mem)
    cpu.run(0x8700)
    page = bytes(mem[0x9600:0xB600])
    return page1_to_rows(page)


def main():
    page, end, steps = decompress_at(0x49EC)
    rows = page1_to_rows(page)
    save_png(render_rows(rows, first_col=0), 'images/makeindata_title.png', scale=2)
    print(f'rendered images/makeindata_title.png  (stream consumed to ${end:04X})')

    logo_rows = build_logo()
    save_png(render_rows(logo_rows, first_col=0), 'images/makeindata_origin.png',
             scale=2)
    print('rendered images/makeindata_origin.png')


if __name__ == '__main__':
    main()
