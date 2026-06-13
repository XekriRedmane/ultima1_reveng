---
name: diagram-infrastructure
description: The TikZ diagram campaign (rounds D1+) -- shared preamble, reusable styles, the bytefield workaround, and the per-figure quality bar for Ultima I main.nw.
metadata:
  type: project
---

The user wants main.nw to LEAN IN to diagrams/flowcharts augmenting the
prose (decided WITH the user). Toolchain is TikZ/PGF only -- NO
graphviz/mermaid/plantuml (can't install without root; TikZ is the best fit
for a LaTeX print doc anyway). Everything must build with stock TeX Live for
reproducibility.

**Why:** the byte-perfect RE is complete; this is a pure prose-side
augmentation phase. Diagrams are conceptual in the Design part and targeted
(beside routines) in the Implementation part.

**How to apply:**

- SHARED INFRASTRUCTURE lives in main.nw's OWN preamble (NOT noweb.sty).
  The user's prompt said noweb.sty, but noweb.sty is loaded at line 4
  (\usepackage{noweb}) BEFORE \usepackage{tikz} at line ~34, so
  \usetikzlibrary there would fail; and noweb.sty's own header says "DON'T
  edit". So the diagram block sits right after the existing tikz line in
  main.nw, bounded by the comment markers "% --- Muted palette" ...
  "\newcommand{\dgfield}" then "\noweboptions". Extra libs loaded:
  shapes.misc, automata, fit, chains, backgrounds (positioning,
  arrows.meta, shapes.geometric, calc etc. were already there).

- BYTEFIELD IS NOT INSTALLED in this TeX Live and can't be added without
  root. Do NOT \usepackage{bytefield}. Instead use the plain-TikZ
  substitute defined in the preamble: the `dgrecord` environment +
  `\dgfield{span}{label}{off-lo}{off-hi}` macro (a vertical stack of
  labelled boxes, row height proportional to byte span, offset gutter at
  left). Offsets in record/memory-layout diagrams are the documented
  address-wrapping exception (like a memory map).

- REUSABLE STYLES (all on a muted palette: dgproc/dgdeci/dgterm/dgio/
  dgstate/dgmem fills, dgline strokes, dgaccent for the win path/hazards):
  * flowchart: dgprocess, dgdecision, dgterminal, dgio, dgsub (call-out),
    dgnote (borderless annotation).
  * state machine: dgstate (circle), dgmode (soft box), dgaccentedge +
    dgaccentnode (the critical/win path).
  * memory: dgmemblock; plus dgrecord/\dgfield above.
  Every tikzpicture opens with [dg, >=Stealth] to get the shared defaults
  (dark-grey Stealth arrowheads, footnotesize). Pass node distance per-fig.
  PITFALL: dgaccentnode and dgaccentedge set ONLY draw=dgaccent+thick (no
  shape/fill/align). dgaccentedge is fine on a \draw. But dgaccentnode must
  be LAYERED on a base node style -- write [dgprocess, dgaccentnode] (or
  dgmode/dgstate + dgaccentnode). Used alone on a \node it has no shape and
  pdflatex dies with "Something's wrong--perhaps a missing \item."

- QUALITY BAR (non-negotiable, enforced every round): clean 2-pass
  pdflatex (0 errors, 0 NEW undefined refs); every diagram is a float with
  \caption + \label, REFERENCED from surrounding prose via Figure~\ref{}
  (the doc uses plain \ref, NOT cleveref -- match it); FAITHFUL to the RE'd
  behavior (derive every transition/branch from the asm + agent-memory
  subsystem notes, never invent -- a wrong diagram is worse than none);
  symbols not raw hex except in memory/disk-layout diagrams; diagrams are
  PROSE-SIDE ONLY (never touch a code chunk; the 16/16 byte-perfect verify
  stays green); keep them reasonably sized (no tikz externalize -- it needs
  shell-escape).

- FAST TEST LOOP (avoids the ~1000-page full build per edit): extract the
  preamble block with
    awk '/^% --- Muted palette/{f=1} /^\noweboptions/{f=0} f' main.nw
  into a standalone .tex with the two \usetikzlibrary lines, then paste the
  figure(s) (convert [[X]] -> \texttt{X} for the standalone). A 36pt
  Overfull \hbox in a caption in the standalone is a HARNESS artifact (the
  test \textwidth is narrower than report+noweb); ignore it. Only run the
  full tangle -> verify.py 16/16 -> 2-pass pdflatex gate before committing.

FIGURES SO FAR (label -> chapter -> page at time of writing):
- Round D1 (Design part): fig:mode-fsm (7-state overlay machine, after the
  GAME_LOAD dispatch in ch:architecture), fig:win-fsm (SPA->CAS->TM
  flag-guarded win machine, sec:winfsm), fig:dng-gen (5-pass dungeon
  generator, ch:algorithms), fig:combat (monster-AI/combat, ch:algorithms).
- Round D2: fig:mode-loop (universal mode main-loop template, ch:architecture
  "anatomy of a mode"), fig:npc-ai (TWN/CAS NPC states, ch:algorithms),
  fig:mondain-ai (Mondain's AI -- the FIRST Implementation-part targeted
  figure, beside MONDAIN_TURN in the TM chapter).
- Round D3 (ch:datastructures, record/memory layouts): fig:playerblock (the
  458-byte /U1.PLAYER save image via dgrecord), fig:soa (the 80-slot object
  table as a structure-of-arrays grid -- plain TikZ + accent brace, NOT
  dgrecord, because the SoA point is the transpose), fig:tcmap (the 764-byte
  TCMAPS record via dgrecord). NOTE: \dgfield was refined this round -- height
  is now CLAMPED (sqrt-compressed past 4 bytes, guarded max(span-4,0) because
  pgfmath ternary evaluates BOTH branches so a bare sqrt(span-4) crashes on
  span<4) and the byte size prints in a right column.

- Round D4: fig:bootflow (cold-start load chain, ch:architecture "Boot and
  load flow"), fig:dispatch (patched-JSR command dispatch call graph,
  targeted in the TWN command-table subsection). fig:bootflow as
  ch:architecture's FIRST figure renumbered that chapter's figures -- fine,
  all cross-refs use \ref and auto-update; always re-verify all labels
  resolve after inserting a figure early in a chapter.

- Round D5 (ch:rendering, the chapter's first figures): fig:pageflip
  (two-page XOR double-buffer flip), fig:tileblit (DRAW_MAP 19x9 nested
  loop), fig:raymarch (DNG_DRAW ray-marcher slice loop, cross-refs
  fig:dng-gen), fig:sprite (SPA/TM BLIT_SHAPE_AT projected-vector + XOR
  sprite, cross-refs fig:pageflip).
- Round D6 (sec:makeindata): fig:mi-decode (MI_DECODE column-major stream
  decompressor state machine), fig:mi-payload ($8700 high-bit RLE).
- Round D7 (Implementation, per overlay): fig:out-loop, fig:dng-loop,
  fig:spa-loop -- the three main-loop variants of the generic fig:mode-loop.
- Round D8: fig:layers (ch:architecture, 3-layer call-direction graph +
  $1583 vector band + the lone GAME_LOAD->OVERLAY_ENTRY upward jump),
  fig:gameload (engine, GAME_LOAD internals), fig:memmap (ch:architecture,
  blocks view of tab:memmap-arch with lifetime braces -- uses
  decorations.pathreplacing brace), fig:disklayout (ch:disk, /U1 files ->
  boot/load chain).

- Round D9 (GEN, the last per-subsystem gap): fig:chargen (ch:algorithms,
  the point-buy editor flow + race/class bonuses with no ceiling re-check),
  fig:format (Implementation, the two-layer disk formatter: RWTS_FORMAT
  physical GCR format then FORMAT_VOLUME ProDOS directory writer).

27 CAMPAIGN FIGURES total after D9. ALL checklist priority families DONE
(state machines, flowcharts, NPC/AI states, per-mode loops, RLE
decompressors, boot/load flow, memory/record layouts, call graphs,
rendering pipeline). Every warranting subsystem has >=1 figure across the
Design + Implementation parts. Remaining work is optional deepening (e.g. a
GEN chargen-flow or disk-formatter-RWTS figure), not a gap.

PDF 1013->1018(D1)->1021(D2)->1023(D3)->1026(D4)->1030(D5)->1032(D6)->
1033(D7)->1038(D8)->1040(D9) pages. 16/16 byte-perfect throughout. The brace
decoration (decorations.pathreplacing, already loaded line 35) is the way to
annotate spans in blocks/memory diagrams.
