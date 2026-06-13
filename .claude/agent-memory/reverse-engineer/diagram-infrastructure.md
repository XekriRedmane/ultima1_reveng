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

ROUND D1 DONE (this session): infrastructure + 4 marquee priority figures,
all in the Design part: fig:mode-fsm (7-state overlay machine, after the
GAME_LOAD dispatch in ch:architecture), fig:win-fsm (SPA->CAS->TM
flag-guarded win machine, in sec:winfsm), fig:dng-gen (5-pass dungeon
generator flowchart in ch:algorithms), fig:combat (monster-AI/combat
flowchart in ch:algorithms). PDF 1013 -> 1018 pages. 16/16 byte-perfect.
See TODO.md "Diagram campaign" for the remaining per-subsystem coverage.
