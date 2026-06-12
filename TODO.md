# TODO

This file is the **loop state** for the autonomous RE process (see the
"Autonomy protocol" in `reveng.md`). Milestone entries at the top record
what each round finished and learned; the open work queue, structural
items, and blocked list live at the bottom. Every round updates this
file before committing. A fresh session resumes from `/re-status` output
plus this file — never by re-deriving history.

## Milestones

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

- [x] Round 1: u1system — DONE.
      Contains "The First Age of Darkness" banner, startup error
      handler, jump table at $2922+. Finds/loads U1.INTRO via MLI.
- [ ] Round 2: `u1intro` (2469 B at $0800) — title/menu. Mostly hi-res
      data up front ($80-heavy), code near $0F23/$0F41 (two JMPs at
      file start). References MAKE.INDATA.
- [ ] Round 3+: `miu1` resident engine (6589 B at $7000) — the Rosetta
      stone: entry `JMP $8956`, item/monster/place name tables, status
      line, player-disk I/O (`/U1.PLAYER`, `/U1.VARS`). RE before the
      overlays.
- [ ] Overlays in order of size/value: out, cas, twn, gen, dng, spa, tm.
- [ ] makeindata (initial game state builder at $1E00).
- [ ] Data targets with graphics rendering (standing rule): mapchars
      (tiles, likely 1024 B = shapes), stuph (shapes), nif (hi-res
      image — render early, probably the title picture), tcmaps (maps —
      render as map images; contains shop-sign text like "ARMOUR").
- [ ] Synthesis chapters once MI.U1 + first overlay are understood.

## Structural

- Hi-res rendering helper exists (`.claude/scripts/render_hires.py`);
  build per-data-file renderers on it as graphics are uncovered.
- The `aux=$8956` overlays likely share a common calling convention
  into MI.U1 — document the interface table once two overlays are RE'd.

## Blocked

(nothing blocked — when an item resists analysis, record here what was
tried and what evidence would unblock it, then move on)
