---
name: spa-subsystem
description: Ultima I SPA space-combat overlay -- rotation/thrust flight sim, enemy craft, the Space Ace counter (scouted round 20)
metadata:
  type: project
---

SPA ($8956-$B01F, 9930 bytes) is the SPACE COMBAT overlay -- the ace-pilot
layer the pub lore and CAS both reference. Scouted round 20; decompose next.

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
