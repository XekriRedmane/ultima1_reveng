# TODO

This file is the **loop state** for the autonomous RE process (see the
"Autonomy protocol" in `reveng.md`). Milestone entries at the top record
what each round finished and learned; the open work queue, structural
items, and blocked list live at the bottom. Every round updates this
file before committing. A fresh session resumes from `/re-status` output
plus this file — never by re-deriving history.

## Milestones

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

- [ ] Round 2: `u1intro` (2469 B at $0800) — title/menu. Mostly hi-res
      data up front ($80-heavy), code near $0F23/$0F41 (two JMPs at
      file start). References MAKE.INDATA.
- [ ] Decompose MIU1_CODE ($7DCE-$89BC): find the engine's JSR
      vector table / entry points used by overlays (grep overlay
      stubs for JSR $7xxx/$8xxx operands first — that maps the API).
- [ ] Structure MIU1_STRINGS (name tables, prompts, pathnames) and
      MIU1_TABLES (pixel masks; likely reveal MAPCHARS tile format).
- [ ] Decompose OUT (smallest overlay) as the template for the other
      six; expect MLIB_* ($B7xx) and MIU1 calls everywhere.
- [ ] makeindata (also builds the intro art at $6000+; resolves the
      ART_* semantics and the one TODO-SYM).
- [ ] mapchars/stuph render once the tile blitter fixes the format;
      tcmaps render after mapchars.
- [ ] Synthesis chapters once MI.U1 + first overlay are understood.

## Structural

- Hi-res rendering helper exists (`.claude/scripts/render_hires.py`);
  build per-data-file renderers on it as graphics are uncovered.
- The `aux=$8956` overlays likely share a common calling convention
  into MI.U1 — document the interface table once two overlays are RE'd.

## Blocked

(nothing blocked — when an item resists analysis, record here what was
tried and what evidence would unblock it, then move on)
