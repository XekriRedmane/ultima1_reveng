---
name: spa-subsystem
description: Ultima I SPA space-combat overlay -- rotation/thrust flight sim, enemy craft, the Space Ace counter (DECOMPOSED round 21, byte-perfect)
metadata:
  type: project
---

SPA ($8956-$B01F, 9930 bytes) is the SPACE COMBAT overlay -- the ace-pilot
layer the pub lore and CAS both reference. DECOMPOSED round 21 (byte-perfect,
62 chunks); scout below kept for the architecture summary.

**Round-21 decomposition facts (proven byte-perfect):**
- Pipeline cloned from gen_cas: .claude/scripts/gen_spa.py + spa_symmap.py +
  spa_labels.py + gen_chapter_spa.py. INLINE map is trivially just MSG_PRINT
  ($8119, 45 calls); no STR_* inline-word calls, no patched-JSR dispatch.
- SMC sites: DISP_OP (the JMP at $8AB0 patched from DISPATCH_TBL),
  SHAPE_SMC/$9E9A + SHAPE_SMC2/$9F02 (the two unrolled blit loops' shape
  pointers), BLIT_EOR/$9F0C + BLIT_OP/$9F0D (EOR mask + patched ORA opcode in
  the draw blit), INFORM_JSR/$93D9 (the Inform sub-handler JSR operand). All
  use `= *+N` anchors; STALE_FFFF EQU $FFFF emits the stale on-disk operand.
- THE blitter has TWO copies: $9E99 = collision-test pass (AND/ORA into
  ZP_BLIT_HIT), $9F01 = draw pass (EOR/ORA to screen). BIT $93F0 (DRAW_MODE
  bit6) selects which. SHAPE_PRESHIFT/$9F2E rotates rows into byte alignment.
- ENGINE addresses corrected vs the scout: PRINT_STAT16 = $8355 (NOT $8230);
  POPUP_FRAME = $841E. WIN_STATS = $15A1 (STUPH). $A107 = MUL8_FIXED (8x8 ->
  16 fixed mul), $A123 = DIV16, $A154 = FUEL_BURN, $A182 = WIN_STATS_DRAW,
  $A1BD = SPEND_TURN (JSR TICK).
- Cross-chunk locals promoted to globals (4): PHYSICS_MOVE/$8AB8,
  RETICLE_PLOT/$9411, RETICLE_STROKE/$97BB (else separate SUBROUTINE scopes
  break the branches). Same lesson as CAS/round-12.
- DATA SPANS pinned: $8C47 base geom, $8F40 ship fuel/shield, $8FF4/$9046
  thrust/retro deltas, $91B6-$9207 scan-state+SCAN_CELLGLYPH+DISPATCH_TBL (26
  words), $9219 DIR strings, $9243-$9298 physics/actor BSS (incl SCALE_TBL
  ramp $928F-$9297), $93DE speed strings, $9BCA-$9C53 starfield BSS, $9C87
  grid offsets, $A0FE xport, $A1CF-$B01F the sprite/projection tables.
- SPRITE ATLAS RENDERED: 36 entries in 6 parallel 36-entry tables
  (SHAPE_PTR_LO/HI $A1CF/$A1F3, XOFF/YOFF $A217/$A23B = also the firing hit
  box, WID/HGT $A25F/$A2A7, DX $A283), pixels at $A2CB. Shapes 0-8 = enemy at
  9 distance scales (1x1 dot -> 3x45), shapes 9-35 = 27 rotation frames +
  planet/sun disc. Renderer .claude/scripts/render_spa_ships.py ->
  images/spa_ships.png + spa_shapes_all.png. The craft is a TIE-fighter shape:
  two outboard pods + central diamond cockpit. 7-pixel-per-byte hi-res, low
  bit leftmost, bit7 (artifact) masked by the blitter.
- THE KILL COUNTER confirmed in code: HIT_ENEMY $96E2 drains enemy HP
  ($B099,Y -= $40), awards +100 exp (cap 9999 at $7EE8=$27/PLR_EXP=$0F), then
  INC PLR_VESSELS/$7EB6 (saturates via BNE/DEC). CMP #$14 BEQ -> "rank of
  Space Ace" popup; >$14 -> "still a Space Ace". This is the ONLY writer of
  PLR_VESSELS; CAS reads it for the princess-rescue TM_REVEAL gate.
- PLR_FUEL/$7EE9 and PLR_SHIELD/$7EEB reuse the food/?? player slots; both
  16-bit. FUEL_BURN clamps at 0 and clears the rotation timer when empty.

----- original round-20 scout (architecture reference) -----

**Why:** it is the largest remaining overlay, structurally unlike the
town/castle/dungeon overlays (a real-time rotation+thrust flight sim, no
patched-JSR dispatch table), and it closes the win-condition loop:
destroying 20 enemy craft makes the player a Space Ace, which CAS's princess
rescue gates on (PLR_VESSELS >= $14) before setting TM_REVEAL.

**How to apply (decomposition skeleton):**
- Reuse the engine-API + STUPH EQU block as for TWN/CAS/DNG (overlay base
  $8956, JSRs into MI.U1). NO patched-JSR dispatch idiom here (no `20 ff ff`
  in the file); commands run through GET_COMMAND then a direct handler-
  address table at $91D3 (8 words, self-modified into the loop at $8AA4).
- ENTRY $8956: restore zp $4E/$4F from $7EEF/$7EF0 (saved space position?),
  set DIR_STR_PTR=$9219 so the movement keys read "Thrust / Retro /
  Clockwise / Counter-Clockwise" (a rotation-based flight model, Star
  Raiders/Asteroids style -- NOT N/S/E/W). Zero a big BSS block ($B01F
  down), run a "10..9..8.." liftoff countdown ($A7 timer + ".." prints,
  KEY_PENDING aborts), "Thou hast lifted off!", seed the starfield/enemy
  tables ($9BFF / $9C29 via RND, $B020/$B099 grids), then the main loop.
- MAIN LOOP $8A53: status "Shld|Fuel" (WIN_STATS), poll KEY_GET ->
  GET_COMMAND; X<8 is a flight command (gated on fuel $7EE9/$7EEA "No
  fuel!! Wilt thou drift forever?!?"), self-modify the handler from $91D3
  into the loop. Handlers: $8FAD Thrust, $900E Retro, $904E Clockwise,
  $9074 Counter-Clockwise, $9207/$9213 others. Then physics: integrate
  velocity $6E/$6F into position $9288/$9289 (wrap at $0E/$F4 -- a torus),
  move enemy craft, test collisions against $8C47/$8C4B (base + enemy
  position tables), star-proximity hazard ("Thy ship melts near the
  star!" -> RESPAWN; "Thy shield is drained!").
- COMBAT: firing reaches the hit handler ~$96E2 ("Hit!!!"): enemy HP
  ($B099,Y -= $40), award +100 exp (cap 9999), then INC PLR_VESSELS at
  $9732. Reaching exactly $14 (20) fires the "Thou hast achieved the rank
  of Space Ace!" popup ($9766); >$14 prints "still a Space Ace". This is
  THE PLR_VESSELS source -- the counter CAS reads. Enemies shoot back:
  "Alien fires!" $9AC3, "You've been hit!" $9AEF, shield drain $9B33;
  must "eliminate all enemy craft first" ($99D1) before some action.
- DOCKING/LANDING: "Docked! Welcome to Base!" $8C52 (refuel at a base;
  "canst not refuel without..." $8C9D; "spacedoors open" $8CFB). Landing
  to a planet needs a shuttle: "Only space shuttles are heat-shielded for
  landings" $8F56 -> "Thou hast landed safely!" $8F90. "View can't be
  changed whilst in space dock" $92A3.
- DATA TAIL: dir-name strings at $9219 ("ThrustRetroClockwiseCounter-
  Clockwise"), handler table $91D3, collision/base tables $8C47/$8C4B,
  per-enemy state in the $B020/$B099 BSS grids and $9243/$924D tables.
  Establish the code/data boundary with overlay_disasm + a HEX dump of
  the $91xx-$92xx band before authoring.
- Pipeline: clone the gen_cas trio (gen_spa.py + spa_symmap.py +
  spa_labels.py + gen_chapter_spa.py). Watch the inline-arg JSRs
  (MSG_PRINT text) and any self-modified handler operands ($8AB1/$8AB2 in
  the main loop is the dispatch operand patched from $91D3).
- RENDER opportunity: the starfield + ship sprites are graphics; render
  them when the format is pinned (standing rule).
