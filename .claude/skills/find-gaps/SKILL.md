# find-gaps

Assemble all targets, compare against the reference binaries, and produce a prioritized list of undocumented gaps.

## Usage

```
/find-gaps
```

No arguments.

## Instructions

### Step 1: Assemble

Run the `/assemble` pipeline (tangle with weave.py, then dasm each target listed in `targets.json`). If assembly fails, report the error and stop — a broken build is the more urgent problem.

### Step 2: Verify

From the project root:

```bash
python3 .claude/skills/assemble/verify.py
```

With no arguments this reports coverage and gaps for every target in `targets.json`.

### Step 3: Contextualize the gaps

For each target with gaps:

1. **Coverage summary**: X/Y bytes (Z%) documented, N gaps remaining.
2. For each large (≥500 B) and medium (100–499 B) gap, find the nearest labels before and after using the target's `.sym` file:

```bash
grep -i 'XXXX' output/TARGET.sym
```

3. Peek at the gap's content in the reference binary (`xxd` at offset = address − base) and classify: code (plausible opcodes), graphics (sprite-like bit patterns), tables (regular strides), text (high-bit ASCII), or zero fill.

### Step 4: Prioritize and proceed

Rank the gaps:

1. Code gaps reachable from documented code (a `JSR`/`JMP` into the gap exists) — highest.
2. Data gaps consumed by documented routines.
3. Large opaque blobs — decompose into classified sub-chunks even if full understanding comes later.
4. Zero-fill / padding — verify it really is padding (check the reference bytes), then emit as a documented filler chunk.

Report the ranked list. When running autonomously, pick the top gap and continue with `/disassemble` (code) or `/trace-address` / data decomposition (data) without asking. When the user invoked this skill interactively and the choice genuinely matters, present the list and let them choose.
