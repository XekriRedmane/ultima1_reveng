#!/usr/bin/env python3
"""Weave authored prose + header plates into the byte-perfect GEN chunks.

Reads /tmp/gen_chunks.nw (from gen_emit_chunks.py), injects a header-plate
comment block after each chunk's SUBROUTINE, and emits the complete GEN
chapter (prose + collection chunk + chunks) to /tmp/gen_section.nw for splicing
into main.nw between the SPA collection chunk and the TM section.
"""
import re
from pathlib import Path

CHUNKS_NW = Path('/tmp/gen_chunks.nw').read_text()

# Parse chunks: name -> body lines (without the <<name>>= header, keeping @ line).
blocks = re.split(r'^<<(.+?)>>=$', CHUNKS_NW, flags=re.M)
chunks = {}
order = []
it = iter(blocks[1:])
for name, body in zip(it, it):
    chunks[name] = body.strip('\n').split('\n')
    order.append(name)

# Header plate per chunk: inserted right after the "        SUBROUTINE" line.
# Each entry is the plate text (lines, no leading indent on the routine label).
PLATE = {
 'gen entry': """        ; Overlay entry: draw the title screen and run the menu.
        ;
        ; Behavior:
        ;   Set MLIB_KEEP_FLAG so the resident library survives, draw the
        ;   decorative border + title ("Ultima I"), and offer two choices:
        ;   (a) generate a new character (-> CHARGEN), or (b) continue a
        ;   previous game -- BLOAD the saved player record to GAME_VARS and
        ;   verify its signature ($CA,$01 = the PLR_SAVE byte length $01CA).
        ;   A missing or bad disk prints "Please put in the Player disk."
        ;   and re-prompts.
        ;
        ; Clobbers: A, X, Y""",
 'gen launch': """        ; Copy the loaded save into the live player block and launch OUT.
        ;
        ; Behavior:
        ;   The first loop copies the BLOADed player record (GAME_VARS, the
        ;   $6000 load buffer) byte-by-byte into the live player state at
        ;   PLR_SAVE, advancing two self-modified pointers (DECRYPT_SRC,
        ;   DECRYPT_PTR) until the destination reaches the end of the block
        ;   ($8037).  The second loop overlays the 13-page initial game-state
        ;   image (GAME_IMAGE) into GAME_VARS, marks the world initialised
        ;   (GAME_VARS_FLAG), restores the saved sound/sfx settings, draws the
        ;   first map frame, and jumps to EXIT_TO_OUT to begin play.
        ;
        ; Clobbers: A, X, Y""",
 'gen chargen': """        ; Character generation: clear the portrait, run the attribute editor.
        ;
        ; Behavior:
        ;   Draw the "Character Generation" header, then a self-modified clear
        ;   loop (CLEAR_SRC/CLEAR_DST patched from #$904F/#$906F) blanks the
        ;   stat region of the template.  Seed the point pool (POINT_POOL <-
        ;   #$1E = 30 points) and the editor cursor (CURSOR_IDX <- #$01),
        ;   print the instructions, and fall into ATTR_INPUT.
        ;
        ; Clobbers: A, X, Y""",
 'gen attr input': """        ; The attribute-point editor input loop.
        ;
        ; Behavior:
        ;   Redraw the six stats (EDITOR_DRAW), read a key, and act on it.  The
        ;   cursor index CURSOR_IDX (1..6) selects a stat word at PLR_HITS,X
        ;   with X = 2*CURSOR_IDX (so STR/AGI/STA/CHA/WIS/INT).  Left arrow
        ;   ($08) lowers the highlighted stat (floor 10, refunding a point to
        ;   POINT_POOL); right arrow ($15) raises it (ceiling 25, spending a
        ;   point); up/down ($0B/$0D or '/'/return) move the cursor with
        ;   wraparound; space finishes (only when POINT_POOL is empty, else a
        ;   "Huh?" beep); escape ($1B) abandons chargen back to the menu.
        ;   When done, fall into PICK_RACE.
        ;
        ; Clobbers: A, X, Y""",
 'gen pick race': """        ; Choose a race and apply its attribute bonuses.
        ;
        ; Behavior:
        ;   Draw "a) Human / b) Elf / c) Dwarf / d) Bobbit", read a letter A..D,
        ;   store the 1-based choice in PLR_RACE, and echo the name from
        ;   STR_RACES.  Each race adjusts attributes: Human +5 INT, Elf +5 AGI,
        ;   Dwarf +5 STR, Bobbit +10 WIS and -5 STR -- the classic Ultima I
        ;   racial trade-offs.  Falls into PICK_SEX.
        ;
        ; Clobbers: A, X, Y""",
 'gen pick sex': """        ; Choose a sex.
        ;
        ; Behavior:
        ;   Draw "a) Male / b) Female", read a letter, store the 0-based choice
        ;   in PLR_SEX, and echo the name from the in-file STR_SEX table.
        ;   Falls into PICK_CLASS.
        ;
        ; Clobbers: A, X, Y""",
 'gen pick class': """        ; Choose a class and apply its attribute bonuses.
        ;
        ; Behavior:
        ;   Draw "a) Fighter / b) Cleric / c) Wizard / d) Thief", read a letter,
        ;   store the 1-based choice in PLR_CLASS, and echo the name from
        ;   STR_CLASSES.  Each class adds +10 to its signature attributes
        ;   (Fighter->STR+AGI, Cleric->WIS, Wizard->INT, Thief->AGI).  Falls
        ;   into PICK_NAME.
        ;
        ; Clobbers: A, X, Y""",
 'gen pick name': """        ; Enter the character's name, then offer to save.
        ;
        ; Behavior:
        ;   Seed the saved space position (PLR_SPACE_X/Y) from the RNG, prompt
        ;   "Enter thy name:", and run NAME_KEYLOOP: accept up to 13 letters
        ;   (first letter forced upper-case, the rest lower-case), backspace
        ;   ($08/$7F) deletes, return ends.  The finished name lands in
        ;   PLR_NAME; control falls into SAVE_PROMPT.
        ;
        ; Clobbers: A, X, Y""",
 'gen save': """        ; "Save this character?" and the BSAVE / format-offer paths.
        ;
        ; Behavior:
        ;   SAVE_PROMPT asks "Save this character? (Y-N)".  N restarts chargen.
        ;   Y -> DO_BSAVE writes the $01CA-byte PLR_SAVE record to PATH_PLAYER
        ;   via the resident library's pointer-path BSAVE.  If the write fails,
        ;   FMT_OFFER inspects the error: a write-protected or absent disk
        ;   prints the matching message and, for "no player disk found", offers
        ;   to format a fresh one (-> FORMAT_ENTRY); RETRY_SAVE re-attempts the
        ;   BSAVE after a successful format.  A clean save returns to the title.
        ;
        ; Clobbers: A, X, Y""",
 'gen editor draw': """        ; Redraw the six attributes and the points-remaining line.
        ;
        ; Behavior:
        ;   For each of the six stats print its STR_STATS name and 16-bit value
        ;   (PRINT_STAT16), drawing the highlighted one (CURSOR_IDX) in inverse
        ;   video, then print "Points left to distribute: NN" from POINT_POOL.
        ;
        ; Clobbers: A, X, Y""",
 'gen format entry': """        ; Disk formatter front end: choose the slot and drive.
        ;
        ; Behavior:
        ;   FORMAT_ENTRY derives a default slot/drive from the ProDOS last-used
        ;   device number (PRODOS_DEVNUM).  FORMAT_RESTART draws "Slot: ( )" /
        ;   "Drive: ( )" and runs SLOT_KEYLOOP / DRIVE_KEYLOOP: digits update
        ;   the field (slot 1..7, drive 1..2), return accepts, escape aborts.
        ;   MLIB_ONLINE rejects a slot/drive with no disk.  When both are set,
        ;   control passes to VOL_CHECK.
        ;
        ; Clobbers: A, X, Y""",
 'gen vol check': """        ; Verify the target disk, confirm, and dispatch the format.
        ;
        ; Behavior:
        ;   VOL_CHECK reads the device's boot block and tests for a Disk II
        ;   ($Cn ROM signature); NO_DISKII rejects other devices.  TEST_ONLINE
        ;   asks ProDOS whether the disk is already a known volume and, if so,
        ;   shows its name; NON_PRODOS handles an unformatted disk.  CONFIRM_FMT
        ;   prints "...? (Y-N)" and waits for Y.  DO_FORMAT saves the zero-page
        ;   scratch, calls the low-level RWTS_FORMAT, then the volume-directory
        ;   writer, restoring zero page around the call.
        ;
        ; Clobbers: A, X, Y""",
 'gen write voldir': """        ; Call FORMAT_VOLUME and report any error.
        ;
        ; Behavior:
        ;   Invoke FORMAT_VOLUME (the ProDOS directory writer) with the unit
        ;   number; on success return, on failure clear the line and print
        ;   "Format failed -- error NN." (the ProDOS error code in hex) before
        ;   restarting the formatter.
        ;
        ; Clobbers: A, X, Y""",
 'gen text helpers': """        ; Bottom-line prompt printer and text-window helpers.
        ;
        ; Behavior:
        ;   PROMPT_LINE homes the cursor to the bottom prompt line (row $14)
        ;   and falls into MSG_PRINT, so callers can pass inline text.
        ;   PRESS_SPACE prints "Press Space to continue:" and waits.
        ;   CLEAR_FROM20 / WINFULL_HOME / CLEAR_LINES blank ranges of text rows
        ;   around the cursor (used between chargen steps).
        ;
        ; Clobbers: A, X, Y""",
 'gen border': """        ; Draw the decorative double-line screen border.
        ;
        ; Behavior:
        ;   Stroke the top rule, the side rules down to row $16, and the bottom
        ;   rule using the font's box-drawing glyphs, then HOME_CURSOR resets
        ;   the text cursor to (1,1).
        ;
        ; Clobbers: A, X, Y""",
 'gen format volume': """        ; ProDOS volume-directory writer: set up the paramblocks.
        ;
        ; Behavior:
        ;   Patch the WRITE_BLOCK paramblock unit fields (FV_WR1/2/3) from the
        ;   unit number, scan the ProDOS device list (PRODOS_DEVLST) for the
        ;   matching drive mask, look up its block count, and fall into
        ;   FV_WRITE_DIR to lay down the four-block directory and the volume
        ;   bitmap.  This reproduces what ProDOS FILER's "format" does: a
        ;   blank but valid volume directory.
        ;
        ; Clobbers: A, X, Y""",
 'gen fv write dir': """        ; Write the volume-directory key block and helpers.
        ;
        ; Behavior:
        ;   FV_WRITE_DIR builds and writes the directory key block (the volume
        ;   header at block 2); FV_DEV_ADDR looks up the device driver address
        ;   for the unit from the ProDOS device table; FV_READ_DIR reads a
        ;   directory block into the buffer; FV_FINISH allocates the bitmap and
        ;   writes the final block.  All go through the MLI / driver vector.
        ;
        ; Clobbers: A, X, Y""",
 'gen fv bitmap': """        ; Build and write the volume bitmap; the driver dispatch.
        ;
        ; Behavior:
        ;   FV_ALLOC_BITMAP marks the boot, directory and bitmap blocks as used
        ;   and the rest free; FV_BITMAP_IO reads/writes a bitmap block;
        ;   FV_DISPATCH jumps through the device-driver vector (FV_VECTOR) and
        ;   FV_DEVENTRY returns a device-table entry for the selected unit.
        ;
        ; Clobbers: A, X, Y""",
 'gen fv write block': """        ; MLI WRITE_BLOCK wrapper.
        ;
        ; Behavior:
        ;   Issue a ProDOS MLI WRITE_BLOCK ($81) for the prepared paramblock,
        ;   incrementing the write counter (FV_WRCNT).
        ;
        ; Clobbers: A, X, Y""",
 'gen fv init dir': """        ; Initialise the directory-header fields.
        ;
        ; Behavior:
        ;   FV_INIT_FIELDS fills in the standard ProDOS volume-directory header
        ;   (storage type/name length, access bits, entry length $27, entries
        ;   per block $0D, the creation date from PRODOS_DATE, ProDOS version);
        ;   FV_SET_ENTRY writes one field, FV_NEXT_BLOCK threads the forward/
        ;   backward block links.
        ;
        ; Clobbers: A, X, Y""",
 'gen fv fill': """        ; Bitmap-fill primitives and the embedded boot-loader image.
        ;
        ; Behavior:
        ;   FV_FILL_BITMAP and its helpers (FV_SET_BITS / FV_FILL_FF /
        ;   FV_PARTIAL / FV_ZERO_BLK / FV_FF_BLK / FV_FILL_PAGE / FV_MASK) build
        ;   the allocation bitmap a byte and a partial byte at a time.  The tail
        ;   of this region is the ProDOS boot-loader image that FORMAT_VOLUME
        ;   stamps onto block 0 of the new disk; in this overlay's address space
        ;   it is inert data (it executes only after the disk boots), so the
        ;   labels here name the directory-writer primitives, not the image.
        ;
        ; Clobbers: A, X, Y""",
 'gen rwts format': """        ; Low-level Disk II formatter: lay down 35 tracks of nibbles.
        ;
        ; Behavior:
        ;   RWTS_FORMAT drives the drive directly through the slot soft
        ;   switches.  RW_FORMAT_DISK steps the arm track by track (RW_SEEK with
        ;   the SEEK_DELAY_A/B settle tables), and RW_FMT_TRACK writes 16
        ;   sectors per track: each sector is a self-synchronising address field
        ;   (the D5 AA 96 prologue, volume/track/sector/checksum in 4-and-4
        ;   encoding) and a 6-and-2 GCR data field (RW_WRITE_SECTOR), verified
        ;   by reading it back (RW_READ_ADDR / RW_FIND_ADDR / RW_READ_DATA).
        ;   This is a complete hand-rolled RWTS, independent of ProDOS, that
        ;   physically initialises a blank disk.
        ;
        ; Clobbers: A, X, Y""",
 'gen rwts delay': """        ; Timed nibble write (motor pacing).
        ;
        ; Behavior:
        ;   Write the nibble in A to the drive's data latch and burn the exact
        ;   number of cycles a 4us nibble cell requires, so the bitstream is
        ;   laid down at the correct density.
        ;
        ; Clobbers: A""",
 'gen rwts verify': """        ; Verify a freshly written track and the long settle delays.
        ;
        ; Behavior:
        ;   RW_VERIFY_TRACK reads back all 16 sectors of the current track and
        ;   confirms each address field is present and correct; a miss fails the
        ;   format.  RW_LONG_DELAY provides the motor-on/seek settle pauses.
        ;
        ; Clobbers: A, X, Y""",
}

# Data-chunk descriptions (no SUBROUTINE; a one-line comment above the data).
# Handled in prose, not as plates.


def inject_plates():
    for name, plate in PLATE.items():
        body = chunks[name]
        # find the SUBROUTINE line
        for i, ln in enumerate(body):
            if ln.strip() == 'SUBROUTINE':
                plate_lines = plate.split('\n')
                chunks[name] = body[:i+1] + plate_lines + body[i+1:]
                break
        else:
            raise SystemExit(f'no SUBROUTINE in chunk {name}')


if __name__ == '__main__':
    inject_plates()
    # Re-emit chunks (with plates) in order; the prose/collection is authored
    # separately in main.nw, so here we just dump the updated chunk bodies.
    out = []
    for name in order:
        out.append(f'<<{name}>>=')
        out += chunks[name]
        out.append('')
    Path('/tmp/gen_chunks_plated.nw').write_text('\n'.join(out) + '\n')
    print('plated', len(PLATE), 'code chunks of', len(order), 'total')
