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
- LITERATE CHUNK BOUNDARIES must fall on instruction starts, never
  inside inline-arg text (round 22/GEN: 3 picker labels were placed
  on the menu TEXT, 7 bytes past the real entry -- the routine begins
  at the LDY/LDX/JSR MSG_AT that PRINTS the menu, and the text is its
  inline arg). A chunk that ORGs mid-inline-text re-disassembles the
  text as garbage code and dasm dies "Origin Reverse-indexed". The
  byte-perfect single-SUBROUTINE emission gets it right (labels via
  labelnames); the per-chunk split must reuse those same starts.
- DATA-vs-CODE TELL: a region that disassembles to many JSR/JMP with
  absolute operands spelling ASCII ("JSR $4F42" = "BO", "JSR $2020"
  = "  ") is a STRING/DATA blob, not code. Confirm with a ref scan
  (does any KNOWN-GOOD code region JSR/JMP into it?) -- if nothing
  references it, emit HEX (round 22: GEN's $A3C5-$A7B7 boot-loader
  image executes only on the booted player disk, inert in GEN's space;
  emitting it as code created 28 phantom raw-hex operands).
- SHARED LABEL NAMES across separate dasm targets are fine at assembly
  time (each target has its own defines) but the noweb @ %def index is
  global: declare a shared name (OVERLAY_ENTRY) in @ %def exactly ONCE
  (the first overlay), and rename any genuinely-different routine that
  reuses an existing @ %def name (round 22: GEN DO_BSAVE->SAVE_PLAYER,
  PRESS_SPACE->FMT_PRESS_SPACE). Duplicate @ %def across defines blocks
  (MON_CH/MON_HOME) only yields a benign "multiply defined label"
  LaTeX warning, not an error -- but distinct-routine collisions must
  be renamed for correct [[xref]] navigation.
- gen_chapter_* name() must fall back to a literal $XXXX for a branch/
  jump target that is NOT an instruction start (operand-byte targets
  from relocated/data code) -- guard with `a16 in targets and a16 in
  starts`, and map targets that land in a named data span to LABEL+off.
- THE SINGLE-SCOPE SELF-TEST HIDES CROSS-CHUNK .L FAILURES. The chapter
  self-test (gen_chapter_*/tm_chapter_* -> /tmp/*_all.asm) emits ONE big
  SUBROUTINE, so any .Lxxxx defined in routine A and referenced from
  routine B resolves fine -- but the REAL tangle gives each literate chunk
  its OWN SUBROUTINE, and dasm scopes .L per-SUBROUTINE, so cross-chunk
  .L refs die "Unknown Mnemonic 'jsr .L9xxx'" (round 23/TM: 36 helper
  subroutines, 62 refs). ALWAYS run the real per-chunk tangle (expand the
  <<tm.asm>> collection keeping every SUBROUTINE) as the FINAL byte-check,
  not just the single-scope self-test. Fix = promote every cross-chunk .L
  target to a named global label (tm_labels.LBL). GEN had 0 cross-chunk
  refs (each routine self-contained) so it never surfaced; multi-helper
  overlays (TM) hit it hard.
- A second inline-text trampoline is easy to miss: TM has BOTH POPUP_TEXT
  ($A436 framed) and POPUP_TEXT_NF ($A43C unframed), each falling into
  MSG_PRINT with inline text; and MLIB_BLOAD ($B703) takes an inline
  zero-terminated PATH ("NIF",0 for the victory screen). Any inline-text
  routine omitted from the INLINE map garbles its string as code (the
  raw-hex-JSR tell). Enumerate every JSR-then-text site before emitting.
- tm_build_section BANDS (the grouped-EQU emitter) must cover EVERY
  out-of-file SYM address or the EQU silently drops and the tangle fails
  undefined (HGR1 $2000 fell between bands). Add a catch-all "other" band.
- In-code 1-byte BSS storage bytes (BRK fillers between routines that are
  abs-referenced as flags/counters: TM GEM_GONE/IDLE_CNT/ANIM_CNT) each
  need a 1-byte DATA_SPAN + DATA_LABEL, else they assemble as part of a
  neighbouring instruction or stay raw-hex.
- Don't EQU an absolute-addressed ZERO-PAGE operand (e.g. LDA $00D6,Y):
  giving $00D6 a symbol lets dasm re-optimize it to 2-byte zero-page form
  and diverge. Leave such deliberate 3-byte abs-to-zp accesses raw.
- TO RECOVER A DECOMPRESSOR'S OUTPUT (round 25/MAKE.INDATA), EMULATE the
  actual 6502 bytes, don't hand-translate the control flow. A scoped 64K-mem
  emulator (.claude/scripts/makeindata_emu.py, ~40 opcodes, run-as-subroutine
  until the entry RTS) is faster and correct where hand-porting the tricky
  backward branches is error-prone. Then de-interleave the page ($2000-relative
  via the canonical hires row formula) and render with render_hires.
- AUTHORING a self-modify-free copy/decompress loop byte-perfect: every
  16-bit pointer advance the original does as INC lo / BNE / INC hi must be
  written out IN FULL -- a bare `INC MI_SRC` assembles to one byte and silently
  diverges (round 25 diverged 83 bytes this way). Transcribe the reference
  disassembly literally; don't "simplify".
- A TIGHTLY INTERWOVEN routine (run-continuations that branch back into the
  header parser and share one store-and-return RTS, like MAKE.INDATA's
  $1E47-$1EFC) must be ONE chunk / ONE SUBROUTINE so the .local branch targets
  resolve. Splitting it on the documented entry points (MI_DECODE_RUN/_BACK)
  forces cross-chunk .L refs that die in the real per-chunk tangle. Keep the
  documented entries as local labels (.run/.back) inside the single scope.
- A `$[[...]]` code-ref inside LaTeX math mode CRASHES pdflatex ("\ttfamily
  invalid in math mode") -- noweb [[ ]] expands to \Tt{} which can't live in
  $...$. Never put an address ref inside math; write the formula in words or
  put the math and the ref in separate spans (round 25).
- The status.py plate heuristic needs the LITERAL "Behavior:" within 15 lines
  of SUBROUTINE; a perfectly good plate written without that header word counts
  as "missing" (round 25 had 4). Always include a "Behavior:" line.
