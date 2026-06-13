---
name: dng-subsystem
description: Ultima I DNG overlay architecture -- procedural maze generator, ray-marched wireframe renderer, vector-shape engine (rounds 13-15)
metadata:
  type: project
---

DNG ($8956-$B098, 10051 bytes) is the first-person wireframe dungeon,
fully decomposed and byte-perfect as of round 15.

**Why:** the renderer's structure is non-obvious and took a full round
to map; future TWN/CAS/SPA rounds reuse the same engine-API EQU block
and the same drawing primitives may recur.

**How to apply:**
- The maze is NOT stored: DNG_GEN ($8C5D) regenerates it from a 2-byte
  seed (place/position/continent/depth) every entry/level-change. Five
  passes over DNG_TEMPLATE ($A619, 11x11). DNG_MAP lives in BSS at
  $B099, past the file end. Cell = high nibble monster slot, low nibble
  feature.
- Cell-feature codes: 0 open, 1 wall, 2 trapdoor, 3 secret door,
  4 door, 5 chest, 6 coffin, 7 ladder down, 8 ladder up, 9 revealed
  trapdoor, $C force field. Solid for movement = 1, 3, and >= $A.
- The view (DNG_DRAW $8982) is a RAY MARCHER: walk VIEW_DEPTH cells
  along facing (DNG_DX/DY), at each slice inspect ahead + the two side
  cells (rotate facing +/-90: left = WORK+(dy,-dx), right = WORK+(-dy,
  dx)), draw, stop when VIEW_BLOCKED. Side cells via CELL_FEAT.
- Perspective is ALL in DNG_GEOM ($9E42, 194 bytes): a packed pool of
  ten-entry columns (depths 1-10) of converging screen coords, indexed
  by VIEW_DEPTH. Kept as ONE labeled blob; the ~12 primitives address
  it by fixed byte offset (DNG_GEOM+$XX,X). Offsets overlap at byte
  granularity (hand-packed) -- do not try to split into clean rows.
  dasm assembles `LDA DNG_GEOM+$54,X` to the right absolute address;
  validated.
- Drawing primitives (all read DNG_GEOM by depth, stroke with
  LINE_AGAIN at ZP $06/$07 start, $08/$09 end): DRAW_COFFIN ($9F04, the
  full 3D box), DRAW_LADDER_SHAFT/_DN/_UP, DRAW_FIELD (red),
  DRAW_OPEN_L/R (+AHEAD_FEAT peek), DRAW_WALL_L/R, DRAW_AHEAD_WALL,
  DRAW_AHEAD_OPEN, DRAW_DOOR_L/R, GLYPH_AT trampoline.
- SHAPE_DRAW ($A449): scaled vector-stroke interpreter. Shapes =
  (x,y,flag) vertex TRIPLES (x rel to centre $80, y rel to baseline,
  flag 0=move/nonzero=draw); (0,0,*) terminates. Scaled down by depth
  halvings via sign-preserving ROR (SHAPE_SCALE_BYTE). Shape pointer is
  self-modified into the fetch LDA (disk's stale $FFFF operand =
  SHAPE_PTR). MON_SHAPES ($A692) = 25-word offset table (offsets from
  $A692) + stroke blob. Renderer: .claude/scripts/render_dng_shapes.py
  -> images/dng_monster_shapes.png.
- Monsters: SIX fixed slots (not OUT's 80 records). Approach via the
  integer-sqrt distance root MON_DIST.
- Sentinels in the view: MON_BASE+slot == $1E/$20/$29 are chest/coffin
  placeholders, not real monsters (no shape, no blocking).
