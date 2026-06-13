---
name: twn-cas-subsystem
description: Ultima I TWN/CAS town+castle overlay architecture -- shared loader, shop system, NPC metadata format, live map buffer layout (round 17+)
metadata:
  type: project
---

TWN ($8956-$AA62, 8461 bytes) is the town overlay; CAS shares its loader and
much of its structure. Decomposed in round 17.

**Why:** the shop system, NPC-table format, and live-map-buffer layout are
intricate and shared with CAS; the TCMAPS grid dimension was wrong in round 16.

**How to apply:**
- CORRECTION to round 16: town/castle maps are 38 cols x **18** rows = 684
  cells, NOT 38x19. The 80-byte NPC table (5 parallel 16-byte arrays) sits
  at grid offset 684, i.e. $B6AC after the map is copied to $B400. Total map
  record = 684 + 80 = 764 bytes. OVERLAY_ENTRY copies 3 full pages (768),
  over-copying 4 harmless bytes. Per-row stride is 38 ($26); MAP_DRAW ($A1AE
  in TWN) draws rows $01..$12 (18 rows) x cols $00..$25 (38) from $B400 via a
  self-modified pointer ($A1C6/7).
- LIVE MAP BUFFER $B400 (768 bytes): cells $B400..$B6AB (grid), then 5 NPC
  arrays of 16 entries each: TYPE $B6AC, XPOS $B6BC, YPOS $B6CC, HP-lo $B6DC,
  HP-hi $B6EC. TYPE $FF = empty slot; $00 player-start marker; $02/$03 hostile
  (guard/monster, the idle anim attacks when type==3); $04 wandering townsfolk
  (Iolo the Bard / pickpocket). HP is 16-bit (e.g. King = $07D0 = 2000).
- Per-row map-row pointer tables in the TWN file: $A96D (lo) / $A97F (hi), 18
  entries = $B400 + row*38. NPC_AT ($A288) reads a cell through these, and if
  the glyph >= $60 scans the 16 NPC slots for one at (x,y), returning
  type+$30 and stashing the slot in $A937.
- DISPATCH: OVERLAY_ENTRY $8956 -> main loop $89EC -> word table $8A56 (26
  entries, X=2*cmd, patched-JSR at $8A4D). Same idiom as OUT/DNG (STALE $FFFF
  on disk). Many commands point at engine QUERY_MARK $8407 (disabled in town):
  Board/Fire/Get-as-such/HyperJump/K-limb/Open/View/X-it. Accelerator $8845
  and Noise $885B reuse the engine sound toggles.
- TOWN COMMANDS (TWN-local handlers): move N/S/E/W $8A8A (probe via $A26F,
  "Blocked", leave town if you step off the 38x18 edge -> EXIT_TO_OUT $8ABF),
  Pass $8AEE, Attack $8AFB (pick weapon, pick dir, march hitting NPCs;
  to-hit vs $7ECA charisma, damage to HP arrays, "Killed!" frees the slot,
  XP award), Cast $8C9F ("no effect" - spells are no-ops in town), Drop $8CBE
  (P/W/A: Drop-Pence $8D0A gives gold to a type-$61 NPC for HP+spell reward;
  Drop-Weapon $8DFA / Drop-Armour $8E15 via DROP_PICK popup $8E78), Get $8F3F
  / Unlock $9EF5 (=" what" + QUERY_MARK), Quit $8F4B ("only allowed
  outdoors"), Ready $8F70 (S/W/A -> engine READY_CMD), Steal $8F86, Transact
  $9093, Inform $A190 ("the city of <place>"), Ztats $9F01 (engine INVENTORY).
- IDLE ANIMATION $9F07 (runs on key-timeout AND after each command): walks the
  16 NPC slots; hostiles (type 3) home on the player and attack (guard combat
  $9FDB: to-hit vs armour+charisma, damage to PLR_HITS, death -> RESPAWN);
  townsfolk (type 4) wander ($A07E -> $A0A0 / $A15B / $A0EB), with the famous
  flavour: "Iolo the Bard sings: Ho eyoh he hum!" and Iolo the pickpocket who
  steals an unreadied weapon.
- SHOP SYSTEM (Transact $9093): NPC type $64..$6C maps through $A9AF to one of
  SIX shop classes. Per-class pointer tables (X=2*class): NAME $A9CF, BUY
  $A9DB, SELL $A9E7. Classes: 0 Armour (buy $918D/sell $9C5B), 1 Grocery (buy
  $9257/sell $9D5C "no used food"), 2 Weapons (buy $9383/sell $9469), 3 Magic
  (buy $9584/sell $9DB1 "we don't buy spells"), 4 Pub (buy $9655/sell $9DD2),
  5 Transport (buy $9AB7/sell $9D7F). Each shop has a POOL of 8 flavour names
  ($A50F..$A92C string pool, ~48 strings); the name shown is place-selected.
- PRICING: item base cost = item_index^2, table $A9BF = 00 01 04 09 10 19 24
  31 40 51 64 79 90 A9 C4 E1 (squares 0..15). Price helper $9ED3 multiplies
  base by a charisma factor derived from $7ED0 (Charisma) / $7ED2; buy uses
  ($C8-$7ED2)>>2 etc. Shop helpers band $9E01-$9EF4: SHOP_DEBIT $9E01,
  CAN_AFFORD $9E17 (carry test), SHOP_GETKEY $9E24, "Sold!"/"Done!"
  $9E3B/$9E4A, TOO_POOR $9E59, price calculators $9E84/$9E94/$9EA1/$9EBF,
  multiply $9ED3.
- PUB ($9655): pay 1 gold for "a cold one"; risk being "seduced" (lose half
  gold, distance/charisma gated via $A3F6 distance + sqrt root $A47E -- same
  integer-sqrt as DNG MON_DIST); else 75/256 chance of a HINT from an 8-entry
  pointer table $A9F3 (self-modified JSR $97BC). The 8 hints are the canonical
  Ultima I tavern lore (20 enemy vessels/ace, rescue princess, time machine,
  destroy evil gem, magic lakes, Mondain created the gem 1000 yrs ago, the
  full quest text).
- TRANSPORT shop ($9AB7) uses the shared engine COURT_CELLS (4-entry lot
  array) to track which vehicles are parked; buying writes transport+8 into a
  free COURT_CELLS slot. Availability is continent/gold/flag gated (Horse/Cart
  land, Raft/Frigate sea, Air Car needs >= $0BB8 gold, Shuttle needs flag
  $7EA4 clear). $A9B8 = transport->passable-terrain map.
- NUMBER INPUT $A2F9: decimal entry into 16-bit $AA69/$AA6A (x10 via shifts),
  backspace via an undo buffer $AA63/$AA65.
- NPC NAME table $A942 (packed, hi-bit): King, Merchant, Princess, Guard,
  Jester. NPC sprite-glyph table $A9A1 (indexed by type). Gendered address
  word $A961/$A967 = "Wench"/"Lecher", chosen by PLR_SEX at entry.
- CODE ends $A50E; DATA $A50F-$AA62 (shop-name string pool, $A942 names,
  gendered words, per-row ptr tables, NPC sprite/shopclass/cost tables, shop
  pointer tables, pub-hint table). Tail past $AA03 is on-disk-stale BSS.
- BSS state vars $A92D-$A941 (zero on disk): $A932 idle-msg flag, $A933
  insulted/aggro flag (set when caught stealing -> "None will talk to thee"),
  $A934 NPC loop idx, $A935 digit count, $A937 hit NPC slot, $A939/A price16,
  $A93D shop item loop, $A93E/F/40 transport-avail counts, $A941 pub visits.
