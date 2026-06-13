---
name: toolchain-pitfalls
description: dasm/weave pitfalls proven in rounds 0-2 of the Ultima I RE (RORG chunks, inline-arg disasm misalignment, SMC stale operands)
metadata:
  type: project
---

Toolchain facts proven byte-perfect in rounds 0-2.

**Why:** these cost debugging time once; don't rediscover them.

**How to apply:**
- Relocated code (load addr != run addr): chunk = `ORG file_addr` +
  `RORG run_addr` ... `REND`. dasm emits at ORG, labels get RORG
  values. File offset math: file = run - run_base + file_base. A
  chunk's ORG must equal previous chunk's end exactly or dasm dies
  with "Origin Reverse-indexed".
- dasm6502.py output misaligns after any JSR-with-inline-args
  (the $B700 library convention, PRINT_INLINE, MLIB_BRUN paths) and
  after DC.B $2C BIT-skip tricks. Always re-sync by hand from a hex
  dump; branch targets near these regions are suspect.
- SMC initial operands on disk are often STALE (different from any
  runtime value). Emit the stale value (byte-perfection), comment
  "stale operand; patched to X". Use `.label = *+1` before the insn.
- This game's code patches CPY/CPX immediates as loop limits and
  whole opcode bytes (JSR $20 <-> RTS $60) to toggle actors.
- NEVER `git stash` in this repo: the untracked .gitattributes
  (*.py eol=lf) keeps weave.py & co. phantom-dirty (CRLF working
  copies), so `stash pop` aborts with "would be overwritten".
  Recovery: `git add weave.py` (normalizes the index) then pop,
  then `git reset weave.py`. The ~20 template files have been
  phantom-modified since round 0 — leave them uncommitted.
- `git diff` (Myers) on main.nw wildly overstates HEX-chunk churn;
  use `--diff-algorithm=histogram` to see the real edit.
- Generate data-heavy chunks (string tables, glyph banks, images)
  programmatically from the reference binary into the noweb source
  -- rounds 6 and 10 were byte-perfect on first assembly that way,
  whereas hand-typed packed strings (round 8 READY_CLASSES) caused
  the only byte mismatches. dasm DC.B "text",$XX with the high-bit
  last char is the proven emission form.
- This codebase's "never-taken branch" idiom: CLC / DC.B $B0 /
  SEC -- the BCS consumes the SEC as its operand, giving dual
  entries that differ only in carry (TICK/TICK_SND, DISK_PROMPT).
- The status.py header-plate heuristic requires the literal string
  "Behavior:" within 15 lines after SUBROUTINE. Write plates with a
  Behavior: section from the start (round 12 had to retrofit 43).
- Overlay decomposition workflow proven in round 12 (OUT, 5230
  bytes, ONE byte wrong on first assembly): (1) full sweep with
  .claude/scripts/overlay_disasm.py --sym output/miu1.sym; (2) dump
  every data/string region programmatically to DC.B; (3) write
  chunks in address order with an EQU defines block for all
  engine/STUPH/state symbols (separate dasm targets cannot share
  labels). The one error was a branch whose target I assumed was
  the near RTS instead of computing it -- compute EVERY branch.
- dasm local labels are invisible across SUBROUTINE scopes; when
  routine B branches into routine A's tail, either merge them into
  one chunk/scope or promote the target to a global label.
- The overlays' hidden-instruction idiom: INY / DC.B $C9 / TAY --
  branch to the TAY lands inside "CMP #$A8" (OUT $97EF). Also the
  6502 trick catalog there: patched-JSR dispatch (operand rests on
  an engine RTS), LDY #imm whose immediate is STA'd to preserve Y.
