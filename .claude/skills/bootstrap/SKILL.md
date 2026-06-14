# bootstrap

Round 0 of a reverse-engineering project: take a raw Apple II `.dsk` image and produce everything the RE loop needs — reference binaries, `targets.json`, and an initialized `main.nw` skeleton.

## Usage

```
/bootstrap [path/to/game.dsk]
```

If no path is given, use the `.dsk` file at the project root (or the one named in `targets.json` if it already exists).

## When this skill applies

Run it when any of these are missing: `targets.json`, the `reference/` directory, or the `<<boot1.asm>>=` collection chunk in `main.nw`. If all three exist and `verify.py` runs green, bootstrap is complete — skip to the normal RE loop.

## Tooling

`'.claude/skills/bootstrap/dsk_tool.py'` — sector dump/extract/search with selectable sector order (`dos33` or `physical`). Run `python3 .claude/skills/bootstrap/dsk_tool.py --help` for subcommands. The disassembler is `.claude/scripts/dasm6502.py --file BIN --base HEX START [END]`.

## Step 1: Extract and disassemble the boot sector

The boot sector is always physical T0 S0, which is at file offset 0 regardless of sector order:

```bash
mkdir -p reference
python3 .claude/skills/bootstrap/dsk_tool.py extract GAME.dsk 0 0 1 reference/boot1.bin --order physical
python3 .claude/scripts/dasm6502.py --file reference/boot1.bin --base 0800 0801
```

Byte 0 of the sector is the sector count the PROM loads; execution starts at $0801. Disassemble and trace it fully. Most Broderbund-era boots fit one of a few shapes: load more of track 0, relocate, jump to a second-stage loader.

If the boot sector is longer than one sector (byte 0 > 1), extract the additional sectors per the PROM's load order and re-extract `reference/boot1.bin` at its true size.

## Step 2: Determine the .dsk sector order

The `.dsk` file stores sectors in some logical order; the game addresses physical sectors. To determine the order: find a multi-sector load in the boot/loader code where consecutive physical sectors go to consecutive memory pages, extract the same range with `--order dos33` and `--order physical`, and see which produces coherent 6502 code across the page boundary (disassemble across the seam; instructions must not be torn). Record the answer in `targets.json` as `dsk_sector_order`.

## Step 3: Trace the boot chain and find the page table

Follow execution from $0801:

1. What does the boot sector load next, and where? Extract that region and disassemble it.
2. Find the second-stage loader's sector-read loop. Identify how it maps (track, sector) to a destination page — usually an indexed table of page numbers ("the page table"). This table is the Rosetta Stone: every reference binary depends on it.
3. Identify which tracks hold persistent code vs. swappable data, what gets relocated where, and the final entry point into game code.

Use `dsk_tool.py search` to locate code/data on disk by byte pattern (e.g. search for the bytes of a routine you know gets relocated).

## Step 4: Build reference binaries

Decide the assembly targets — one per contiguous load region (boot sector, loader, relocated regions, main game code, one level/data set). For each target, write a page-map file (`track sector dest_page` per line, hex) and build the binary:

```bash
python3 .claude/skills/bootstrap/dsk_tool.py extractmap GAME.dsk maps/main.map reference/main.bin
```

Keep the map files in `maps/` and commit them — they document the disk layout and make the reference binaries reproducible. Spot-check each binary: disassemble its entry point and a few interior routines; torn instructions or implausible opcodes mean the page map or sector order is wrong.

## Step 5: Write targets.json

Create the project manifest at the repo root:

```json
{
  "game": "Name (Publisher, Year)",
  "disk_image": "game.dsk",
  "dsk_sector_order": "dos33",
  "nw_source": "main.nw",
  "output_dir": "output",
  "targets": [
    {"name": "boot1", "base": "$0800", "reference": "reference/boot1.bin", "description": "Boot sector (T0S0)"}
  ],
  "site_pregen": []
}
```

Every script in the pipeline (`verify.py`, `reorder_chunks.py`, status tooling) reads this file. `site_pregen` is an optional list of shell commands the gen-html skill runs before weaving (e.g. the `render_*.py` image generators).

## Step 6: Initialize main.nw

Create the skeleton if it doesn't exist (or only contains the template preamble):

- Markdown title (`# Title`) and chapter structure (`# Boot sequence`, `# Loader`, `# Game code`, plus reference chapters for memory map and disk layout). Prose is Markdown; diagrams are Mermaid; there is no LaTeX preamble.
- A disk-layout chapter documenting what Step 3 found: track/sector → memory tables, the page table, persistent vs. swappable regions.
- For each target: a `<<NAME defines>>=` chunk and a `<<NAME.asm>>=` collection chunk (`PROCESSOR 6502` + defines ref).
- The first real code chunk: the fully annotated boot sector from Step 1, following all CLAUDE.md chunk/annotation rules.

## Step 7: Verify and commit

```bash
python3 weave.py main.nw output
cd output && dasm boot1.asm -f3 -oboot1.bin -lboot1.lst -sboot1.sym && cd ..
python3 .claude/skills/assemble/verify.py boot1
```

The boot1 target must be byte-perfect before bootstrap is declared done. Commit `targets.json`, `maps/`, `reference/`, and `main.nw` together with a message describing the boot chain and disk layout findings.

## Update CLAUDE.md

Fill in the project-specific sections of CLAUDE.md: the assembly-targets table, the disk layout description, and the memory map. These sections are per-game; the conventions sections are template-stable.
