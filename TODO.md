# TODO

This file is the **loop state** for the autonomous RE process (see the
"Autonomy protocol" in `reveng.md`). Milestone entries at the top record
what each round finished and learned; the open work queue, structural
items, and blocked list live at the bottom. Every round updates this
file before committing. A fresh session resumes from `/re-status` output
plus this file — never by re-deriving history.

## Milestones

### Round 6 (2026-06-12): STUPH = the resident library, fully RE'd

- STUPH is NOT shape data: it is the resident low-memory library at
  $0800-$1FFF with a 34-entry JMP vector API at $1583-$15E9. All of
  it is now annotated and byte-perfect; fonts and tiles rendered
  (images/stuph_font.png, stuph_tiles.png, mapchars_font.png;
  renderer .claude/scripts/render_font.py).
- Glyph formats: bank A = 128 glyphs x 8 scanlines, plane-major
  (scanline s of glyph g at $0800+s*$80+g); chars $00-$19 are
  pre-shifted even/odd pairs; $7C-$7F = cursor frames. Bank B =
  96 glyphs x 16 scanlines at $0C00+s*$60+g = 48 outdoor map tiles
  (2 glyphs wide). MAPCHARS = alternate bank A for towns/castles
  (walls + inverse shop-sign letters; TCMAPS cells embed ASCII).
- DRAW_MAP ($15B3): 19x9 tile viewport centered on player at zp
  $00/$01, map = 64x64 bytes at $6000; cell AND #$7E -> glyph pair
  (c,c+1); codes $20-$58 are creatures w/ random 2-frame wobble;
  PLAYER_TILE at $1582. Tile animation = plane-byte rotation/swaps.
- Double buffering: $7F = draw-page XOR ($00/$60), $80 = toggle
  mask; text writes BOTH pages; $7E = inverse-video EOR mask.
- Input: 4-key typeahead $74-$77/$78 (space flushes); sound-effect
  queue $79-$7C/$7D drained at PAGE_FLIP; 9 speaker effects.
- FILE_LOAD ($1589/$158C): BLOADs via MLIB with transparent /RAM
  caching on 128K machines (BSAVEs a shadow copy, retries /RAM
  first). RND = 16-byte lagged additive generator, re-seeded by
  cursor-flash timing.
- Machine layer: AppleMouse card used ONLY as a VBL interrupt
  source (SETMOUSE mode 8); $C019 polling on enhanced IIe/IIgs;
  IIgs CYAREG speed control; DRIVE_OFF reads as accelerator nudge.
- miu1 now carries the full 35-name vector EQU list; LOW_1598 ->
  CLR_EOL. Engine rounds can use real names everywhere.
- PDF 433 pages. Hygiene: 1 EQU stub (CAP_FLAG), 13 ORG stubs,
  1 TODO-SYM (intro art, resolves with makeindata).

### Round 5 (2026-06-12): MI.U1 text-output cluster decomposed

- Overlay->engine call census (all 7 overlays): 147 distinct targets;
  top: $8119 (349 calls), $8062 (50), $80B8 (45), $8115 (33), $8254
  (27), $83A9/$83B4/$8407/$820D/$826C/$8207... ($73xx/$74xx hits are
  false positives — '$20'=space inside text). The $80xx-$84xx band is
  the engine API.
- Decomposed $8037-$8143: MSG_PRINT/MSG_AT (inline zero-terminated
  text, $7F=tab), STR_NTH/STR_FIRST/STR_NTH_CAP (packed string tables,
  last char high-bit-set, X = index, inline table pointer), PRINT_HEX,
  PUTCH (layout codes: |=newline, ~=NL+col1, }=conditional NL+col1),
  NEWLINE/CR/WIN_SHRINK. Text renders via low-RAM helpers $1592/$1598/
  $15B0 (FONT_DRAW etc., installed by MAKE.INDATA — EQU stubs).
- Next decomposition targets, by call count: $8062 group done; next
  $8254, $83A9, $83B4, $8407, $820D, $8207, $826C, $840F, $836E.

### Round 4 (2026-06-12): all 16 targets byte-perfect (stub bootstrap)

- miu1 bootstrapped: MIU1_ENTRY (JMP OVERLAY_ENTRY at $8956) + three
  classified stubs (mask tables $7003-$73AE, ~2.6K string region
  $73AF-$7DCD, engine code $7DCE-$89BC).
- All remaining targets (7 overlays, makeindata, mapchars, tcmaps,
  stuph) emitted as single STUB chunks — **every target now verifies
  100% byte-perfect**; remaining work is measured by the 14 ORG stub
  chunks. The loop from here: /re-next style stub decomposition,
  starting with MIU1_CODE (the engine: every overlay JSRs into it),
  then MIU1_STRINGS structuring, then OUT as the first overlay.
- PDF 373 pages (stub HEX is transitional bulk; shrinks as stubs are
  replaced with annotated code).

### Round 3 (2026-06-12): NIF byte-perfect, rendered

- `nif` 7680/7680 with rendered figure: it is the **endgame victory
  screen** ("FIN" reversed) — calligraphic text about Mondain's death.
  Format: line-sequential raster, 192 rows x 40 bytes, no interleave,
  no screen holes. Renderer: .claude/scripts/render_nif.py.
- MAPCHARS render attempted (2x8/2x16/1x8/1x16, row+column major) —
  no hypothesis produced clearly-right tiles; deferred per the
  don't-ship-broken-renders rule until the tile blitter in MI.U1/OUT
  reveals the record format. Same for STUPH.

### Round 2 (2026-06-12): U1.INTRO byte-perfect

- `u1intro` 2469/2469. The file is the attract-mode title animation:
  castle drawn in self-modified strip blits, score-driven flashes,
  pennant flutter, star twinkle, bird, banner, sky wipe + curtain,
  then a 16-bit-LFSR fizzle dissolve of the page-2 title image. Any
  key BRUNs MI.U1; 'K'/ctrl-@ set mailbox $03CE (INTRO_FLAG) to 4/$10
  enabling banner/bird; ESC pauses.
- Cold start BRUNs MAKE.INDATA, which **builds the intro artwork at
  $6000-$8Fxx** (ART_* EQUs named per consumer; semantics + the one
  TODO-SYM resolve when makeindata is RE'd). INTRO_FLAG is also read
  with values 8/$0C — likely set elsewhere; watch for it in MI.U1 /
  MAKE.INDATA.
- RORG technique proven for relocated code (u1system $0100/$B700).

### Round 1 (2026-06-12): U1.SYSTEM byte-perfect

- `u1system` 1682/1682, all hygiene metrics zero, PDF 70 pages.
- U1.SYSTEM is a standard-form ProDOS system program (startup-path
  buffer at $2004, default `U1.INTRO`): banner, then installs a
  **resident MLI file library at $B700-$BAFF** (documented in full:
  20 vectors — BLOAD/BLOAD_AT/BSAVE/BRUN/SET_PREFIX/DESTROY/QUIT/
  READ_BLOCK/WRITE_BLOCK/raw MLI — JSR-plus-inline-args convention,
  text vs pointer path variants, error translation table, parameter
  blocks in page $BA, file buffer $BB00-$BEFF). **The game's whole
  disk interface goes through these $B7xx vectors** — expect MI.U1
  and overlays to JSR $B7xx everywhere; symbol names MLIB_* are
  ready for propagation.
- Page-one helpers at $0100-$016E survive overlay loads: inline
  print, reset trampoline, BRUN-the-startup-file + startup error
  display.
- `git push` FAILS in this container (https remote, no credentials).
  Commits are local; push from a credentialed environment.

### Round 0 (2026-06-12): Bootstrap complete

- Identified the game: **Ultima I: The First Age of Darkness** (Origin
  Systems, 1986 assembly remake; 4am crack). The disk is a ProDOS 1.1.1
  volume `/U1` in a DOS-order `.dsk` — no custom RWTS, all game data in
  ordinary ProDOS files.
- Wrote `.claude/scripts/prodos_extract.py` (ProDOS filesystem reader);
  extracted all 16 reference binaries plus the stock kernel
  (`reference/prodos111.bin`, verified "PRODOS 1.1.1 18-SEP-84
  COPYRIGHT APPLE" — excluded from RE targets as an OS dependency).
- Wrote `targets.json` (16 targets), filled all CLAUDE.md bootstrap
  sections (targets table, disk layout, memory map).
- `main.nw`: intro chapter, disk-layout chapter (sector-order math,
  volume file table), and the **boot block fully annotated and
  byte-perfect** (512/512) — entry/controller detection, PROM code
  relocation+patching trick, directory scan, sapling-file kernel load,
  Disk II seek/read with the overlapped timeout/nibble-search loop.
- PDF builds cleanly (37 pages).

## Work queue

- [ ] Decompose MIU1_CODE high stub ($8144-$89BC) — already scouted
      in round 6's disassembly pass: CHAR_REPEAT/DRAW_BORDERS $8144,
      BIN2BCD $81AD (+BCD pow table $8204), PRINT_NUM16/8 $8207/
      $820D (pad state $8248/9), DIV10 $824A, RND_MOD $8254, key
      helpers $8266/$826C, KEY_ALIAS $827D (CR/[//';/DEL -> arrow
      codes), GET_COMMAND $82A2 (26-key table at $7E53, names from
      string table $75CB, returns X=2*index), TICK/damage $82E2/4
      (BCD food frac $7EE4, food $7EE5/6, move counter $7EDA+),
      status panel $8331/$836E (Hits $7EC6/7, Food $7EE5/6, Exp
      $7EE7/8, Coin $7ED4/5; <100 -> inverse flash via $7E),
      WIN_SAVE/RESTORE $83B4/$83A9 (6 bytes <-> $7E31), cursor/'?'
      feedback $83C8/$8407/$840F, KBD_CLEAR $8414, popup window +
      lines $841E, R-eady cmd $8466 (S/W/A -> $7E79/7A/7B),
      generic menu picker $84DF (inline args), inventory display
      $85A2-$87F9 (item lists at $7E75/7D/83/93/9E, name tables
      $73AF/$74D4/$75CB...), press-space $87FA, player name $7EB8,
      sound toggles $8845/$885B, death $8870 (death image is in
      MIU1_MASKS at $7003!), respawn $88F8 (loads GEN), QUIT $893F,
      OVERLAY_ENTRY $8956 (BLOADs STUPH at $8978 + overlay by name
      from table $8016).
- [ ] Decompose MIU1 low stub $7DCE-$8036: disk-prompt routine
      $7DCC (!! the last 2 bytes of MIU1_STRINGS chunk are code --
      move the boundary), page-show $8005, overlay name table
      $8016 ("GEN/OUT/DNG/TWN/CAS/SPA/TM"), bytes $8032-$8036.
- [ ] Structure MIU1_STRINGS ($73AF-$7DCD): string tables at $73AF,
      $74D4 (weapons), $75CB (command names)... X-indexed,
      high-bit-terminated; map them via STR_NTH inline pointers.
- [ ] MIU1_MASKS $7003-$73AE: contains the death-screen bitmap
      ($7003, read by $8870 via row tables) — render it.
- [ ] Decompose OUT (smallest overlay) as the template; expect
      heavy VEC_* ($15xx) and engine ($80xx-$84xx) calls.
- [ ] makeindata (builds intro art at $6000+; resolves ART_*
      semantics and the one TODO-SYM). Lower priority now that
      STUPH covered the low-RAM helpers.
- [ ] tcmaps: structure as town/castle maps (cell codes = MAPCHARS
      glyphs; "FOOD" visible in bytes). Render with mapchars bank.
- [ ] Synthesis chapters once MI.U1 + first overlay are understood.

## Structural

- Hi-res rendering helper exists (`.claude/scripts/render_hires.py`);
  build per-data-file renderers on it as graphics are uncovered.
- The `aux=$8956` overlays likely share a common calling convention
  into MI.U1 — document the interface table once two overlays are RE'd.

## Blocked

(nothing blocked — when an item resists analysis, record here what was
tried and what evidence would unblock it, then move on)
