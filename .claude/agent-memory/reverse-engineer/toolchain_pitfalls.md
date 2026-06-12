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
