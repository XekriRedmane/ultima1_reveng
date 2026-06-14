# re-status

Print the project scoreboard: every measurable completion criterion for the reverse-engineering effort. This is the compass for the autonomous loop — run it at the start of every session and after every round to decide what to do next and whether the project is done.

## Usage

```
/re-status
```

No arguments.

## Instructions

1. Build first so coverage numbers are current: run the `/assemble` pipeline (tangle + dasm all targets). If the build is broken, that IS the status — report it and fix before anything else.
2. Run the scoreboard from the project root:

```bash
python3 .claude/skills/re-status/status.py
```

3. Interpret the result and choose the next unit of work, in this priority order:

| Failing criterion | Next action |
|---|---|
| Not bootstrapped (no targets.json) | `/bootstrap` |
| Coverage < 100% on any target | `/find-gaps`, then `/disassemble` or data-chunk work on the chosen gap |
| EQU stubs or ORG stub chunks > 0 | `/re-next` (it prioritizes stubs) |
| Raw-hex JSR/JMP operands in code > 0 | Replace with labels/EQUs (label hygiene pass) |
| TODO-SYM markers > 0 | TODO-SYM sweep per reveng.md standing rule |
| Routines missing header plates > 0 | `/annotate` the affected sections |
| Chunk-placement violations > 0 | `/chunk-placement` |

4. When ALL of the above are green, the remaining work is editorial and is not fully machine-measurable. Check these by inspection:
   - Synthesis chapters exist and are current (`/synthesize`): subsystem overviews, data-structure reference, platform-independent algorithm descriptions.
   - Chapter organization matches function, not just memory address (see "When to reorganize" in reveng.md).
   - All uncovered graphics data has been rendered and embedded (standing rule in reveng.md).
   - The HTML site builds cleanly with no broken links (`/gen-html`).

5. The project is DONE when the scoreboard is green, the editorial checklist passes, and a full `/gen-html` run succeeds. Report the final status rather than looping further.

## Notes

- The "missing header plates" heuristic looks for `Behavior:` within 15 lines after each `SUBROUTINE`. A routine documented in a different but complete style may need its plate reformatted rather than written from scratch.
- Coverage is byte-perfect assembly match, which proves the bytes are *accounted for*, not that they are *understood*. HEX blobs count as covered — the stub/TODO metrics and editorial checks are what push toward understanding.
