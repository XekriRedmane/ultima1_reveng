# Symbol map: address -> EQU/label name for GEN (character-generation overlay).
# Engine/STUPH/state symbols (reused from SPA/CAS/TWN defines) + GEN-local labels.
SYM = {
 # --- STUPH resident library ---
 0x1580:'SOUND_ON', 0x1581:'SFX_ON',
 0x158F:'PAGE_COPY', 0x158C:'FILE_LOAD_AT',
 0x159E:'WIN_FULL', 0x15A1:'WIN_STATS', 0x15A4:'WIN_TEXT', 0x15A7:'WIN_VIEW',
 0x1592:'TEXT_SCROLL', 0x1598:'CLR_EOL', 0x159B:'CLR_WINDOW',
 0x15AD:'PAGE_FLIP', 0x15B0:'FONT_DRAW', 0x15B9:'RND',
 0x15BF:'KEY_WAIT', 0x15C2:'KEY_GET', 0x15BC:'KEY_POLL',
 0x15E0:'SOUND_SET',
 # --- MI.U1 engine API ---
 0x804F:'PRINT_HEX', 0x8058:'PRINT_DIGIT', 0x8062:'CHAR_OUT',
 0x807E:'PUTCH_NL_COL1', 0x8081:'CURSOR_COL1', 0x809C:'CR',
 0x80B1:'STR_NTH_CAP',
 0x8115:'MSG_AT', 0x8119:'MSG_PRINT', 0x820D:'PRINT_NUM8',
 0x8144:'CHAR_REPEAT', 0x814B:'DRAW_SCREEN',
 0x8331:'STATS_DRAW', 0x8355:'PRINT_STAT16',
 0x83A9:'WIN_RESTORE', 0x83B4:'WIN_SAVE', 0x841E:'POPUP_FRAME',
 0x8407:'QUERY_MARK', 0x840F:'BEEP_HUH', 0x8414:'KBD_CLEAR',
 0x8837:'PRINT_NAME', 0x88FB:'EXIT_TO_OUT',
 0x7DCC:'DISK_PROMPT',
 # --- MLIB resident library ($B700) ---
 0xB721:'MLIB_BLOAD_AT_P', 0xB724:'MLIB_BSAVE_P',
 0xB733:'MLIB_PARSE_PATH', 0xB739:'MLIB_ONLINE', 0xB73C:'MLIB_KEEP_FLAG',
 # --- screen / hi-res / soft switches ---
 0x4000:'HGR2',
 0x6000:'GAME_VARS', 0x6001:'GAME_VARS+1',  # game-state image buffer (BLOAD target / 13-page copy dest)
 0x6D00:'GAME_VARS_FLAG',                   # the init-done flag inside the image ($6000+$D00)
 0xC040:'STROBE', 0xC030:'SPEAKER',
 # --- ProDOS global page + MLI ---
 0xBF00:'MLI', 0xBF10:'PRODOS_DEVTAB', 0xBF30:'PRODOS_DEVNUM', 0xBF31:'PRODOS_DEVCNT',
 0xBF32:'PRODOS_DEVLST', 0xBF90:'PRODOS_DATE',
 0xBB00:'PRODOS_BUF', 0xBB04:'PRODOS_BUF+4', 0xBB05:'PRODOS_BUF+5',
 0xF479:'MON_PREAD_LIKE',                       # ROM helper used by the formatter
 # --- player state block (shared across overlays) ---
 0x7E38:'PATH_PLAYER',
 0x7E6D:'PLR_SAVE',
 0x7E71:'PLR_SOUND', 0x7E72:'PLR_SFX',
 0x7EB7:'PLR_SEX', 0x7EB8:'PLR_NAME',
 0x7EC6:'PLR_HITS',
 0x7EC8:'PLR_STR', 0x7ECA:'PLR_AGI', 0x7ECC:'PLR_STA',
 0x7ECE:'PLR_CHA', 0x7ED0:'PLR_WIS', 0x7ED2:'PLR_INT',
 0x7ED6:'PLR_RACE', 0x7ED8:'PLR_CLASS',
 0x7EEF:'PLR_SPACE_X', 0x7EF0:'PLR_SPACE_Y',
 # --- MIU1 string tables ---
 0x73AF:'STR_RACES', 0x748E:'STR_STATS', 0x755D:'STR_CLASSES',
}

# Zero-page additions.
ZP = {
 0x02:'ZP_A2L', 0x03:'ZP_A2H',        # ProDOS-style A2 pointer / save ptr
 0x24:'MON_CH', 0x25:'MON_CV',        # text cursor (Monitor CH/CV)
 0x7F:'ZP_PAGE_XOR', 0x80:'ZP_PAGE_TGL',  # draw-page selector / toggle mask
 0xA7:'ZP_BLK_PTR', 0xA8:'ZP_BLK_PTR+1',  # block/boot pointer (volume check)
 0xA9:'ZP_NAMLEN',                    # online-name length scratch
 0xAA:'ZP_DRIVE', 0xAB:'ZP_SLOT',     # selected drive (1-2) / slot (1-7)
 # --- RWTS / format zero-page scratch ($D0-$DD, saved/restored around $A800) ---
 0xD0:'RW_T0', 0xD1:'RW_SECTOR', 0xD2:'RW_T2', 0xD3:'RW_T3',
 0xD4:'RW_COUNT', 0xD5:'RW_NIB', 0xD6:'RW_T6',
 0xD8:'RW_ERR', 0xD9:'RW_T9', 0xDA:'RW_TA', 0xDB:'RW_TB',
 0xDC:'RW_TC', 0xDD:'RW_TD',
 0xE0:'RW_E0', 0xE1:'RW_E1', 0xE2:'RW_E2',  # loader-image pointers ($A3C5+)
 0xE6:'RW_E6', 0xE7:'RW_E7', 0xE8:'RW_E8', 0xE9:'RW_E9',
}

# State variables in GEN's BSS bands and in-file data/code labels.
STATE = {
 # --- char-gen counters/strings ($903F-$904F) ---
 0x903F:'POINT_POOL',                          # attribute points left to distribute
 0x9041:'CURSOR_IDX',                          # attribute-editor cursor (1..6)
 0x9042:'NAME_LEN',                            # name-entry length / scratch
 0x9043:'STR_SEX',                             # "male"/"female" STR_NTH_CAP table
 0x904D:'SAVE_SIG',                            # player-record signature template CA 01
 0x904F:'PLR_TEMPLATE',                        # default player-state template (-> $7EC6)
 # --- READ_BLOCK paramblock + scratch ($93E3) ---
 0x93E3:'RDBLK_PARAM',                         # ProDOS READ_BLOCK param block
 0x93E4:'FMT_UNIT',                            # unit number (slot/drive), SMC-patched
 0x93E9:'ZP_SAVE',                             # 14-byte save of zp $D0-$DD
 # --- the $6000 image copy block ---
 0x9440:'GAME_IMAGE',                          # 13-page initial-state image copied to $6000
 0xA104:'IMG_PREFIX',                          # "U1." path prefix inside the image
 0xA106:'IMG_PLAYER',                          # "U1.PLAYER" pathname inside the image
 # --- FORMAT_VOLUME embedded paramblocks / SMC fields ---
 0xA189:'FV_SAVED_A2',                         # saved zp $02/$03
 0xA18B:'FV_DIRBLK',                           # directory block number
 0xA18C:'FV_WR1',                              # WRITE_BLOCK paramblock #1
 0xA192:'FV_WR2',                              # WRITE_BLOCK paramblock #2
 0xA20B:'FV_BMPTR',                            # bitmap block pointer
 0xA282:'FV_DRVMASK',                          # drive mask (AND #$F0)
 0xA283:'FV_TRACK',                            # current track
 0xA284:'FV_VECTOR',                           # JMP ($A284) indirect dispatch vector
 0xA290:'FV_WR3',                              # WRITE_BLOCK paramblock #3
 0xA294:'FV_WRCNT',                            # write counter
 0xA2D7:'FV_REMAIN',                           # sector remainder scratch
 # --- embedded boot-loader disk image ---
 0xA3C5:'BOOT_IMAGE',                          # ProDOS boot loader stamped onto block 0 of the new disk
 # --- RWTS format BSS + PRO param block ---
 0xA7B7:'RW_BSS',                              # formatter BSS (zeros)
 0xA7C7:'PRO_PARAM',                           # "PRO" volume-name ProDOS param block
 # --- RWTS seek delay tables + geometry + scratch ---
 0xAB4B:'SEEK_DELAY_A', 0xAB57:'SEEK_DELAY_B',  # arm-step phase settle times
 0xAC1F:'FMT_GEOM',                            # format geometry params (tracks/retries)
 0xAC23:'RW_DRVSEL',                           # slot*4 drive-select scratch
 0xAC24:'RW_HALFTRK',                          # current half-track (ASL/LSR self-mod)
 0xAC25:'RW_RETRY',                            # retry/loop counter
 0xAC26:'RW_SECMAP',                           # 16-byte found-sector bitmap
 0xAC36:'RW_SWIDX',                            # soft-switch index scratch
 0xAC38:'RW_SEEKDLT',                          # seek delta scratch
}
