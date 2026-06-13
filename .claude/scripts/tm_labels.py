# In-file global labels for TM (time-machine endgame overlay), addr -> name.
# Routine entry points and data-table labels discovered by tracing.
LBL = {
 0x8956:'OVERLAY_ENTRY',
 # --- fixed-point / BCD arithmetic helpers (file head) ---
 0x8959:'MUL8',            # 8-bit binary multiply (A*$00 -> $04)
 0x8975:'MUL16',           # 16-bit multiply ($00/$01 * A -> $04..$06)
 0x899F:'MUL16B',          # 16-bit multiply variant ($00/$01 * $02/$03)
 0x89CD:'DIV16',           # 16-bit divide ($04/$05 / $02/$03)
 0x89FE:'BCD_DBL',         # convert byte to BCD-doubled scratch
 0x8A13:'BIN2BCD16',       # 16-bit binary -> packed BCD via ($00) ptr
 0x8A40:'BCD_ADD_HI',      # BCD add helper (high nibble)
 0x8A44:'BCD_ADD_LO',      # BCD add helper (low nibble)
 0x8A5D:'BCD_WEIGHTS',     # BCD digit-weight table (data)
 0x8A61:'BCD_FROM8',       # 8-bit -> BCD via ($00)
 0x8A7E:'BCD_FROM16',      # 16-bit -> BCD via ($00)
 0x8AAF:'BCD_W_HI', 0x8AB3:'BCD_W_LO',  # weighted BCD add (decimal mode)
 0x8ACF:'BCD_WEIGHTS2',    # second BCD weight table (data)
 # --- real entry / launch sequence ---
 0x8AD7:'TM_ENTRY',
 # --- main loop / dispatch ---
 0x8E5E:'MAIN_LOOP', 0x8E67:'TURN_TOP', 0x8E8E:'DISPATCH',
 0x8EA8:'DISPATCH_TBL',
 # --- command handlers (TM_ prefix: the overlay command set; the bare
 #     CMD_* names are already @ %def'd by OUT/DNG for different routines) ---
 0x8EDC:'TM_ATTACK',
 0x91FB:'TM_CAST', 0x9249:'TM_SPELL_TBL',
 0x94D6:'TM_GET',
 0x95AC:'TM_INFORM',
 0x963F:'TM_QUIT', 0x9654:'TM_READY', 0x965D:'TM_STEAL',
 0x968A:'TM_TRANSACT', 0x96AD:'TM_ZTATS',
 0x96B8:'TM_MOVE_N', 0x96BE:'TM_MOVE_S', 0x96C4:'TM_MOVE_E', 0x96CA:'TM_MOVE_W',
 0x9801:'TM_PASS', 0x9808:'TURN_END',
 # --- idle / animation ---
 0x9815:'IDLE_POLL', 0x9827:'IDLE_FRAME',
 0x9844:'SCENE_TICK',          # per-turn scene animation (main loop tick)
 # --- mondain AI ---
 0x98C1:'MONDAIN_TURN',        # decide Mondain's action by distance to player
 0x9936:'MONDAIN_STEP',        # Mondain wander/approach step
 0x9971:'MONDAIN_MELEE',       # melee attack on the player
 0x99E7:'MONDAIN_CAST',        # pick + cast one of three spells
 0x9A0F:'MONDAIN_SPELL_TBL',
 0x9B15:'MONDAIN_HIT',         # resolve a hit on the player (damage)
 0x9B61:'TM_DEATH',            # "THOU ART DEAD!" defeat ending
 # --- shared helpers promoted to globals (referenced across chunks) ---
 0x8F80:'HIT_RESOLVE',         # "Hit Mondain! N damage" -> drain GEM_HP (shared by attack+spells)
 0x9034:'TM_VICTORY',          # "THOU ART VICTORIOUS!" -> NIF + Control-RESET
 0x916F:'PICK_DIR',            # poll a direction key; return X=2 if it faces the target cell
 0x925F:'CAST_CHECK',          # spell cast-success check (charge/class/INT/range gate)
 0x929F:'SPELL_FAILED',        # " failed!" + beep
 0x92CE:'SPELL_PRAYER',        # prayer / default spell entry
 0x934A:'SPELL_STATUS',        # status-effect spell (band 2)
 0x9791:'SCREEN_FLASH',        # XOR-invert the hi-res view (damage flash)
 0x9BDF:'SCENE_REDRAW',        # per-command scene redraw (post-turn)
 0x9C1F:'CELL_PLACE',          # place player/object into its grid cell + draw
 0x9C47:'CELL_CLEAR',          # clear (erase) a grid cell
 0x9C64:'DRAW_MONDAIN',        # draw Mondain's current sprite
 0x9C93:'ERASE_MONDAIN',       # erase Mondain's sprite
 0x9CB5:'DRAW_GEM',            # draw the gem sprite
 0x9CE4:'DRAW_OBJ3',           # draw the third scene object
 0x9D06:'PROJECT_CELL',        # project a grid cell to screen coords (entry)
 0x9D15:'PROJECT_XY',          # look up projected X/Y/Z for a cell index
 0x9D5C:'CELL_DISTANCE',       # distance from player to a target cell
 0x9D74:'CELL_DELTA_Y',        # signed cell offset in Y -> $B62D
 0x9D98:'CELL_DELTA_X',        # signed cell offset in X -> $B62C
 0x9DBC:'CELL_LOOKUP',         # CELL_STATE[ CELL_COL[y] + x ] fetch
 # --- renderer / graphics ---
 0x9DCB:'CRAFT_REDRAW',
 0x9E45:'NEGATE_SIGN',         # sign-flip helper
 0x9E50:'SCENE_CLEAR',         # clear the scene scratch / cursor
 0x9E6C:'PLACE_SHAPE',         # set a shape's cell + queue it for drawing
 0x9E95:'SETUP_SHAPE',         # initialise a shape pointer from its index
 0x9EB5:'SHAPE_NEXT',          # advance shape pointer / copy NPC arrays
 0x9ED9:'COPY_SCENE_ROW',      # copy a row of the $B600 scene arrays
 0x9EE5:'SHAPE_STEP',          # vector-shape vertex stepper (the stroker)
 0xA018:'PLOT_VERTEX',         # plot one shape vertex into the cell map
 0xA034:'PLOT_VERTEX2',        # plot variant (with $A471 self-mod)
 0xA07B:'ANIM_FRAME',          # one scene-animation frame
 0xA084:'ANIM_SETUP',          # set up the animation self-mod pointers
 0xA176:'BLIT_LINE',           # the line-segment blitter (BLIT_VEC target)
 0xA26E:'COORD_SUB',           # 16-bit coordinate subtract / compare
 0xA3EE:'CELL_INDEX',          # compute a CELL_STATE index from (x,y)
 0xA436:'POPUP_TEXT',          # framed popup-text trampoline -> MSG_PRINT
 0xA43C:'POPUP_TEXT_NF',       # no-frame popup-text trampoline -> MSG_PRINT
 0xA44B:'DRAW_SOCKET',         # draw one colored gem-socket marker
}
