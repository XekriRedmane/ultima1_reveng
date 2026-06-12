# assemble

Tangle main.nw and assemble every target with dasm, then verify byte-perfect matches against the reference binaries. Reports any errors.

## Usage

```
/assemble
```

## Instructions

The target list lives in `targets.json` at the project root. For each entry, the assembly source is `output/NAME.asm` and the reference is the `reference` path in the manifest.

1. Tangle: `python3 weave.py main.nw output`
2. Assemble each target (from `output/`):

```bash
dasm NAME.asm -f3 -oNAME.bin -lNAME.lst -sNAME.sym
```

3. Report the result:
   - If assembly succeeds with no errors, say so.
   - If there are unresolved symbols, list them all.
   - If there is an "Origin Reverse-indexed" error, run `python3 .claude/skills/assemble/reorder_chunks.py` (from the project root) to auto-fix, then retry.
   - If there are other errors (excluding "unreferenced chunk" warnings from weave.py), list them.

## Verify against reference binaries

After assembling, verify every target (from the project root):

```bash
python3 .claude/skills/assemble/verify.py          # all targets
python3 .claude/skills/assemble/verify.py NAME     # one target
```

Every target must be byte-perfect (or, during active RE of a new region, the only diffs must be the region not yet documented). Report each target's status.

## Reorder chunks

If chunk references get out of ORG order (causing "Origin Reverse-indexed" errors), from the project root:

```bash
python3 .claude/skills/assemble/reorder_chunks.py        # all targets
python3 .claude/skills/assemble/reorder_chunks.py NAME   # one target
```

## dasm notes

- Always use `-f3` (raw binary, no header) and always produce `.lst` and `.sym` files — other skills consume them.
