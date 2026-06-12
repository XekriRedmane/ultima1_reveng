# TODO

This file is the **loop state** for the autonomous RE process (see the
"Autonomy protocol" in `reveng.md`). Milestone entries at the top record
what each round finished and learned; the open work queue, structural
items, and blocked list live at the bottom. Every round updates this
file before committing. A fresh session resumes from `/re-status` output
plus this file — never by re-deriving history.

## Milestones

### Round 8 (2026-06-12): MI.U1 engine code complete ($841E-$89BC)

- The high stub is GONE -- all engine code $8037-$89BC annotated:
  POPUP_FRAME (blue LINE_TO rectangle on the visible page),
  READY_CMD (S/W/A dispatch; proves $7E79=readied SPELL, $7E7A=
  weapon, $7E7B=armour -- round-7 names corrected), MENU_PICK
  (generic picker: 5 inline arg bytes = count, owned-array ptr,
  name-table ptr; letters track item indexes; item 0 always
  allowed), INVENTORY (level = exp/1000+1 recomputed, coin purse =
  one 16-bit number shown as pence/silver/gold = ones/tens/over-
  100), COL_ADVANCE/ITEM_LINE (two-column dot-leader lines; name
  table = caller's inline word consumed by STR_NTH_CAP through the
  stack; $1B marker = readied), POPUP_END/PRESS_SPACE, PRINT_NAME,
  SOUND/SFX_TOGGLE (mirrored to $7E71/72 for the save file),
  DEATH (death image = 10x94 bytes at MIU1_TABLES $7003; render
  it when carving masks), RESPAWN/GAME_LOAD (LOC_NAME $7E16 table
  "GEN/OUT/DNG/TWN/CAS/SPA/TM" at 4-byte offsets; A=offset; A=0 ->
  GEN/new game; death -> A=4 = OUT; loads land AT OVERLAY_ENTRY),
  QUIT + OVERLAY_ENTRY bootstrap (saves ProDOS reset vector INTO
  QUIT's JMP operand; hooks Reset; loads STUPH; the final
  GAME_LOAD(0) overwrites the bootstrap itself with GEN and jumps
  back into $8956).
- Low-stub layout pinned: $7DCC disk prompt entry, $7E05
  PAGE1_LOCK, $7E16 location-name table, $7E31 win-save, full
  player state block to ~$7EFF (PLR_NAME "Glinda" default at
  $7EB8). String table entry points EQU'd (STR_RACES $73AF,
  STR_WEAPONS $73C8, STR_SPELLS $74D4, STR_STATS $748E,
  STR_ARMOUR $7520, STR_CLASSES $755D, STR_TRANSPORT $757C,
  STR_ITEMS $7687, STR_COMMANDS $75CB).
- PDF 474 pages; 12 ORG stubs left (miu1 masks/strings/low-stub +
  7 overlays + makeindata + tcmaps).

### Round 7 (2026-06-12): MI.U1 engine core services ($8144-$841D)

- High stub front carved into 12 annotated chunks, byte-perfect on
  first assembly: CHAR_REPEAT, DRAW_SCREEN/DRAW_BORDERS (frame from
  terrain-strip glyphs; divider col 30), BIN2BCD (double-dabble,
  BCD_POW at $8204), PRINT_NUM16/8 + DIGIT_OUT (NUM_ZSTATE/$8248,
  NUM_PAD/$8249 leading-zero padding), DIV10, RND_MOD, KEY_PENDING,
  PAUSE_ABORTABLE, KEY_ALIAS (CR,[ up; / down; ' right; ;,DEL left
  -- ][+ has no up/down arrows), GET_COMMAND (CMD_KEYS table $7E53,
  echo from STR_COMMANDS $75CB, movement names overridable via
  DIR_STR_PTR $7E51, returns X=2*index/C-set on "Huh?"), TICK/
  TICK_HURT (food -= Y BCD hundredths via FOOD_FRAC, 16-bit binary
  PLR_FOOD clamps at 0; moves += A into multi-byte BCD MOVE_CNT;
  hurt entry queues sfx 0; CLC/DC.B $B0/SEC dual-entry trick),
  STATS_DRAW/STATS_VALUES/PRINT_STAT16 (<100 -> inverse video),
  WIN_SAVE/WIN_RESTORE ($7E31), PRINT_WEAPON, CURSOR_TO_TEXT
  (baseline-scanline ink scan), NO_EFFECT_MSG/BEEP_CMD/QUERY_MARK/
  BEEP_HUH, KBD_CLEAR (flushes BOTH queues).
- Player state EQU'd (PLR_HITS/FOOD/EXP/COIN all 16-bit binary;
  display-only BCD conversion). Stats live in the $7Exx block
  inside the low stub -- labels arrive when round 8 carves it.
- High stub now starts at $841E. PDF 453 pages.

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

- [ ] Round 9: carve the MIU1 low stub $7DCE-$8036: DISK_PROMPT
      $7DCC-$7E04 (move the 2 code bytes out of MIU1_STRINGS),
      PAGE1_LOCK $7E05-$7E15, LOC_NAME table $7E16-$7E31ish, then
      the player state block through $8036 (defaults incl. name
      "Glinda", stats, owned arrays -- turn the round-7/8 PLR_*/
      OWNED_*/READY_* EQUs into labels).
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
