# Symbol map: address -> EQU/label name for TM (time-machine endgame overlay).
# Engine/STUPH/state symbols (reused from the prior overlays) + TM-local labels.
SYM = {
 # --- STUPH resident library ---
 0x1581:'SFX_ON',
 0x1598:'CLR_EOL', 0x159B:'CLR_WINDOW', 0x159E:'WIN_FULL',
 0x15A7:'WIN_VIEW', 0x15AA:'VIEW_CLEAR',
 0x15AD:'PAGE_FLIP', 0x15B0:'FONT_DRAW', 0x15B9:'RND',
 0x15BF:'KEY_WAIT', 0x15C8:'CURSOR_FLASH',
 0x15CB:'SFX_PLAY', 0x15D1:'SFX_DRAIN',
 0x15D4:'COLOR_SET', 0x15DA:'LINE_TO',
 0x15E3:'ACCEL_NUDGE', 0x15E6:'FRAME_SYNC', 0x15E9:'VDELAY',
 # --- MI.U1 engine API ---
 0x807F:'PUTCH_NL_COL1', 0x8081:'CURSOR_COL1',
 0x8089:'NEWLINE', 0x80A1:'WIN_SHRINK',
 0x80B1:'STR_NTH_CAP', 0x80B8:'STR_NTH',
 0x8115:'MSG_AT', 0x8119:'MSG_PRINT',
 0x8207:'PRINT_NUM16', 0x820D:'PRINT_NUM8',
 0x8254:'RND_MOD', 0x8266:'KEY_PENDING', 0x827D:'KEY_ALIAS',
 0x82A2:'GET_COMMAND', 0x82E2:'TICK', 0x82E4:'TICK_SND',
 0x8331:'STATS_DRAW', 0x836E:'STATS_VALUES', 0x8355:'PRINT_STAT16',
 0x838C:'STATS_HITS',                       # mid-STATS line: hits/food entry
 0x83A9:'WIN_RESTORE', 0x83B4:'WIN_SAVE',
 0x83BF:'PRINT_SPELL', 0x83EB:'NO_EFFECT_MSG',
 0x8403:'BEEP_CMD', 0x8407:'QUERY_MARK', 0x840F:'BEEP_HUH', 0x8414:'KBD_CLEAR',
 0x841E:'POPUP_FRAME',
 0x8466:'READY_CMD', 0x85A2:'INVENTORY',
 0x87F7:'POPUP_REDRAW',                     # PAGE_COPY + PRESS_SPACE flow
 0x88F8:'RESPAWN', 0x8954:'QUIT_VEC',
 0x7DCC:'DISK_PROMPT',
 # --- MLIB resident library ($B700) ---
 0xB703:'MLIB_BLOAD',
 0xB721:'MLIB_BLOAD_AT_P', 0xB724:'MLIB_BSAVE_P',
 # --- stale self-modified-dispatch operands (patched at runtime) ---
 0x841D:'STALE_DISPATCH',   # disk value of the patched JSR operand at DISPATCH_JSR
 0x1111:'STALE_BLITVEC',    # disk value of the patched JMP operand at the blit vector
 # --- screen / hi-res / soft switches ---
 0x4000:'HGR2',
 0x6000:'GAME_VARS',
 0xC000:'KBD', 0xC010:'KBDSTRB',
 # --- hi-res pages + scene buffers ---
 0x2000:'HGR1',
 0xB400:'SCENE_BUF', 0xB404:'SCENE_BUF+4',
 0xB500:'SCENE_BUF2', 0xB504:'SCENE_BUF2+4',
 0xB600:'SCENE_ARR',
 0x1200:'HGR_ROW_LO', 0x12C0:'HGR_ROW_HI',
 # --- player state block (shared across overlays) ---
 0x7E4B:'DMG_AMT', 0x7E4C:'DMG_AMT+1',
 0x7EF5:'GEM_HP+1',
 0x7E79:'READY_SPELL', 0x7E7A:'READY_WEAPON', 0x7E7B:'READY_ARMOUR',
 0x7E93:'OWNED_SPELLS',
 0x7EC6:'PLR_HITS', 0x7EC7:'PLR_HITS+1',
 0x7EC8:'PLR_STR', 0x7ECA:'PLR_AGI', 0x7ECC:'PLR_STA',
 0x7ECE:'PLR_CHA', 0x7ED0:'PLR_WIS', 0x7ED2:'PLR_INT',
 0x7ED8:'PLR_CLASS',
 0x7EE5:'PLR_FOOD', 0x7EE6:'PLR_FOOD+1',
 0x7EF2:'CUR_MON',
}

# Zero-page additions.
ZP = {
 0x00:'ZP_PTR', 0x01:'ZP_PTR+1',          # general 16-bit pointer (map/draw base)
 0x02:'ZP_M0', 0x03:'ZP_M1',              # multiply/divide operand A (lo/hi)
 0x04:'ZP_M2', 0x05:'ZP_M3',              # product/quotient byte 0/1
 0x06:'ZP_M4', 0x07:'ZP_M5',              # product byte 2/3 (and coord scratch)
 0x08:'ZP_MCNT', 0x09:'ZP_MREM',          # shift counter / remainder scratch
 0x24:'MON_CH', 0x25:'MON_CV',            # text cursor (Monitor CH/CV)
 0x7D:'ZP_SFX_TAIL', 0x7F:'ZP_PAGE_XOR', 0x80:'ZP_PAGE_TGL',
 0xC3:'ZP_C3', 0xC4:'ZP_C4', 0xC5:'ZP_C5', 0xC6:'ZP_C6',  # combat/draw scratch
 0xE6:'ZP_SH0', 0xE7:'ZP_SH0+1',         # shape pointer 0 (renderer self-mod)
 0xE8:'ZP_SH1', 0xE9:'ZP_SH1+1',         # shape pointer 1
 0xEA:'ZP_SH2', 0xEB:'ZP_SH2+1',         # shape pointer 2
 0xEC:'ZP_SH3', 0xED:'ZP_SH3+1',         # shape pointer 3
 0xEE:'ZP_SH4', 0xEF:'ZP_SH4+1',         # shape pointer 4
}

# State variables in TM's BSS bands and in-file data/code labels.
STATE = {
 0x7EF4:'GEM_HP',                         # Mondain's gem HP (entry sets $03E8 = 1000)
 0x95AB:'GEM_GONE',                       # set by TM_GET when the gem is destroyed (victory gate)
}

# Scene state above the file (shared high-RAM scratch the renderer uses).
SCENE = {
 0xB626:'SCENE_T0', 0xB627:'SCENE_T1',    # renderer scratch
 0xB628:'TGT_X', 0xB629:'TGT_Y',          # reference (Mondain/origin) cell X/Y
 0xB62A:'GEM_X', 0xB62B:'GEM_Y',          # gem cell X/Y
 0xB62C:'DST_X', 0xB62D:'DST_Y',          # computed destination/working cell X/Y
}
