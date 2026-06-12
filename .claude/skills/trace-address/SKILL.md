# trace-address

Trace all uses of a data address across the game binaries to determine its purpose and assign a label.

## Usage

```
/trace-address $XXXX
```

Where `$XXXX` is a hex address (e.g., `$5A74`, `0x5A74`, or just `5A74`).

## Instructions

You are analyzing a 6502 Apple II game (see `targets.json` for targets, reference binaries, and base addresses). Given a data address, determine what it stores and assign an EQU/label.

### Step 1: Check existing context

Search `main.nw` for existing references, comments, or prose about the address. Check `output/*.sym` for an existing symbol at or near it.

### Step 2: Find all references in main.nw

Grep main.nw for the address in operand positions (`$XXXX` with word boundaries). Documented code is the richest context: each hit comes with its routine's prose and comments.

### Step 3: Find references the document may have missed

Scan every reference binary for the absolute-addressing byte patterns, where `LL HH` are the little-endian address bytes:

- `8D LL HH` (STA) — write; `AD LL HH` (LDA), `AE` (LDX), `AC` (LDY), `CD` (CMP), `2C` (BIT), `0D/2D/4D/6D` (ORA/AND/EOR/ADC) — reads
- `CE LL HH` (DEC), `EE LL HH` (INC) — read/write
- Indexed forms: `9D/BD` (STA/LDA abs,X), `99/B9` (abs,Y), `BE/BC` (LDX abs,Y / LDY abs,X)

```bash
# example: find all LDA $1234 in a reference binary
xxd -p reference/main.bin | tr -d '\n' | grep -ob 'ad3412'
```

(Each hit's file offset = matched hex offset / 2; address = offset + target base. Beware false positives where the pattern spans two instructions — confirm each hit by disassembling around it with `dasm6502.py`.)

### Step 4: Analyze each reference

For each confirmed site:

1. Disassemble the surrounding routine (`.claude/scripts/dasm6502.py --file BIN --base HEX START`), or read it in main.nw if already documented.
2. Classify as READ or WRITE.
3. Note what value is written (constant? computed?) or how the read value is used (branch condition, index, arithmetic).
4. Note the enclosing routine's purpose if known.

### Step 5: Conclude and apply

Summarize the reference table (address, routine, access, context), state the variable's purpose, and choose a concise UPPER_SNAKE_CASE name. Then apply it — do not wait for confirmation:

1. Add the EQU in the appropriate defines chunk (placed just before first use, per chunk-placement rules) with a descriptive comment. If the address falls inside an existing data chunk, prefer a real label in that chunk over an EQU.
2. Add the name to that chunk's `@ %def` line (no duplicates across chunks).
3. Replace all raw `$XXXX` references in main.nw — code operands, comments, and prose `[[$XXXX]]` — using word-boundary regex, skipping `EQU` and `%def` lines.
4. Re-run `/assemble`; all targets must stay byte-perfect.

### Notes

- The same ZP or data address may serve different purposes in different subsystems — use the zero-page aliasing convention (multiple EQU names, contextually applied) rather than one vague name.
- If the evidence is genuinely insufficient to name the address, give it a provisional descriptive name (what it *does*, e.g. `FRAME_PHASE_BYTE`), note the open question in prose with a `% TODO` marker, and move on — don't stall.
