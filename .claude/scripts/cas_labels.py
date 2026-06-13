# CAS-local global routine labels (address -> name). Branch-internal targets
# stay as .Lxxxx local labels; these are the named subroutine entry points.
LBL = {
 0x8956:'OVERLAY_ENTRY',
 0x89E6:'MAP_PROMPT',          # scroll + cursor home before each prompt
 0x89EE:'CAS_LOOP',            # prompt + idle-poll loop
 0x8A1F:'CAS_GETCMD',
 0x8A25:'KEY_IDLE',            # poll keyboard with idle timeout
 0x8A31:'CAS_DISPATCH',        # death-check + command dispatch
 0x8A41:'CAS_DEATH',           # out of hits or food: scroll + RESPAWN
 0x8A93:'CMD_MOVE',
 0x8AC1:'PRINCESS_RESCUE',     # reached throne cell: save the princess
 0x8C00:'MOVE_STEP',           # ordinary step / blocked
 0x8C4C:'CMD_PASS',
 0x8C56:'CMD_ATTACK',
 0x8D08:'ATTACK_HIT',          # to-hit succeeded: roll damage
 0x8D9A:'ATTACK_KILL',         # NPC reached 0 HP: free slot, award exp
 0x8E0F:'AWARD_EXP',           # add A:X to PLR_EXP, clamp at 9999
 0x8E3C:'CMD_CAST',            # spells are no-ops in the castle
 0x8E5B:'CMD_DROP',
 0x8EA7:'DROP_PENCE',          # give gold to an NPC for HP/spell reward
 0x8FA6:'DROP_WEAPON',
 0x8FC1:'DROP_ARMOUR',
 0x8FDC:'CAP_FOOD',            # clamp PLR_FOOD to 9999
 0x900D:'DROP_PICK',           # popup item picker (inline args)
 0x90D4:'CMD_GET',             # take from a storeroom (king's permission)
 0x9134:'CMD_QUIT',            # "only allowed outdoors"
 0x9159:'CMD_READY',
 0x916F:'CMD_STEAL',
 0x91D2:'STOREROOM_FIND',       # award a random item from the storeroom
 0x927C:'CMD_TRANSACT',        # audience with the King
 0x931A:'KING_PENCE',          # donate gold for hit points (1.5x)
 0x93FB:'QUEST_ASSIGN',        # accept a new quest
 0x94B4:'QUEST_KILL',          # odd castle: "kill a <monster>"
 0x94E7:'QUEST_COMPLETE',      # turn in a finished quest
 0x959D:'QUEST_REWARD_HINT',   # odd castle reward: a gem + a lore hint
 0x95DE:'HINT_CONT0',          # red gem (all four gems needed)
 0x963E:'HINT_CONT1',          # green gem (the time machine wins)
 0x969B:'HINT_CONT2',          # blue gem (princess helps a space ace)
 0x96F4:'HINT_CONT3',          # white gem (nine items from storerooms)
 0x975E:'CMD_UNLOCK',          # open a storeroom door with a found key
 0x97FE:'CMD_ZTATS',
 0x9804:'CASTLE_TICK',         # idle turn: NPC reactions + guard combat
 0x980C:'GUARD_HOME',          # angered guard homes on the player
 0x9933:'GUARD_COMBAT',        # guard attacks; player damage / death
 0x99E4:'NPC_WANDER',          # peaceful NPC turns (jester sings / steals)
 0x9A06:'WANDER_JESTER',
 0x9ACA:'WANDER_DRIFT',        # plain townsfolk drift one step
 0x9AFA:'CMD_INFORM',
 0x9B06:'MAP_DRAW',            # blit the 38x18 cell grid + NPC glyphs
 0x9B6E:'FONT_SWAP',           # swap MAPCHARS <-> the live font bank
 0x9BA8:'PLOT_GLYPH',          # draw glyph A at cell (X,Y)
 0x9BC0:'CELL_PROBE',          # CELL_AT, treat the player cell as solid
 0x9BD9:'CELL_AT',             # read a map cell; resolve NPCs to type+$30
 0x9C23:'RAND_STEP',           # random -1/0/+1
 0x9C37:'RAND_ADJ',            # random adjacent cell of NPC Y
 0x9C4A:'NUM_INPUT',           # decimal entry into AMOUNT (16-bit)
 0x9CF1:'RND_BYTE',            # one random byte into ZP_T0 + MUL_MASK
 0x9CFC:'RND_TWO',             # two random bytes (multiplier + mask)
 0x9D0C:'MUL8',                # 8x8 -> 16-bit multiply (mask-and-add)
 0x9D3E:'CLEAR_MSGS',          # restore the map window + press-space
 0x9D47:'NPC_DIST',            # distance from player to NPC slot X
 0x9E06:'ADD_CAP',             # add A:X with the 500-pt cap helper
}
