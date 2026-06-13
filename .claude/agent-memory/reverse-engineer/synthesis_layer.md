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

Added chapter labels for cross-refs: ch:boot, ch:intro, ch:stuph,
ch:engine (the assembly chapters), plus the five above. sec:makeindata is
the MAKE.INDATA section (a \section under \chapter{Game data}, NOT a chapter).

KEY CONVENTIONS proven for synthesis prose:
- verbatim/struct/pseudocode blocks are EXEMPT from the prose [[ ]] address-
  wrapping rule (they are literal, like code) -- the style-sweep awk must skip
  \begin{verbatim}..\end{verbatim}.
- a $[[...]] code-ref inside LaTeX MATH MODE crashes pdflatex; never put an
  address ref inside $...$ (write the formula in words or split the spans).
- opcode BYTE values in prose (\texttt{\$B0}, \texttt{\$2C}) are an allowed
  exception (CLAUDE.md) -- texttt, not [[ ]].
- \ref a section as section~\ref{sec:...}, not chapter~\ref -- mismatched
  \chapter/\section labels show as "undefined" only on the 2nd pdflatex pass.

WHAT REMAINS (all optional; the doc is functionally done): dedicated
algorithm sections for the SPA flight model + chargen point-buy math if
deeper treatment is wanted; the TM CRAFT_GFX render (own focused round, twin
of DNG 15, recipe in tm_subsystem.md); a possible Round-7 reorg promoting the
five synthesis chapters into a \part{Design} ahead of a \part{Implementation}.
BLOCKED: the four-continent world map render (needs /U1.VARS, absent from the
crack disk -- see makeindata_subsystem.md + TODO blocked list).
