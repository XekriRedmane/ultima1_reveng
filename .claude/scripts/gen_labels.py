# GEN-local global routine labels (address -> name). Branch-internal targets
# stay as .Lxxxx local labels; these are the named subroutine entry points.
LBL = {
 # --- title / menu / character generation ---
 0x8956:'OVERLAY_ENTRY',
 0x895B:'TITLE_REDRAW',        # redraw title + menu (re-entry after a sub-step)
 0x89FD:'MENU_KEYLOOP',        # title-screen keypress loop (a/b)
 0x8A5B:'LAUNCH_GAME',         # decrypt + copy the $6000 image, exit to OUT
 0x8AC3:'CHARGEN',             # character-generation top
 0x8C00:'ATTR_INPUT',          # attribute-editor input loop
 0x8C7E:'PICK_RACE',           # race menu + bonuses
 0x8D3C:'PICK_SEX',            # sex menu
 0x8D98:'PICK_CLASS',          # class menu + bonuses
 0x8E54:'PICK_NAME',           # name entry
 0x8E83:'NAME_KEYLOOP',        # name-entry key loop
 0x8EEE:'SAVE_PROMPT',         # "Save this character? (Y-N)"
 0x8F23:'SAVE_PLAYER',            # BSAVE the player record
 0x8F31:'FMT_OFFER',           # "Format a new player disk?" branch
 0x8FA8:'RETRY_SAVE',          # after a format, retry the BSAVE
 0x8FB1:'EDITOR_DRAW',         # redraw the attribute editor (6 stats + pool)
 # --- disk formatter front end ---
 0x90D7:'FORMAT_ENTRY',        # derive slot/drive from ProDOS last-device
 0x90EC:'FORMAT_RESTART',      # slot/drive prompt restart
 0x9170:'SLOT_KEYLOOP',        # slot-number entry loop
 0x919F:'DRIVE_KEYLOOP',       # drive-number entry loop
 0x91CB:'VOL_CHECK',           # read the volume's boot block, test ProDOS
 0x9211:'NO_DISKII',           # "Disk II not connected" error
 0x9230:'TEST_ONLINE',         # ProDOS ONLINE: is the disk a known volume?
 0x9266:'NON_PRODOS',          # "Non-ProDOS disk"
 0x92A0:'CONFIRM_FMT',         # "? (Y-N)" confirm
 0x92BA:'DO_FORMAT',           # save zp, call RWTS_FORMAT, then FORMAT_VOLUME
 0x933F:'WRITE_VOLDIR',        # call FORMAT_VOLUME, report errors
 # --- GEN-local text/window helpers ---
 0x9388:'PROMPT_LINE',         # home to the bottom prompt line, fall into MSG_PRINT
 0x9396:'FMT_PRESS_SPACE',         # "Press Space to continue:"
 0x93BD:'CLEAR_FROM20',        # clear text from row $14 down
 0x93C6:'WINFULL_HOME',        # full window + home cursor
 0x93CC:'CLEAR_LINES',         # clear lines below the cursor
 0x93F7:'BORDER_DRAW',         # draw the decorative screen border
 0x9439:'HOME_CURSOR',         # cursor to (1,1)
 # --- ProDOS volume-directory writer (FORMAT_VOLUME) ---
 0xA119:'FORMAT_VOLUME',       # write a fresh ProDOS volume directory + bitmap
 0xA198:'FV_WRITE_DIR',        # write the directory key block
 0xA1EF:'FV_FINISH',           # allocate the volume bitmap, write the final block
 0xA1BE:'FV_DEV_ADDR',         # look up the device driver address for the unit
 0xA1D4:'FV_READ_DIR',         # read a directory block into the buffer
 0xA20D:'FV_ALLOC_BITMAP',     # build the volume bitmap
 0xA253:'FV_BITMAP_IO',        # read/write a bitmap block
 0xA273:'FV_DISPATCH',         # JMP ($A284) device-driver dispatch
 0xA277:'FV_DEVENTRY',         # device-table entry for the unit
 0xA286:'FV_WRITE_BLOCK',      # MLI WRITE_BLOCK wrapper
 0xA296:'FV_INIT_FIELDS',      # initialise directory-header fields
 0xA2AF:'FV_SET_ENTRY',        # set a directory entry field
 0xA2BC:'FV_NEXT_BLOCK',       # advance to the next directory block
 0xA2D8:'FV_FILL_BITMAP',      # fill the bitmap for allocated blocks
 0xA357:'FV_SET_BITS',         # set a run of bitmap bits
 0xA37C:'FV_FILL_FF',          # fill a buffer with $FF
 0xA384:'FV_PARTIAL',          # partial-byte bitmap fill
 0xA390:'FV_ZERO_BLK',         # zero a 512-byte block buffer
 0xA394:'FV_FF_BLK',           # fill a block buffer with $FF
 0xA3A1:'FV_FILL_PAGE',        # fill a page of the buffer
 0xA3A9:'FV_MASK',             # build a partial-byte mask
 # --- low-level Disk II format / RWTS ---
 0xA800:'RWTS_FORMAT',         # entry: format the whole disk surface
 0xA823:'RW_SEEK_PHASE',       # pulse a stepper phase soft switch
 0xA83A:'RW_FORMAT_DISK',      # the track-by-track format driver
 0xA86E:'RW_FMT_TRACK',        # format one track (write 16 sectors)
 0xA8F9:'RW_FMT_DONE',         # merge the per-track error code
 0xA907:'RW_READ_ADDR',        # read and verify a sector address field
 0xA96A:'RW_FIND_ADDR',        # spin until the address prologue D5 AA 96
 0xA9C6:'RW_SEEK',             # seek the arm to a track (uses the delay tables)
 0xAA1D:'RW_PHASE_ON',         # energise a stepper phase
 0xAA20:'RW_PHASE_OFF',        # de-energise a stepper phase
 0xAA2E:'RW_WRITE_SECTOR',     # write one sector's data field
 0xAAA4:'RW_WRITE_NIB',        # write a single disk nibble (timed)
 0xAAAE:'RW_READ_DATA',        # read and decode a sector data field
 0xAB1B:'RW_WR_NIB1',          # checksum nibble writer
 0xAB2C:'RW_WR_NIB2',          # checksum nibble writer (variant)
 0xAB3A:'RW_WRITE_DELAY',      # timed nibble write (motor pacing)
 0xAB63:'RW_VERIFY_TRACK',     # verify all 16 sectors of a track
 0xAB68:'RW_VERIFY_LOOP',      # verify-loop body
 0xAC0E:'RW_RTS',              # shared RTS
 0xAC0F:'RW_LONG_DELAY',       # long settle delay
}
