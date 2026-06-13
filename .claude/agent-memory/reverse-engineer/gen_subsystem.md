---
name: gen-subsystem
description: Ultima I GEN overlay -- title menu, character generation, player-save writer, bundled ProDOS disk formatter + RWTS (DECOMPOSED round 22, byte-perfect)
metadata:
  type: project
---

GEN ($8956-$AC39, 8932 bytes) is the NEW-GAME / TITLE overlay -- the A=0
GAME_LOAD slot from MI.U1. DECOMPOSED round 22 (byte-perfect, 37 chunks);
scout below kept for architecture reference.

**Round-22 decomposition facts (proven byte-perfect):**
- Pipeline cloned from gen_spa: .claude/scripts/gen_gen.py + gen_symmap.py +
  gen_labels.py + gen_chapter_gen.py + gen_emit_chunks.py + gen_author.py +
  gen_build_section.py. INLINE map: MSG_PRINT $8119, MSG_AT $8115, STR_NTH_CAP
  $80B1 (w), the GEN-LOCAL trampoline PROMPT_LINE $9388 (text! homes cursor to
  bottom line then falls into MSG_PRINT), and the MLIB pointer paths $B721 (w,w)
  / $B724 (w,w,w).
- SMC sites (all `= *+N` anchored): DECRYPT_SRC/$8A5B + DECRYPT_PTR/$8A5E (the
  continue-game record copy GAME_VARS->PLR_SAVE, two walking ptrs), COPY_SRC/
  $8A84 + COPY_DST/$8A87 (the 13-page GAME_IMAGE->$6000 copy), CLEAR_SRC/$8B02
  + CLEAR_DST/$8B05 (the chargen portrait-clear loop). The formatter's $A1xx/
  $A2xx/$ACxx "SMC" are paramblock fields / RWTS scratch bytes, handled as
  labeled HEX data spans, NOT instruction-operand SMC.
- THE KEY CODE/DATA SUBTLETY: the file block-copies $9440-$A13F (13 pages) to
  $6000. Inside those pages: GAME_IMAGE ($9440-$A119, data) THEN FORMAT_VOLUME
  code ($A119-$A3C5). Past that, BOOT_IMAGE ($A3C5-$A7B7) is a ProDOS boot
  loader stamped onto block 0 of the new disk -- it is PURE DATA in GEN's
  address space (NO real GEN code refs it; verified by ref scan), so emit it as
  HEX. Disassembling it as code produced 28 spurious raw-hex JSR/JMP (ASCII
  string bytes like "BO"/"PR" decoding as JSR $4F42 etc.) -- the tell that a
  region is data, not code.
- ATTRIBUTE EDITOR: six 16-bit stats at PLR_HITS,X with X=2*CURSOR_IDX (idx 1..6
  = STR/AGI/STA/CHA/WIS/INT at $7EC8.. -- idx 0 = HITS, skipped). Point pool
  POINT_POOL=$903F starts $1E (30), per-stat floor $0A ceil $19. Race bonuses
  (PICK_RACE): Human +5 INT, Elf +5 AGI, Dwarf +5 STR, Bobbit +10 WIS -5 STR.
  Class bonuses (PICK_CLASS): Fighter +10 STR+AGI, Cleric +10 WIS, Wizard +10
  INT, Thief +10 AGI.
- THE DISK FORMATTER is two layers: RWTS_FORMAT $A800 (a complete hand-rolled
  Disk II RWTS -- steps the arm 35 tracks via SEEK_DELAY_A/B tables at $AB4B/
  $AB57, writes 16 sectors/track as D5/AA/96 address fields + 6-and-2 GCR data,
  verifies by read-back; talks raw $C0xx soft switches, no ProDOS) THEN
  FORMAT_VOLUME $A119 (the ProDOS volume-directory writer: patches WRITE_BLOCK
  paramblocks, scans PRODOS_DEVLST $BF32, writes the 4 dir blocks + bitmap via
  MLI $BF00). DO_FORMAT $92BA brackets both with a zp $D0-$DD save/restore
  (ZP_SAVE $93E9). This is the ONLY place in the game that bypasses MLIB and
  touches drive hardware.
- NAME COLLISIONS fixed (separate-target labels but shared noweb @ %def index):
  OVERLAY_ENTRY is @ %def'd only ONCE (miu1 bootstrap) -- exclude from GEN's
  @ %def (DEFINED_ELSEWHERE set in gen_emit_chunks). GEN's BSAVE wrapper renamed
  DO_BSAVE->SAVE_PLAYER, its "press space" PRESS_SPACE->FMT_PRESS_SPACE (both
  collide with engine/MLIB routines of the same name at different addresses).
- $6000 buffer = GAME_VARS (BLOAD target for the continue-game record + the
  13-page new-game image dest). $6D00 = GAME_VARS_FLAG (world-initialised flag).
- 3 picker labels were mis-placed on inline menu TEXT, not the routine entry
  (classic inline-text pitfall): real PICK_RACE=$8C7E, PICK_SEX=$8D3C,
  PICK_CLASS=$8D98 (each begins JSR EDITOR_DRAW/CLEAR_LINES then LDY #$12 menu
  draw). Chunk boundaries MUST fall on instruction starts, never mid-inline-text.

----- original round-21 scout (architecture reference) -----

**Why:** it is the game's front door (title menu + character creation) and it
also bundles a complete ProDOS disk formatter for initialising the player save
disk -- a self-contained low-level disk subsystem worth documenting.

**How to apply (decomposition skeleton):**
- Reuse the engine-API + STUPH EQU block as for SPA/CAS (overlay base $8956,
  JSRs into MI.U1). Inline-arg JSRs: MSG_PRINT $8119 + MSG_AT $8115 (text),
  STR_NTH_CAP $80B1 (inline word), and the MLIB pointer-path BLOAD/BSAVE at
  $B721/$B724 (inline word,word -- addr + path pointer). Set the INLINE map
  accordingly (MSG_AT takes text; the $B7xx pointer paths take w,w).
- ENTRY $8956: WIN_FULL, draw the title + menu "a) Generate new character /
  b) Continue previous game" (MSG_AT $896C), PAGE_FLIP, KEY_WAIT. 'a' ($41)
  -> chargen $8AC3; 'b' ($42) -> BLOAD the saved player ($B721 ptr-path,
  word $6000, word PATH_PLAYER), verify the $6000 signature == $01CA
  (PLR_SAVE length, lo=$CA hi=$01), else "Please put in the Player disk."
  and retry / offer to format.
- CHARGEN $8AC3: "Character Generation" header; an SMC clear loop $8B01
  (LDA $FFFF / STA $FFFF, operands patched from $8B02/$8B05 = src/dst,
  clears the portrait region $904F.. to $90D6..). Then the attribute editor.
- ATTRIBUTE EDITOR $8FB1 (draw) + $8C00 (input loop): six stats shown with a
  highlight cursor HILITE_IDX; "Points left to distribute" = $903F (starts
  $1E=30? note $8B28 sets $903F=$1E, $9041=1). Keys: up/down ($1B esc ->
  back to menu $895B) move the cursor; left ($08) decrements a stat (floor
  $0A=10, returns the point to the pool); right ($15) increments (ceil
  $19=25, costs a point); space = done. Stats live at PLR_HITS,X with X =
  2*HILITE_IDX (the six 16-bit attribute pairs STR/AGI/STA/CHA/WIS/INT). The
  STR_STATS table names them.
- THE PROMPTS (chargen sub-steps, each KEY_WAIT a/b/c/d): RACE $8C8E
  "a)Human b)Elf c)Dwarf d)Bobbit" -> PLR_RACE; SEX $8D46 "a)Male b)Female"
  -> PLR_SEX (the sex-name strings "male"/"female" are an in-file table at
  $9043, used by STR_NTH_CAP); CLASS $8DA2 "a)Fighter b)Cleric c)Wizard
  d)Thief" -> PLR_CLASS; NAME $8E6A "Enter thy name:" -> PLR_NAME (input
  loop $8EB3/$8EC7, padded). Each echoes "Race/Sex/Class ... <value>".
- SAVE: BSAVE PLR_SAVE, $01CA bytes, to PATH_PLAYER via $B724 (ptr path).
  Then GAME_LOAD(OUT) presumably -- trace the exit.
- DISK FORMATTER (the second subsystem, ~$9100-$A7B6 and $A800-$AC22):
  "Drive: ( )" $9143, "Non-ProDOS disk" $9269, "? (Y-N)" $92A3, "Press Space
  to continue" $939D. Low-level: JMP ($00E8), JSR $F479 (ROM), $C040/$C0xx
  disk soft switches, a ProDOS parameter/buffer block at $A7C7 ("PRO..."),
  block-format helpers $A800+ (sector nibblize $A823/$A83A, $A9C6). This
  formats/initialises a blank player save disk so the player can save. It is
  self-contained code running in place (NOT relocated). Decode carefully --
  expect ROM entry EQUs ($F479 etc.) and disk soft-switch EQUs.
- DATA SPANS to pin: BSS at $903F-$9042 (point/cursor counters), the sex
  strings $9043+, more BSS $9050-$90A6, $93E8-$93F7; the big tail BSS
  $A7B7-$A7FF (format scratch + the "PRO" param block at $A7C7); and the
  $AC23-$AC39 tail. Establish boundaries with overlay_disasm + raw HEX dumps,
  exactly as for SPA.
- PIPELINE: clone gen_spa.py + spa_symmap.py + spa_labels.py +
  gen_chapter_spa.py -> gen_gen.py / gen_symmap / gen_labels /
  gen_chapter_gen.py. Watch the SMC clear loop ($8B02/$8B05 operands) and the
  disk-formatter SMC ($AC24/$AC36 patched in $A823). Continue option's BLOAD
  signature check is a clean known-quantity.

**Engine-address note (carried from SPA round 21, verify in GEN too):**
PRINT_STAT16 = $8355, POPUP_FRAME = $841E, WIN_STATS = $15A1, PRINT_NUM8 =
$820D, STR_NTH_CAP = $80B1, MSG_AT = $8115. GEN also uses WIN_FULL and
PAGE_FLIP (STUPH) -- get their addresses from the existing defines blocks.
