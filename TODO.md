# TODO

This file is the **loop state** for the autonomous RE process (see the
"Autonomy protocol" in `reveng.md`). Milestone entries at the top record
what each round finished and learned; the open work queue, structural
items, and blocked list live at the bottom. Every round updates this
file before committing. A fresh session resumes from `/re-status` output
plus this file — never by re-deriving history.

## Milestones

### Round 11 (2026-06-12): OUT scouted; cross-corrections applied

- OUT entry ($8956) read: restores zp $00/$01 from $7E73/74 (now
  labeled PLR_OUT_X/Y), enables double-buffering, copies $6000
  +14 pages to $A900 (buffer above the overlay -- purpose TBD),
  zeroes DIR_STR_PTR hi (default direction names), checks $B600
  flag else JSR $9691 (world/map load?), JSR $94C1 (initial draw),
  death-check, then THE MAIN LOOP at $8995: stack reset, prompt,
  $8A6A (key fetch) -- idle turn = JSR $82E4 with Y=5/A=$50 (food
  5/100, +50 moves?? verify) -- GET_COMMAND -> patched-JSR dispatch
  through the address table at $9AAA (26 entries, X=2*index), then
  $96B0 (end-of-turn/monsters), loop. Death penalty path: lose
  current transport, all weapons/armour/spells zeroed, respawn
  position from $9461.
- Corrections from this evidence: TICK_HURT renamed TICK_SND --
  effect 0 is the per-turn MOVE THUMP, not a damage cue; $7E73/74
  identified as the saved outdoor position.
- Next session: decompose OUT from this skeleton (entry/main loop
  first, then the 26 command handlers via the $9AAA table, then
  $9461/$9691/$94C1/$96B0 world machinery). Then DNG (wireframe
  via PLOT/LINE_TO), then the town/castle pair w/ TCMAPS format.

### Round 10 (2026-06-12): MI.U1 100% decomposed; world census in hand

- The "mask tables" are exactly one picture: the 10x94 death SKULL
  (DEATH_IMG, rendered: images/miu1_death.png).
- MIU1_STRINGS carved into 15 labeled tables: races (lizard/human/
  elf/dwarf/bobbit), weapons long+short (16 each, "hands" at 0),
  stats (10, incl. Gold/Race/Type for chargen), spells (11,
  "Prayer" at 0!), armour (6, "skin" at 0), classes (peasant/
  fighter/cleric/wizard/thief), transport (11: foot..time machine),
  the 26 commands (Pass=space, ctrl-A=Accelerator, HyperJump,
  K-limb, X-it, Ztats...), 4 gems, 46 monsters (6 blank entries
  then sea/land/dungeon sets), 4 CONTINENTS (Lord British/Feudal
  Lords/Dark Unknown/Danger and Despair), and all 84 PLACE names.
- Two unidentified embedded tables flagged: ENGINE_TBL_A ($76A8,
  46 bytes, ascending runs -- costs/limits?) and ENGINE_TBL_B
  ($786F, 168 bytes between continents and places -- per-place
  data?). Expect the overlays to resolve both.
- ORG stubs down to 9 (7 overlays + makeindata + tcmaps).

### Round 9 (2026-06-12): MI.U1 low region carved; EQU stubs = 0

- MIU1_CODE_A is gone: DISK_PROMPT/$7DCC (dual entry, DC.B $2C
  trick, carry = caller's error flag, "Ultima"/"Player" disk
  names), PAGE1_LOCK/$7E05 (end double-buffering with the image
  live on page 1), and the full player state block $7E16-$8036 as
  labeled data: LOC_NAME table, WIN_SAVE_BUF, CAP_FLAG, the
  /U1.PLAYER + /U1.VARS pathnames, TICK params, CMD_KEYS (26:
  arrows, space, ctrl-A, ABCDEFGHIKNOQRSTUVXZ), sound mirrors,
  OWNED_*/READY_* arrays, PLR_NAME..PLR_EXP (shipped snapshot:
  Glinda, female, 900 hits, 2104 coin -- the crack's master save),
  two unidentified $03E8 words + a few flag bytes, 325-byte BSS.
- All round-7/8 state EQUs converted to real labels; CAP_FLAG EQU
  stub resolved -> EQU-stub metric is now ZERO. The 2 stray code
  bytes ($7DCC) moved out of MIU1_STRINGS.
- Remaining ORG stubs: 11 (miu1 masks $7003 + strings $73AF, 7
  overlays, makeindata, tcmaps). PDF 477 pages.

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
