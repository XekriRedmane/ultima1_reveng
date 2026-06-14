# Reverse Engineering an Apple II Game Binary

This document describes the process for reverse engineering an Apple II game from a `.dsk` disk image into a fully documented, reassemblable literate programming document (`main.nw`). It is written to be carried out **autonomously**: given only a disk image and the template repository, the agent works continuously — round after round, session after session — until the definition of done at the end of this document is met.

## Audience and goal

The reader of `main.nw` wants to learn how the game was written and how it works, in enough detail to **reproduce or port the game in any language, on any platform** — not just 6502 assembly on the Apple II. This shapes every round:

- Byte-perfect annotated assembly is the **evidence base**, necessary but not sufficient.
- The document must also **recover the design**: game mechanics, data structures, algorithms, and rendering described in platform-independent terms (the `/synthesize` skill).
- Prose explains game design and intent; comments explain instruction purpose; neither restates mechanics the reader can see.

## Prerequisites

The template repository must contain:

- `main.nw` — literate programming source (Markdown prose + noweb code chunks)
- `weave.py` — noweb tangler + chunk-graph engine (extracts byte-perfect `.asm` from `main.nw`)
- `weave_html.py`, `web/` — HTML weaver (Markdown→multi-page site) and its CSS/JS assets
- `.claude/scripts/dasm6502.py` — 6502 disassembler for reference binaries
- `.claude/skills/bootstrap/` — Round 0 skill: disk image → reference binaries, `targets.json`, initial `main.nw` (includes `dsk_tool.py` for sector dump/extract/search)
- `.claude/skills/assemble/verify.py` — byte-level comparison of assembled output against reference
- `.claude/skills/assemble/reorder_chunks.py` — fix ORG address ordering in chunks
- `.claude/skills/chunk-placement/check_placement.py` — verify chunk placement rules
- `.claude/skills/re-status/` — the scoreboard: every measurable completion criterion
- `.claude/skills/annotate/` — routine annotation skill
- `.claude/skills/disassemble/` — disassembly skill
- `.claude/skills/trace-address/` — data-address tracing skill
- `.claude/skills/re-next/` — find and RE the next unlabeled address
- `.claude/skills/find-gaps/` — locate and prioritize undocumented byte ranges
- `.claude/skills/synthesize/` — write the platform-independent design chapters
- `CLAUDE.md` — project conventions (assembly style, chunk rules, code chunk rules, annotation rules)

Input: a `.dsk` disk image of the game. Nothing else is assumed — no Ghidra, no emulator (an emulator is a nice-to-have for spot checks, never a dependency). All analysis runs on the disk image, the extracted reference binaries, `dasm6502.py`, and the dasm `.lst`/`.sym` outputs.

`targets.json` at the repo root is the **project manifest** — game name, disk image, sector order, and one entry per assembly target (name, base address, reference binary). It is created during Round 0 and read by every pipeline script. The only game-specific configuration lives there and in CLAUDE.md's project sections; skills and scripts are game-agnostic.

## Agent architecture

A **main agent** coordinates the reverse engineering process. It dispatches work to **skill agents** that run sequentially (not in parallel), because each step depends on the output of the previous one. The main agent:

1. Runs `/re-status` to see the scoreboard and picks the next unit of work
2. Launches a skill agent to disassemble, document, or annotate
3. Verifies the result (assemble + binary compare)
4. Updates the collection chunk, runs the round-end protocol, and commits

Skill agents should not edit `main.nw` concurrently. Each skill agent completes its work, returns results to the main agent, and the main agent applies changes and verifies before proceeding. (Exception: read-only analysis agents may run in parallel; only `main.nw` edits are serialized.)

## Autonomy protocol

The loop runs without a human in it. These rules keep it moving and recoverable:

- **Never wait on the user.** No skill or round may end by asking which target to pick, whether to apply a label, or whether to proceed. Make the call, record a one-line rationale, and continue. The only reasons to stop are: the definition of done is met, or an external failure (e.g. `git push` rejection) makes every further round moot — and even then, finish the current round locally and report.
- **TODO.md is the loop state.** It is the cross-session memory of progress: milestone entries at the top, the open work queue and "Structural" items at the bottom. Every round updates it — what was finished, what was learned, what the next-session priorities are. A fresh session resumes by reading `/re-status` output plus TODO.md, not by re-deriving history.
- **Blocked items go on a list, not in the way.** When something resists analysis (undecodable data format, ambiguous code/data boundary), write a `Blocked` entry in TODO.md stating what was tried and what evidence would unblock it, then take the next item. Re-check the blocked list each time a round produces new context (the discovery cycle routinely unblocks old items).
- **Decisions are recorded, not deferred.** Naming choices, chapter placement, code-vs-data judgments: pick the best-supported option and document the reasoning in prose or TODO.md. The revisit culture (see "The discovery cycle") makes wrong choices cheap to fix; stalling is the only unrecoverable error.
- **Every round ends green.** The build-verify gate and commit protocol below are unconditional. A session that ends mid-round must first roll back or finish to a green build, then update TODO.md so the next session knows where it stands.

## Round 0: Project setup

Round 0 is automated by the **`/bootstrap` skill** — run it whenever `targets.json`, `reference/`, or the boot1 collection chunk is missing. The skill's `dsk_tool.py` handles sector dumping, extraction (with selectable skew), page-map-driven reference-binary building, and on-disk byte search. What follows is the reasoning the skill carries out.

### Extract reference binaries

Before any RE work, extract the raw binary data from the `.dsk` image. This requires understanding the game's boot chain and disk layout.

1. **Identify the disk format.** Most Apple II games use either DOS 3.3, ProDOS, or a custom boot chain. Check Track 0 Sector 0 for the boot sector.

2. **Determine the sector interleave.** The `.dsk` file format stores sectors in a specific order. Common orderings:
   - **DOS order (.do/.dsk):** sectors stored in DOS 3.3 logical order. Physical sector P is at file offset `track * 4096 + DOS_SKEW[P] * 256`, where `DOS_SKEW = [0, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1, 8, 15]`.
   - **ProDOS order (.po):** sectors stored in ProDOS block order.
   - **Raw physical order:** no translation needed.

   To determine which: disassemble the boot sector, find the sector read routine, and compare assembled code against the `.dsk` data. If the bytes don't match, try applying the DOS 3.3 skew. Verify against an emulator if available.

3. **Trace the boot chain.** Starting from the boot sector:
   - What sectors are loaded, to what addresses?
   - Is there a page table or sector map?
   - What relocations happen after loading?
   - What is the final entry point?

4. **Build reference binaries.** Write a page-map file per assembly target (`track sector dest_page` lines) and build each flat binary with `dsk_tool.py extractmap`. Each binary should cover a contiguous address range. Commit the map files in `maps/` — they make the reference binaries reproducible. Sanity-check by disassembling entry points and verifying instructions aren't torn at page seams.

5. **Document the disk layout** in `main.nw` with tables showing track/sector to memory mappings, and **write `targets.json`** listing every target with its base address and reference binary.

### Initialize main.nw

Set up the document structure as Markdown headings (no LaTeX preamble):

```markdown
# Boot sequence
# Loader          (if a second-stage loader / RWTS exists)
# Game code       (main game logic)
# Memory map      (reference material)
```

Create the first assembly target (e.g., `boot1.asm`) with a defines chunk and a collection chunk.

## Round 1: Boot sector

The boot sector is the simplest starting point — it's small (usually 256 bytes), self-contained, and the entry point is known ($0801 for standard Apple II boot).

### Process

1. **Disassemble** the boot sector from the reference binary using `dasm6502.py`.
2. **Trace the logic** — register states, memory writes, conditional branches.
3. **Identify phases** — boot sectors typically: load more sectors, relocate code, set up vectors, jump to loader.
4. **Write the chunk** in `main.nw`:
   - Create `<<boot1 defines>>=` with EQUs for all referenced addresses.
   - Create `<<boot1 entry>>=` with the annotated assembly.
   - Create `<<boot1.asm>>=` collection chunk.
   - Add `SUBROUTINE` after `ORG`, header plate comment, `@ %def` line.
5. **Assemble and verify**: `python3 weave.py main.nw output && dasm output/boot1.asm -f3 -oboot1.bin && python3 .claude/skills/assemble/verify.py boot1`.
6. **Commit** with a descriptive message.

### What to learn from the boot sector

- Slot detection and disk I/O method
- Memory layout (where code gets loaded)
- Relocation targets (language card, high memory)
- Reset/NMI vector setup
- Entry point to the next stage (loader)

## Round 2: Loader / RWTS

The loader is typically the next stage — it reads the game from disk into memory. It reveals the complete memory map.

### Process

1. **Start with the RWTS** (Read/Write Track/Sector) — the low-level sector reading routines. These are usually compact and self-contained.
2. **Document the page table** — the mapping from sector positions to memory pages. This is critical for building correct reference binaries.
3. **Document the seek and motor control** routines.
4. **Document the high-level loader** — the dispatch logic that decides which tracks to load and when.
5. **Document any relocated code** — code that lives at one address on disk but runs at another after relocation.

### What to learn from the loader

- Complete disk-to-memory mapping (which tracks → which pages)
- Persistent vs. swappable memory regions
- Level/phase loading mechanism
- The game's entry point after loading completes
- Any initialization performed before entering game code

### Key pattern: the page table

The page table is the Rosetta Stone of the project. It maps sector numbers to destination memory pages. Document it thoroughly — every subsequent reference binary depends on it being correct.

## Round 3: Game entry and main loop

With the boot chain documented, trace execution into the game code.

### Find the entry point

1. Check what address the loader jumps to after loading completes.
2. It may be indirect (`JMP ($xxxx)`) — check what the zero-page pointer contains from the initial ZP state.
3. The entry point may be in a swappable region (level data) — this is normal for games that show a title screen before gameplay.

### Document the main loop

Most games have a recognizable main loop structure:

```
MAIN_LOOP:
    JSR render_setup
    JSR read_input
    JSR update_physics
    JSR check_collisions
    JSR draw_sprites
    JSR flip_page
    JMP MAIN_LOOP
```

1. **Disassemble the main loop dispatcher.** Identify each JSR target.
2. **Create EQU stubs** for all called routines (`RENDER_SETUP = $XXXX ; STUB`).
3. **Identify self-modifying code** — games often patch JSR/BIT opcodes to enable/disable subsystems (e.g., attract mode vs. game mode).
4. **Document the frame structure** — what order things happen each frame.
5. **Identify exit conditions** — level complete, game over, return to attract.

### Document the input system

The input system is a high-value early target because:
- It reveals the control scheme (what keys/buttons do what)
- It often patches the main loop (enabling movement directions)
- It references game state variables that help understand other systems

### Attract mode

Many games have an attract/demo mode that shares code with the main loop but disables input. Document how attract mode differs — typically self-modifying JSR/BIT toggles.

## Round 4: Systematic routine documentation

After the main loop is understood, work outward from the most-referenced routines.

### Prioritization

1. **Most called** — routines called from many places provide the most context.
2. **Adjacent to documented code** — fills gaps, reduces fragmentation.
3. **Small and self-contained** — quick wins that build coverage.
4. **Data tables** — understanding lookup tables unlocks multiple routines at once.

### Process for each routine

Use the `/re-next` skill to find candidates, or pick manually based on the main loop's JSR targets. For each routine:

1. **Disassemble** from the reference binary.
2. **Trace register and memory state** through every instruction.
3. **Identify inputs, outputs, and side effects.**
4. **Choose a descriptive name** (UPPER_SNAKE_CASE).
5. **Write the chunk** with:
   - A Markdown section heading and prose explaining the routine's purpose
   - EQU defines for any new addresses (in a defines chunk, placed just before first use)
   - Annotated assembly with header plate, section headers, aligned comments
   - `@ %def` declaring exported symbols
6. **Replace the EQU stub** in the defines chunk with the real label.
7. **Update raw hex references** throughout `main.nw` — replace `JSR $XXXX` with `JSR LABEL_NAME`.
8. **Add to the collection chunk** in ascending ORG address order.
9. **Assemble, verify, commit.**

### Building up data structure understanding

Game state is typically stored in zero-page arrays and fixed-memory tables. Understanding builds gradually:

1. **Name ZP addresses as you encounter them.** Use contextual aliases — the same address may serve different purposes in different routines.
2. **Track record structures.** When you see indexed access patterns like `LDA table,X` with X iterating, you've found an array. When you see `LDY #offset; LDA (ptr),Y`, you've found a record field. Create EQUs for field offsets.
3. **Build the memory map incrementally.** Each routine reveals which addresses are code, which are data tables, and which are scratch buffers.
4. **Cross-reference.** When routine A writes to an address and routine B reads it, document the data flow in both routines' prose.

### Common 6502 game patterns to recognize

- **Self-modifying code**: `STA target+1` to patch an operand. Use `label = *+1` or `label = *+2` for the modified byte.
- **BIT abs as 3-byte NOP**: `DC.B $2C` before `LDA #imm` creates a multi-entry point. The `BIT` reads the `LDA` operand harmlessly.
- **JSR/BIT toggle**: Patching a `JSR` opcode byte ($20) to `BIT` ($2C) disables a subroutine call without changing the operand bytes.
- **Indexed dispatch**: `LDA table,X; STA target+1` followed by `JMP target` implements a jump table.
- **Page-crossing tricks**: Placing data at page boundaries to exploit 6502 page-crossing behavior.
- **Unrolled loops**: Repeated instruction sequences with different operands for speed.

## Round 5: Data regions

After code routines are documented, fill in data regions:

1. **Sprite/shape tables** — typically contiguous byte arrays with a known record size.
2. **Level data** — maps, enemy placements, item locations. Often in swappable memory regions.
3. **String tables** — text displayed on screen.
4. **Lookup tables** — math tables (multiply, divide), screen address tables, color tables.

For each data region:
- Determine the structure (record size, field layout)
- Create labels and EQUs for field offsets
- Emit as `HEX` with comments, or as structured `DC.B`/`DC.W` where the format is known
- Document the structure in prose

### Fonts and images

See the "Standing rule: render any graphics data you uncover" section below
for the process. Graphics rendering is not a Round-5-specific task — it
applies whenever a session uncovers pixel data, code or data round alike.

Round-5-specific notes: when fonts and sprite sheets are the primary focus
of a session, render the full character set as a grid and label each frame
of each sprite-animation sequence. Note the ASCII offset or custom character
order for fonts. Cross-reference the tile dimensions against the draw
routines that consume them (often the draw routine's `ZP_SPRITE_W`/`_H`
values or SMC-patched operands encode these).

## Round 6: Synthesis — recovering the design

Run the **`/synthesize` skill** once the main loop and major subsystems are documented, and again whenever a round completes a subsystem. This round serves the document's actual audience (see "Audience and goal"): it produces the chapters a porter reads *first* — game overview, architecture overview, data structure reference, platform-independent algorithm descriptions (pseudocode), rendering pipeline (Apple II-specific vs. portable, explicitly separated), and porting notes per subsystem.

The quality bar: a competent programmer who has never read 6502 assembly could reimplement each subsystem from its synthesis section alone, using the assembly chapters only for edge cases. Synthesis is not a final pass to be deferred — a subsystem's round is not complete until its design is recoverable from prose.

## Round 7: Organization and polish

The closing rounds, interleaved with late synthesis work:

1. **Reorganize chapters by function.** Address-order chapter structure is scaffolding; the final document is organized by subsystem (boot/load, main loop, input, rendering, entities, audio, level data), with the memory map as an appendix. Reorganize when the current structure actively misleads (see "When to reorganize").
2. **Hygiene to zero.** EQU stubs, ORG stub chunks, `TODO-SYM` markers, raw-hex JSR/JMP operands, missing header plates, and placement violations all go to zero — `/re-status` measures each.
3. **HTML quality pass.** Build with `/gen-html`; fix any weave errors, confirm internal links resolve (no broken `[[ ]]`/anchor references), confirm Mermaid diagrams and tables render, and confirm every rendered image is referenced from prose.

## Definition of done

The project is finished when ALL of the following hold (the `/re-status` skill checks the measurable ones):

1. Every target in `targets.json` assembles **byte-perfect** against its reference binary.
2. Zero EQU stubs, zero `; STUB — not yet disassembled` chunks, zero raw-hex `JSR`/`JMP` operands in code, zero `TODO-SYM` markers.
3. Every `SUBROUTINE` routine has a header plate; chunk-placement check passes.
4. All graphics data is rendered to `images/` and embedded with prose (standing rule below).
5. The synthesis layer is complete to the Round 6 quality bar for every subsystem.
6. Chapters are organized by function; the HTML site builds cleanly with no broken links.
7. Everything is committed and pushed.

When done, report the final scoreboard and stop — do not loop further.

## Standing rule: render any graphics data you uncover

This is a **continuous** behavior, not a Round-5-only task. Any time a session
uncovers graphics data — a sprite, font glyph, tile, title/HUD image, unpacker
stream, or any byte region that is used as pixel data by a draw routine —
render it to a PNG and embed it in the document in the same commit as the RE.

The rule applies even when the graphics are a byproduct of RE'ing a code
routine (e.g. you RE a draw routine and it reveals where its sprite table
lives, or you decode a self-modifying sprite pointer and resolve where it
points). Don't defer the image work to a separate pass; do it in the same
session while the data layout is fresh.

### Steps

1. **Figure out the record format** — dimensions (W×H in bytes or columns×rows),
   data ordering (row-major vs column-major, forward vs reversed), how many
   frames, what palette bits do.
2. **Write or extend a Python renderer.** Save to `.claude/scripts/render_<name>.py`.
   Build it on the shared library `.claude/scripts/render_hires.py`: it
   implements the Apple~II hi-res palette/artifact rules (`color_row`,
   `render_rows`, `render_screen`, `save_png`) — open the reference
   binary, slice the data at offset = address − target base, and hand
   the byte rows to the library. Do not rewrite palette logic from
   scratch. For sprite tables, iterate each frame and either save one
   PNG per frame or assemble them into a grid image.
3. **Run the renderer** with `python3`. Pillow (`PIL`) is preinstalled
   in the container image.
4. **Save the output under `images/`** at the repo root. Filenames should
   describe the content: `sprite_player_walk_frame3.png`, `font_glyphs.png`,
   `enemy_a_sprites.png`, `hud_frame.png`, etc. Use lowercase with
   underscores.
5. **Embed the image in `main.nw`**, right where the data is documented.
   Use a Markdown image followed by a `**Figure — …**` caption paragraph;
   if the figure is cross-referenced, precede it with an anchor
   `<a id="fig:..."></a>`. Path: `![alt](images/<name>.png)` (the HTML
   weaver copies `images/` into `output_site/`). HTML has no LaTeX-style
   scale knob, so for tiny sprites (7-14 px wide) the `render_*.py` script
   should upscale before saving the PNG.
6. **Describe the decoding in prose** immediately before or after the
   figure: record size, dimensions, frame count, how the game indexes into
   the table, any palette/color quirks specific to this data.
7. **Verify visually.** Read the PNG back (or trust the `Read` tool's
   display) and confirm it looks like recognizable game content. If it
   renders as noise or garbage, the format guess is wrong — don't ship a
   useless image; iterate until the picture makes sense.
8. **Commit in the same commit as the RE.** The image file, the renderer
   script, and the `main.nw` edits all go together.

### When the data format is genuinely unknown

If you find sprite-table entries referenced by a self-modifying pointer but
can't yet decode the format (e.g. RLE, stream-based, or tiled), note the
address, dimensions guess, and a TODO in the commit message. Don't force a
broken render.

### Don't skip this

Rendered images are the single highest-bandwidth communication between the
document and the reader — far more than prose describing byte layouts. Every
session that finds graphics without rendering them is leaving the document
less useful than it should be. Treat graphics rendering with the same
priority as writing prose or annotating assembly.

## Standing rule: addresses in prose

Applies every session, not just graphics work. Three rules for numeric
addresses in Markdown prose inside `main.nw`:

1. **Wrap every address in `[[ ]]`.** Never bare `$XXXX` in prose — always
   `[[$XXXX]]` or `[[SYMBOL]]`. The `[[ ]]` form renders as a navigable
   cross-reference link; raw hex does not.
2. **Prefer symbol over hex, and never annotate a symbol with its own
   address.** `[[SYMBOL]]`, not `[[SYMBOL]] ([[$XXXX]])` — the parenthetical
   hex adds no information. Only range appositions conveying extent
   (`[[SYMBOL]] ([[$XXXX]]--[[$YYYY]])`) are permitted.
3. **No backslash inside `[[ ]]`.** `[[$XXXX]]`, never `[[\$XXXX]]`.

During active RE with no symbol yet, `[[$XXXX]]` is fine but flag it:

```markdown
The routine reads from [[$XXXX]] <!-- TODO-SYM: needs label -->
```

When introducing a label, grep prose for the raw hex and replace with the
symbol in the same commit. Full policy (including exceptions for
memory-map tables and ORG directives) lives in the `### Prose rules`
section of `CLAUDE.md`.

## Standing rule: every round ends with style-sweep, commit, push

Every RE round ends with three non-optional steps, in order. Do not report
the round "done" until all three succeed.

### 1. Style-guideline sweep

After the main RE work, pass over `main.nw` and apply the style rules in
`CLAUDE.md` to anything this round touched or surfaced. In particular:

- **New symbols.** For every label/EQU introduced this round, grep `main.nw`
  for raw hex occurrences of that address and replace with the symbol — in
  code operands (`JSR $XXXX` → `JSR LABEL`, `LDA $XXXX,X` → `LDA LABEL,X`),
  in inline comments, and in prose (`[[$XXXX]]` → `[[LABEL]]`). Use
  word-boundary regex to avoid prefix collisions. Skip lines containing
  `EQU` or `%def` to avoid circular definitions.
- **Prose address wrapping.** Every numeric address in prose must be
  `[[SYMBOL]]` or `[[$XXXX]]` — never bare `\$XXXX`, never `[[\$XXXX]]`.
- **TODO-SYM elimination.** Every round must try to clear as many existing
  `TODO-SYM` markers as possible — not just the ones this round introduced.
  `TODO-SYM` flags any raw numeric literal that could become a symbol.
  The number may be:
  - an **address** (code, data, ZP slot, ROM entry),
  - a **constant** (record-field offset, bitmask, state-value sentinel,
    sprite id, score delta, threshold, timer seed, opcode byte), or
  - any other magic literal that readers would want named.

  Grep `main.nw` for `TODO-SYM` and for each hit, decide:
  - If a label/EQU now exists for the value, replace the raw
    `[[$XXXX]]` / `[[$XXX]]` / `[[$XX]]` with `[[SYMBOL]]` and remove the
    marker. The rule applies to literals of any width — 2-digit
    (`[[$5B]]`, `[[$1C]]`), 3-digit (`[[$1FF]]`), and 4-digit (`[[$629E]]`)
    alike. Do not skip the 2-digit cases: small hex values are commonly
    zero-page addresses with existing ZP EQUs, record offsets with
    existing offset EQUs, or state constants with existing symbolic names.
  - If no symbol exists but the value is a meaningful constant
    (frequently-referenced record offset, bitmask, state sentinel), that
    round is a good opportunity to **introduce a new EQU** and then
    symbol-replace. Prefer this to deferring indefinitely.
  - If the number is not actually needed to communicate the sentence's
    point (e.g. the prose already says what the value is, or the
    surrounding sentence refers to a region that's now a labeled chunk),
    drop the literal entirely and remove the marker.
  - If the value is still unsymbolized and the number is load-bearing,
    leave the marker in place — but document in the round summary why it
    couldn't be resolved this round. Uninvestigated `TODO-SYM`s are not
    acceptable; every marker must have been looked at.

  Also do a second sweep for **unflagged raw-hex prose literals** —
  `[[$XX]]` / `[[$XXX]]` / `[[$XXXX]]` occurrences (addresses or
  constants) that lack a `TODO-SYM` marker but where a symbol now
  exists. These are common because earlier rounds introduced labels
  after the prose was written. Symbol-replace them too.

  High-yield patterns to grep for: `at [[\$` and `from [[\$` and
  `to [[\$` in prose almost always introduce a location that should be
  named — these idioms ("the routine at $XXXX", "reads from $XX",
  "jumps to $XXXX") are exactly where a symbol would clarify the
  sentence. Also look for `([[\$` (parenthetical hex after a symbol,
  which is redundant and should be dropped) and `\$[0-9A-F]` outside of
  `[[ ]]` brackets in prose (unwrapped addresses that fail the prose
  wrapping rule entirely).

  The round summary must include a `TODO-SYM` count delta (before vs.
  after) so regressions are visible.
- **Code comments.** Remove comments that merely restate the instruction or
  carry a raw `$XXXX` where a symbol exists. Use `<-` and `#$` in
  assignment comments. Refer to indexed tables as `SYMBOL[Y]` in prose
  (never `SYMBOL,Y`). Comments are ASCII-only.
- **Immediates.** `LDA #imm` where `imm` is a label or label byte must be
  `#<label` / `#>label`.
- **Chunk placement.** Run
  `python3 .claude/skills/chunk-placement/check_placement.py`. Report any
  NEW violations introduced by this round (pre-existing violations are not
  the round's responsibility, but note the count delta in the round
  summary).
- **ORG order.** If the collection chunk's ORG addresses are out of
  ascending order, run `.claude/skills/assemble/reorder_chunks.py`.

### 2. Build-verify gate

Run the full tangle-build-verify pipeline (the `/assemble` skill, or
equivalently re-run `python3 weave.py main.nw output`, `dasm` each target
in `targets.json`, then `python3 .claude/skills/assemble/verify.py` with
no arguments to verify all targets).

All targets must be byte-perfect. If any target diverges, roll back the
offending edit and re-verify. Do not commit a red build.

Then run the `/gen-html` skill (or equivalently: run any `site_pregen`
commands from `targets.json`, then `python3 weave_html.py main.nw
output_site`). The site must build cleanly — `weave_html.py` should
finish without an error, and a link check should report zero broken
internal references. Weave errors (missing chunk, malformed `[[ ]]`)
must be fixed before committing. Do not commit a site that fails to
build.

### 3. Commit and push

Once verification is green, stage the round's changes, commit with a
descriptive message, and push. (Git identity and `safe.directory` are
configured by the container entrypoint; override the identity via the
`GIT_USER_NAME`/`GIT_USER_EMAIL` compose environment variables.)

```bash
git add \
    main.nw \
    TODO.md \
    images/ \
    .claude/agent-memory/reverse-engineer/ \
    .claude/scripts/

git commit -m "$(cat <<'EOF'
<concise subject, <=72 chars: address or region reversed>

<body: what was learned, names introduced, verification result>

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

git push
```

Only stage files the round actually modified or created — do not use
`git add -A` (it can pick up stray build artifacts or credential files).
If `git push` fails (network, credentials, non-fast-forward), surface the
failure in the round summary rather than retrying blindly or force-pushing.

## Chunk hygiene

Throughout all rounds, maintain chunk quality:

### Every commit must pass

```bash
python3 weave.py main.nw output
cd output
dasm target.asm -f3 -otarget.bin -ltarget.lst -starget.sym
python3 .claude/skills/assemble/verify.py target
```

### Apply code chunk rules

After writing any chunk, verify it follows the rules in CLAUDE.md:
- `JSR $XXXX` / `JMP $XXXX` must use labels (create EQU stubs if not yet RE'd)
- Non-ZP data addresses must use labels
- ZP addresses must use symbolic EQU names
- Immediate values that are label addresses must use `#<label` / `#>label`
- 16-bit pointer EQUs use a single name with `+1` for the high byte
- Record field offsets get named EQUs
- Every routine with `SUBROUTINE` gets a header plate comment
- Chunk ends with `@ %def` for exported symbols
- Collection chunk lists chunks in ascending ORG address order

### Apply chunk placement rules

- EQU defines go just before the chunk that first uses them
- Data chunks go just before the first code chunk that references them
- Run `check_placement.py` after adding chunks

### Naming conventions

- Routine labels: `UPPER_SNAKE_CASE` describing purpose, not mechanism
- Local labels: `.lower_name` within `SUBROUTINE` scope
- EQU constants: `UPPER_SNAKE_CASE` with descriptive comment
- Chunk names: `<<lowercase with spaces>>`
- Section headers: no numeric addresses

## The discovery cycle

Reverse engineering is not a linear process. It is a continuous cycle of discovery:

```
    disassemble → analyze → name → document → discover new context
         ↑                                            |
         └────────── revisit and correct ←────────────┘
```

Each routine you document teaches you something that changes your understanding of routines you documented earlier. A zero-page address you named `ZP_TEMP` in round 3 might turn out to be `PLAYER_FLOOR` by round 5. A data table you emitted as raw HEX might reveal structure once you understand the record format from a later routine. A routine you named `GAME_ROUTINE_1255` gets a real name once you see what it does.

### Expect to revisit everything

- **Names evolve.** First pass: `COPY_HGR1_TO_HGR2`. After understanding purpose: `START_ATTRACT`. The initial name described mechanism; the final name describes intent. Rename freely as understanding deepens.
- **Comments get corrected.** "Set up vectors at $03F8" turns out to be "Initialize floor Y-coordinate table" once you find the code that reads it. Go back and fix the comment immediately — stale comments are worse than no comments.
- **Data becomes structured.** A HEX blob becomes `DC.W address` + `HEX pixel_data` once you understand the record format. Revisit data chunks as the routines that consume them are documented.
- **EQU stubs become real labels.** Every `STUB — not yet disassembled` is a promise to revisit. When you RE the routine, replace the EQU with an ORG + label, update all references, and verify.
- **Zero-page aliases multiply.** The same ZP address serves different purposes in different subsystems. Add aliases as you encounter new uses — `ZP_STREAM` in the unpacker, `ZP_SCROLL_PTR` in the renderer, both at $A0.

### The feedback loop

When you document routine B and discover it writes to an address that routine A reads:

1. Go back to routine A's documentation.
2. Update the comment on the load instruction to explain what B stored there.
3. Update A's header plate to list the new input.
4. Consider whether A's name still makes sense given the new context.
5. Consider whether the ZP/data address deserves a better name now that two routines use it.

This is not rework — it is the core of the process. The document improves in waves, not in a single pass.

### Practical cycle within a session

A typical session looks like:

1. **Pick a target** — highest-value unlabeled routine (most referenced, adjacent to known code, or blocking understanding of something else).
2. **Disassemble** — get the raw bytes, trace the logic instruction by instruction.
3. **Analyze** — what does it do? What are the inputs, outputs, side effects? What game concept does it implement?
4. **Name and document** — choose a name that describes purpose. Write the chunk with proper style. Add EQUs for new addresses.
5. **Discover** — the routine revealed new information. Maybe it writes to an address you've seen before. Maybe it calls routines you now understand differently. Maybe a "data" region is actually code.
6. **Propagate** — go back and update earlier documentation with the new knowledge. Rename EQU stubs. Fix comments. Restructure data.
7. **Verify and commit** — assemble, binary compare, commit. Never break the build.
8. **Repeat** — pick the next target, informed by what you just learned.

### Signs of progress

- Raw hex addresses in code are replaced with labels.
- EQU stubs (`STUB — not yet disassembled`) are replaced with real code.
- HEX data blobs gain structure (DC.W, record comments).
- Zero-page addresses have descriptive names in every routine that uses them.
- Prose sections explain game mechanics, not just byte manipulation.
- Cross-references between routines are documented in both directions.

### When to reorganize

As understanding grows, the chapter structure may need revision:

- Code that seemed related by address may be unrelated by function.
- A chapter called "RWTS" may contain mostly non-disk routines.
- Multiple small routines may belong together as a subsystem (e.g., "sprite rendering" spanning several address ranges).

Reorganize when the current structure actively misleads. Don't reorganize speculatively — wait until you have enough documented routines to see the real structure.

At every stage, the document must build and verify byte-perfect against the reference binary. Never break the build.
