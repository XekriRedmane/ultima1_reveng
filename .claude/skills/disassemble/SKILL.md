# disassemble

Reverse engineer a 6502 subroutine at a given address: disassemble it, understand its logic, document it in main.nw, and verify byte-perfect assembly.

## Usage

```
/disassemble $XXXX
```

Where `$XXXX` is the entry address of the routine (e.g., `$0C25`, `0x0C25`, or just `0C25`).

## Instructions

You are reverse engineering a 6502 Apple II game. Given a subroutine address, fully document it. Targets, reference binaries, and base addresses come from `targets.json`; the routine lives in the target whose address range contains it (file offset = address − base).

### Step 1: Get the disassembly

```
python3 .claude/scripts/dasm6502.py --file FILE --base BASE $START [$END]
```

Where FILE is the reference binary containing the routine and BASE is its load address in hex, e.g.:

```
python3 .claude/scripts/dasm6502.py --file reference/boot1.bin --base 0800 0801
```

If END is omitted, it auto-detects the end at the next RTS/JMP/BRK. Don't trust the auto-detected end blindly: check for fall-through, multiple entry points, and code after a conditional branch past the "end".

Also dump the raw bytes (`xxd` at the file offset) and manually verify every branch offset — `target = branch_addr + 2 + signed_offset` (offset ≥ $80 is backward). Most disassembly errors are branch labels on the wrong instruction.

### Step 2: Trace the logic

Work through the instructions step by step:
- Track register values (A, X, Y) and flags (C, Z, N, V).
- Identify the inputs (what registers/memory the routine reads on entry).
- Identify the outputs (what registers/memory it sets before returning).
- Note any side effects (memory writes, self-modification).
- For loops, determine the iteration count and exit condition.
- For branches, describe both paths.
- Watch for 6502 idioms:
  - `CLC; ADC #$XX` where $XX > $7F = subtract (unsigned complement)
  - `SEC; SBC` = subtract
  - `ASL/ROL` chains = multiply by powers of 2
  - `LSR/ROR` chains = divide by powers of 2
  - `AND #mask; CMP` = bit field extraction
  - `EOR #$FF; CLC; ADC #$01` = negate
  - Self-modifying code: `STA` into an instruction operand
  - `DC.B $2C` (BIT abs) skipping the next 2-byte instruction — multi-entry point

### Step 3: Identify callers

Find all callers without external tools:

1. Grep main.nw for the address (documented callers come with context).
2. Scan every reference binary for the call byte patterns `20 LL HH` (JSR) and `4C LL HH` (JMP), little-endian. Confirm each hit by disassembling around it — a match can span two unrelated instructions.

Sample a few callers to confirm your understanding: what values they pass in A/X/Y, and how they use the results.

### Step 4: Choose a name

Pick a descriptive UPPER_SNAKE_CASE name based on what the routine does (purpose, not mechanism). Examples:
- Arithmetic: `POS_TO_COLROW`, `MUL_BY_16`, `RANDOM`
- Lookups: `GET_SPRITE_PTR`, `COMPUTE_ROW_ADDR`
- Actions: `PRINT_FONTCHAR`, `SCROLL_STATUS_WINDOW`
- Predicates: `CHECK_COLLISION`, `IS_ON_FLOOR`

### Step 5: Write the documentation in main.nw

Add a new section with the routine's documentation and assembly chunk:

```
\section{What the routine does}

One or two sentences describing what the routine does, its inputs, and
outputs. Important details about the algorithm or side effects.

<<chunk name>>=
        ORG     $XXXX
ROUTINE_NAME:
        SUBROUTINE
        ; [header plate per CLAUDE.md annotation rules]

        [assembly with comments]
@ %def ROUTINE_NAME
```

Follow all CLAUDE.md rules: header plate after SUBROUTINE, `.local` labels, labels/EQUs instead of raw addresses (EQU stubs for not-yet-RE'd callees), `label = *+1` for self-modified operands, ASCII-only comments, section headers without numeric addresses. Place the chunk per chunk-placement rules and add its reference to the target's collection chunk in ascending ORG order.

### Step 6: Verify the assembly

Run `/assemble`. The target must be byte-perfect. If there are mismatches:
- Branch target off by N bytes → label on the wrong instruction (recompute from the binary).
- Zero-page vs absolute addressing → check the original opcode byte; force absolute with `DC.B` if dasm optimizes.
- Missing fall-through between adjacent routines.
- Self-modifying storage bytes emitting runtime values instead of disk-image values.

### Step 7: Update references

Replace every raw `$XXXX` reference to the routine in main.nw — `JSR`/`JMP` operands, comments, and prose `[[$XXXX]]` — with the new label (word-boundary regex; skip `EQU` and `%def` lines). Remove any EQU stub for the address. Re-run `/assemble` and `check_placement.py`.
