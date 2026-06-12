#!/usr/bin/env python3
"""Apple II hi-res graphics rendering library.

Shared helpers for the per-project render scripts that turn sprite
tables, fonts, and screen data into PNGs for embedding in main.nw
(see the "render any graphics data you uncover" standing rule in
reveng.md). Import this from a render_<name>.py script; don't rewrite
palette logic from scratch.

Hi-res byte format: each byte holds 7 pixels. Bit 0 is the leftmost
pixel of the byte's 7-pixel slice, bit 6 the rightmost; bit 7 is the
palette bit (0 = violet/green, 1 = blue/orange). Color comes from NTSC
artifacts: an isolated on-bit is colored by its absolute pixel-column
parity and the host byte's palette bit; two or more adjacent on-bits
render white.

Typical use:

    from render_hires import render_rows, save_png

    data = open('reference/main.bin', 'rb').read()
    off = 0x6000 - 0x0800          # address - target base
    rows = [data[off + r*W : off + r*W + W] for r in range(H)]
    img = render_rows(rows, first_col=0)
    save_png(img, 'images/my_sprite.png', scale=4)
"""

from __future__ import annotations

from typing import Sequence

from PIL import Image

# Approximate NTSC artifact palette.
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
VIOLET = (180, 0, 255)
ORANGE = (255, 128, 0)
BLUE = (0, 128, 255)
TRANSPARENT = (32, 32, 32)  # grey backdrop for transparent cells


def row_bits(row_bytes: Sequence[int]) -> tuple[list[int], list[int]]:
    """Expand one row of hi-res bytes to (bits, palette-per-pixel)."""
    bits: list[int] = []
    pal: list[int] = []
    for b in row_bytes:
        p = (b >> 7) & 1
        for i in range(7):
            bits.append((b >> i) & 1)
            pal.append(p)
    return bits, pal


def color_row(row_bytes: Sequence[int], first_col: int = 0
              ) -> list[tuple[int, int, int]]:
    """Apply NTSC artifact rules to one row of bytes.

    first_col is the absolute screen pixel column of the row's first
    pixel — column parity decides green/violet vs orange/blue, so
    rendering a sprite at its true X parity matters.
    """
    bits, pal = row_bits(row_bytes)
    out: list[tuple[int, int, int]] = []
    n = len(bits)
    for i, bit in enumerate(bits):
        if not bit:
            out.append(BLACK)
            continue
        left = bits[i - 1] if i > 0 else 0
        right = bits[i + 1] if i < n - 1 else 0
        if left or right:
            out.append(WHITE)
            continue
        odd = (first_col + i) & 1
        if pal[i]:
            out.append(ORANGE if odd else BLUE)
        else:
            out.append(GREEN if odd else VIOLET)
    return out


def render_rows(rows: Sequence[Sequence[int]], first_col: int = 0
                ) -> Image.Image:
    """Render a list of byte rows (top to bottom) to a 1:1 PIL image."""
    if not rows:
        raise ValueError('no rows')
    width = max(len(r) for r in rows) * 7
    img = Image.new('RGB', (width, len(rows)), BLACK)
    px = img.load()
    for y, row in enumerate(rows):
        for x, c in enumerate(color_row(row, first_col)):
            px[x, y] = c
    return img


def hires_row_addr(row: int, page_base: int = 0x2000) -> int:
    """Screen address of hi-res row 0..191 (the classic interleave)."""
    return (page_base
            + (row & 0x07) * 0x400
            + ((row >> 3) & 0x07) * 0x80
            + (row >> 6) * 0x28)


def render_screen(mem: bytes, mem_base: int, page_base: int = 0x2000
                  ) -> Image.Image:
    """Render a full 280x192 hi-res screen from a memory image.

    mem is a flat binary; mem_base its load address. page_base is
    $2000 (page 1) or $4000 (page 2).
    """
    rows = []
    for r in range(192):
        a = hires_row_addr(r, page_base) - mem_base
        rows.append(mem[a:a + 40])
    return render_rows(rows, first_col=0)


def save_png(img: Image.Image, path: str, scale: int = 4) -> None:
    """Save scaled with hard pixel edges (nearest neighbor)."""
    img.resize((img.width * scale, img.height * scale),
               Image.NEAREST).save(path)
    print(f'wrote {path} ({img.width}x{img.height} @ x{scale})')
