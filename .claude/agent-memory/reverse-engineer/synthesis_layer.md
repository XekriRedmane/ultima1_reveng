---
name: synthesis-layer
description: Ultima I main.nw synthesis (design) chapters -- the platform-independent layer added rounds 26-30. All 6 synthesize-skill section types now exist.
metadata:
  type: project
---

The document is byte-complete (all 16 targets byte-perfect, hygiene fully
green) AND now carries a full SYNTHESIS LAYER -- the platform-independent
design prose that makes it "done" per CLAUDE.md. Added rounds 26-30, placed
as five chapters right after \chapter{Introduction} and before the
\chapter{Disk layout and boot chain} assembly chapters (overview before
evidence):

1. ch:architecture -- Architecture overview (engine/overlay model, GAME_LOAD
   dispatch, the universal mode template + patched-JSR idiom, shared state,
   THE WIN CONDITION as a state machine, rendering overview).
2. ch:datastructures -- Data-structure reference (the PlayerBlock struct =
   the /U1.PLAYER save format; the 5x80 object records; the 764-byte TCMAPS
   record; the world map; the 3 coordinate frames).
3. ch:algorithms -- Algorithm descriptions (the 2 PRNGs; the TICK food/time
   economy; procedural dungeon generation; the ray marcher; shop pricing
   index^2*charisma; monster spawn-by-tier + sqrt pursuit).
4. ch:rendering -- The rendering pipeline (Apple-II-specific-vs-portable
   table: interleaved hires/NTSC/page-XOR/softswitches discarded; glyph
   banks + DRAW_MAP 19x9 + the 2 wireframe styles portable).
5. ch:porting -- Porting notes (the 6502 idiom catalogue: SMC dispatch/
   operands/opcodes, the CLC/.byte $B0/SEC + .byte $2C dual-entries, inline-
   arg conventions, binary-vs-BCD, machine/OS seams).

These five cover all six synthesize-skill section types (overview +
architecture are both in #1). PDF grew 962 -> 1005 pages across the layer.

ROUND 31-32 (final polish, all optional items now resolved):
- ch:algorithms gained TWO more sections: "The space-flight model" (SPA's
  real-time rotation/thrust torus sim -- the one non-turn-based mode) and
  "Character generation: the point-buy" (the 30-pt pool, floor 10/ceiling 25,
  race/class deltas applied AFTER point-buy with no ceiling re-check, derived
  values from GAME_IMAGE). All constants verified firsthand from the asm.
- THE DOCUMENT IS NOW SPLIT INTO TWO \part's: \part{Design} (part:design,
  before ch:architecture) holds the five synthesis chapters; \part{Implementation}
  (part:implementation, before the disk-layout chapter) holds the nine
  annotated-assembly chapters. Purely additive -- the chapters were already
  in that order. Introduction got a two-part roadmap paragraph. Both part
  labels resolve; both appear in the ToC. PDF now 1013 pages.
- THE DOC IS COMPLETE. Nothing valuable left. The two un-imaged graphics
  (world map, TM craft interior) are blocked with full evidence they cannot
  be faithfully produced from the materials on hand (see TODO blocked list,
  makeindata_subsystem.md, tm_subsystem.md).

Added chapter labels for cross-refs: ch:boot, ch:intro, ch:stuph,
ch:engine (the assembly chapters), plus the five above. sec:makeindata is
the MAKE.INDATA section (a \section under \chapter{Game data}, NOT a chapter).

KEY CONVENTIONS proven for synthesis prose (now Markdown/HTML -- the doc
weaves to HTML via weave_html.py; the old LaTeX notes below are restated):
- fenced code / pseudocode blocks (```text, ```mermaid) are literal and
  EXEMPT from the prose [[ ]] address-wrapping rule, like code chunks.
- don't put a [[ ]] address ref inside $...$ math -- KaTeX renders the span
  as TeX, so the ref won't link; write the formula in words or split spans.
- opcode BYTE values in prose are written as `code` backticks (e.g. `$B0`,
  `$2C`), not [[ ]] -- and wrapping a $NN that sits next to another $ in
  backticks also stops the $...$ math rule from eating the span.
- diagrams are Mermaid (```mermaid), state machines/flowcharts included;
  byte/record/memory layouts are HTML tables; data tables are pipe tables.
- cross-reference with a Markdown link to the target's anchor
  (`[text](#fig:...)` / `[[SYMBOL]]`); the weaver resolves anchors
  site-wide across the multi-page split, so cross-page refs just work.

WHAT REMAINS: nothing valuable. All three formerly-open optional items are
resolved (rounds 31-32): the SPA flight-model + chargen point-buy algorithm
sections were ADDED; the \part{Design}/\part{Implementation} reorg was DONE;
and the TM CRAFT_GFX render was RE-ASSESSED as INFEASIBLE (not just deferred)
-- it is a scanline-RLE display list over ~13 indirect ZP base pointers the
resident STUPH/MI.U1 actor engine sets up at runtime, none initialized in any
target, so a faithful image needs a full actor-engine emulator with no
correctness guarantee (tm_subsystem.md). BLOCKED (genuinely, not lazy): the
four-continent world map render needs /U1.VARS, absent from the crack disk
(makeindata_subsystem.md + TODO blocked list). Both un-imaged graphics are
documented in prose + their verbatim data, the honest level of treatment.
