# Symbol map: address -> EQU/label name for SPA (space-combat overlay).
# Engine/STUPH/state symbols (reused from CAS/TWN/DNG/OUT defines) + SPA-local labels.
SYM = {
 # --- STUPH resident library ---
 0x1581:'SFX_ON', 0x1592:'TEXT_SCROLL', 0x1598:'CLR_EOL', 0x159B:'CLR_WINDOW',
 0x15A1:'WIN_STATS', 0x15A4:'WIN_TEXT', 0x15A7:'WIN_VIEW', 0x158C:'FILE_LOAD_AT',
 0x15B0:'FONT_DRAW', 0x15B9:'RND', 0x15BC:'KEY_POLL', 0x15BF:'KEY_WAIT',
 0x15C2:'KEY_GET', 0x15C8:'CURSOR_FLASH', 0x15CB:'SFX_PLAY', 0x15D1:'SFX_DRAIN',
 0x15D4:'COLOR_SET', 0x15D7:'PLOT', 0x15DA:'LINE_TO', 0x15E6:'FRAME_SYNC',
 0x15E9:'VDELAY',
 # --- MI.U1 engine API ---
 0x8037:'MSG_GETC', 0x8040:'MSG_PTR', 0x8058:'PRINT_DIGIT', 0x8062:'CHAR_OUT',
 0x8078:'PUTCH_NL_COND', 0x807E:'PUTCH_NL_COL1', 0x8081:'CURSOR_COL1',
 0x80A1:'WIN_SHRINK', 0x809C:'CR', 0x80B1:'STR_NTH_CAP', 0x80B6:'STR_FIRST',
 0x80B8:'STR_NTH', 0x8115:'MSG_AT', 0x8119:'MSG_PRINT',
 0x8207:'PRINT_NUM16', 0x820D:'PRINT_NUM8', 0x8355:'PRINT_STAT16',
 0x8249:'NUM_PAD', 0x8266:'KEY_PENDING', 0x826C:'PAUSE_ABORTABLE',
 0x827D:'KEY_ALIAS', 0x82A2:'GET_COMMAND', 0x82E2:'TICK', 0x82E4:'TICK_SND',
 0x836E:'STATS_VALUES', 0x83A9:'WIN_RESTORE', 0x83B4:'WIN_SAVE',
 0x83C8:'CURSOR_TO_TEXT', 0x841E:'POPUP_FRAME', 0x8407:'QUERY_MARK',
 0x840F:'BEEP_HUH', 0x8414:'KBD_CLEAR', 0x8466:'READY_CMD', 0x85A2:'INVENTORY',
 0x876C:'POPUP_CLOSE', 0x8837:'PRINT_NAME', 0x87FA:'PRESS_SPACE',
 0x8845:'SOUND_TOGGLE', 0x885B:'SFX_TOGGLE', 0x88F8:'RESPAWN', 0x88FB:'EXIT_TO_OUT',
 0x7DCC:'DISK_PROMPT', 0xB733:'MLIB_SET_PREFIX',
 # POPUP_FRAME is $841D here (entry differs from CAS $841E by the fall-in);
 # the SPA caller targets $90DE/$9766 which are in-file -> handled as labels.
 # --- screen / hi-res ---
 0x4000:'HGR2',
 # --- player state block (shared across overlays) ---
 0x7ED5:'PLR_COIN+1', 0x7ED4:'PLR_COIN',
 0x7EE7:'PLR_EXP', 0x7EE8:'PLR_EXP+1',
 0x7EE9:'PLR_FUEL', 0x7EEA:'PLR_FUEL+1',      # ship fuel (16-bit), SPA reuse of food slot
 0x7EEB:'PLR_SHIELD', 0x7EEC:'PLR_SHIELD+1',  # ship shield/hits (16-bit)
 0x7EEF:'PLR_SPACE_X', 0x7EF0:'PLR_SPACE_Y',  # saved space sector position
 0x7EB6:'PLR_VESSELS',                         # destroyed-craft counter (Space Ace gate)
 0x7E52:'DIR_STR_PTR+1', 0x7E51:'DIR_STR_PTR',
 0x7E7B:'READY_ARMOUR', 0x7E7C:'READY_ARMOUR+1', 0x7EDF:'READY_TRANSPORT',
 # --- soft switches ---
 0xC030:'SPEAKER', 0xC050:'TXTCLR',
 0x841D:'RTS_HOOK',                            # engine RTS just before POPUP_FRAME
 0x402A:'HGR2+42',                             # hi-res page 2 + $2A (star backup)
}

# Zero-page additions.
ZP = {
 0x00:'ZP_X', 0x01:'ZP_Y',            # player sector cell column/row
 0x06:'ZP_PX', 0x07:'ZP_PY',          # PLOT/LINE pixel column/row
 0x0C:'ZP_TX', 0x0D:'ZP_TY',          # scan-grid column/row
 0x20:'MON_WNDLFT', 0x21:'MON_WNDWDTH', 0x23:'MON_WNDBTM',
 0x24:'MON_CH', 0x25:'MON_CV',        # text cursor (Monitor CH/CV)
 0x7E:'ZP_INVERSE', 0x7F:'ZP_PAGE_XOR',  # video EOR mask / draw-page selector
 0x26:'ZP_HGR_PTR', 0x27:'ZP_HGR_PTR+1',  # hi-res screen pointer (blitter)
 0x28:'ZP_SHIFT_CNT', 0x2A:'ZP_SHIFT_ROW',  # sprite pre-shift scratch
 0x4E:'ZP_RNG', 0x4F:'ZP_RNG+1',      # Fibonacci RNG state (seeded from space pos)
 0x60:'ZP_CNT',
 0x6C:'ZP_CX', 0x6D:'ZP_CY',          # grid cursor pair (cell scan)
 0x6E:'ZP_VX', 0x6F:'ZP_VY',          # velocity vector (signed) integrated into position
 0x70:'ZP_SHP_SRC', 0x71:'ZP_SHP_SRC+1',  # shape source pointer (blitter)
 0x72:'ZP_SHP_DST', 0x73:'ZP_SHP_DST+1',  # shape dest pointer (blitter / scratch)
 0xA7:'ZP_T0', 0xA8:'ZP_T1',          # general scratch
 0xA9:'ZP_T2',
 0xAA:'ZP_M0', 0xAB:'ZP_M1', 0xAC:'ZP_M2', 0xAD:'ZP_M3',  # multiply/projection scratch
 0xAE:'ZP_MUL_B',                     # MUL8_FIXED multiplicand
 0xB0:'ZP_FX0', 0xB1:'ZP_FX1', 0xB2:'ZP_FX2', 0xB3:'ZP_FX3',  # fixed-point trig regs
 0xB4:'ZP_FX4', 0xB5:'ZP_FX5',        # DIV16 dividend/result high words
 0xB6:'ZP_FX_CNT', 0xB7:'ZP_FX_T',
 0xB8:'ZP_BLIT_A', 0xB9:'ZP_BLIT_HIT',  # blit pixel + collision-accumulator
 0xBA:'ZP_RET_X', 0xBB:'ZP_RET_Y',    # reticle column/row (radar + targeting)
 0xBC:'ZP_RET_CNT',                   # reticle / hyperspace countdown
}

# State variables in SPA's BSS bands and in-file data/code labels.
STATE = {
 # engine ZP high byte
 0x8041:'MSG_PTR+1',
 # --- in-file data tables (labeled by the tail/data chunks) ---
 0x8C47:'BASE_RADIUS', 0x8C4B:'BASE_AXIS',     # docking-base collision geometry
 0x8F40:'SHIP_FUEL', 0x8F43:'SHIP_FUEL+3', 0x8F46:'SHIP_SHIELD', 0x8F49:'SHIP_SHIELD+3',
 0x8FF4:'THRUST_DX', 0x8FF8:'THRUST_DY',       # thrust velocity deltas by heading
 0x9046:'RETRO_DX', 0x904A:'RETRO_DY',         # retro velocity deltas by heading
 0x91B6:'SCAN_GLYPH', 0x91B7:'SCAN_COL', 0x91B8:'SCAN_ROW',  # sector-scan blink state
 0x91B9:'SCAN_CELLGLYPH',                       # cell-content glyphs for the scan grid
 0x91D3:'DISPATCH_TBL', 0x91D4:'DISPATCH_TBL+1',  # command handler address table
 0x98F1:'HYPER_SPEED',                          # HyperJump: saved cruise speed
 0xA101:'XPORT_FRAME+3',                        # craft base-frame table, slot 3
 0x9219:'DIR_STR_FLIGHT',                       # "Thrust/Retro/Clockwise/..." movement names
 0x93DE:'DIR_STR_SPEED',                        # "Speedbtw" velocity-menu names
 # --- physics / actor state band $923E-$928F (zeroed on disk) ---
 0x923E:'HEAD_NEW', 0x923F:'HEAD_CUR',         # ship heading (0-3), new vs current
 0x9240:'IN_DOCK',                             # 1 while docked (physics frozen)
 0x9241:'CELL_LO', 0x9242:'CELL_HI',           # current grid cell packed contents
 0x9243:'ENEMY_INIT_LO', 0x924D:'ENEMY_INIT_HI',  # initial enemy-grid seed bytes
 0x9257:'ACTOR_SHAPE', 0x9261:'ACTOR_HEAD', 0x926B:'ACTOR_X', 0x9275:'ACTOR_Y',
 0x925B:'ACTOR_SHAPE+4', 0x925C:'ACTOR_SHAPE+5', 0x925D:'ACTOR_SHAPE+6',
 0x925E:'ACTOR_SHAPE+7', 0x925F:'ACTOR_SHAPE+8',  # berth-occupancy flags (top/bot/lft/rgt)
 0x9274:'ACTOR_X+9', 0x927E:'ACTOR_Y+9',       # the player's own ship marker slot
 0x926F:'BASE_X', 0x9279:'BASE_Y',             # docking base position (actor slot 4)
 0x927F:'CELL_NW', 0x9280:'CELL_NE', 0x9281:'CELL_SW',  # decoded cell quadrant counts
 0x9286:'CELL_ENEMY',                          # this cell holds enemy craft
 0x9287:'RND_MOD',                             # modulus scratch for RND_RANGE
 0x9288:'SHIP_X', 0x9289:'SHIP_Y',             # ship position on the sector torus
 0x928A:'REL_X', 0x928B:'REL_Y',               # signed offset of target from ship
 0x928C:'DRAW_FLAG', 0x928D:'ROT_STEP', 0x928E:'ROT_TIMER', 0x928F:'SCALE_TBL',
 0x9297:'SCALE_TBL+8',                         # last ramp entry = enemy draw scale
 # --- HyperJump / reticle scratch $93F0-$93FD ---
 0x93F0:'DRAW_MODE', 0x93F1:'AI_AGGRO', 0x93F2:'AI_RET_X', 0x93F3:'AI_RET_Y',
 0x93F4:'SPEED', 0x93F5:'SPEED_SUB', 0x93F6:'STAR_IDX', 0x93F7:'CUR_RET_X',
 0x93F8:'CUR_RET_Y', 0x93F9:'PAN_DX', 0x93FA:'PAN_DY', 0x93FB:'RNG_SAVE',
 0x93FC:'RNG_SAVE+1', 0x93FD:'SFX_SAVE',
 0x9496:'SCAN_TIMEOUT',
 # --- starfield tables ($9BFF / $9C29, 42 entries each) ---
 0x9BFF:'STAR_X', 0x9C29:'STAR_Y',
 0x9BCA:'AI_FIXED',                            # 1 = AI reticle locked (hyperspace)
 0x9BCB:'INFORM_TBL', 0x9BCC:'INFORM_TBL+1',   # Inform sub-handler addresses
 0x9C87:'GRID_ROW_OFF_DATA',                   # row offset into the 8x8 enemy grid
 0x9D87:'DIST_A', 0x9D88:'DIST_B',             # two actor indices for the distance call
 0x9D9A:'BLIT_SHAPE', 0x9D9B:'BLIT_SHAPE_PREV',
 0x9D9C:'BLIT_W', 0x9D9D:'BLIT_DX',
 0x9F7D:'SHIFT_SCRATCH', 0x9F7E:'SHIFT_SCRATCH+1',  # SHAPE_PRESHIFT stride/count
 # --- big BSS grids past the file end ($B020 / $B099) ---
 0xB01F:'BSS_TOP',                             # last file byte; zero-fill base for BSS
 0xB020:'ENEMY_GRID_LO', 0xB099:'ENEMY_GRID_HI',
 0xB112:'SHAPE_BUF',                           # 256-byte shape scratch buffer
 # --- engine row-address tables installed by MAKE.INDATA ---
 0x1210:'HGR_ROW_LO', 0x12D0:'HGR_ROW_HI',     # hi-res row base address tables
 0x1380:'HGR_ROW_BIT', 0x1480:'PRESHIFT_TBL',  # column bit + pre-shift count tables
 # --- the file-tail sprite/projection tables ---
 0xA0FE:'XPORT_FRAME', 0xA104:'CRAFT_TYPE',
 0xA1CF:'SHAPE_PTR_LO', 0xA1F3:'SHAPE_PTR_HI',
 0xA217:'SHAPE_XOFF', 0xA23B:'SHAPE_YOFF', 0xA25F:'SHAPE_WID', 0xA283:'SHAPE_DX',
 0xA2A7:'SHAPE_HGT', 0xA2CB:'SHAPE_PIXELS',
}
