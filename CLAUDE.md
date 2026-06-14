# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Reverse engineering of an Apple II game from a `.dsk` disk image. The project uses literate programming (noweb format) to produce annotated 6502 assembly that assembles to byte-perfect matches against the original disk image.

The game is **Ultima I: The First Age of Darkness** (Origin Systems, 1986) — the all-assembly remake of Richard Garriott's 1981 *Ultima*. The disk is the 4am crack preservation release: a ProDOS 1.1.1 volume named `/U1` containing the unmodified game files. The player explores Sosaria across six play modes (outdoors, towns, castles, 3-D dungeons, space flight, time-machine endgame), each implemented as a separate overlay file loaded at `$8956` over a memory-resident engine (`MI.U1` at `$7000`).

**Audience and goal.** The reader of `main.nw` wants to learn how the game was written and how it works, in enough detail to reproduce or port the game in any language on any platform — not just 6502 assembly on the Apple II. Byte-perfect annotated assembly is the evidence base; the document is not done until the design has also been recovered into platform-independent prose (see the `/synthesize` skill and `reveng.md`).

**Project manifest.** `targets.json` at the repo root defines the game, disk image, and all assembly targets (name, base address, reference binary). It is created by the `/bootstrap` skill during Round 0. Pipeline scripts (`verify.py`, `reorder_chunks.py`, `status.py`) and skills read it — keep it current when targets change. The end-to-end RE process and autonomy rules live in `reveng.md`.

## Build pipeline

```bash
# Tangle: extract assembly files from literate source
python3 weave.py main.nw output

# Assemble each target listed in targets.json (from output/)
cd output
dasm NAME.asm -f3 -oNAME.bin -lNAME.lst -sNAME.sym

# Verify against reference binaries (from project root)
python3 .claude/skills/assemble/verify.py          # all targets
python3 .claude/skills/assemble/verify.py NAME     # one target

# Disassemble a region from a reference binary
python3 .claude/scripts/dasm6502.py --file reference/NAME.bin --base XXXX START [END]

# Weave the human-readable HTML site (also tangles, via the same tangler)
python3 weave_html.py main.nw output_site
```

Skill: `/assemble` runs the full tangle+build+verify pipeline. `/gen-html` builds the HTML site into `output_site/`. `/re-status` prints the project scoreboard.

The document output is **HTML** (`weave_html.py`), not PDF. The LaTeX/`pdflatex` pipeline has been retired; `weave.py` is kept as the tangler and chunk-graph engine that `weave_html.py` reuses unchanged.

## Assembly targets

The 16 assembly targets mirror `targets.json` — one per ProDOS file (plus the boot block). All produce `output/NAME.bin` verified against `reference/NAME.bin`.

| Target | Base | Bytes | Contents |
|---|---|---|---|
| `boot1` | `$0800` | 512 | ProDOS boot block (T0 phys S0+S2) |
| `u1system` | `$2000` | 1682 | `U1.SYSTEM` — launcher (SYS) |
| `u1intro` | `$0800` | 2469 | `U1.INTRO` — title and main menu |
| `miu1` | `$7000` | 6589 | `MI.U1` — resident engine |
| `out` | `$8956` | 5230 | outdoors overlay |
| `twn` | `$8956` | 8461 | town overlay |
| `cas` | `$8956` | 5524 | castle overlay |
| `dng` | `$8956` | 10051 | dungeon overlay |
| `spa` | `$8956` | 9930 | space overlay |
| `gen` | `$8956` | 8932 | character generation overlay |
| `tm` | `$8956` | 8123 | time machine (endgame) overlay |
| `makeindata` | `$1E00` | 13877 | initial game state builder |
| `mapchars` | `$0800` | 1024 | town/castle glyph bank (alternate font bank A) |
| `tcmaps` | `$4000` | 7660 | town/castle map data |
| `nif` | `$4000` | 7680 | hi-res image data |
| `stuph` | `$0800` | 6144 | resident low-memory library: fonts, tiles, blitters, keyboard, sound, RNG ($1583 vector API) |

The ProDOS 1.1.1 kernel (file `PRODOS`, byte-identical to Apple's 18-SEP-84 release) is extracted as `reference/prodos111.bin` for inspection but is **not** an RE target — it is treated as an external dependency like the monitor ROM.

## Architecture: main.nw

`main.nw` is the single source of truth. It contains **Markdown** documentation interleaved with 6502 assembly code chunks. `weave.py` tangles it to produce `.asm` files; `weave_html.py` weaves it to a multi-page HTML site (`output_site/`). The chunk syntax (`<<name>>=`, `@`/`@ %def`) is unchanged noweb; only the prose/output is Markdown/HTML rather than LaTeX/PDF. See `html-migration-design.md` for the format spec.

### Assembly file structure

Each `.asm` file is built from named chunks. A collection chunk at the end of the chapter assembles them in address order:

```noweb
<<boot1.asm>>=
        PROCESSOR 6502
<<boot1 defines>>
<<boot1 entry>>
...
```

Individual routine chunks are named after their subroutine (e.g., `<<scroll up>>`). EQU definitions go in a `<<xxx defines>>` chunk referenced at the top of the collection.

### Chunk conventions

- Each `\section{}` gets its own code chunk with the routine's assembly.
- Section headers never contain numeric addresses.
- Chunk names are lowercase with spaces (e.g., `<<boot1 entry>>`).
- End chunks with `@ %def SYMBOL1 SYMBOL2` to declare exported symbols.
- `<<filename.asm>>=` chunks produce output files when tangled.
- Every data and code chunk must start with an `ORG` directive (hex literal, never a symbol).
- After every `ORG`, there must be a label. If unreferenced, investigate as potential dead code.

### Chunk placement rules

- Data chunks with labels go immediately before the first code chunk that references the label.
- EQU definitions go just before the chunk that first uses them, with prose explaining purpose.
- Chunk references in the collection chunk follow ascending ORG address order.
- After adding a chunk, run `python .claude/skills/chunk-placement/check_placement.py` to verify.

### Code chunk rules

- Replace raw hex addresses to code with labels in the code: `JSR $XXXX` and `JMP $XXXX` must use labels.
- Replace raw hex addresses to data that is not in zero-page with labels for the data: `LDA $XXXX` / `STA $XXXX`, especially when indexed, e.g. `LDA $XXXX,X` or `LDA ($XXXX),Y`. If the address is a zero-page address, then use
a symbolic name with EQU.
- If a label is not known in the reverse-engineered code or data yet, then it may be given a symbolic name with
an EQU until such time as the code or data is reverse-engineered. For addresses in ROM, an EQU may be used.
- If an immediate value is known to be a label, then use the label.
- If an immediate value is known to be the low or high value of the label, then use `#<label` or `#>label`.
- If an immediate value is known to be an offset into a record, then create a symbolic name for the offset
with an EQU and use the symbolic name.
- For 16-bit data addresses, only create a label for the first address. Use label+1 for the second address.

### Chunk annotation

Every routine with a `SUBROUTINE` directive must have a **header plate** comment block immediately after `SUBROUTINE`:

```asm
ROUTINE_LABEL:
        SUBROUTINE
        ; Brief one-line description of what the routine does.
        ;
        ; Inputs:
        ;   LABEL1  — what it means and how the routine uses it
        ;   LABEL2  — ...
        ;
        ; Behavior:
        ;   2-4 lines summarizing the algorithm or control flow.
        ;
        ; Outputs:  (if applicable)
        ;   What registers or memory locations hold results on return.
        ;
        ; Modifies:
        ;   List of memory locations written (EQU names, not raw addresses).
        ; Clobbers: A, X, Y  (whichever apply)
```

Omit the Outputs section if the routine doesn't return meaningful values (e.g., ends with `JMP`). Omit Modifies if only registers are affected.

Additional annotation rules:
- Comment the **purpose**, not the mechanics: "extract location tier" not "rotate left 4 times".
- **Don't restate the instruction.** `LDA TABLE,Y ; TABLE[Y]` and `STA ZP_SPRITE_Y ; ZP_SPRITE_Y` both carry zero information — the reader already sees the operand. A restating comment should be deleted. If the instruction's purpose is non-obvious, replace with an actual explanation (`; direction: $FF=left, $01=right`, `; row within band`). If the purpose is obvious from the symbol, no comment at all.
- **Assignment comments: use `<-` and `#$` for values.** `STA ZP_SPRITE_H ; $57 = $1C` has two problems — `$57` is an address where a symbol exists (should be `ZP_SPRITE_H`), and `$1C` is a value being stored, not an address (should be `#$1C`). Correct form: `STA ZP_SPRITE_H ; ZP_SPRITE_H <- #$1C`. Use `<-` for the assignment direction (makes destination/source unambiguous), `#$` to prefix numeric values, and plain hex (or a symbol) for memory references. This mirrors the 6502 immediate-vs-absolute distinction `LDA #$1C` (value) vs `LDA $1C` (zero-page read) — the `#$` keeps the comment unambiguous about which is which.
- **Numeric addresses in comments must serve a purpose beyond identification.** The rule applies to addresses of any width — 2-digit zero-page (`$5B`), 3-digit (`$1FF`), 4-digit (`$629E`). A raw `$XX…` in a comment is wrong when it is either (a) the instruction's own assembled address, which the `.lst` file already carries; or (b) the address of a symbol that exists, in which case use the symbol; or (c) a **compiled branch target**, which the programmer never knew in numeric form — use the local label or drop the address if the behavioral description is enough. Bare `; $XX…` comments that carry no other information get removed entirely. Addresses may remain in comments when they are something the reader actually needs to know in numeric form — an unlabeled address not yet RE'd (flag with a `TODO-SYM` note), a memory-region span described literally, an opcode byte value, etc.
- **In comments, refer to indexed tables by `SYMBOL[Y]` notation, never `$XXXX,Y` or `SYMBOL,Y`.** The `,Y` form mimics the instruction syntax on the same line. Write `LDA FOO,Y ; FOO[Y] -> ptr` instead (or simply `; load pointer by frame index` if the mechanic is what matters). The `[Y]` bracket form is unambiguously prose, not asm.
- **Code comments are ASCII-only: no LaTeX commands, no Unicode.** Noweb copies code-chunk content verbatim into the PDF via `\Tt{}`, which means `\Delta`, `\to`, `\ge`, `\S{...}` etc. render as literal backslash-text, and non-ASCII characters like `—` (em-dash), `→`, `≥`, `Δ` render as literal glyphs only if the font has them. Use ASCII equivalents: `delta`, `->`, `>=`, `<-`, `<=`, `<->`, `*`, `+/-`, `--`. LaTeX-escaped address forms like `\$XXXX` are also wrong inside code comments — write `$XXXX` (assembly syntax; dasm ignores everything after `;`). LaTeX commands *are* fine in prose/documentation chunks.
- Use `; --- section name ---` headers between logical phases within a long routine.
- Align all `;` comments to the same column within each routine.
- Routines without `SUBROUTINE` (simple trampolines like `JMP target`) get a one-line `;` comment above instead of a full plate.

The `/annotate` skill automates these passes for an existing routine.

## Assembly style and rules

### Labels and naming

- All routine labels must be `UPPER_SNAKE_CASE` (e.g., `BOOT1_ENTRY`).
- Local labels: `.local_name` within `SUBROUTINE` scope.
- EQU constants: `UPPER_SNAKE_CASE` with descriptive comment.
- Zero-page aliasing: define multiple EQU names for the same address when used for different purposes; use the contextually appropriate name at each reference.
- Align all `;` comments to the same column within each chunk/subroutine.

### Label hygiene

- Before creating a label, search for existing EQUs at that address. If one exists, keep the label and remove the EQU.
- After documenting a routine, grep `main.nw` for raw hex references (`JSR $XXXX`, `JMP $XXXX`) and replace with the new label name. When replacing, skip lines containing `EQU` and `%def` to avoid circular definitions.
- Never use EQU stubs for routines — create an ORG stub chunk with `; STUB — not yet disassembled` instead.
- Before doing `replace_all` on a label, verify one instance first. Assemble and binary-compare before applying globally.
- Watch for prefix collisions when renaming (use word-boundary regex).

### dasm specifics

- `SUBROUTINE` after each `ORG` to scope `.local` labels.
- ORG directives must be in strictly ascending address order. Use `python .claude/skills/assemble/reorder_chunks.py` to fix.
- Accumulator addressing: use bare `ASL`/`LSR`/`ROL`/`ROR`, not `ASL A`.
- `HEX` directives: at most 8 bytes per line. Longer rows overflow the PDF column and wrap awkwardly. Break any hex blob into 8-byte lines; put the inline comment (if any) on the first line only.
- Use `-f3` for raw binary output (not `-f1` which adds a 2-byte header).
- Always produce `.lst` and `.sym` files when assembling.
- Force absolute addressing when dasm optimizes to zero-page: `DC.B $9D,$00,$00` for `STA $0000,X`.
- BIT-abs skip trick for multi-entry points: `DC.B $2C` before `LDA #imm`.
- Self-modifying code: `label = *+1` or `label = *+2` to name the patched operand byte. For indexed self-modification (`STA base,X`), calculate: base = effective\_addr - X.
- NMOS 6502 has no `STZ` instruction.

### Noweb / Markdown

- The chunk syntax is unchanged noweb: `<<name>>=` opens a code chunk; a bare `@` or `@ %def …` line opens a doc chunk. Prose inside doc chunks is **Markdown**.
- Do not escape underscores or dollar signs inside `[[ ]]` refs. Write `[[$4000]]` and `[[GAME_INIT]]`, not `[[\$4000]]` or `[[GAME\_INIT]]` — `[[ ]]` content is literal code that the weaver escapes for HTML automatically; an author-written `\` renders as a visible backslash.
- Never put `<<chunk>>` inside assembly comments — the tangler expands them.
- `@ %def` must not have duplicate identifiers across chunks.
- **Diagrams are Mermaid** — author them as ```mermaid fenced blocks, followed by a `**Figure — …**` caption paragraph. Use the shared visual language: accent stroke `#b03a2e` (via `linkStyle`/`classDef fill:#f6dccb,stroke:#b03a2e`) for win/critical paths, dashed edges (`-.->`) for death/discarded paths. Avoid raw `<`/`>` in node *labels* (use words or `≤`/`≥`). Memory-map and byte-field layouts are block-level HTML tables; ordinary data tables are Markdown pipe tables.
- **Inline math** stays `$…$` (rendered by KaTeX). Wrap a raw `$NN` byte value that sits next to another `$` (e.g. in a table) in **backticks** so the `$…$` rule cannot read the span between them as math.
- A page break inside an oversized chapter is an explicit marker on its own line: `<!-- nwpage: slug | Page Title -->` (slug becomes the stable `.html` filename).

### Prose rules

Markdown prose in `main.nw` (paragraphs, headings, captions, list items, table-cell text) must follow these standing rules for memory addresses:

**1. Every numeric address gets wrapped in `[[ ]]`.** Never write a bare `$XXXX` in prose. Always `[[$XXXX]]` or `[[SYMBOL]]`. The `[[ ]]` form renders as a cross-reference link (to the defining chunk for a `@ %def` symbol; styled-but-unlinked for a raw address). A bare `$XXXX` is also at risk of being parsed as inline math. The wrap is mechanical and total — not captions, not parentheticals, nothing.

**2. Prefer the symbol over the hex, and do not annotate the symbol with its own address.** When a label, EQU, or `@ %def`-exported name exists for the address, write `[[SYMBOL]]` — never `[[SYMBOL]] ([[$XXXX]])`. The parenthetical hex adds no information: a reader who wants the numeric address can click the symbol and jump to its defining chunk. The only permissible numeric annotation on a symbol is a **range** that conveys extent (e.g. `[[SYMBOL]] ([[$XXXX]]–[[$YYYY]])`), and even then prefer stating the size in bytes (`SYMBOL (256 bytes)`) if that's the actual information being added.

**3. No backslash inside `[[ ]]`.** Write `[[$XXXX]]`, never `[[\$XXXX]]`. `[[ ]]` content is literal code; the weaver escapes it for HTML automatically, so any `\` you write renders as a visible backslash.

**Unsymbolized addresses during active RE** (no label yet) are fine as `[[$XXXX]]`, but flag them so a later pass can upgrade, with an HTML comment:

```markdown
The routine reads from [[$XXXX]] <!-- TODO-SYM: needs label -->
```

Grep for `TODO-SYM` periodically. When introducing a new label for an address, grep main.nw for `$XXXX` occurrences in prose and replace with the symbol in the same commit.

**Exceptions where raw (unwrapped) addresses are expected** — narrow and specific:

- Memory-map tables and disk-layout tables designed to show raw addresses in their own column. Even then, consider whether wrapping makes the page more navigable.
- `ORG` directives in code chunks (governed by assembly rules, not prose).
- Comments explaining *why* a specific numeric value matters mechanically (e.g. "chosen because the address is page-aligned"). The address is the subject, not a reference.
- Code chunks themselves — governed by the separate code chunk rules above, which already require symbolic addresses in code.

If you're unsure whether something is prose or an exception, wrap it. Over-wrapping produces a navigable page; under-wrapping produces a worse one.

## Assembly pitfalls

### Branch labels

- **Compute branch targets from the binary first.** Most disassembly errors are labels placed on the wrong instruction. Calculate: `target = branch_addr + 2 + signed_offset`. If offset byte >= $80, it's a backward branch.
- **Loop labels must include re-executed calls.** If a loop re-calls a JSR each iteration, the branch target must be BEFORE the JSR. A 3-byte offset mismatch is the telltale sign.
- **Shared branch targets across routines** must share the same `SUBROUTINE` scope.
- **Backward branches for code reuse.** 6502 code heavily reuses earlier code via backward branches. Disassembler output can misrepresent these as forward branches — always check the offset byte manually.

### Self-modifying code

- Use `= *+N` labels for EACH modified operand byte; don't use arithmetic on another label.
- Self-modifying storage bytes must emit their disk-image initial values, not runtime values. Always check the reference binary.
- For indexed self-modification (`STA label+N,X`), the effective address is `label+N+X`. Work backward from the desired effective address.

### Code/data boundaries

- When a data region overlaps with code, truncate the HEX data at the overlap boundary and let the code ORG define the overlapping bytes.
- "Padding" bytes between routines may have specific values — always check the reference binary, never assume $00.
- Before creating a chunk for address $XXXX, grep main.nw for `ORG.*XXXX` to avoid duplicates.

### Fall-through and multiple entry points

- Watch for fall-through between adjacent routines — they must stay adjacent and the first must NOT duplicate the second's code.
- When branch/jump targets don't match by exactly 3 bytes, check for a second entry point that skips a JSR/JMP.

### Verification

After writing any new assembly chunk:
1. Assemble and compare byte-for-byte against the reference binary.
2. Verify every JSR/JMP operand, not just the ORG address.
3. Run `/assemble` for full regression.
4. Run `python .claude/skills/chunk-placement/check_placement.py` for label placement.

### Disassembly caveats

- Work with disassembly directly — never reason from a C-like decompilation.
- Automated function-boundary and branch-structure analysis is unreliable for hand-written 6502. For routines >50 bytes, dump raw bytes and manually trace every branch offset.
- "Fall-through" between routines must be verified from actual bytes, never assumed.

## Disk layout

The disk is a **ProDOS 1.1.1 volume** (`/U1`) stored in a DOS-order `.dsk`. There is no custom RWTS and no page table — all game data lives in ordinary ProDOS files (see the targets table above). Reference binaries are extracted with `.claude/scripts/prodos_extract.py`, which understands the volume directory and seedling/sapling/tree storage.

Boot chain: Disk II PROM loads the 512-byte boot block (ProDOS block 0 = T0 physical sectors 0 and 2) at `$0800` → boot block loads the `PRODOS` kernel at `$2000` via the volume directory → ProDOS relocates high and runs the first `.SYSTEM` file (`U1.SYSTEM` at `$2000`) → `U1.SYSTEM` runs `U1.INTRO` → intro loads `MI.U1` (resident, `$7000-$8955`) and one mode overlay at `$8956`.

ProDOS block math (for manual sector work): block B is on track B//8; its halves are ProDOS sectors 2*(B%8) and 2*(B%8)+1; ProDOS sector s maps to physical sector `PRODOS_PHYS[s]` with `PRODOS_PHYS = [0,2,4,6,8,10,12,14,1,3,5,7,9,11,13,15]`. Compose with `DOS_SKEW` below for `.dsk` file offsets. The two halves of any block are exactly two physical sectors apart.

The P5A Disk II PROM reads sectors in physical position order: 0, 7, E, 6, D, 5, C, 4, B, 3, A, 2, 9, 1, 8, F. A DOS-order `.dsk` file stores sectors in DOS 3.3 logical order; to read physical sector P from the file: `dsk_offset = track * 4096 + DOS_SKEW[P] * 256`, where `DOS_SKEW = [0, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1, 8, 15]`. The actual sector order for this game is recorded in `targets.json` (`dsk_sector_order`).

## Memory map

Known so far (refined as RE progresses):

| Range | Contents |
|---|---|
| `$0800-$09FF` | boot block (boot time); `MAPCHARS` tiles / `U1.INTRO` / `STUPH` load here at run time |
| `$0C00-$13FF` | boot-time volume directory buffer |
| `$1E00-$1FFF` | boot-time kernel index-block buffer; `MAKE.INDATA` load address |
| `$2000-$3FFF` | hi-res page 1; `PRODOS` / `U1.SYSTEM` load here first |
| `$4000-$5FFF` | hi-res page 2; `TCMAPS` / `NIF` data load address |
| `$7000-$8955` | `MI.U1` resident engine |
| `$8956-` | mode overlay region (`OUT`/`TWN`/`CAS`/`DNG`/`SPA`/`GEN`/`TM`) |
| high memory | relocated ProDOS kernel (`$9A00+` MLI, language card) |

Saved state lives on a player disk in ProDOS files `U1.PLAYER` and `U1.VARS`.
