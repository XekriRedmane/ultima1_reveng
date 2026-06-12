# annotate

Annotate an existing documented routine: replace raw addresses and constants with named EQUs, add inline comments, align comments, and add a header comment plate.

## Usage

```
/annotate ROUTINE_NAME
/annotate all routines in SECTION_NAME
```

ROUTINE_NAME is the label of a routine already in main.nw.

When annotating all routines in a section or subsection:
1. Find the section boundaries by **line number**: search for the `\section{...}` or `\subsection{...}` header, then find the NEXT header at the same or higher level. The range is ALL lines between these two headers. Do NOT use any address range in the section title as the boundary — the title is just a summary and may not cover all routines in the section.
2. List ALL routines (ORG + `@ %def` pairs) within the line range. Print the list and verify it is complete before proceeding.
3. Skip routines that already have plate comments (a `;` comment block with `; Inputs:` or `; Behavior:` immediately after SUBROUTINE).
4. Launch **parallel sub-agents** (one per routine, or group small related routines). Each sub-agent receives the routine source text as INPUT and returns PROPOSED REPLACEMENT TEXT. Sub-agents must **NOT edit the file directly** — they only return text. This prevents concurrent clobbering when multiple agents run in parallel on the same file.
5. Collect all sub-agent results. The parent (you) applies each replacement **sequentially** to main.nw, normalizing comment style as needed.
6. Assemble and verify after all changes are applied.

## Instructions

This skill improves the readability of an already-documented routine by applying the passes below. After each pass, run `/assemble` — annotation must never change assembled output.

### Pass 1: Replace raw addresses and constants with names

For every raw hex address or constant in the routine:

1. **Subroutine calls** (`JSR $XXXX`, `JMP $XXXX`): look up the label in the target's `.sym` file or main.nw and replace. If the callee isn't RE'd yet, create an EQU stub per CLAUDE.md.
2. **Data addresses** (`LDA $XXXX`, `STA $XXXX`, etc.): check if an EQU or label exists. If not and the address is meaningful (game state, display buffer, table), create one with a descriptive name.
3. **Immediate constants** (`LDA #$XX`, `CMP #$XX`): if the value has a known meaning (field offset, bitmask, record size, sprite id, state sentinel), create an EQU. Define the EQU WITHOUT `#` (e.g., `LEVEL_MASK EQU $1F`) and use `#` on the instruction (`AND #LEVEL_MASK`). If the immediate is a label's address or byte, use `#<label` / `#>label`.
4. **Record field offsets**: ANY `LDY #imm` followed by `LDA (ptr),Y` / `STA (ptr),Y` is a record field access; the immediate MUST get a named field-offset EQU. Determine the record type from the pointer and use a consistent per-record prefix (e.g., a project with entity records might use `EFIELD_*`). Group all field-offset EQUs for the same record type together in one defines chunk; check for an existing EQU before creating a new one. When `INY`/`DEY` moves Y to another field, comment which field Y now points to.
5. **Bitmasks**: ANY `AND #$XX` / `ORA #$XX` MUST have a named EQU for the mask, named after the field it operates on. If a mask and its complement both appear, define both. Reuse existing mask EQUs for the same field.
6. **Zero-page addresses**: ANY ZP operand without an EQU MUST get one. Globally meaningful state gets a global name; per-subsystem scratch gets a contextual alias. Follow the zero-page aliasing convention: the same address used for different purposes in different subsystems gets a different EQU name per use.
7. **Indirect addressing** (`LDA ($XX),Y`): the ZP pointer needs an EQU name.
8. **Indexed addressing** (`STA $XXXX,X`): the base address needs a label or EQU.

### Pass 2: Add inline comments and align

1. **Comment the purpose**, not the mechanics: "extract location tier", not "rotate left 4 times". Never restate the instruction — delete comments that carry zero information beyond the operand.
2. **Assignment comments** use `<-` with `#$` for values: `STA ZP_SPRITE_H ; ZP_SPRITE_H <- #$1C`. Refer to indexed tables as `SYMBOL[Y]`, never `$XXXX,Y` or `SYMBOL,Y`.
3. **Section headers** (`; --- section name ---`) between logical phases of a long routine.
4. **Label comments** on `.local` labels explaining the branch condition or loop purpose.
5. **Align all `;` comments** to the same column within the routine.
6. Comments are ASCII-only — no Unicode arrows/dashes, no LaTeX (see CLAUDE.md).

### Pass 3: Add header comment plate

Add the standard plate immediately after `SUBROUTINE` (format in CLAUDE.md "Chunk annotation"): one-line description, Inputs, Behavior, Outputs (if it returns results), Modifies, Clobbers. Simple trampolines without `SUBROUTINE` get a one-line comment instead.

### Pass 4: Rewrite prose documentation

The noweb `@` prose preceding each chunk should be a clear, structured summary — not a wall of text:

1. **Opening paragraph**: 1-2 sentences on what the routine does and when it is called.
2. **`\paragraph{}` blocks** for each distinct game mechanic or algorithm phase, with descriptive names ("Hit roll.", "Spawn gating.", "Page selection.").
3. **Itemized lists** for branching conditions, thresholds, or multi-step processes; **tables** for data-driven mechanics with multiple modifiers or lookup values.
4. **Cross-references** with `[[LABEL]]` for routines and variables; follow the prose address rules in CLAUDE.md (always `[[ ]]`, prefer symbols, no backslashes inside).
5. Keep prose concise — code comments carry instruction-level detail; the prose explains the *game design* and *algorithm structure*.

### Reference example

Before annotating, pick a reference: grep main.nw for a routine that already has a full plate (`; Behavior:`) and structured prose, and match its style. Consistency within the document beats any external template.

### Notes

- Always verify byte-for-byte after changes; comments and EQU substitutions must not change assembled output.
- Do NOT rename labels that are already well-named.
- Do NOT add EQUs for well-known Apple II ROM entry points or softswitches unless they improve clarity — but named ones already in the document must be reused.
- When creating EQUs, place them per chunk-placement rules (just before first use) and run `check_placement.py`.
- If a raw value is used once and has no broader meaning, a comment may serve better than an EQU.
- **dasm EQU values are always addresses/numbers, never immediates.** Put `#` on the instruction, never in the EQU value — dasm would silently assemble zero-page addressing instead of immediate.
