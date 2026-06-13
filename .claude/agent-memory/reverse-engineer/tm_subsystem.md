---
name: tm-subsystem
description: Ultima I TM overlay -- the time-machine endgame: Mondain battle, the Gem-of-Immortality win gate, the NIF victory + Control-RESET, the wireframe scene renderer (DECOMPOSED round 23, byte-perfect)
metadata:
  type: project
---

TM ($8956-$AD11, 8123 bytes) is the FINAL overlay -- the endgame battle inside
the time machine. DECOMPOSED round 23 (byte-perfect, 37 chunks, 27 plates).
Reached when CAS sets TM_REVEAL (space ace + princess rescue) and the player
travels to the time machine. See [[twn-cas-subsystem]] for the handoff.

**THE WIN CONDITION (the whole point of the game):**
1. Enter the craft with the four gems -> four sockets shown (R/G/B/W markers
   drawn by DRAW_SOCKET $A44B at x=$5E/$73/$88/$9D, colors 5/1/6/7).
2. Press LAUNCH -> time-travel narration -> "face to face with the evil Mondain".
3. Mondain is shielded by his Gem of Immortality: GEM_HP=$7EF4 (16-bit, entry
   sets $03E8 = 1000). Striking Mondain (TM_ATTACK) drains GEM_HP via the shared
   HIT_RESOLVE ($8F80). But killing Mondain WITHOUT first destroying the gem only
   yields " ...or is he?" -- he regenerates (MONDAIN_TURN heals $7EF4/F5 += 5).
4. TM_GET ($94D6) on the gem cell -> "The Gem is DESTROYED!" sets GEM_GONE
   ($95AB) and weakens his aura ("magical aura doth seem substantially
   diminished").
5. THEN reducing GEM_HP to 0 with GEM_GONE set -> "Mondain is dead!" -> "THOU ART
   VICTORIOUS!" -> TM_VICTORY ($9034) BLOADs NIF (the victory screen, via
   MLIB_BLOAD inline path "NIF"), hooks Control-RESET ($03F2-$03F4 = reset vector
   + powerup byte XOR $A5), runs a hi-res screen-MELT dissolve into NIF with sfx,
   prints STR_RESTART "Press Control-RESET to restart." and hangs. THE END.
   Lose path: MONDAIN_HIT drains PLR_HITS -> 0 -> TM_DEATH "THOU ART DEAD! ...
   defeated by Mondain the Wizard! THE UNIVERSE IS DOOMED!!" -> RESPAWN.

**ARCHITECTURE (same overlay skeleton as OUT/DNG/TWN/CAS/SPA):**
- File head $8959-$8AD6 = fixed-point MATH suite (MUL8/MUL16/MUL16B/DIV16 +
  binary->BCD print helpers + two digit-weight DATA tables BCD_WEIGHTS $8A5D /
  BCD_WEIGHTS2 $8ACF). Generic support; the renderer + combat lean on it.
- Real entry TM_ENTRY $8AD7. Main loop $8E5E with patched-JSR dispatch
  (DISPATCH_JSR=*+1 at $8E9F, stale disk operand $841D = STALE_DISPATCH, table
  DISPATCH_TBL $8EA8 26 words). Cast uses a second patched JMP SPELL_JMP=*+1 ->
  TM_SPELL_TBL $9249 (11 words). Mondain's AI rolls RND_MOD(3) of
  MONDAIN_SPELL_TBL $9A0F (magic missile / mind blaster / psionic shock).
- Combat is on a small INTERIOR GRID: CELL_STATE $A2FC array, CELL_COL $A3E3
  per-row base table. Player at ZP_PTR cell; Mondain/origin ref at TGT_X/Y
  ($B628/$B629); gem at GEM_X/Y ($B62A/$B62B); working cell DST_X/Y ($B62C/D).
  Move handler reads the faced cell: empty -> walk, force-field $03 -> "Blocked!",
  else "Burned!" (lose HP/10). The combat is grid melee + spells, not the
  real-time flight of SPA.
- The SCENE is drawn as a WIREFRAME pseudo-3D craft interior: SHAPE_STEP $9EE5
  is a vertex/filled-band stroker walking a shape display list from a self-mod
  pointer ($B2), plotting via HGR row pointers ($B8/$BB) through BLIT_VEC $A16E
  (3-entry jump table, stale $1111 = STALE_BLITVEC) -> BLIT_LINE $A176. Shapes
  pointed to by the table at $9EB3 (-> CRAFT_GFX $A470, the vertex-list data
  blob). PROJ_TBL $9D2A = three 20-byte cell->screen projection tables.

**RENDERER NOT RENDERED -- and now judged INFEASIBLE from the materials on hand,
NOT merely deferred (re-assessed round 31, final-polish pass):** CRAFT_GFX is a
single runtime-interpreted display list bound to live cell-projection state (NOT
a gallery of static sprites like SPA/DNG shapes -- those rendered precisely
because they are self-contained scaled vector lists). The shape table at $9EB3
has effectively ONE entry ($A47C). The bytes at CRAFT_GFX are a header/control
block ($00..FF..3E030210) + 80-fill rows + PRE-RASTERIZED hi-res byte runs (the
80-high-bit screen-byte pattern), NOT (dx,dy,pen) vectors -- SHAPE_STEP/BLIT_LINE
is a SCANLINE RUN-LENGTH BLITTER (LDA ($C1,X)/STA ($B2),Y), not a vector
interpreter.
  THE BLOCKER (verified by grep over all 16 targets): the stroker's inner loop
and ANIM_SETUP dereference ~13 indirect ZP BASE pointers -- ($D6),Y ($D8),Y
($DA),Y ($DC),Y ($DE),Y ($E0),Y ($E2),Y ($F0),Y ($F2),Y ($F4),Y ($F6),Y ($F8),Y
($FA),Y -- and NONE of these base pointers is initialized anywhere in main.nw.
They are set up by the RESIDENT STUPH/MI.U1 shape-ANIMATION ACTOR ENGINE at
runtime (the same ZP cells are EQU-aliased as RWTS temporaries RW_T6/RW_ERR/
RW_TA/RW_TC -- the engine repurposes them as actor-table bases). SHAPE_NEXT only
writes the working NPC array at $00D6 itself, never the ($D6) base.
  So a faithful image requires reverse-engineering and emulating that entire
resident actor engine (where those 13 bases come from + the frame/displacement/
colour tables they reference) AND reconstructing the exact live cell-projection
state -- a large separate effort with NO guarantee of a correct raster. Per the
don't-ship-broken-renders standing rule, attempting it risks shipping a garbage
figure. CONCLUSION: leave CRAFT_GFX un-imaged; it is documented in prose + the
verbatim HEX blob + the SHAPE_STEP/BLIT_LINE plates, which is the correct and
honest level of treatment. Do NOT re-attempt without a full STUPH actor-engine
emulator. This is the only TM graphic outstanding and it is acceptably so.

**PIPELINE (cloned from gen_gen, kept for reference/reuse):**
.claude/scripts/tm_gen.py + tm_symmap.py + tm_labels.py + tm_chapter_tm.py
(self-test -> /tmp/tm_all.asm byte-perfect) + tm_emit_chunks.py (37 chunks) +
tm_build_section.py (prose+plates+defines+collection -> /tmp/tm_section.nw).
INLINE map: MSG_PRINT $8119, MSG_AT $8115, POPUP_TEXT $A436 (framed) +
POPUP_TEXT_NF $A43C (no frame) -- BOTH fall into MSG_PRINT and take inline text,
MLIB_BLOAD $B703 (inline path text!), STR_NTH_CAP $80B1 (inline word).

**ROUND-23 PITFALLS (added to [[toolchain-pitfalls]] too):**
- TWO TM-local inline-text trampolines ($A436 framed, $A43C unframed). Missing
  $A436 from INLINE garbled the "THOU ART VICTORIOUS!" panel as code.
- MLIB_BLOAD ($B703) takes an INLINE zero-terminated path -- the NIF load
  ("JSR $B703 / 'NIF',0") disassembles as garbage if not in INLINE.
- 7 command-handler names collide with OUT/DNG @ %def (CMD_ATTACK/CAST/INFORM/
  PASS/QUIT/READY, SPELL_TBL): renamed all TM commands TM_* / TM_SPELL_TBL.
- 36 helper subroutines were referenced ACROSS chunk boundaries via .Lxxxx
  locals -- dasm scopes .L per-SUBROUTINE so the per-chunk tangle (unlike the
  single-scope self-test) fails "Unknown Mnemonic 'jsr .L9xxx'". MUST promote
  every cross-chunk .L target to a global label. The self-test (one SUBROUTINE)
  HIDES this; only the real per-chunk tangle catches it -- ALWAYS run the real
  tangle (keep all SUBROUTINE directives) as the final byte-check, not just the
  single-scope self-test.
- 3 in-code 1-byte BSS storage bytes (GEM_GONE $95AB, IDLE_CNT $9826, ANIM_CNT
  $9843) sit between routines (BRK fillers) and are abs-referenced -> make each a
  1-byte data span + DATA_LABEL.
- tm_build_section BANDS must cover every out-of-file SYM addr or the EQU
  silently drops and the tangle fails on an undefined symbol (HGR1 $2000 fell in
  no band). Added a catch-all "other" band as a guard.
