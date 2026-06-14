# Ultima I — Reverse Engineering

A complete, byte-perfect reverse engineering of **Ultima I: The First Age of
Darkness** (Origin Systems, 1986) — the all-assembly remake of Richard
Garriott's 1981 *Ultima* — for the Apple II, recovered from its `.dsk` disk
image into a literate-programming document that:

- assembles to **byte-perfect** copies of every original binary,
- explains how the game works in enough detail to **reproduce or port it in any
  language, on any platform**, and
- weaves into a cross-referenced, searchable **HTML site** with Mermaid
  diagrams and rendered sprites, fonts, and screens.

## 📖 Read it online

**→ [xekriredmane.github.io/ultima1_reveng](https://xekriredmane.github.io/ultima1_reveng/)**

The site is the primary output: a three-pane, searchable rendering of the
annotated 6502 assembly alongside platform-independent design chapters for
porters. It is rebuilt and republished automatically from `main.nw` on every
push to `main` (see `.github/workflows/pages.yml`).

## The subject

The game is the 4am crack preservation release: a ProDOS 1.1.1 volume named
`/U1` containing the unmodified game files. The player explores Sosaria across
six play modes — outdoors, towns, castles, 3-D dungeons, space flight, and the
time-machine endgame — each implemented as a separate overlay loaded at
`$8956` over a memory-resident engine (`MI.U1` at `$7000`).

| | |
|---|---|
| Title | Ultima I: The First Age of Darkness |
| Publisher | Origin Systems, 1986 (remake of California Pacific's 1981 *Ultima*) |
| Platform | Apple II |
| Disk | 4am crack — DOS-order `.dsk`, ProDOS 1.1.1 volume `/U1` |
| Code | Entirely 6502 assembly |

## Assembly targets

16 targets, one per ProDOS file (plus the boot block); every one assembles to
a byte-perfect match against the reference binary extracted from the disk.

| Target | Base | Bytes | Contents |
|---|---|---|---|
| `boot1` | `$0800` | 512 | ProDOS boot block |
| `u1system` | `$2000` | 1682 | `U1.SYSTEM` — launcher |
| `u1intro` | `$0800` | 2469 | `U1.INTRO` — title and main menu |
| `miu1` | `$7000` | 6589 | `MI.U1` — resident engine |
| `out` | `$8956` | 5230 | outdoors overlay |
| `twn` | `$8956` | 8461 | town overlay |
| `cas` | `$8956` | 5524 | castle overlay |
| `dng` | `$8956` | 10051 | dungeon overlay |
| `spa` | `$8956` | 9930 | space overlay |
| `gen` | `$8956` | 8932 | character generation overlay |
| `tm` | `$8956` | 8123 | time machine (endgame) overlay |
| `makeindata` | `$1E00` | 13877 | initial game-state builder |
| `mapchars` | `$0800` | 1024 | town/castle glyph bank |
| `tcmaps` | `$4000` | 7660 | town/castle map data |
| `nif` | `$4000` | 7680 | hi-res image data |
| `stuph` | `$0800` | 6144 | resident low-memory library: fonts, tiles, blitters, keyboard, sound, RNG |

The ProDOS 1.1.1 kernel is byte-identical to Apple's 18-SEP-84 release; it is
extracted for inspection but treated as an external dependency, not an RE
target.

## How it's built

`main.nw` is the single source of truth — Markdown documentation interleaved
with 6502 assembly code chunks in noweb format. Two backends consume it:

```bash
# Tangle the literate source to .asm, assemble, and verify byte-for-byte
python3 weave.py main.nw output
cd output && dasm NAME.asm -f3 -oNAME.bin -lNAME.lst -sNAME.sym
python3 .claude/skills/assemble/verify.py        # all 16 targets

# Weave the human-readable HTML site into output_site/
python3 weave_html.py main.nw output_site
```

The HTML site needs only Python plus `mistune` (`pip install mistune absl-py`);
KaTeX, Mermaid, and MiniSearch load from a CDN, so the published site is
self-contained static HTML. `weave.py` is the byte-perfect tangler and
chunk-graph engine; `weave_html.py` reuses it unchanged and replaces only the
output backend.

## Repository layout

| Path | Purpose |
|---|---|
| `main.nw` | The literate document — the single source of truth |
| `weave.py` | Noweb tangler and chunk-graph engine (byte-perfect `.asm`) |
| `weave_html.py`, `web/` | HTML weaver and its CSS/JS assets |
| `targets.json` | Project manifest: game, disk image, sector order, assembly targets |
| `reference/` | Flat binaries extracted from the disk image (the ground truth) |
| `images/` | Rendered sprites, fonts, and screens, embedded in the document |
| `reveng.md` | The RE process: rounds, standing rules, definition of done |
| `CLAUDE.md` | Conventions: assembly style, chunk rules, annotation and prose rules |
| `.claude/skills/`, `.claude/scripts/` | The RE toolchain (assemble, disassemble, render, status) |
| `output/`, `output_site/` | Build artifacts — tangled `.asm`/`.bin` and the woven site (gitignored) |

## Method

The work was carried out with Claude Code running an autonomous
`reverse-engineer` agent: it bootstrapped reference binaries from the disk
image, reverse engineered the boot chain, loader, engine, overlays, and data,
rendered the graphics, and wrote platform-independent design chapters —
committing after every verified round. The process and conventions are
documented in `reveng.md` and `CLAUDE.md`.

## Legal

This repository contains original analysis, annotations, and prose. It does
**not** redistribute the game; reproducing the work requires a legally obtained
copy of the disk image. *Ultima* is a trademark of its respective rights
holders; this is an independent preservation and educational study.
