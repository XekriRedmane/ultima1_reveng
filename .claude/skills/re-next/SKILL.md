# re-next

Find the next highest-value unit of reverse-engineering work in main.nw and do it — identify the address's purpose, document it, verify the assembly, and propagate the new name.

## Usage

```
/re-next
```

No arguments. The skill scans the project to find the best candidate automatically and proceeds without asking — state the chosen candidate and a one-line rationale, then do the work.

## Instructions

You are reverse engineering a 6502 Apple II game (see `targets.json` for the game, targets, and reference binaries). This skill finds the next address worth reverse engineering, then fully documents it.

### Phase 1: Find a candidate

Candidates, in priority order:

1. **ORG stub chunks** — chunks marked `; STUB — not yet disassembled`. Grep main.nw for `STUB`.
2. **EQU stubs** — `EQU` lines whose comment marks them as stubs for un-RE'd routines.
3. **Raw hex `JSR $XXXX` / `JMP $XXXX` operands** in code chunks — unlabeled subroutine calls.
4. **Raw hex data operands** (`LDA $XXXX`, `STA $XXXX,X`, ...) outside zero page without a label.
5. **`TODO-SYM` markers** in prose — unsymbolized addresses/constants.
6. **HEX blobs without structure** — large data chunks whose format is unknown (lowest priority unless a recently RE'd routine consumes them).

**Prioritization within a class:**

1. **Most referenced** — count occurrences of each unlabeled address across main.nw.
2. **Called from already-documented routines** — understanding callees deepens understanding of callers.
3. **Adjacent to already-documented code** — fills gaps, reduces fragmentation.
4. **Game-state variables** — data addresses read/written by many routines clarify everything that touches them.

**Exclusions:**

- Addresses that already have labels or EQUs (check `output/*.sym` after a build, and grep main.nw).
- ROM ($D000-$FFFF) and I/O ($C0xx) addresses — give these EQU names if referenced, but they are not RE targets.

**Search method:**

1. Run `/assemble` so `output/*.sym` and `output/*.lst` are fresh.
2. Grep main.nw for `\$[0-9A-Fa-f]{4}` in code-chunk operand positions; cross-reference against existing EQU/label definitions.
3. Count occurrences, apply the priority order, pick one candidate. Do not ask the user — record the choice and a one-line rationale, then proceed.

### Phase 2: Classify the candidate

- Referenced by `JSR`/`JMP` → subroutine → `/disassemble` workflow.
- Referenced only by load/store/compare ops → data → `/trace-address` workflow.
- Both → treat as subroutine first (data refs may be self-modification or entry-point tables).

### Phase 3: Execute

Follow the `/disassemble` or `/trace-address` skill end to end, including verification (byte-perfect assembly via `verify.py`), label propagation (replace all raw-hex references to the address throughout main.nw — code, comments, and prose), and the chunk-placement check.

### Phase 4: Propagate and close out

1. Re-grep main.nw for the raw address (word-boundary regex, skipping `EQU` and `%def` lines) to confirm nothing was missed.
2. Update any prose `[[$XXXX]]` to `[[NEW_LABEL]]` and drop resolved `TODO-SYM` markers.
3. Re-run `/assemble`; all targets must remain byte-perfect.
4. Report what was learned: the routine/variable's purpose, new symbols introduced, and any earlier documentation this contradicts or enriches — then go fix that documentation (see "The feedback loop" in reveng.md).

### Notes

- File offset within a reference binary = address − base, where base comes from `targets.json`.
- Find callers by grepping main.nw for the address and by scanning the reference binaries for absolute-operand byte patterns (`20 LL HH` for JSR, `4C LL HH` for JMP).
- All analysis runs on the reference binaries, `output/*.lst`/`*.sym`, and main.nw — no external tools (Ghidra, emulators) are assumed.
