# TODO

This file is the **loop state** for the autonomous RE process (see the
"Autonomy protocol" in `reveng.md`). Milestone entries at the top record
what each round finished and learned; the open work queue, structural
items, and blocked list live at the bottom. Every round updates this
file before committing. A fresh session resumes from `/re-status` output
plus this file — never by re-deriving history.

## Milestones

### Round D7 (2026-06-13): Per-mode main-loop variants (OUT/DNG/SPA)

- Three targeted loop-variant flowcharts in the Implementation part, each
  beside its overlay's main loop, each distinct from the generic
  fig:mode-loop in dispatch + tick contents:
  * fig:out-loop -- OUT_MAIN: reset stack/prompt -> STATS_VALUES -> death
    gate (hits=0 OR food=0 -> DEATH) -> KEY_OR_IDLE -> idle (food -0.05,
    time +0.50, TURN_PASS) or cmd (GET_COMMAND -> CMD_TBL -> patch
    DISPATCH_VEC -> JSR) -> TURN_PASS -> loop. After the OUT_MAIN chunk.
  * fig:dng-loop -- DNG_MAIN: DNG_DRAW redraw at top (accent-highlighted)
    -> death gate -> DNG_PROMPT (idle cheaper 0.01/0.10, MON_TURNS each
    beat, FIGHT_FLAG re-prompt) -> DNG_CMDS patched JSR -> MON_TURNS -> loop.
    After the DNG_CMDS table.
  * fig:spa-loop -- SPA_LOOP: status -> KEY_GET (timeout -> straight to
    PHYSICS) -> SPEND_TURN/GET_COMMAND -> flight cmd (idx<8) gated on fuel
    -> DISPATCH_PATCH self-modified JMP (tail jump, NOT JSR) -> PHYSICS
    (torus integrate + dock/collide/star hazard, continuous, no discrete
    tick) -> loop. After the spa main loop chunk; added a short intro para.
- All faithful to the asm (read OUT_MAIN, DNG_MAIN+DNG_PROMPT, SPA_LOOP+
  PHYSICS firsthand): the idle food/time costs, the DNG top-of-turn redraw,
  the SPA tail-jump dispatch + fuel gate + continuous physics. dgaccentnode
  must be LAYERED on a base style (dgprocess, dgaccentnode) -- alone it sets
  only the draw colour and triggers a "missing \item" error.
- Prose-side only; 16/16 byte-perfect; 2-pass pdflatex 0 errors / 0
  undefined refs; all 3 labels resolve + \ref'd. PDF 1032 -> 1033 pages.
- NEXT: the remaining structural call/memory graphs (STUPH jump-vector
  table, overlay->engine call directions, GAME_LOAD internals flow,
  resident memory map + disk track/sector layout).

### Round D6 (2026-06-13): The two makeindata RLE decompressors as flowcharts

- Two targeted flowcharts in the MAKE.INDATA section (sec:makeindata,
  Implementation part's Game-data chapter):
  * fig:mi-decode -- the MI_DECODE stream decompressor as a per-call state
    machine: resume vertical run / resume background run / else fetch byte
    -> sentinel A (vertical (length,value) run) / sentinel B (background
    (rows,span) run + MI_BACK back-reference replay) / literal; all paths
    converge on .store_ret. Placed after the MI_DECODE chunk.
  * fig:mi-payload -- the $8700 payload's high-bit-flagged RLE: zero the
    $9600-$B5FF buffer -> fetch byte -> bit7 set = (value,count) run else
    literal -> OR $80 onto each output byte -> stop at dest page $B7. Placed
    after the MI_PAYLOAD_IMAGE blob; cross-refs fig:mi-decode.
- Both faithful to the asm + makeindata_subsystem.md: fig:mi-decode from the
  MI_DECODE 3-mode interwoven scope (the two run flags MI_F_RUN/MI_F_BACK,
  the .startA/.back continuations, the shared .store_ret exit); fig:mi-payload
  from the payload prose (bit7 literal/run split, ORA #$80 on output, dest-hi
  == $B7 stop).
- Prose-side only; 16/16 byte-perfect; 2-pass pdflatex 0 errors / 0
  undefined refs; both labels resolve + \ref'd from prose. PDF 1030 -> 1032.
- NEXT: per-mode loop variants (OUT/DNG/SPA); the remaining structural
  call/memory graphs (STUPH jump-vector table, overlay->engine directions,
  GAME_LOAD internals, resident memory map + disk layout).

### Round D5 (2026-06-13): Rendering-pipeline diagrams (ch:rendering)

- Four conceptual figures, all in ch:rendering (Design part) -- the first
  figures in that chapter:
  * fig:pageflip -- the two-page XOR double-buffer flip: ZP_PAGE_XOR
    high-byte XOR ($00/$60) retargets every write; PAGE_FLIP = FRAME_SYNC ->
    show drawn page -> XOR ZP_PAGE_TGL to swap. Inserted after the "Two
    display pages, flipped" paragraph.
  * fig:tileblit -- the DRAW_MAP 19x9 tile-viewport blit as a nested-loop
    flowchart (terrain pass, then object/NPC overlay, then player tile).
    After the draw_viewport pseudocode.
  * fig:raymarch -- the DNG_DRAW ray-marcher slice loop (step forward,
    probe ahead+/-90 sides, draw_slice from DNG_GEOM[depth], SHAPE_DRAW
    monsters halved per depth, stop at solid/VIEW_DEPTH). Cross-refs
    fig:dng-gen. In the wireframe subsection.
  * fig:sprite -- the SPA/TM BLIT_SHAPE_AT sprite path (project -> pick
    frame -> SHAPE_PRESHIFT -> DRAW_MODE selects XOR draw/erase pass with
    ZP_BLIT_HIT collision vs OR/AND copy pass). Cross-refs fig:pageflip.
- All faithful to the asm: fig:pageflip from PAGE_FLIP/PAGE_COPY/VIEW_CLEAR
  (the EOR ZP_PAGE_XOR idiom + FRAME_SYNC + TXTPAGE soft switch + the
  ZP_PAGE_TGL swap); fig:raymarch from the DNG_DRAW pseudocode + the
  +/-90 integer-swap rotation; fig:sprite from BLIT_SHAPE_AT's two unrolled
  passes (DRAW_MODE bit6 = XOR+collision EOR write, BLIT_OP/BLIT_EOR copy).
- Prose-side only; 16/16 byte-perfect; 2-pass pdflatex 0 errors / 0
  undefined refs; all 4 labels resolve + are \ref'd from prose. PDF
  1026 -> 1030 pages.
- NEXT: the two makeindata RLE decompressors as flowcharts; the per-mode
  loop variants (OUT/DNG/SPA); the remaining structural call/memory graphs
  (STUPH jump-vector table, overlay->engine directions, GAME_LOAD
  internals, resident memory map + disk layout).

### Round D4 (2026-06-13): Dispatch call graph + boot/overlay-load flow

- Two structural diagrams:
  * fig:bootflow -- the cold-start LOAD CHAIN (PROM -> boot block -> ProDOS
    -> U1.SYSTEM -> MAKE.INDATA -> U1.INTRO -> keypress -> engine+overlay ->
    the GAME_LOAD loop), conceptual in ch:architecture's "Boot and load
    flow" (page 20). Cross-refs fig:mode-fsm. Load addresses shown (the
    documented memory-layout exception).
  * fig:dispatch -- the patched-JSR command DISPATCH call graph
    (GET_COMMAND -> CMD_TBL[X] -> patch the JSR operand -> JSR -> handler or
    QUERY_MARK -> back to loop), TARGETED in the TWN "command table and
    dispatch" subsection (page 393).
- Both faithful: bootflow from the architecture boot-chain enumerate +
  ch:boot/ch:intro; dispatch from the TWN CMD_TBL + the SMC dispatch idiom
  documented in ch:architecture and twn_cas_subsystem.md.
- Prose-side only; 16/16 byte-perfect; 2-pass pdflatex 0 errors / 0
  undefined refs. PDF 1023 -> 1026 pages. NOTE: adding fig:bootflow as
  ch:architecture's first figure renumbered that chapter's figures (mode-fsm
  2.1->2.2, etc.) -- all cross-refs use \ref so they auto-updated; verified
  all 12 campaign labels resolve and each is \ref'd from prose.

CAMPAIGN STATE after D4: 12 figures across both parts. Design part:
fig:bootflow, fig:mode-fsm, fig:mode-loop, fig:win-fsm (ch:architecture);
fig:playerblock, fig:soa, fig:tcmap (ch:datastructures); fig:dng-gen,
fig:npc-ai, fig:combat (ch:algorithms). Implementation part: fig:dispatch
(TWN), fig:mondain-ai (TM). Priority families (a) state machines and (b)
flowcharts are well covered; record layouts + boot/dispatch graphs started.

### Round D3 (2026-06-13): Memory/record bytefield layouts (data-structure chapter)

- Exercised the plain-TikZ bytefield substitute (dgrecord/\dgfield) on the
  three persistent structures, all in ch:datastructures:
  * fig:playerblock -- the 458-byte player block / /U1.PLAYER save image as a
    byte-layout map (logical bands, offset gutter, size column, row height
    tracking span so the 4 owned-item arrays read as the bulk). Page 30.
  * fig:soa -- the 80-slot object table drawn as a STRUCTURE OF ARRAYS (5
    named field-arrays as columns, one object = a highlighted slot-k row read
    across all five, with an accent brace). Page 31. Plain-TikZ grid, not
    dgrecord -- the SoA point is the transpose, which a vertical stack hides.
  * fig:tcmap -- the 764-byte TCMAPS town/castle record (684-byte grid + the
    5x16 NPC arrays at offset 684). Page 33.
- Refined \dgfield: row height now grows with span but is CLAMPED
  (proportional to ~4 bytes, sqrt-compressed beyond, guarded with
  max(span-4,0) so pgfmath never sqrt's a negative -- the ternary evaluates
  both branches), and the exact byte size is printed in a right column so it
  is never lost. The clamp keeps a 458-byte record compact on the page.
- All faithful to the verbatim structs already in the chapter (same field
  names/offsets); diagrams COMPLEMENT the structs, they don't replace them.
- Prose-side only; 16/16 byte-perfect; 2-pass pdflatex 0 errors / 0
  undefined refs; all 3 labels resolve + \ref'd. PDF 1021 -> 1023 pages.
  (The \dgfield macro change did not disturb the D1/D2 figures.)
- NEXT: the engine-API/dispatch CALL GRAPHS (STUPH jump-vector table, the
  patched-JSR dispatch, overlay<->engine call directions); the per-mode loop
  VARIANTS (OUT/DNG/SPA); the RLE decompressors; boot/overlay-load flow; the
  rendering-pipeline diagrams (double-buffer flip, ray-marcher slice loop).

### Round D2 (2026-06-13): AI state diagrams + universal mode-loop flowchart

- Continued the diagram campaign with 3 figures across BOTH parts:
  * fig:mode-loop -- the UNIVERSAL MODE MAIN-LOOP flowchart (entry -> status
    -> poll -> key/timeout -> dispatch -> ends? -> tick/GAME_LOAD), the
    template all seven overlays share. Conceptual, in ch:architecture's
    "anatomy of a mode" (page 22).
  * fig:npc-ai -- TWN/CAS NPC behaviour as a state machine (empty/hostile-
    kind-3/wanderer-kind-4, the AGGRO global-mood accent edge). Conceptual,
    in ch:algorithms beside the town/castle NPC paragraph (page 39).
  * fig:mondain-ai -- Mondain's AI (the 3-way distance choice melee/cast/step
    + the highlighted GEM_HP-regen-toward-500 side effect). TARGETED in the
    Implementation part beside MONDAIN_TURN in the TM chapter (page 910) --
    the first Implementation-part diagram, demonstrating the inline pattern.
- All faithful to the asm: fig:npc-ai from the TOWN_TICK branch logic
  (NPC_TYPE==3 -> dist<2 GUARD_COMBAT else home; ==4 NPC_WANDER; AGGRO
  switches all to wander); fig:mondain-ai from the MONDAIN_TURN plate +
  SCENE_TICK gem-heal ($19/per the regen path) + MONDAIN_SPELL_TBL (3
  spells). Derived firsthand, not invented.
- Prose-side only; 16/16 byte-perfect; 2-pass pdflatex 0 errors / 0
  undefined refs; all 3 labels resolve + are \ref'd from prose. PDF
  1018 -> 1021 pages.
- NEXT (see "Diagram campaign"): the per-mode main-loop VARIANTS targeted
  beside OUT/DNG/SPA loops; the RLE-decompressor + boot/overlay-load
  flowcharts; the memory/record bytefield layouts (dgrecord); the
  engine-API/dispatch call graphs.

### Round D1 (2026-06-13): Diagram campaign begun -- infrastructure + 4 marquee figures

- NEW WORK PHASE (decided with the user): lean the doc INTO TikZ
  diagrams/flowcharts that augment the prose. TikZ/PGF only (no
  graphviz/mermaid -- can't install without root; TikZ is the right fit for a
  LaTeX print doc anyway), builds with stock TeX Live for reproducibility.
- INFRASTRUCTURE (the foundation every later round reuses): added a
  documented shared-diagram block to main.nw's preamble (right after the
  existing tikz line -- NOT noweb.sty, which loads before tikz and is a
  vendored "don't edit" file; rationale recorded). Loaded shapes.misc,
  automata, fit, chains, backgrounds. Defined a muted 8-colour palette and a
  set of REUSABLE named tikzstyles: dgprocess/dgdecision/dgterminal/dgio/
  dgsub/dgnote (flowchart), dgstate/dgmode/dgaccentedge/dgaccentnode (state
  machine), dgmemblock (memory). bytefield is NOT installed and can't be
  added without root, so I built a plain-TikZ substitute: the dgrecord
  environment + \dgfield macro (a labelled vertical cell stack with an
  offset gutter) -- to be used for record/memory layouts in later rounds.
- 4 MARQUEE PRIORITY FIGURES authored (all in the Design part, all faithful
  to the RE'd behavior derived from the asm + agent-memory subsystem notes):
  * fig:mode-fsm -- the overall game as a 7-state machine over the overlays
    (GEN start, OUT hub, the flag-gated CAS->TM win arrow highlighted, the
    death->RESPAWN dashed path). In ch:architecture after the GAME_LOAD
    dispatch paragraph.
  * fig:win-fsm -- the SPA->CAS->TM win condition as a flag-GUARDED state
    machine (gem loop in castles, kill loop in space, the highlighted spine
    from rescue-the-princess -> TM_REVEAL -> destroy gem -> kill Mondain ->
    VICTORIOUS). In the new-labelled sec:winfsm.
  * fig:dng-gen -- the 5-pass procedural dungeon generator flowchart, with
    pass-4's level-1/level-10 special cases as dashed decisions. In
    ch:algorithms after the generator pseudocode.
  * fig:combat -- the monster-AI/combat-resolution flowchart (tier-gated
    spawn, fire-vs-close-vs-melee, to-hit vs armour, death frees slot +
    grants tier exp). In ch:algorithms after the spawn/pursuit prose.
- Every figure is a float with \caption + \label and is referenced from the
  surrounding prose via Figure~\ref{} (the doc uses plain \ref, not
  cleveref). All 4 labels + sec:winfsm resolve to real page numbers.
- DIAGRAMS ARE PROSE-SIDE ONLY -- not one code chunk touched. Full gate
  green: tangle clean, ALL 16 TARGETS BYTE-PERFECT (16/16), 2-pass pdflatex
  0 errors / 0 undefined refs (only the pre-existing benign font-shape +
  multiply-defined warnings remain, unchanged). PDF 1013 -> 1018 pages.
- NEXT: comprehensive per-subsystem fill-in across BOTH parts (see the
  "Diagram campaign" work-queue section). Priority families still to do:
  AI/NPC state diagrams (TWN/CAS idle anim, Mondain's AI), per-mode main
  loops, the RLE decompressors + boot/overlay-load flow flowcharts, then
  memory/disk maps + dgrecord bytefield layouts (player block, object
  arrays, TCMAPS, live map buffer), then engine-API/dispatch call graphs.
  Targeted Implementation-part diagrams beside the routines they explain.

### Round 32 (2026-06-13): Final polish -- Design/Implementation \part split

- The Round-7-style reorganization, evaluated and DONE because it cleanly
  improves the document with zero content churn. The five synthesis chapters
  were ALREADY contiguous and ALREADY ahead of the implementation chapters
  (built that way in rounds 26-30), so this was purely additive: inserted
  \part{Design: how the game works} (label part:design) before the
  Architecture overview, and \part{Implementation: the annotated program}
  (label part:implementation) before the Disk-layout chapter. Each part gets
  a short framing paragraph; added a two-part roadmap paragraph to the
  Introduction with cross-refs both ways (Part I <-> Part II).
- NOT ONE chapter moved and NOT ONE existing cross-reference changed -- the
  only risk was the two new \part labels, which resolve (part:design -> I,
  part:implementation -> II; both \ref{}s in the Introduction render "Part I"
  / "Part II"). Both parts appear in the ToC.
- Prose/structure-only; all 16 targets byte-perfect (16/16); hygiene fully
  green; PDF 1013 pages (the \part title pages add ~5), 0 LaTeX errors, 0
  genuinely-undefined references.
- THE DOCUMENT IS NOW COMPLETE. Every measurable criterion is green, all six
  synthesis section types exist (with the SPA + chargen algorithm sections
  added round 31), the design/implementation structure is explicit, every
  renderable graphic is rendered, and the two un-imaged graphics (world map,
  TM craft interior) are on the blocked list with full evidence that they
  cannot be faithfully produced from the materials on hand. Nothing valuable
  is left to do.

### Round 31 (2026-06-13): Final polish -- SPA + chargen algorithm sections; TM render judged infeasible

- Optional-polish pass on the functionally-done document. Two outcomes:
- (1) TM CRAFT_GFX render: RE-ASSESSED as INFEASIBLE from the materials on
  hand, NOT merely deferred. SHAPE_STEP/BLIT_LINE is a scanline run-length
  blitter (not a self-contained vector interpreter like the DNG/SPA shape
  galleries that rendered cleanly); CRAFT_GFX is pre-rasterized hi-res byte
  runs, not (dx,dy,pen) vectors. The stroker + ANIM_SETUP dereference ~13
  indirect ZP base pointers (($D6)..($FA),Y) that the RESIDENT STUPH/MI.U1
  shape-actor engine sets up at runtime -- verified by grep that NONE is
  initialized in any of the 16 targets. Imaging it needs a full actor-engine
  emulator + the live projection state, no correctness guarantee -> would
  risk a broken render (violates the don't-ship-broken-renders rule). Left
  un-imaged, documented in prose + the HEX blob + the SHAPE_STEP/BLIT_LINE
  plates. Moved from the work queue to the blocked list with full evidence;
  tm_subsystem.md updated. This is the honest call, not a skipped chore.
- (2) Added TWO new sections to the Algorithm descriptions chapter
  (ch:algorithms), the two gaps that genuinely help a porter and carry no
  render risk: "The space-flight model" (SPA -- the real-time
  rotation/thrust torus sim: ship state, the integration step + torus wrap
  $0E/$F4 and y AND $7F, the heading-indexed thrust/retro delta tables
  (0,-1)(+2,0)(0,+1)(-2,0) and their negation, the +/-8 velocity clamp,
  the coarse-4 flight heading vs the fine 27-frame render index, fuel costs
  5/5/2/fire, the star/dock/collide hazards, and PLR_VESSELS as the ONLY
  bridge to CAS at $14=20) and "Character generation: the point-buy" (the
  six 16-bit stats at PLR_HITS+2i, pool 30 floor 10 ceiling 25, the
  race/class bonus deltas applied AFTER point-buy with NO ceiling re-check
  so a Dwarf Fighter can reach 40 STR, sex cosmetic, derived values from
  GAME_IMAGE so starting level = 1). ALL CONSTANTS VERIFIED FIRSTHAND from
  the assembly (THRUST_DX/DY, RETRO_DX/DY, CLAMP_VEL, FUEL_BURN costs,
  POINT_POOL/floor/ceiling, the hardcoded PICK_RACE/PICK_CLASS deltas) --
  not taken on trust from the scout, which had a couple of self-flagged
  ambiguities (the star "drains shield" doc-vs-code; corrected to a warning).
- Prose-only; all 16 targets byte-perfect (16/16); hygiene fully green
  (0 stubs/TODO-SYM/missing-plates(348)/placement/raw-hex); PDF 1008 pages
  (was 1005), 0 LaTeX errors, 0 genuinely-undefined references (the only
  warnings are the pre-existing benign font-substitution + multiply-defined
  @ %def-overlap, unchanged -- my edit added 0 new labels). verbatim
  pseudocode blocks exempt from address-wrapping as established.
- REMAINING optional polish: only the Round-7-style reorganization
  (promote the 5 synthesis chapters into \part{Design} ahead of a
  \part{Implementation}) -- evaluate whether it cleanly improves the doc,
  skip if risky. After that the document has nothing valuable left to do.

### Round 30 (2026-06-13): Synthesis -- the Porting notes chapter (all 6 types done)

- Fifth synthesis chapter: \chapter{Porting notes: the 6502 idioms}
  (label ch:porting), after the rendering pipeline. The capstone of the
  synthesis layer -- a catalogue of every recurring 6502/Apple-II idiom,
  what it MEANS, and its portable replacement: (1) self-modifying code
  (patched-JSR/JMP dispatch -> function-pointer table; patched operands
  as variables incl. the stale-on-disk STALE_FFFF sentinel; patched
  opcodes JSR<->RTS toggling actors -> a boolean); (2) multi-entry
  routines (the CLC/.byte $B0/SEC carry dual-entry; the .byte $2C BIT-abs
  skip -> defaulted parameters); (3) inline-argument calling conventions
  (JSR-then-data -> ordinary args; the disassembler trap); (4) numbers &
  tables (binary quantities + BCD displays; precomputed squares/
  perspective/row-addr tables -- keep table CONTENTS where they encode
  tuning, drop them where they're just speed); little-endian 16-bit pairs
  via label+1; (5) machine/OS dependencies (soft switches, the VBL beat +
  the mouse-card-as-VBL trick, the file library/overlays, the hooked
  reset vector).
- THE SYNTHESIS LAYER NOW HAS ALL SIX synthesize-skill section types:
  game overview + architecture (ch:architecture), data structures
  (ch:datastructures), algorithms (ch:algorithms), rendering
  (ch:rendering), porting notes (ch:porting). A competent programmer who
  has never seen 6502 can reproduce/port each subsystem from these
  chapters, using the assembly only to check edge cases.
- Prose-only; all 16 targets byte-perfect; hygiene fully green; PDF 1005
  pages, 0 errors, 0 undefined refs.
- REMAINING (optional polish, the doc is functionally "done"): dedicated
  algorithm sections for the SPA flight model + chargen point-buy math if
  deeper treatment is wanted; the TM CRAFT_GFX render (its own focused
  round, twin of DNG 15; recipe in tm_subsystem.md); a Round-7 pass to
  consider promoting the five synthesis chapters into a "\part{Design}"
  ahead of a "\part{Implementation}" for the assembly chapters.

### Round 29 (2026-06-13): Synthesis -- the Rendering pipeline chapter

- Fourth synthesis chapter: \chapter{The rendering pipeline}
  (label ch:rendering), after the Algorithm descriptions. Draws the sharp
  Apple-II-specific-vs-portable line the synthesize skill's section 5
  asks for: (1) the hi-res screen a port DISCARDS (interleaved scanline
  layout, NTSC colour-artifact palette, two-page XOR double-buffer via
  ZP_PAGE_XOR, soft switches + VBL pacing); (2) the glyph banks that ARE
  portable (128-glyph plane-major font, 48 outdoor tiles, the MAPCHARS
  town bank; the ZP_INVERSE EOR mask = a "draw inverted" flag; plane-byte
  tile animation = two-frame cycling); (3) the two render styles (the
  19x9 tile viewport DRAW_MAP, given as portable pseudocode; the two
  wireframe variants -- the dungeon ray marcher and the SPA/TM projected
  vector strokes + the XOR sprite blitter); (4) a one-table summary
  mapping each Apple-II mechanism to its portable equivalent.
- Prose-only; all 16 targets byte-perfect; hygiene green; PDF 1001 pages
  (crossed 1000), 0 errors, 0 undefined refs.
- NEXT synthesis gaps: Porting notes per subsystem (the 6502 idioms a
  port must replace -- patched-JSR dispatch, self-modifying operands and
  the state they encode, the CLC/DC.B $B0/SEC dual-entry trick, indexed
  SMC); optionally dedicated algorithm sections for the SPA flight model
  and chargen math. Optionally the TM CRAFT_GFX render. The 5 of 6
  synthesize-skill section types now exist (overview, architecture, data
  structures, algorithms, rendering); porting notes is the 6th.

### Round 28 (2026-06-13): Synthesis -- the Algorithm descriptions chapter

- Third synthesis chapter: \chapter{Algorithm descriptions}
  (label ch:algorithms), after the Data-structure reference. Collects the
  non-trivial mechanics as platform-independent pseudocode + design
  intent -- the parts a porter cannot recover by translating instructions:
  (1) the TWO PRNGs (library lagged-additive = atmospheric/unpredictable;
  the DNG Fibonacci seed_step A'=A+B+9,B'=A = deterministic mazes);
  (2) the turn economy (TICK: food spent in BCD hundredths, faster
  transports cost less food AND time); (3) PROCEDURAL DUNGEON GENERATION
  (seed = 8*place^outdoor_x^level / 4*outdoor_y^continent; the five
  passes: edges 6/6/8, walls+fields 2*level+1, containers, fixed cells +
  ladders by parity, monsters; the cell-byte nibble packing + blocking
  rule); (4) the dungeon RAY MARCHER (walk facing, inspect ahead+2 sides
  via exact +/-90 vector rotation, perspective entirely in DNG_GEOM;
  SHAPE_DRAW vector shapes scaled by depth-halving); (5) shop pricing
  (base = index^2 squares table * charisma/wis/int haggle factor);
  (6) monster spawn (tier-gated on a rising difficulty bar, hp/exp =
  10*tier) + greedy integer-sqrt pursuit + melee-vs-armour.
- Prose-only; all 16 targets byte-perfect; hygiene green; PDF 997 pages,
  0 errors, 0 undefined refs. verbatim pseudocode blocks exempt from
  address-wrapping.
- NEXT synthesis gaps: a Rendering-pipeline chapter (tile blit + the two
  wireframe engines + double-buffering + the hi-res layout: what is
  Apple-II-specific vs portable), then Porting notes per subsystem (the
  6502 idioms a port must replace: patched-JSR dispatch, SMC operands,
  softswitches, cycle timing). Then the SPA flight model + chargen math
  could get their own algorithm sections. Optionally TM CRAFT_GFX render.

### Round 27 (2026-06-13): Synthesis -- the Data-structure reference chapter

- Second synthesis chapter: \chapter{Data-structure reference}
  (label ch:datastructures), placed after the Architecture overview.
  Documents every persistent structure abstractly with language-neutral
  pseudocode (same symbol names as the asm) + field tables + invariants:
  (1) THE PLAYER BLOCK as a struct -- it IS the /U1.PLAYER save format
  (458 bytes, first word = own length); all 30 fields named, the six
  attributes (STR/AGI/STA/CHA/WIS/INT at PLR_HITS+2), owned-item arrays
  as counts, level = exp/1000+1, coin shown as pence/silver/gold; the
  binary-vs-BCD note (only MOVE_CNT + FOOD_FRAC are BCD, a micro-opt).
  (2) THE OBJECT RECORDS -- five parallel 80-entry arrays (structure of
  arrays), OBJ_YC packs continent in top 2 bits, OBJ_HP unsaved, parked
  transports are object records. (3) THE TCMAPS town/castle record (764b:
  38x18 grid + 5x16 NPC arrays at offset 684). (4) The world map (4x
  64x64, RLE read-only from /U1.VARS, absent here). (5) The three
  coordinate frames (world / grid / 19x9 viewport) a port must not
  conflate.
- Prose-only; all 16 targets still byte-perfect; hygiene green; PDF 991
  pages, 0 errors, 0 undefined refs. verbatim struct blocks exempt from
  prose address-wrapping (literal, like code).
- NEXT: per-subsystem Algorithm descriptions (the biggest remaining
  synthesis gap) -- the dungeon maze generator + ray-marcher, the shop
  pricing/haggle, monster spawn/AI, the SPA flight model, chargen math,
  the PRNG, the turn/food/time economy. Then a Rendering-pipeline
  chapter, then Porting notes. Optionally the TM CRAFT_GFX render.

### Round 26 (2026-06-13): Synthesis begun -- the Architecture overview chapter

- FIRST synthesis chapter written: \chapter{Architecture overview}
  (label ch:architecture), placed right after the Introduction (overview
  before evidence, per the synthesize skill). The document had NO synthesis
  layer before this -- it was organized purely by file/subsystem. This is
  the spine the per-subsystem synthesis will hang from.
- Covers, in platform-independent terms a porter can use without reading
  6502: (1) the engine-and-overlays memory model (STUPH library + MI.U1
  engine resident, one mode overlay at a time over $8956; the overlay
  scheme is the 1986 memory-limit answer, not a design requirement);
  (2) boot/load flow + the single GAME_LOAD mode-dispatch (one integer,
  never returns -> a port models it as set_mode(id)); (3) the universal
  mode template (entry / timeout-polled main loop / per-command handlers /
  end-of-turn tick) + the patched-JSR dispatch idiom and its portable
  function-pointer-table equivalent; (4) the shared-state model (player
  block = the /U1.PLAYER save format; object records as structure-of-
  arrays; progress flags); (5) THE WIN CONDITION AS A STATE MACHINE (the
  gem prophecies -> Space Ace counter -> princess rescue sets the endgame
  flag -> TM: destroy the gem then kill Mondain; every arrow is a shared
  flag, so the progression is data, not control flow); (6) rendering in
  one paragraph (tile viewport vs wireframe vector; Apple-II-specifics
  isolated in STUPH).
- Added 4 chapter labels for cross-refs (ch:boot, ch:intro, ch:stuph,
  ch:engine). All [[ ]]-wrapped, ASCII-clean, refs resolve.
- Prose-only; all 16 targets still byte-perfect; hygiene fully green; PDF
  985 pages, 0 errors, 0 undefined refs.
- NEXT: continue the synthesis layer (the biggest remaining gaps, in
  rough priority): the Data-structure reference (player block fields +
  invariants, object-record arrays, the NPC/shop tables, coordinate
  systems), then per-subsystem Algorithm descriptions (dungeon maze
  generator + ray-marcher, the shop pricing/haggle, monster AI/spawn,
  the SPA flight model, chargen math), then a Rendering-pipeline chapter
  (tile blit + the two wireframe engines, double-buffering, the hi-res
  layout), then Porting notes per subsystem. Optionally the TM CRAFT_GFX
  render. Quality bar: a programmer who has never seen 6502 could
  reimplement each subsystem from its synthesis section alone.

### Round 25 (2026-06-13): MAKE.INDATA fully decomposed -- the LAST stub cleared

- MAKE.INDATA ($1E00-$5435, 13877 bytes) is decomposed across 13 chunks
  (8 code + 3 HEX data + entry + collection); byte-perfect (13877/13877).
  It is the cold-start BUILDER: the first program U1.SYSTEM chains to,
  predates the MI.U1 engine, runs once at $1E00, never touches the disk,
  and is discarded. THE FINAL ORG STUB IS GONE.
- WHAT IT ACTUALLY DOES (corrects the scout's guess): it builds the TWO
  TITLE SCREENS, not the world map. MI_BUILD ($1F17) stamps the $8700
  payload + the $6000 intro art into place, decompresses the castle title
  onto hi-res page 1 (MI_DECOMP from MI_TITLE_STREAM $49EC), runs the
  payload (which unpacks the ORIGIN SYSTEMS logo to $9600), then
  LFSR-fizzles the logo onto page 2. Leaves the castle ready on page 1
  for U1.INTRO to animate.
- TWO DECOMPRESSORS, both ported to a scoped 6502 emulator
  (.claude/scripts/makeindata_emu.py) to recover the rasters: MI_DECOMP
  ($1E03 driver + MI_DECODE $1E47 inner, ONE interwoven scope) is a
  column-major hi-res RLE with 2 sentinels (vertical run / background run
  with a back-reference replay); the $1E1D math is the canonical Apple II
  hi-res row->addr formula (verified). The $8700 payload is a second,
  simpler high-bit-flagged RLE that builds the logo at $9600.
- RENDERED both screens (standing rule): images/makeindata_title.png (the
  castle-by-the-sea night scene -- moon, stars, blue sea) and
  images/makeindata_origin.png (ORIGIN SYSTEMS INC.). Both embedded as
  figures. Renderer .claude/scripts/render_makeindata.py.
- RESOLVED the last TODO-SYM: the U1.INTRO ART_* region is the on-disk
  MI_ART_IMAGE ($27BD-$49EB, copied to $6000); art ends at $85FF, NOT the
  guessed $8Fxx. Updated the U1.INTRO prose + the ART_* defines comment.
- CORRECTED a stale claim: OUT's "/U1.VARS is written once by MAKE.INDATA"
  is FALSE -- makeindata has no disk code and builds only the title
  screens. Reworded the OUT save section. The packed world map loads
  read-only from /U1.VARS (absent from the crack disk); its origin is
  unconfirmed and is NOT makeindata. So "render the four continents" is
  NOT achievable here -- moved to the blocked list.
- Pitfalls (agent memory): every stream-ptr advance is a full 16-bit
  INC/BNE/INC (bare INC diverged 83 bytes); the interwoven decompressor
  must be ONE SUBROUTINE (run continuations branch back into the header
  parser, share .store_ret); emulate tricky backward-branch decompressors
  rather than hand-translating; 4 plates needed a literal "Behavior:"
  line for the status heuristic; data chunks reordered before first use
  to satisfy chunk-placement; one $[[...]] math-mode code-ref crashed
  pdflatex (no [[ ]] inside $...$).
- ALL 16 TARGETS BYTE-PERFECT. Hygiene FULLY GREEN: 0 EQU stubs, 0 ORG
  stubs, 0 TODO-SYM, 0 missing plates (348 routines), 0 placement
  violations, 0 raw-hex operands. PDF 979 pages, clean (0 errors, 0
  undefined refs). The scoreboard verdict is now "All measurable
  criteria met -- remaining work is editorial (synthesis)."
- Pipeline kept: .claude/scripts/makeindata_emu.py (canonical recovery
  emulator), makeindata_decomp.py (early hand-port), render_makeindata.py,
  mi_author.py (chapter generator), gen_makeindata.py (region math).
- NEXT SESSION: the SYNTHESIS CHAPTERS (/synthesize) -- the document is
  byte-complete; what remains to make it "done" per CLAUDE.md is the
  platform-independent design prose (game overview, data structures, the
  quest/gem/time-machine win condition, the overlay/engine architecture).
  Optionally the TM CRAFT_GFX render as its own focused round.

### Round 24 scout (2026-06-13): MAKE.INDATA scouted -- the art/map builder

MAKE.INDATA ($1E00-$5435, 13877 bytes) is the LAST target and the only one
that is NOT an overlay: a one-shot BUILDER BRUN at cold start. It is pure
binary (no strings) -- a hi-res DECOMPRESSOR + a build driver + ~13KB of
packed art/map data.
- The driver ($1F17, via JMP at $1E00): PAGE_COPY ($1EFD) stamps $2000-$27FF
  into $8700 and `JSR $8700` (a copied-in helper -- likely the low-RAM text/
  font blitter the U1.INTRO chapter says MAKE.INDATA installs); then copies 38
  pages $27BD-> $6000 (the ART_BASE artwork region); sets the decompress
  pointer $00/01=$49EC and JSR $1E03 (decompressor); clears HGR2, flips to
  hi-res, runs an LFSR fizzle (EOR #$B4) -- pre-rendering the title image.
- The decompressor ($1E03/$1E47) reads a byte stream via ($00), sentinel $08
  introduces runs, and the $1E1D address math converts a 0..$BF row index to
  hi-res raster addresses -- it unpacks straight into the screen.
- This resolves the ART_* EQU semantics (U1.INTRO chapter) + the last TODO-SYM
  (ART_BASE..$8Fxx bound), and -- per OUT round 12's deduction (no verbatim
  4096-cell map exists) -- GENERATES/packs the four-continent world map at
  $6000. Render the continents once the decompressor is ported.
- Full scout in agent memory (makeindata_subsystem.md). Decompose next: clone
  gen_gen at BASE=$1E00 (no overlay engine EQUs -- it predates the engine,
  calls ROM + its own code + the $8700 payload); port the decompressor to
  Python to recover the rasters; emit packed data as labeled HEX; render the
  intro frames AND the four continents.
- No build change this scout (memory + TODO only). All 16 targets still
  byte-perfect; PDF 962 pages clean; ORG stubs unchanged at 1 (makeindata).

### Round 23 (2026-06-13): TM fully decomposed, byte-perfect -- the endgame

- The time-machine endgame overlay is annotated across 37 chunks (27
  plated routines): the fixed-point math + BCD-print suite, TM_ENTRY +
  the gem-socket setup, the launch/time-travel narration, the combat
  scene setup, the main loop + patched-JSR dispatch, TM_ATTACK (melee
  Mondain/gem), TM_CAST + the 11-entry spell table + magic missile +
  the INTERFICIO-NUNC backfire, TM_GET (destroy the gem), the move
  handlers on the interior grid, Mondain's AI (approach/melee/cast with
  his 3 spells), TM_DEATH, the scene tick + cell helpers, the wireframe
  SHAPE_STEP stroker + BLIT_LINE blitter + projection tables, the cell
  grid, and CRAFT_GFX. byte-perfect (8123/8123); full doc tangles +
  builds. PDF 962 pages, clean (0 errors).
- THE WIN CONDITION is now pinned in code, end to end: Mondain is
  shielded by GEM_HP=$7EF4 (16-bit, $03E8=1000). TM_ATTACK/spells drain
  it via HIT_RESOLVE. Killing Mondain alone -> " ...or is he?" (he
  regenerates). TM_GET on the gem cell -> "The Gem is DESTROYED!" sets
  GEM_GONE ($95AB); THEN GEM_HP->0 -> "THOU ART VICTORIOUS!" -> TM_VICTORY
  loads NIF, hooks Control-RESET, melts the screen into the victory
  image. Lose -> TM_DEATH "THE UNIVERSE IS DOOMED!!". The SPA->CAS->TM
  win loop is now fully decompiled at every link.
- THE SCENE is a wireframe pseudo-3D craft interior on a small cell grid
  (CELL_STATE $A2FC / CELL_COL $A3E3); SHAPE_STEP $9EE5 is a vertex/
  filled-band stroker drawing a display list (CRAFT_GFX $A470) at
  cell-projected positions (PROJ_TBL $9D2A). The combat is grid melee +
  spells -- structurally unlike SPA's real-time flight.
- Pitfalls recorded in agent memory (tm_subsystem.md + toolchain): the
  single-scope self-test HIDES cross-chunk .L failures -- 36 helper subs
  (62 refs) had to be promoted to globals; the REAL per-chunk tangle is
  the only true byte-check. Two inline-text trampolines ($A436/$A43C) +
  MLIB_BLOAD inline path. 7 CMD_* names renamed TM_* (OUT/DNG collide).
  3 in-code BSS bytes -> 1-byte data spans. EQU-band catch-all guard.
- Pipeline kept for reuse: .claude/scripts/tm_gen.py + tm_symmap.py +
  tm_labels.py + tm_chapter_tm.py + tm_emit_chunks.py + tm_build_section.py
  (clone of the gen_gen sextet).
- All 16 targets byte-perfect. Hygiene: 0 EQU stubs, 0 raw-hex operands,
  0 missing plates (342 routines), 0 placement violations, 1 TODO-SYM
  (intro art, resolves with makeindata). ORG stubs 2 -> 1 (makeindata
  only). The remaining renderer IMAGE (CRAFT_GFX) is deferred -- it is a
  runtime-interpreted display list bound to live projection state, not a
  static sprite gallery; unblock = emulate SHAPE_STEP+BLIT_LINE+projection
  (see tm_subsystem.md). This is the only TM graphic outstanding.
- Next session: makeindata (13877 bytes, the LAST overlay/data target --
  builds the intro art AND likely generates the world map for /U1.VARS;
  resolves ART_* semantics and the last TODO-SYM; render the four
  continents). Then the synthesis chapters. Optionally the TM CRAFT_GFX
  render as its own focused round (twin of DNG round 15).

### Round 22 (2026-06-13): GEN fully decomposed, byte-perfect

- The new-game / title overlay is annotated across 37 chunks: the
  title menu + the two paths (new char / continue), the character
  generator (chargen entry, the point-buy attribute editor, the
  race/sex/class/name pickers with their bonus tables, the save
  prompt), the local text/window helpers, and -- the intricate half
  -- a complete bundled DISK FORMATTER. byte-perfect (8932/8932);
  full doc tangles + builds. PDF 895 pages, clean (0 errors).
- THE FORMATTER is two layers, the only code in the game that bypasses
  MLIB and touches the drive: RWTS_FORMAT ($A800) is a hand-rolled
  Disk II RWTS (35-track arm stepping via the SEEK_DELAY tables, 16
  sectors/track written as D5/AA/96 address fields + 6-and-2 GCR data,
  read-back verified, raw $C0xx soft switches); FORMAT_VOLUME ($A119)
  is the ProDOS volume-directory writer (patches WRITE_BLOCK
  paramblocks, scans PRODOS_DEVLST, writes the 4 dir blocks + bitmap
  via the MLI). DO_FORMAT brackets both with a zp $D0-$DD save.
- THE CODE/DATA INTERLEAVE pinned: the file block-copies $9440-$A13F
  to $6000 -- GAME_IMAGE (data, the 13-page new-game state image) then
  FORMAT_VOLUME code; past it BOOT_IMAGE ($A3C5-$A7B7) is a ProDOS boot
  loader stamped onto the new disk's block 0, PURE DATA in GEN's space
  (no GEN code refs it), emitted as HEX -- disassembling it as code had
  produced 28 phantom raw-hex operands (ASCII string bytes as JSRs).
- CHARGEN math pinned: six 16-bit stats at PLR_HITS,X (X=2*idx, idx
  1..6 = STR/AGI/STA/CHA/WIS/INT), 30-point pool, floor 10 ceil 25.
  Race: Human +5INT/Elf +5AGI/Dwarf +5STR/Bobbit +10WIS-5STR. Class:
  Fighter +10STR+AGI/Cleric +10WIS/Wizard +10INT/Thief +10AGI.
- Pitfalls recorded in agent memory: 3 picker labels were mis-placed
  on inline menu TEXT (real entries $8C7E/$8D3C/$8D98); chunk
  boundaries must fall on instruction starts; shared @ %def names
  (OVERLAY_ENTRY once; GEN DO_BSAVE->SAVE_PLAYER, PRESS_SPACE->
  FMT_PRESS_SPACE renamed). Pipeline kept: .claude/scripts/gen_gen.py,
  gen_symmap.py, gen_labels.py, gen_chapter_gen.py, gen_emit_chunks.py,
  gen_author.py, gen_build_section.py.
- All 16 targets byte-perfect. Hygiene: 0 EQU stubs, 0 raw-hex
  operands, 0 missing plates (315 routines), 0 placement violations,
  1 TODO-SYM (intro art, resolves with makeindata). ORG stubs 3 -> 2
  (tm, makeindata).
- Next session: TM (8123, the time-machine endgame where TM_REVEAL
  pays off -- Mondain's gem, the win); then makeindata (13877,
  world-map render, resolves ART_* + the last TODO-SYM); then the
  synthesis chapters.

### Round 21 (2026-06-13): SPA fully decomposed, byte-perfect

- The space-combat overlay is annotated across 62 chunks (entry/
  liftoff, main loop + dispatch, physics/torus/hazards, docking +
  the four-berth ship system, the flight commands with their delta
  tables, the radar + 42-star field, firing + the kill counter, the
  front/nav view machinery + enemy AI, the cell/RNG helpers, the XOR
  sprite blitter + fixed-point projection, and the file-tail tables).
  byte-perfect (9930/9930); full doc tangles + builds. PDF 842 pages,
  clean (0 errors, 0 undefined refs).
- THE SPACE ACE GATE is now pinned in code: HIT_ENEMY ($96E2) drains
  the enemy HP, awards +100 exp (capped 9999), then INC PLR_VESSELS
  ($7EB6) with saturation -- the ONLY writer of the counter CAS reads.
  Reaching exactly $14 (20) fires the "rank of Space Ace" popup; the
  win-condition loop SPA -> CAS (princess rescue >=20 -> TM_REVEAL) ->
  TM is fully traced end to end now.
- THE FLIGHT MODEL pinned: real-time rotation+thrust (NOT the grid
  overlays' turn model). Ship has SHIP_X/Y on a torus (wrap $0E/$F4),
  signed velocity ZP_VX/VY, heading HEAD_CUR 0..3. Thrust/Retro add
  THRUST/RETRO deltas; Clockwise/Counter rotate. PLR_FUEL/PLR_SHIELD
  (16-bit, reuse food/?? slots) gate actions; the central star drains
  the shield; collisions bounce + damage. NO patched-JSR dispatch --
  GET_COMMAND -> DISPATCH_TBL (26 words) self-modified into a JMP.
- THE SPRITE ATLAS rendered (standing rule): 36 entries in 6 parallel
  tables; shapes 0-8 = the enemy at 9 distance scales (a far dot
  growing into a TIE-fighter-like craft -- two pods + diamond
  cockpit), shapes 9-35 = 27 rotation frames + the planet/sun disc.
  images/spa_ships.png + spa_shapes_all.png (renderer
  render_spa_ships.py), both embedded as figures. The XOR blitter has
  two unrolled passes (collision-test + draw) selected by DRAW_MODE.
- Pipeline kept for reuse: .claude/scripts/gen_spa.py + spa_symmap.py
  + spa_labels.py + gen_chapter_spa.py (clone of the gen_cas trio).
  Engine-address corrections recorded in agent memory (PRINT_STAT16 =
  $8355, POPUP_FRAME = $841E; trig helpers MUL8_FIXED/$A107,
  DIV16/$A123). 4 cross-chunk locals promoted to globals.
- All 16 targets byte-perfect. Hygiene: 0 EQU stubs, 0 raw-hex
  operands, 0 missing plates (291 routines), 0 placement violations,
  1 TODO-SYM (intro art, resolves with makeindata). ORG stubs 4 -> 3
  (gen, tm, makeindata).
- Next session: GEN (8932, character generation / new game -- the
  A=0 GAME_LOAD slot) and TM (8123, the time-machine endgame where
  TM_REVEAL pays off -- Mondain's gem, the win); then makeindata
  (world-map render, resolves the last TODO-SYM); then synthesis.

### Round 21 scout (2026-06-13): GEN scouted -- the new-game overlay

GEN ($8956-$AC39, 8932 bytes) is the TITLE / NEW-GAME overlay (the
A=0 GAME_LOAD slot) and bundles a ProDOS disk formatter. Two
subsystems:
- CHARACTER GENERATION: title menu (a = new char / b = continue =
  BLOAD the save, signature $6000 == $01CA), then race (Human/Elf/
  Dwarf/Bobbit), sex (Male/Female), class (Fighter/Cleric/Wizard/
  Thief), name entry, and a cursor-driven attribute-point editor
  ($8FB1 draw / $8C00 input): six stats at PLR_HITS,X (X=2*idx), a
  point pool $903F, per-stat floor 10 / ceil 25, "Points left to
  distribute". Saves PLR_SAVE ($01CA bytes) to PATH_PLAYER.
- DISK FORMATTER (~$9100-$A7B6, $A800-$AC22): "Drive: ( )",
  "Non-ProDOS disk", "? (Y-N)"; low-level JMP ($00E8), JSR $F479
  (ROM), $C040/$C0xx disk soft switches, a "PRO" ProDOS param block
  at $A7C7, block-format helpers $A800+. Initialises a blank player
  save disk. Self-contained, runs in place (not relocated).
Full scout in agent memory (gen_subsystem.md). Decompose next with a
cloned gen_spa pipeline. No build change this scout (memory + TODO
only); all 16 targets still byte-perfect, PDF 842 pages clean, ORG
stubs unchanged at 3 (gen, tm, makeindata).

### Round 20 scout (2026-06-13): SPA scouted -- the space-combat overlay

SPA ($8956-$B01F, 9930 bytes) is the SPACE COMBAT overlay and the
source of the Space Ace status CAS gates the princess rescue on. It
is structurally unlike the other overlays: a real-time rotation+
thrust flight sim (movement names "Thrust/Retro/Clockwise/Counter-
Clockwise" via DIR_STR_PTR=$9219), NO patched-JSR dispatch (commands
go GET_COMMAND -> handler-address table $91D3, self-modified into the
loop at $8AB1).

- ENTRY $8956: restore space position from $7EEF/$7EF0, liftoff
  countdown ("10..9..8.." with KEY_PENDING abort), "Thou hast lifted
  off!", seed starfield/enemy tables ($9BFF/$9C29 via RND, $B020/
  $B099 grids).
- MAIN LOOP $8A53: "Shld|Fuel" status; flight commands gated on fuel
  ($7EE9/$7EEA "No fuel!! Wilt thou drift forever?!?"); integrate
  velocity $6E/$6F into position $9288/$9289 on a torus; move enemies;
  collide vs $8C47/$8C4B; star hazard ("Thy ship melts near the
  star!" -> RESPAWN).
- COMBAT (~$96E2): a hit drains enemy HP, awards +100 exp, and
  INC PLR_VESSELS at $9732 -- THE kill counter. Hitting exactly $14
  (20) fires "Thou hast achieved the rank of Space Ace!" -- the gate
  CAS reads. Enemies fire back ("Alien fires!", "You've been hit!").
- DOCKING/LANDING: "Docked! Welcome to Base!" (refuel); landing needs
  a shuttle ("Only space shuttles are heat-shielded for landings" ->
  "Thou hast landed safely!").
- Win-condition loop now traced end to end: SPA grows PLR_VESSELS ->
  CAS princess rescue (>=20) sets TM_REVEAL -> TM endgame.
- Full scout in agent memory (spa_subsystem.md). Decompose next with a
  cloned gen_cas pipeline; render the starfield/ship sprites when the
  format is pinned.
- All 16 targets still byte-perfect; PDF clean. ORG stubs unchanged
  at 4 (spa, gen, tm, makeindata) -- this round added no code.

### Round 19 (2026-06-13): CAS fully decomposed, byte-perfect

- The castle overlay is annotated across 25 chunks (entry/loader,
  command table + dispatch, the move handler with the Princess
  rescue, attack, cast/drop, the King audience, quest assign/
  complete, the four gem prophecies, get/steal/unlock storeroom,
  the castle tick, and the shared map/helper/math engine).
  byte-perfect (5524/5524); full doc tangles + builds.
- THE QUEST SYSTEM is now pinned in code, not just scouted:
  CMD_TRANSACT $927C (King audience, NPC kind $6C) gates on
  KING_REJECT; pence path donates gold for HP at 1.5x; service path
  QUEST_ASSIGN marks QUEST_FLAGS[CASTLE_IDX] and -- by castle parity
  -- sends the player to FIND a place (even) or KILL a monster
  (odd, STR_MONSTERS idx = 5*PLR_CONT+$1E). QUEST_COMPLETE clears
  the flag: even reward = strength ((99-STR)/8); odd reward =
  QUEST_REWARD_HINT, a per-continent prophecy from GEM_HINT_TBL that
  ALSO hands over a gem (red/green/blue/white in OWNED_GEMS; white
  sets STORE_PERMIT=9, the King's "nine items" permission).
- PRINCESS RESCUE folded into CMD_MOVE: stepping into the throne
  wall (ZP_X=0) with the King slot near awards +500 HP/pence/exp via
  ADD_CAP; the space-ace gate (PLR_VESSELS>=$14 plus experience)
  sets TM_REVEAL and announces the time machine "to the northwest".
  Together with the gems this is the whole endgame breadcrumb trail.
- STOREROOMS: CMD_GET (gated on STORE_PERMIT, the white-gem counter)
  and CMD_STEAL (thief class auto-succeeds; caught -> KING_REJECT)
  share STOREROOM_FIND -- armour/food/weapon by faced cell kind.
  CMD_UNLOCK opens a door ($6A silver/$6B gold) with a key dropped
  by a slain guard (KEY_KIND set in the attack handler).
- CASTLE_TICK forks on KING_REJECT: angered -> GUARD_HOME +
  GUARD_COMBAT (death -> CAS_DEATH/RESPAWN); calm -> NPC_WANDER with
  Gwino the Jester (sings "I've got the key!" / filches a weapon).
- Gen pipeline kept for reuse: .claude/scripts/gen_cas.py +
  cas_symmap.py + cas_labels.py + gen_chapter_cas.py (twin of the
  gen_twn trio; the chapter author script in /tmp is disposable).
  Pitfalls recorded in agent memory: DROP_PICK 5 inline-arg bytes,
  two cross-chunk locals promoted to globals (CAS_DEATH/
  STOREROOM_FIND), the GEM_HINT_TBL data-span-in-code.
- All 16 targets byte-perfect. Hygiene: 0 EQU stubs, 0 raw-hex
  operands, 0 missing plates (247 routines), 0 placement violations,
  1 TODO-SYM (intro art, resolves with makeindata). ORG stubs 5 ->
  4 (spa, gen, tm, makeindata). PDF 767 pages, clean (0 errors, 0
  undefined refs).
- Next session: SPA (9930 bytes) -- the space/shuttle combat
  overlay; then GEN (8932, character generation / new game) and TM
  (8123, the time machine endgame); then makeindata (world-map
  render, resolves the last TODO-SYM); then the synthesis chapters.

### Round 18 scout (2026-06-13): CAS scouted end-to-end (quest system pinned)

CAS (5524 bytes, $8956-$9EE9) is a near-twin of TWN: same loader
skeleton, same main loop, same patched-JSR dispatch (table $8A5F,
26 words, patched JSR $8A56), and BYTE-IDENTICAL draw/helper
structure -- MAP_DRAW $9B06, FONT_SWAP $9B6E, NPC_DRAW, PLOT_GLYPH
$9BA8, CELL_PROBE $9BC0, NPC_AT $9BD9, all the same 38x18 grid +
$B6AC NPC arrays as TWN. CAS-local NPC glyph table at $9EDC. Reuse
the entire TWN engine-EQU block and the gen pipeline.

Entry differences: castle index = PLR_PLACE mod $15, then
+2*PLR_CONT into $9E3B (continent-adjusted), with an even/odd
parity flip ($06-idx). TCMAPS dir read at $4000,X/$4001,X (vs TWN's
+4). Map copy + draw via $9B06.

Dispatch (CAS handlers): move $8A93-8AA8, Pass $8C4C, Attack $8C56,
Cast $8E3C, Drop $8E5B, Get $90D4, Inform $9AFA, Quit $9134, Ready
$9159, Steal $916F, Transact $927C (= TALK TO KING), Unlock $975E,
Ztats $97FE. Board/Enter/Fire/HyperJump/K-limb/Open/View/X-it ->
QUERY_MARK; Accel/Noise -> engine toggles.

THE QUEST SYSTEM (Transact $927C = audience with the King, NPC type
$6C):
- $9E2A = king-rejects flag. $9E3B = castle index -> QUEST_FLAGS,X.
- "Dost thou offer pence or service?" P = give gold for HP (1.5x,
  like TWN drop-pence). S = accept/complete a quest.
- ASSIGN ($93FB): INC QUEST_FLAGS,X. EVEN castle -> "Go forth and
  find <place>" (STR_PLACES, continent math). ODD castle -> "Go now
  and kill a <monster>" (STR_MONSTERS, PLR_CONT*5+$1E). $9EE2,X =
  per-castle display column.
- COMPLETE ($94E7, entered when QUEST_FLAGS,X high bit set): clear
  the flag, reward. EVEN -> strength points ((99-STR)/8). ODD ->
  a per-continent hint via self-modified JSR (table $95D6) that
  ALSO GIVES THE QUEST GEM: green ($7E76)="time machine must be
  used to win", blue ($7E77)="princess helps a space ace through
  time", white ($7E78)="take nine items from storerooms - but only
  nine!" (sets $9E3D=9, the Get permission counter). Red gem path
  too. OWNED_GEMS=$7E75.
- PRINCESS RESCUE (in the move handler $8AAF, reaching the throne/
  cell): "Thou hast saved the Princess <name>!" -> +500 HP, pence,
  exp ($9E06 = add-with-cap helper); "space ace" (PLR_VESSELS>=$14)
  unlocks the time-travel bonus. Pins TM_REVEAL.
- GET ($90D4) = take from the storeroom, gated on $9E3D (king's
  permission, the white-gem "nine items" counter); each Get
  decrements it.

CAS BSS state: $9E29 idle-msg, $9E2A king-reject, $9E2E?, $9E32/33
pence amount, $9E37, $9E3B castle index, $9E3D storeroom-permission
counter. Data tail from ~$9E40: kings' names ($9E63), NPC glyphs
($9EDC), per-castle params ($9EE2), continent hint pointers ($95D6).

Next session: decompose CAS with the TWN gen pipeline (gen_twn.py +
twn_symmap/twn_labels as templates). It will pin QUEST_FLAGS /
TM_REVEAL / COURT_CELLS quest semantics fully.

### Round 17 (2026-06-13): TWN fully decomposed, byte-perfect

- The whole town overlay is annotated across 28 chunks: entry/
  loader/main loop (patched-JSR dispatch via CMD_TBL), the command
  handlers, the six-class shop system, the idle/combat animation,
  the map/NPC draw, and the cell/distance helpers. byte-perfect
  (8461/8461) on the spliced chapter; full chapter tangles + builds.
- CORRECTION to round 16: town/castle maps are 38 cols x **18**
  rows = 684 cells, NOT 38x19. The metadata is an 80-byte NPC
  table (5 parallel 16-entry arrays: TYPE/X/Y/HP-lo/HP-hi) at grid
  offset 684 (= $B6AC after copy to TOWN_MAP $B400). Total record
  = 764 bytes. The move handler proves it: leaving town fires when
  ZP_TX>=$26 (38) or ZP_TY>=$12 (18). Fixed the TCMAPS appendix
  prose + the "38x19" comments + the figure caption.
- SHOP SYSTEM pinned: counter NPC type $64..$6C -> NPC_SHOPCLASS ->
  one of SIX classes (Armour/Grocery/Weapons/Magic/Pub/Transport),
  each with a buy + sell handler via SHOP_BUY_TBL/SHOP_SELL_TBL
  (self-modified JSR) and a pool of 8 flavour names. Pricing =
  item_index^2 (ITEM_COST squares table) scaled by a charisma
  factor (PRICE_MUL); CHA/WIS/INT all feed the haggle. Transport
  shop writes purchased craft into a free COURT_CELLS slot
  (transport+8) -- the same shared 4-cell lot CAS will use.
- The PUB is the lore core: pay 1 gold, risk seduction (NPC_DIST +
  ISQRT gated), else one of 8 canonical Ultima I rumours from
  PUB_HINT_TBL (ace pilot, princess, time machine, evil gem, magic
  lakes, Mondain's gem 1000 yrs ago, the full quest text).
- Idle anim (TOWN_TICK): hostiles (type 3) home + attack
  (GUARD_COMBAT, death -> RESPAWN); wanderers (type 4) drift --
  Iolo the Bard sings / picks a pocket. NPC_AT reads cells through
  the 18-entry MAP_ROW_LO/HI pointers.
- Drop gold to a type-$61 NPC = HP+1.5x + random spell. Steal from
  $65/$67/$69 (thief auto-succeeds; caught sets AGGRO = no one will
  trade). DROP_PICK is a 5-inline-arg popup picker.
- All 16 targets byte-perfect. Hygiene: 0 EQU stubs, 0 raw-hex
  operands, 0 missing plates (227), 0 placement violations, 1
  TODO-SYM (intro art, resolves with makeindata). ORG stubs 6 ->
  5 (cas, spa, gen, tm, makeindata). PDF 715 pages, clean (0
  errors, 0 undefined refs).
- Generators kept for CAS reuse: .claude/scripts/gen_twn.py +
  /tmp build scripts (symbol/label/SMC maps). CAS shares TWN's
  loader, NPC format, COURT_CELLS, and most helpers -- decompose it
  next from the same engine-API EQU block. CAS adds: kings,
  COURT_CELLS writer for quest items, QUEST_FLAGS assignment,
  TM_REVEAL (princess rescue / time-machine scatter).
- Next session: decompose CAS (5524 bytes), reusing the TWN engine
  EQU block and gen scripts; it pins the quest-assignment system.

### Round 16 (2026-06-13): TCMAPS decoded + rendered; TWN scouted

- TCMAPS format fully decoded and the data target STRUCTURED
  (stub -> TCMAPS_DIR + 10 named maps, byte-perfect): a 10-word
  pointer directory at $4000, then ten 764-byte maps. Each map =
  a 38x19 grid of MAPCHARS glyph codes (the displayed cells) +
  42 bytes of NPC/shop metadata. Shop signs ("ARMOUR", "FOOD",
  "WEAPONRY", "THE PUB", "MESS HALL"...) are spelled into the
  cell grid as ASCII glyph codes. TWN draws a cell by printing
  its byte through the MAPCHARS font (swap $B000<->$0800).
- RENDERED all 10 maps: images/tcmaps_0..9.png + tcmaps_all.png
  (renderer .claude/scripts/render_tcmaps.py), embedded as a
  figure. Clearly legible towns (shops + courtyards) and a castle
  (map 1: MESS HALL / PRISON / STABLES).
- TWN scouted (not yet decomposed): OVERLAY_ENTRY $8956 sets
  zp $00/01=$1311, copies a 6-byte block by PLR_SEX ($A967->
  $A961, gendered text?), reduces PLR_PLACE mod $15 then -$0D to
  a town/castle index ($9186), BLOADs TCMAPS@$4000 + MAPCHARS@
  $B000, self-modifies a 3-page copy ($4004,X directory lookup ->
  copy 768 bytes of the chosen map to $B400 the live buffer),
  draws via $A1AE (38x19 text blit with the font-swap LA1E7),
  then the main loop $89EC: STATS_VALUES, key-or-idle poll
  ($8A1C, $80 timeout = idle animation $9F07/$8AEE), GET_COMMAND
  dispatch. Per-map metadata (42 bytes) = NPC/shop table: leading
  type codes ($FF=empty) then $01/$F4 runs (guard/shopkeeper tile
  + position) -- decode with the TWN handler next round.
- TWN gameplay strings confirm the town layer: combat (Blocked/
  Missed!/Hit/Killed!/damage/Nothing), shops (Pence,Weapon,Armour
  / "How much?" / "Thou hast not that much!"), magic (Shazam! /
  "no effect?"). Expect buy/sell, talk-to-NPC, steal, and guard
  combat handlers.
- All 16 targets byte-perfect. Hygiene green: 0 EQU stubs, 0 raw-
  hex operands, 0 missing plates (203), 0 placement violations,
  1 TODO-SYM. ORG stubs 7 -> 6 (twn, cas, spa, gen, tm,
  makeindata). PDF 653 pages, clean.
- Next session: decompose TWN from this skeleton (entry/loader/
  map-draw first, then the command handlers and the metadata
  format), then CAS (shares the loader; castle-specific: kings,
  COURT_CELLS, QUEST_FLAGS, TM_REVEAL). CAS will pin the quest
  assignment.

### Round 15 (2026-06-13): DNG renderer decomposed -- DNG fully done

- The four remaining DNG stubs are gone; DNG is 100% annotated,
  byte-perfect. The first-person view is a RAY MARCHER: DNG_DRAW
  ($8982) walks VIEW_DEPTH cells along the facing vector and at
  each depth slice inspects three cells -- ahead (VIEW_CELL) and
  the two beside it (VIEW_L/R, found by rotating the facing
  vector +/-90 deg) -- drawing the wireframe in perspective until
  a solid cell sets VIEW_BLOCKED. The status line decodes the
  facing into a compass word.
- The perspective is entirely in the tables, not the code:
  DNG_GEOM ($9E42, 194 bytes) is a packed pool of ten-entry
  columns (depths 1-10) of converging screen coordinates, indexed
  by VIEW_DEPTH. Kept as one labeled blob; the ~12 drawing
  primitives address it by fixed byte offset (DNG_GEOM+$XX,X).
- Twelve wireframe primitives, each one feature: DRAW_COFFIN (the
  full 3D box), DRAW_LADDER_SHAFT/_DN/_UP, DRAW_FIELD (red bars),
  DRAW_OPEN_L/R (branch openings, peek one deeper via AHEAD_FEAT),
  DRAW_WALL_L/R, DRAW_AHEAD_WALL (corridor end face + prev-slice
  connectors), DRAW_AHEAD_OPEN (doorway), DRAW_DOOR_L/R, plus the
  GLYPH_AT trampoline. All read box-edge coords from DNG_GEOM and
  stroke with LINE_AGAIN; only DRAW_FIELD changes colour.
- SHAPE_DRAW ($A449) is a scaled vector-stroke interpreter: shapes
  are (x,y,flag) vertex triples (move/draw), scaled down by depth
  halvings (SHAPE_SCALE_BYTE, sign-preserving ROR). The shape
  pointer is self-modified into SHAPE_FETCH (the disk's stale
  $FFFF operand, now named). MON_SHAPES ($A692) restructured into
  a 25-word pointer table + SHAPE_STROKES blob.
- RENDERED the 25 vector shapes:
  images/dng_monster_shapes.png (renderer
  .claude/scripts/render_dng_shapes.py), embedded as a figure --
  humanoids, beasts, the chest, a sack, the eye/gazer; sparse
  tiles are the chest/coffin/ladder glyphs and unused sentinels.
- Cell-feature legend confirmed against the renderer: 0 open, 1
  wall, 2 trapdoor, 3 secret door, 4 door, 5 chest, 6 coffin,
  7 ladder down, 8 ladder up, 9 revealed trapdoor, $C force
  field; high nibble = monster slot. Sentinels $1E/$20/$29 in the
  view = chest/coffin placeholders (no shape / no block).
- Three branch-target bugs caught by byte-compare on first build
  (JMP .check_blocked and two JMP .after_ahead2 mislabeled) --
  compute every branch, as ever. Hygiene all green: 0 EQU stubs,
  0 raw-hex operands, 0 missing plates (203 routines), 0
  placement violations, 1 TODO-SYM. ORG stubs 11 -> 7 (twn, cas,
  spa, gen, tm, makeindata, tcmaps). PDF 641 pages, clean.
- Next session: TWN/CAS pair (pins TCMAPS format, COURT_CELLS
  writer, quest assignment, TM_REVEAL), then SPA/GEN/TM, then
  makeindata (world map render), then synthesis.

### Round 14 (2026-06-13): DNG decomposed (everything but the renderer)

- DNG ($8956-$B098, 10051 bytes) is now decomposed into 84
  annotated chunks across 22 sections; byte-perfect. Only three
  honest stubs remain, all in the renderer band: DNG_GEOM ($9E42,
  perspective tables + wireframe primitives), SHAPE_DRAW ($A449,
  scaled vector-shape renderer), and the monster shape art
  MON_SHAPES. Next DNG round = the wireframe renderer.
- LEVEL GENERATOR pinned (DNG_GEN $8C5D). No dungeon map is stored
  anywhere -- the maze is a pure function of a 2-byte seed:
  SEED_A = 8*PLR_PLACE ^ PLR_OUT_X ^ level, SEED_B = 4*PLR_OUT_Y ^
  PLR_CONT. SEED_RND ($A3F3) is a Fibonacci swap-add (A' = A+B+9,
  B' = A). Five passes over DNG_TEMPLATE (border + even-even
  pillar lattice): (1) edge features via EDGE_PICK -- open/secret-
  door/door weighted 6/6/8 on a d20 (trapdoor codes 2,9 in
  EDGE_FEATURE are overridden to secret doors -- vestige of an
  earlier design); (2) 2*level+1 walls/force-fields from
  WALL_POS_A/B (transposed on odd levels, field prob 96/256);
  (3) `level` containers (chest/coffin -- the ONLY non-seeded
  roll, uses library RND); (4) fixed cells: clear (1,2), ladders
  at (7,3)/(3,7) dir by level parity, level 10 drops its down
  ladder, level 1 forces the arrival up-ladder at (1,1); (5) fall
  into LEVEL_INIT -- pick 5 monster kinds, release 3.
- CELL_WRITE ($A3xx): DNG_MAP[X + 11*Y] := A (row-major 11x11).
  AHEAD_XY = cell one step along facing. NEGATE = two's-comp.
- Map access + the distance root section documents how monsters
  home on the player; Inform/search, the ten Cast spells
  (Open/Unlock incantations APERTUS!/PECUNIA!, missile, ladder-
  blink), K-limb (ladders, re-gen on level change), Open, Quit,
  Ready, Unlock, Ztats all annotated. Monsters: SIX fixed slots,
  turn walker counts DNG_MON_TIMER 5..0, approach logic homes via
  the distance root.
- DNG reuses the engine API EQU block (MI.U1 services + STUPH
  vectors) as its defines template, exactly as planned. STALE_FFFF
  EQU documents the on-disk stale dispatch operand.
- Fixed a pre-existing dangling \ref: added \label{ch:overlays}
  to the Mode overlays chapter (MI.U1 prose forward-referenced
  it). PDF now 614 pages, zero undefined references, zero LaTeX
  errors. All 16 targets byte-perfect. Hygiene: 0 EQU stubs,
  0 raw-hex operands, 0 missing plates, 0 placement violations,
  1 TODO-SYM (intro art, resolves with makeindata). ORG stubs:
  11 (twn, cas, 3 DNG renderer stubs, spa, gen, tm, makeindata,
  tcmaps).
- Next session: DNG renderer (DNG_GEOM/SHAPE_DRAW/MON_SHAPES --
  the wireframe geometry, monsters 21-45 shapes), then TWN/CAS.

### Round 13 (2026-06-13): DNG scouted end to end

- DNG ($8956-$B098, 10051 bytes) is the first-person wireframe
  dungeon. Entry sets DIR_STR_PTR=$A538: movement commands are
  renamed "Forward / Turn around / Turn right / Turn left" --
  same dispatch skeleton as OUT (table at $8E14, patched JSR
  at $8E0B w/ STALE $FFFF operand on disk; main loop $8DE6;
  prompt $8D99; idle tick Y=1/A=$10 = .01 food/.10 time).
- Dispatch decoded (OUT names): 0-3 move/turn $8E95/$8E48/
  $8E5B/$8E78, Pass $8F8C, Attack $8F96, Cast $90C5, Inform
  $9CD2, K-limb $961B (ladders; $8C5D re-gen on level change at
  $9728/$974D), Open $9768 ("APERTUS!" incantation at $A55D),
  Quit $9804, Ready $9829, Unlock $9848 ("PECUNIA!" at $A567),
  Ztats $98D1; everything else QUERY_MARK. Engine SOUND/SFX
  toggles reused. Death $98DD -> JMP RESPAWN (engine).
- HEADLINE: dungeons are PROCEDURALLY GENERATED, deterministic
  per site. $8C5D seeds $A504/05 from PLR_PLACE*8 ^ PLR_OUT_X ^
  level and PLR_OUT_Y*4 ^ PLR_CONT, copies a 121-byte (11x11?)
  template $A619->$B099 (map lives in BSS past the file), lays
  a grid, then strews features from the seeded RNG $A3F3
  (helpers $A406/$A41F). Levels 1 and 10 get fixed extras
  (ladder up / something at bottom).
- State: $A4E8/E9 = X/Y (entry 1,1), $A4EC/ED = facing dx/dy
  (entry 0,1), $A506 = level, $A4FC prompt flag, $A504/05 RNG
  seed. Monsters: SIX fixed slots, not OUT's 80 records --
  kind $A508+i, X $A50E+i, Y $A514+i (i=0..5; turn walker
  $98EC counts $A4FE 5..0, approach logic at $9912).
- View renderer entered via $9BED; line helpers $A3F3/$A406/
  $A41F cluster near the geometry tables at file tail
  ($AFxx-$B098, coordinate-list shaped). Status bar $8982
  prints "Level N" + facing from $A4EC/ED signs.
- Next session: decompose from this skeleton in file order;
  expect dungeon spells 1,2,4-9 in Cast and monsters 21-45.

### Round 12 (2026-06-13): OUT fully decomposed, byte-perfect

- The whole overworld overlay is annotated: entry/main loop
  (patched-JSR dispatch via CMD_TBL at $9AAA), resurrection,
  all command handlers (Attack/Board/Cast+Prayer/Enter/Fire/
  Quit-save/Ready/X-it/Inform/moves), monster AI (spawn gated
  on tier vs difficulty bar; roam with terrain classes; the 4
  ranged shooters; melee w/ armour+stamina defense), the object-
  record system (5 parallel 80-entry arrays; OBJ_HP at $B600
  unsaved, $B600 doubles as world-init sentinel), RLE map
  decompression (4-continent 2x2 torus, 10-cell ocean margins,
  edge crossing = continent +/-1 or +/-2), tick fare tables
  (faster transports cost less food AND less time), landmarks
  (8 sites: quest completion, stat boons, the Signpost weapon),
  the time-machine gem gate, and all message text.
- Both round-10 mysteries resolved: ENGINE_TBL_A -> MON_TIER
  (per-monster difficulty 0-10, scales exp/HP via TIER_HP =
  10*tier), ENGINE_TBL_B -> PLACE_Y + PLACE_X (84 world coords
  parallel to STR_PLACES; landmarks are local places 2,3 of
  each continent).
- MI.U1 carved further: PLR_BSS replaced by CUR_MON/TGT_REC/
  OBJ_COUNT/OBJ_X/OBJ_YC/OBJ_TILE/OBJ_UNDER; PLR_SAVE ($7E6D,
  word = own length $01CA), PLR_CONT/_BITS, QUEST_FLAGS,
  COURT_CELLS, TM_REVEAL, DMG_AMT, PLR_PLACE, PLR_LASTMARK.
  Engine locals promoted for overlay use: CURSOR_COL1,
  MOVE_CNT_INC, SFX_PLAY_FLUSH, POPUP_BORDER(_A).
- World-map data is NOT in OUT: /U1.VARS (written by
  MAKE.INDATA, absent from the crack disk) loads the packed
  maps at $6000; OUT stashes them at $A900. RLE scan of
  makeindata.bin found no verbatim 4096-cell streams -> the
  world map is likely GENERATED by MAKE.INDATA; render the four
  continents in that round.
- Unreferenced-in-OUT code noted (TGT_CELL_PTR, SPAWN_AT_WATER/
  LAND): shared ancestral source; check usage in siblings.
- ORG stubs down to 8. PDF 549 pages. All 16 targets verify.

### Round 11 (2026-06-12): OUT scouted; cross-corrections applied

- OUT entry ($8956) read: restores zp $00/$01 from $7E73/74 (now
  labeled PLR_OUT_X/Y), enables double-buffering, copies $6000
  +14 pages to $A900 (buffer above the overlay -- purpose TBD),
  zeroes DIR_STR_PTR hi (default direction names), checks $B600
  flag else JSR $9691 (world/map load?), JSR $94C1 (initial draw),
  death-check, then THE MAIN LOOP at $8995: stack reset, prompt,
  $8A6A (key fetch) -- idle turn = JSR $82E4 with Y=5/A=$50 (food
  5/100, +50 moves?? verify) -- GET_COMMAND -> patched-JSR dispatch
  through the address table at $9AAA (26 entries, X=2*index), then
  $96B0 (end-of-turn/monsters), loop. Death penalty path: lose
  current transport, all weapons/armour/spells zeroed, respawn
  position from $9461.
- Corrections from this evidence: TICK_HURT renamed TICK_SND --
  effect 0 is the per-turn MOVE THUMP, not a damage cue; $7E73/74
  identified as the saved outdoor position.
- Next session: decompose OUT from this skeleton (entry/main loop
  first, then the 26 command handlers via the $9AAA table, then
  $9461/$9691/$94C1/$96B0 world machinery). Then DNG (wireframe
  via PLOT/LINE_TO), then the town/castle pair w/ TCMAPS format.

### Round 10 (2026-06-12): MI.U1 100% decomposed; world census in hand

- The "mask tables" are exactly one picture: the 10x94 death SKULL
  (DEATH_IMG, rendered: images/miu1_death.png).
- MIU1_STRINGS carved into 15 labeled tables: races (lizard/human/
  elf/dwarf/bobbit), weapons long+short (16 each, "hands" at 0),
  stats (10, incl. Gold/Race/Type for chargen), spells (11,
  "Prayer" at 0!), armour (6, "skin" at 0), classes (peasant/
  fighter/cleric/wizard/thief), transport (11: foot..time machine),
  the 26 commands (Pass=space, ctrl-A=Accelerator, HyperJump,
  K-limb, X-it, Ztats...), 4 gems, 46 monsters (6 blank entries
  then sea/land/dungeon sets), 4 CONTINENTS (Lord British/Feudal
  Lords/Dark Unknown/Danger and Despair), and all 84 PLACE names.
- Two unidentified embedded tables flagged: ENGINE_TBL_A ($76A8,
  46 bytes, ascending runs -- costs/limits?) and ENGINE_TBL_B
  ($786F, 168 bytes between continents and places -- per-place
  data?). Expect the overlays to resolve both.
- ORG stubs down to 9 (7 overlays + makeindata + tcmaps).

### Round 9 (2026-06-12): MI.U1 low region carved; EQU stubs = 0

- MIU1_CODE_A is gone: DISK_PROMPT/$7DCC (dual entry, DC.B $2C
  trick, carry = caller's error flag, "Ultima"/"Player" disk
  names), PAGE1_LOCK/$7E05 (end double-buffering with the image
  live on page 1), and the full player state block $7E16-$8036 as
  labeled data: LOC_NAME table, WIN_SAVE_BUF, CAP_FLAG, the
  /U1.PLAYER + /U1.VARS pathnames, TICK params, CMD_KEYS (26:
  arrows, space, ctrl-A, ABCDEFGHIKNOQRSTUVXZ), sound mirrors,
  OWNED_*/READY_* arrays, PLR_NAME..PLR_EXP (shipped snapshot:
  Glinda, female, 900 hits, 2104 coin -- the crack's master save),
  two unidentified $03E8 words + a few flag bytes, 325-byte BSS.
- All round-7/8 state EQUs converted to real labels; CAP_FLAG EQU
  stub resolved -> EQU-stub metric is now ZERO. The 2 stray code
  bytes ($7DCC) moved out of MIU1_STRINGS.
- Remaining ORG stubs: 11 (miu1 masks $7003 + strings $73AF, 7
  overlays, makeindata, tcmaps). PDF 477 pages.

### Round 8 (2026-06-12): MI.U1 engine code complete ($841E-$89BC)

- The high stub is GONE -- all engine code $8037-$89BC annotated:
  POPUP_FRAME (blue LINE_TO rectangle on the visible page),
  READY_CMD (S/W/A dispatch; proves $7E79=readied SPELL, $7E7A=
  weapon, $7E7B=armour -- round-7 names corrected), MENU_PICK
  (generic picker: 5 inline arg bytes = count, owned-array ptr,
  name-table ptr; letters track item indexes; item 0 always
  allowed), INVENTORY (level = exp/1000+1 recomputed, coin purse =
  one 16-bit number shown as pence/silver/gold = ones/tens/over-
  100), COL_ADVANCE/ITEM_LINE (two-column dot-leader lines; name
  table = caller's inline word consumed by STR_NTH_CAP through the
  stack; $1B marker = readied), POPUP_END/PRESS_SPACE, PRINT_NAME,
  SOUND/SFX_TOGGLE (mirrored to $7E71/72 for the save file),
  DEATH (death image = 10x94 bytes at MIU1_TABLES $7003; render
  it when carving masks), RESPAWN/GAME_LOAD (LOC_NAME $7E16 table
  "GEN/OUT/DNG/TWN/CAS/SPA/TM" at 4-byte offsets; A=offset; A=0 ->
  GEN/new game; death -> A=4 = OUT; loads land AT OVERLAY_ENTRY),
  QUIT + OVERLAY_ENTRY bootstrap (saves ProDOS reset vector INTO
  QUIT's JMP operand; hooks Reset; loads STUPH; the final
  GAME_LOAD(0) overwrites the bootstrap itself with GEN and jumps
  back into $8956).
- Low-stub layout pinned: $7DCC disk prompt entry, $7E05
  PAGE1_LOCK, $7E16 location-name table, $7E31 win-save, full
  player state block to ~$7EFF (PLR_NAME "Glinda" default at
  $7EB8). String table entry points EQU'd (STR_RACES $73AF,
  STR_WEAPONS $73C8, STR_SPELLS $74D4, STR_STATS $748E,
  STR_ARMOUR $7520, STR_CLASSES $755D, STR_TRANSPORT $757C,
  STR_ITEMS $7687, STR_COMMANDS $75CB).
- PDF 474 pages; 12 ORG stubs left (miu1 masks/strings/low-stub +
  7 overlays + makeindata + tcmaps).

### Round 7 (2026-06-12): MI.U1 engine core services ($8144-$841D)

- High stub front carved into 12 annotated chunks, byte-perfect on
  first assembly: CHAR_REPEAT, DRAW_SCREEN/DRAW_BORDERS (frame from
  terrain-strip glyphs; divider col 30), BIN2BCD (double-dabble,
  BCD_POW at $8204), PRINT_NUM16/8 + DIGIT_OUT (NUM_ZSTATE/$8248,
  NUM_PAD/$8249 leading-zero padding), DIV10, RND_MOD, KEY_PENDING,
  PAUSE_ABORTABLE, KEY_ALIAS (CR,[ up; / down; ' right; ;,DEL left
  -- ][+ has no up/down arrows), GET_COMMAND (CMD_KEYS table $7E53,
  echo from STR_COMMANDS $75CB, movement names overridable via
  DIR_STR_PTR $7E51, returns X=2*index/C-set on "Huh?"), TICK/
  TICK_HURT (food -= Y BCD hundredths via FOOD_FRAC, 16-bit binary
  PLR_FOOD clamps at 0; moves += A into multi-byte BCD MOVE_CNT;
  hurt entry queues sfx 0; CLC/DC.B $B0/SEC dual-entry trick),
  STATS_DRAW/STATS_VALUES/PRINT_STAT16 (<100 -> inverse video),
  WIN_SAVE/WIN_RESTORE ($7E31), PRINT_WEAPON, CURSOR_TO_TEXT
  (baseline-scanline ink scan), NO_EFFECT_MSG/BEEP_CMD/QUERY_MARK/
  BEEP_HUH, KBD_CLEAR (flushes BOTH queues).
- Player state EQU'd (PLR_HITS/FOOD/EXP/COIN all 16-bit binary;
  display-only BCD conversion). Stats live in the $7Exx block
  inside the low stub -- labels arrive when round 8 carves it.
- High stub now starts at $841E. PDF 453 pages.

### Round 6 (2026-06-12): STUPH = the resident library, fully RE'd

- STUPH is NOT shape data: it is the resident low-memory library at
  $0800-$1FFF with a 34-entry JMP vector API at $1583-$15E9. All of
  it is now annotated and byte-perfect; fonts and tiles rendered
  (images/stuph_font.png, stuph_tiles.png, mapchars_font.png;
  renderer .claude/scripts/render_font.py).
- Glyph formats: bank A = 128 glyphs x 8 scanlines, plane-major
  (scanline s of glyph g at $0800+s*$80+g); chars $00-$19 are
  pre-shifted even/odd pairs; $7C-$7F = cursor frames. Bank B =
  96 glyphs x 16 scanlines at $0C00+s*$60+g = 48 outdoor map tiles
  (2 glyphs wide). MAPCHARS = alternate bank A for towns/castles
  (walls + inverse shop-sign letters; TCMAPS cells embed ASCII).
- DRAW_MAP ($15B3): 19x9 tile viewport centered on player at zp
  $00/$01, map = 64x64 bytes at $6000; cell AND #$7E -> glyph pair
  (c,c+1); codes $20-$58 are creatures w/ random 2-frame wobble;
  PLAYER_TILE at $1582. Tile animation = plane-byte rotation/swaps.
- Double buffering: $7F = draw-page XOR ($00/$60), $80 = toggle
  mask; text writes BOTH pages; $7E = inverse-video EOR mask.
- Input: 4-key typeahead $74-$77/$78 (space flushes); sound-effect
  queue $79-$7C/$7D drained at PAGE_FLIP; 9 speaker effects.
- FILE_LOAD ($1589/$158C): BLOADs via MLIB with transparent /RAM
  caching on 128K machines (BSAVEs a shadow copy, retries /RAM
  first). RND = 16-byte lagged additive generator, re-seeded by
  cursor-flash timing.
- Machine layer: AppleMouse card used ONLY as a VBL interrupt
  source (SETMOUSE mode 8); $C019 polling on enhanced IIe/IIgs;
  IIgs CYAREG speed control; DRIVE_OFF reads as accelerator nudge.
- miu1 now carries the full 35-name vector EQU list; LOW_1598 ->
  CLR_EOL. Engine rounds can use real names everywhere.
- PDF 433 pages. Hygiene: 1 EQU stub (CAP_FLAG), 13 ORG stubs,
  1 TODO-SYM (intro art, resolves with makeindata).

### Round 5 (2026-06-12): MI.U1 text-output cluster decomposed

- Overlay->engine call census (all 7 overlays): 147 distinct targets;
  top: $8119 (349 calls), $8062 (50), $80B8 (45), $8115 (33), $8254
  (27), $83A9/$83B4/$8407/$820D/$826C/$8207... ($73xx/$74xx hits are
  false positives — '$20'=space inside text). The $80xx-$84xx band is
  the engine API.
- Decomposed $8037-$8143: MSG_PRINT/MSG_AT (inline zero-terminated
  text, $7F=tab), STR_NTH/STR_FIRST/STR_NTH_CAP (packed string tables,
  last char high-bit-set, X = index, inline table pointer), PRINT_HEX,
  PUTCH (layout codes: |=newline, ~=NL+col1, }=conditional NL+col1),
  NEWLINE/CR/WIN_SHRINK. Text renders via low-RAM helpers $1592/$1598/
  $15B0 (FONT_DRAW etc., installed by MAKE.INDATA — EQU stubs).
- Next decomposition targets, by call count: $8062 group done; next
  $8254, $83A9, $83B4, $8407, $820D, $8207, $826C, $840F, $836E.

### Round 4 (2026-06-12): all 16 targets byte-perfect (stub bootstrap)

- miu1 bootstrapped: MIU1_ENTRY (JMP OVERLAY_ENTRY at $8956) + three
  classified stubs (mask tables $7003-$73AE, ~2.6K string region
  $73AF-$7DCD, engine code $7DCE-$89BC).
- All remaining targets (7 overlays, makeindata, mapchars, tcmaps,
  stuph) emitted as single STUB chunks — **every target now verifies
  100% byte-perfect**; remaining work is measured by the 14 ORG stub
  chunks. The loop from here: /re-next style stub decomposition,
  starting with MIU1_CODE (the engine: every overlay JSRs into it),
  then MIU1_STRINGS structuring, then OUT as the first overlay.
- PDF 373 pages (stub HEX is transitional bulk; shrinks as stubs are
  replaced with annotated code).

### Round 3 (2026-06-12): NIF byte-perfect, rendered

- `nif` 7680/7680 with rendered figure: it is the **endgame victory
  screen** ("FIN" reversed) — calligraphic text about Mondain's death.
  Format: line-sequential raster, 192 rows x 40 bytes, no interleave,
  no screen holes. Renderer: .claude/scripts/render_nif.py.
- MAPCHARS render attempted (2x8/2x16/1x8/1x16, row+column major) —
  no hypothesis produced clearly-right tiles; deferred per the
  don't-ship-broken-renders rule until the tile blitter in MI.U1/OUT
  reveals the record format. Same for STUPH.

### Round 2 (2026-06-12): U1.INTRO byte-perfect

- `u1intro` 2469/2469. The file is the attract-mode title animation:
  castle drawn in self-modified strip blits, score-driven flashes,
  pennant flutter, star twinkle, bird, banner, sky wipe + curtain,
  then a 16-bit-LFSR fizzle dissolve of the page-2 title image. Any
  key BRUNs MI.U1; 'K'/ctrl-@ set mailbox $03CE (INTRO_FLAG) to 4/$10
  enabling banner/bird; ESC pauses.
- Cold start BRUNs MAKE.INDATA, which **builds the intro artwork at
  $6000-$8Fxx** (ART_* EQUs named per consumer; semantics + the one
  TODO-SYM resolve when makeindata is RE'd). INTRO_FLAG is also read
  with values 8/$0C — likely set elsewhere; watch for it in MI.U1 /
  MAKE.INDATA.
- RORG technique proven for relocated code (u1system $0100/$B700).

### Round 1 (2026-06-12): U1.SYSTEM byte-perfect

- `u1system` 1682/1682, all hygiene metrics zero, PDF 70 pages.
- U1.SYSTEM is a standard-form ProDOS system program (startup-path
  buffer at $2004, default `U1.INTRO`): banner, then installs a
  **resident MLI file library at $B700-$BAFF** (documented in full:
  20 vectors — BLOAD/BLOAD_AT/BSAVE/BRUN/SET_PREFIX/DESTROY/QUIT/
  READ_BLOCK/WRITE_BLOCK/raw MLI — JSR-plus-inline-args convention,
  text vs pointer path variants, error translation table, parameter
  blocks in page $BA, file buffer $BB00-$BEFF). **The game's whole
  disk interface goes through these $B7xx vectors** — expect MI.U1
  and overlays to JSR $B7xx everywhere; symbol names MLIB_* are
  ready for propagation.
- Page-one helpers at $0100-$016E survive overlay loads: inline
  print, reset trampoline, BRUN-the-startup-file + startup error
  display.
- `git push` FAILS in this container (https remote, no credentials).
  Commits are local; push from a credentialed environment.

### Round 0 (2026-06-12): Bootstrap complete

- Identified the game: **Ultima I: The First Age of Darkness** (Origin
  Systems, 1986 assembly remake; 4am crack). The disk is a ProDOS 1.1.1
  volume `/U1` in a DOS-order `.dsk` — no custom RWTS, all game data in
  ordinary ProDOS files.
- Wrote `.claude/scripts/prodos_extract.py` (ProDOS filesystem reader);
  extracted all 16 reference binaries plus the stock kernel
  (`reference/prodos111.bin`, verified "PRODOS 1.1.1 18-SEP-84
  COPYRIGHT APPLE" — excluded from RE targets as an OS dependency).
- Wrote `targets.json` (16 targets), filled all CLAUDE.md bootstrap
  sections (targets table, disk layout, memory map).
- `main.nw`: intro chapter, disk-layout chapter (sector-order math,
  volume file table), and the **boot block fully annotated and
  byte-perfect** (512/512) — entry/controller detection, PROM code
  relocation+patching trick, directory scan, sapling-file kernel load,
  Disk II seek/read with the overlapped timeout/nibble-search loop.
- PDF builds cleanly (37 pages).

## Work queue

- [x] DNG fully decomposed (Round 15: renderer, perspective
      tables, SHAPE_DRAW, MON_SHAPES rendered). DNG is done.
- [x] TWN overlay: DONE (Round 17, byte-perfect, 28 chunks). NPC
      format = 5x16-byte arrays at grid offset 684; map 38x18; shop
      system = 6 classes; pub = 8 hints; pricing = index^2 * CHA.
- [x] CAS overlay: DONE (Round 19, byte-perfect, 25 chunks). Quest
      system, gem prophecies, princess rescue (TM_REVEAL), storerooms
      (Get/Steal/Unlock), castle tick all decomposed. Pins the quest
      assignment and the endgame breadcrumb trail.
- [x] tcmaps: DONE (Round 16: structured + rendered).
- [x] SPA overlay (9930 bytes): DONE (Round 21, byte-perfect, 62
      chunks). Rotation+thrust flight sim; HIT_ENEMY pins PLR_VESSELS /
      the Space Ace gate; sprite atlas rendered. Pins the SPA->CAS->TM
      win-condition loop in code.
- [x] GEN overlay (8932): DONE (Round 22, byte-perfect, 37 chunks).
      Title menu + character generator (race/sex/class/name + the
      attribute-point editor) AND the bundled ProDOS disk formatter
      (RWTS_FORMAT + FORMAT_VOLUME). Pins the new-game path, the
      chargen attribute math, and the only raw-hardware disk code in
      the game.
- [x] TM overlay (8123): DONE (Round 23, byte-perfect, 37 chunks). The
      time-machine endgame -- Mondain battle, the Gem-of-Immortality win
      gate (destroy the gem THEN kill Mondain -> VICTORIOUS -> NIF +
      Control-RESET), the wireframe interior scene, the grid combat +
      spells, Mondain's AI. Pins the entire SPA->CAS->TM win loop in code.
- [x] makeindata (13877): DONE (Round 25, byte-perfect, 13 chunks). The
      cold-start title-screen BUILDER -- two RLE decompressors build the castle
      title (page 1) + the ORIGIN logo (page 2, fizzle-revealed) + the intro
      art ($6000). Both screens rendered. Cleared the LAST ORG stub and the
      last TODO-SYM (ART_* region ends $85FF). It does NOT build the world map
      (corrected the scout + a stale OUT claim). See makeindata_subsystem.md.
- [skip] TM CRAFT_GFX render: RE-ASSESSED round 31 as INFEASIBLE from the
      materials on hand (not merely deferred), and moved to the blocked list.
      The stroker is a scanline RLE blitter over ~13 indirect ZP base pointers
      (($D6)..($FA),Y) that the RESIDENT STUPH/MI.U1 actor engine sets up at
      runtime -- NONE is initialized in any of the 16 targets. Imaging it needs
      a full actor-engine emulator + the live projection state, with no
      correctness guarantee -> would risk a broken render. Documented in prose +
      the HEX blob + the SHAPE_STEP/BLIT_LINE plates instead. See tm_subsystem.md.
- [x] Synthesis chapters (the quality bar that makes the doc "done").
      DONE Rounds 26-30: all six synthesize-skill section types exist --
      Architecture overview (ch:architecture), Data-structure reference
      (ch:datastructures), Algorithm descriptions (ch:algorithms),
      Rendering pipeline (ch:rendering), Porting notes (ch:porting).
      Round 31 added the SPA flight-model and chargen point-buy sections
      to ch:algorithms (the two deepest remaining algorithm gaps).
- [x] Round-7-style reorganization: DONE Round 32. Promoted the 5 synthesis
      chapters into \part{Design} ahead of \part{Implementation} for the
      assembly chapters. Purely additive (the chapters were already in the
      right order), zero content churn, both part labels resolve, both parts
      in the ToC. THIS WAS THE LAST OPTIONAL ITEM -- the document is complete.

## Diagram campaign (rounds D1+)

Lean the doc into TikZ diagrams/flowcharts. Infrastructure + styles are in
main.nw's preamble (see diagram-infrastructure.md). Per-figure quality bar:
clean 2-pass build, float + \caption + \label + \ref'd from prose, FAITHFUL
to the asm (never invented), symbols not raw hex (except memory/disk maps),
prose-side only (16/16 byte-perfect must stay green).

Priority families (do in this rough order):

- [x] (a) state machines & mode flow: overall mode FSM (fig:mode-fsm),
      SPA->CAS->TM win FSM (fig:win-fsm). DONE round D1.
- [x] (b) control-flow flowcharts: dungeon generator (fig:dng-gen),
      combat resolution (fig:combat). DONE round D1.
- [x] (a cont.) monster/NPC AI state diagrams: TWN/CAS idle-anim NPC states
      (fig:npc-ai) + Mondain's AI (fig:mondain-ai). DONE round D2.
- [x] (b cont.) per-mode main-loop flowcharts: the GENERIC template
      (fig:mode-loop, ch:architecture, round D2) PLUS the three targeted
      variants -- fig:out-loop (OUT: hits+food death gate, idle 0.05/0.50,
      TURN_PASS, CMD_TBL patched JSR), fig:dng-loop (DNG: DNG_DRAW redraw at
      top, idle 0.01/0.10 + MON_TURNS each beat, DNG_CMDS), fig:spa-loop
      (SPA: no discrete tick, continuous PHYSICS, fuel-gated flight cmds,
      tail-jump JMP dispatch). DONE round D7.
- [x] (b cont.) the two RLE decompressors (makeindata MI_DECODE column-major
      RLE state machine = fig:mi-decode + the $8700 high-bit RLE = fig:mi-payload;
      makeindata_subsystem.md) as flowcharts, in the MAKE.INDATA section.
      DONE round D6.
- [x] (b cont.) boot/overlay-load flow: the boot chain (fig:bootflow,
      ch:architecture) DONE round D4. The GAME_LOAD-internals flow
      (fig:gameload: reset stack -> A>=$19? GEN : copy name -> FILE_LOAD via
      /RAM -> DISK_PROMPT retry -> redraw frame -> JMP OVERLAY_ENTRY)
      targeted after the RESPAWN/GAME_LOAD chunk. DONE round D8.
- [~] memory/disk maps + dgrecord bytefield layouts: PlayerBlock
      (fig:playerblock), object-record SoA (fig:soa), TCMAPS 764-byte record
      (fig:tcmap) all DONE round D3. STILL TODO: a bytefield/blocks version of
      the resident MEMORY MAP (have tab:memmap-arch as a table) and a
      DISK-LAYOUT diagram (the boot chain / ProDOS file load order); the
      $B400 live map buffer is covered by fig:tcmap (it IS the copied record).
- [x] engine-API / dispatch call graphs (manual TikZ layout): the patched-JSR
      command dispatch (fig:dispatch, TWN) DONE round D4. The STUPH
      jump-vector table + overlay->engine call directions are now ONE figure
      (fig:layers, ch:architecture): three resident layers, downward-only
      calls through the $1583 vector band, and the single upward
      GAME_LOAD->OVERLAY_ENTRY jump (engine never calls a specific overlay).
      DONE round D8.
- [x] rendering-pipeline diagrams (ch:rendering): the two-page XOR
      double-buffer flip (fig:pageflip); the tile-viewport blit (fig:tileblit);
      the ray-marcher slice loop (fig:raymarch, companion to fig:dng-gen);
      the SPA/TM projected-vector + XOR-sprite path (fig:sprite). DONE round D5.

Coverage by subsystem (figures so far): architecture (mode-fsm, win-fsm),
algorithms (dng-gen, combat). REMAINING with no figure yet: boot/intro,
STUPH, MI.U1 engine, OUT, DNG renderer, TWN, CAS, SPA, GEN, TM, makeindata,
data structures, rendering, porting. Lean in -- every subsystem that
warrants a diagram should get one in both the Design and Implementation
parts.

## Structural

- Hi-res rendering helper exists (`.claude/scripts/render_hires.py`);
  build per-data-file renderers on it as graphics are uncovered.
- The `aux=$8956` overlays likely share a common calling convention
  into MI.U1 — document the interface table once two overlays are RE'd.

## Blocked

- Render the four-continent WORLD MAP. Tried: full decomposition of
  MAKE.INDATA (round 25) -- it builds only the title screens, NOT the
  map; OUT round 12's RLE scan of makeindata found no 4096-cell stream.
  The packed continents load read-only from /U1.VARS at MAP_BASE, but
  /U1.VARS is ABSENT from this 4am crack disk (only /U1.PLAYER and the
  code files are present). Unblock = obtain a /U1.VARS file (a full,
  uncracked Ultima I ProDOS disk) and run OUT's RLE map loader on it.
  Until then the four continents cannot be imaged from the materials on
  hand. (The 10 town/castle maps ARE rendered -- they live in TCMAPS,
  which is present; see images/tcmaps_*.png.)
- TM CRAFT_GFX render: RE-ASSESSED round 31 -- INFEASIBLE from the
  materials on hand, not merely an unwritten round. SHAPE_STEP ($9EE5) +
  BLIT_LINE ($A176) is a scanline RLE blitter, and CRAFT_GFX is
  pre-rasterized hi-res byte runs (not (dx,dy,pen) vectors like the DNG/SPA
  galleries that rendered cleanly). The stroker + ANIM_SETUP dereference
  ~13 indirect ZP base pointers (($D6)..($FA),Y) that the RESIDENT
  STUPH/MI.U1 shape-actor engine initializes at runtime -- verified by grep
  that NONE of them is set in any of the 16 targets. Imaging it requires
  reverse-engineering and emulating that whole actor engine + reconstructing
  the live cell-projection state, with no correctness guarantee -> a wrong
  image would violate the don't-ship-broken-renders rule. So it is left
  un-imaged and documented in prose + the verbatim HEX blob + the
  SHAPE_STEP/BLIT_LINE plates, which is the honest level of treatment. Do
  NOT re-attempt without a full STUPH actor-engine emulator. See
  tm_subsystem.md for the full evidence.
