# Symbol map: address -> EQU/label name for CAS (castle overlay).
# Engine/STUPH/state symbols (reused from TWN/DNG/OUT defines) + CAS-local labels.
SYM = {
 # --- STUPH resident library ---
 0x1592:'TEXT_SCROLL', 0x1598:'CLR_EOL', 0x159B:'CLR_WINDOW', 0x15A4:'WIN_TEXT',
 0x15A7:'WIN_VIEW', 0x158C:'FILE_LOAD_AT', 0x15B0:'FONT_DRAW', 0x15B9:'RND',
 0x15BF:'KEY_WAIT', 0x15C2:'KEY_GET', 0x15CB:'SFX_PLAY', 0x15D1:'SFX_DRAIN',
 0x15E9:'VDELAY',
 # --- MI.U1 engine API ---
 0x8037:'MSG_GETC', 0x8040:'MSG_PTR', 0x8062:'CHAR_OUT', 0x8078:'PUTCH_NL_COND',
 0x807E:'PUTCH_NL_COL1', 0x8081:'CURSOR_COL1', 0x809C:'CR', 0x80B1:'STR_NTH_CAP',
 0x80B6:'STR_FIRST', 0x80B8:'STR_NTH', 0x8115:'MSG_AT', 0x8119:'MSG_PRINT',
 0x8207:'PRINT_NUM16', 0x820D:'PRINT_NUM8', 0x8249:'NUM_PAD', 0x8266:'KEY_PENDING',
 0x826C:'PAUSE_ABORTABLE', 0x827D:'KEY_ALIAS', 0x82A2:'GET_COMMAND',
 0x82E4:'TICK_SND', 0x836E:'STATS_VALUES', 0x83A9:'WIN_RESTORE', 0x83B4:'WIN_SAVE',
 0x83C8:'CURSOR_TO_TEXT', 0x8407:'QUERY_MARK', 0x840F:'BEEP_HUH', 0x8414:'KBD_CLEAR',
 0x841E:'POPUP_FRAME', 0x8466:'READY_CMD', 0x85A2:'INVENTORY', 0x876C:'POPUP_CLOSE',
 0x8837:'PRINT_NAME', 0x87FA:'PRESS_SPACE', 0x8845:'SOUND_TOGGLE', 0x885B:'SFX_TOGGLE',
 0x88F8:'RESPAWN', 0x88FB:'EXIT_TO_OUT', 0x7DCC:'DISK_PROMPT', 0xB733:'MLIB_SET_PREFIX',
 # --- engine string tables ---
 0x7438:'STR_WEAPONS_S', 0x73C8:'STR_WEAPONS', 0x74D4:'STR_SPELLS',
 0x7520:'STR_ARMOUR', 0x757C:'STR_TRANSPORT', 0x7917:'STR_PLACES',
 0x76D6:'STR_MONSTERS',
 # --- player state block ---
 0x7EB7:'PLR_SEX', 0x7EB1:'COURT_CELLS', 0x7EB5:'TM_REVEAL', 0x7EB6:'PLR_VESSELS',
 0x7E6F:'PLR_CONT',
 0x7EC6:'PLR_HITS', 0x7EC8:'PLR_STR', 0x7ECA:'PLR_AGI', 0x7ECC:'PLR_STA',
 0x7ECE:'PLR_CHA', 0x7ED0:'PLR_WIS', 0x7ED2:'PLR_INT', 0x7ED4:'PLR_COIN',
 0x7ED8:'PLR_CLASS', 0x7EE5:'PLR_FOOD', 0x7EE7:'PLR_EXP', 0x7EED:'PLR_PLACE',
 0x7E79:'READY_SPELL', 0x7E7A:'READY_WEAPON', 0x7E7B:'READY_ARMOUR',
 0x7E83:'OWNED_WEAPONS', 0x7E93:'OWNED_SPELLS', 0x7E7D:'OWNED_ARMOUR',
 0x7E52:'DIR_STR_PTR+1', 0x7E51:'DIR_STR_PTR',
 0x7E9E:'OWNED_TRANSPORT', 0x7EA9:'QUEST_FLAGS',
 0x7E75:'OWNED_GEMS', 0x7E76:'OWNED_GEMS+1', 0x7E77:'OWNED_GEMS+2', 0x7E78:'OWNED_GEMS+3',
 # 16-bit high bytes referenced directly:
 0x7EC7:'PLR_HITS+1', 0x7ED5:'PLR_COIN+1', 0x7EE6:'PLR_FOOD+1', 0x7EE8:'PLR_EXP+1',
}

# Zero-page additions for the literate version.
ZP = {
 0x00:'ZP_X', 0x01:'ZP_Y',            # player column/row on the map
 0x04:'ZP_DX', 0x05:'ZP_DY',          # step delta
 0x0C:'ZP_TX', 0x0D:'ZP_TY',          # target column/row
 0x24:'MON_CH', 0x25:'MON_CV',        # text cursor (Monitor CH/CV)
 0x67:'ZP_PICK_PTR', 0x68:'ZP_PICK_PTR+1', 0x69:'ZP_PICK_CNT',  # DROP_PICK
 0x72:'ZP_T0', 0x73:'ZP_T1',          # general scratch pair
}

# State variables in the CAS BSS band $9E24-$9E3E and the live map buffer.
STATE = {
 # --- CAS BSS state (zeroed on disk) ---
 0x9E24:'DIST_IDX', 0x9E25:'DIST_LO', 0x9E26:'DIST_LO+1',
 0x9E27:'DIST_HI', 0x9E28:'DIST_HI+1',
 0x9E29:'IDLE_MSG',                   # set when an idle event prints
 0x9E2A:'KING_REJECT',                # king refuses audience after theft/assault
 0x9E2B:'NPC_IDX',                    # NPC slot loop counter
 0x9E2C:'NUM_UNDO', 0x9E2E:'NUM_T',   # NUM_INPUT undo + accumulator pair
 0x9E30:'PENCE_HALF', 0x9E31:'PENCE_HALF+1',  # spare amount (drop reward)
 0x9E32:'AMOUNT', 0x9E33:'AMOUNT+1',  # NUM_INPUT result (16-bit)
 0x9E34:'NUM_DIGITS',                 # digits entered
 0x9E35:'ATK_CNT',                    # attack reach counter (weapon hitkind)
 0x9E36:'HIT_SLOT',                   # NPC slot last hit
 0x9E37:'KEY_KIND',                   # which key the player holds (0/1/2)
 0x9E38:'MUL_MASK', 0x9E39:'MUL_ACC', 0x9E3A:'MUL_ACC+1',  # bit-multiply
 0x9E3B:'CASTLE_IDX',                 # castle index 0..7 (continent-adjusted)
 0x9E3C:'ABS_TMP',                    # abs() scratch in NPC_DIST
 0x9E3D:'STORE_PERMIT',               # king's storeroom permission counter
 0x9E3E:'TICK_PHASE',                 # idle-anim alternation byte
 # --- live map buffer + NPC arrays ($B400) ---
 0xB400:'CASTLE_MAP', 0xB6AC:'NPC_TYPE', 0xB6BC:'NPC_X', 0xB6CC:'NPC_Y',
 0xB6DC:'NPC_HP', 0xB6EC:'NPC_HP+16',
 0xB6BD:'NPC_X+1', 0xB6CD:'NPC_Y+1',  # king is always slot 1 (throne/princess refs)
 # --- engine ZP high byte ---
 0x8041:'MSG_PTR+1',
 # --- in-file data tables ---
 0x8A5F:'CMD_TBL', 0x8A60:'CMD_TBL+1', 0x9EE2:'CASTLE_COL',
 0x8E9B:'DROP_KEYS', 0x8E9F:'DROP_JMP', 0x8EA0:'DROP_JMP+1',
 0x8FF3:'DROP_STRINGS',
 0x90D3:'PICK_CNT', 0x95D6:'GEM_HINT_TBL', 0x95D7:'GEM_HINT_TBL+1',
 0x9E3F:'STR_NPCS', 0x9E63:'STR_PRINCESS',
 0x9EA8:'MAP_ROW_LO', 0x9EBA:'MAP_ROW_HI',
 0x9ECC:'WEAPON_HITKIND', 0x9EDC:'NPC_GLYPH',
 0x95D6:'GEM_HINT_TBL',
 # --- TCMAPS directory (loaded at $4000) ---
 0x4000:'TCMAPS_DIR', 0x4001:'TCMAPS_DIR+1',
 # --- font banks for the swap ---
 0x0800:'FONT_BANK', 0x0900:'FONT_BANK+256', 0x0A00:'FONT_BANK+512', 0x0B00:'FONT_BANK+768',
 0xB000:'MAPCHARS_BANK', 0xB100:'MAPCHARS_BANK+256', 0xB200:'MAPCHARS_BANK+512', 0xB300:'MAPCHARS_BANK+768',
}
