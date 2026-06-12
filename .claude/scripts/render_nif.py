#!/usr/bin/env python3
"""Render NIF (the endgame text screen) to images/nif_ending_screen.png.

NIF is a full 280x192 hi-res image stored as a line-sequential raster:
192 rows of 40 bytes, top to bottom, no interleave and no screen
holes (7680 bytes exactly). Run from the project root.
"""
import sys
sys.path.insert(0, '.claude/scripts')
from render_hires import render_rows, save_png

data = open('reference/nif.bin', 'rb').read()
rows = [data[r * 40:(r + 1) * 40] for r in range(192)]
save_png(render_rows(rows), 'images/nif_ending_screen.png', scale=2)
