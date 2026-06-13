#!/usr/bin/env python3
"""Assemble the complete GEN chapter for main.nw.

Combines authored prose, the defines chunk, the collection chunk, and the
plated code/data chunks into /tmp/gen_section.nw, ready to splice into main.nw
in place of the old GEN stub. All assembly content comes from the byte-perfect
emission; only prose and the defines/collection wrappers are authored here.
"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen_chapter_gen as G
import gen_gen as g

# --- defines (EQU) block, grouped with comments -----------------------------
DEFINES_HEAD = """<<gen defines>>=
        PROCESSOR 6502
;
; GEN runs at the shared overlay base and calls into the resident STUPH
; library ($15xx), the MI.U1 engine API ($80xx-$88xx), the MLIB file library
; ($B7xx), and -- uniquely among the overlays -- straight into the ProDOS MLI
; ($BF00) and the Disk II card soft switches to format a player save disk.
;
"""

# Group EQUs by address band with a section comment.
BANDS = [
    (0x0000, 0x0100, '; --- zero page ---'),
    (0x1580, 0x1600, '; --- STUPH resident library ---'),
    (0x4000, 0x7000, '; --- buffers ---'),
    (0x73AF, 0x7F00, '; --- MI.U1 string tables + player state ---'),
    (0x8000, 0x8900, '; --- MI.U1 engine API ---'),
    (0xB000, 0xC000, '; --- MLIB file library + ProDOS MLI / global page ---'),
    (0xC000, 0xF500, '; --- soft switches + ROM ---'),
]


def build_defines():
    lines = [DEFINES_HEAD.rstrip('\n')]
    seen = set()
    items = sorted(G.SYM.items())
    for (lo, hi, comment) in BANDS:
        band = []
        for a, nm in items:
            base_nm = nm.split('+')[0]
            if base_nm in seen:
                continue
            if 0x8956 <= a < g.END:
                continue
            base_a = a - (int(nm.split('+')[1]) if '+' in nm else 0)
            if not (lo <= base_a < hi):
                continue
            seen.add(base_nm)
            band.append(f'{base_nm:16s}EQU ${base_a:04X}')
        if band:
            lines.append(comment)
            lines += band
    lines.append('STALE_FFFF      EQU $FFFF')
    lines.append('@ %def STALE_FFFF')
    lines.append('')
    return '\n'.join(lines)


# --- collection chunk -------------------------------------------------------
import gen_emit_chunks as E

def build_collection():
    refs = '\n'.join(f'<<{nm}>>' for (nm, s, e) in E.CHUNKS)
    return f"""<<gen.asm>>=
        PROCESSOR 6502
<<gen defines>>
{refs}
@
"""


# --- prose blocks, keyed by the chunk they precede --------------------------
PROSE = {
 'gen defines': r"""\section{GEN: character generation and the disk formatter}
\label{ch:gen}

\texttt{GEN} is the overlay the engine loads for slot~0 of \texttt{GAME\_LOAD}
--- the \emph{new game} slot reached from the title screen and whenever a save
is absent. It is two programs sharing one file. The first is the
character generator: the \texttt{Ultima~I} title, a race/sex/class/name
questionnaire, and a point-buy attribute editor, ending in a player record
written to disk. The second, reached only when that write fails for want of a
formatted disk, is a complete \emph{ProDOS disk formatter} --- a hand-rolled
Disk~II RWTS that physically initialises a blank disk plus a ProDOS
volume-directory writer that makes it a valid, empty \texttt{/U1.PLAYER}
volume. The formatter is the only place in the whole game that bypasses the
MLIB library and touches the drive hardware directly, so it is documented here
in full.

The overlay shares the engine's calling conventions: \texttt{MSG\_PRINT} and
\texttt{MSG\_AT} take inline zero-terminated text, \texttt{STR\_NTH\_CAP} an
inline name-table pointer, and the library's pointer-path
\texttt{MLIB\_BLOAD\_AT\_P}/\texttt{MLIB\_BSAVE\_P} an inline address and path
pointer. \texttt{GEN} adds one local convention of its own,
\texttt{PROMPT\_LINE}, a trampoline that homes the cursor to the bottom line
and falls into \texttt{MSG\_PRINT}.

\subsection{Title screen and the two paths}

Entry draws the title and offers ``Generate new character'' or ``Continue
previous game''. The continue path \texttt{BLOAD}s the saved record to
[[GAME_VARS]] and checks its first word against \texttt{\$01CA}, the byte
length of a [[PLR_SAVE]] record, used here as a file signature.""",

 'gen launch': r"""When ``continue'' validates, \texttt{LAUNCH\_GAME} installs the loaded record
and starts the overworld. Its two loops use self-modified pointers: the first
copies the player record from the load buffer into the live player state at
\texttt{PLR\_SAVE} (stopping when the destination reaches the end of the
block), and the second overlays the 13-page initial game-state image
(\texttt{GAME\_IMAGE}, stored in this file) onto \texttt{GAME\_VARS} before
handing control to \texttt{EXIT\_TO\_OUT}. The same launch tail serves the new
game once its record is saved.""",

 'gen chargen': r"""\subsection{Character generation}

The ``a'' choice enters \texttt{CHARGEN}. It blanks the stat area of the
working template with a self-modified clear loop, primes the point pool
(\texttt{POINT\_POOL} $\leftarrow$ 30) and the cursor, prints the on-screen
instructions, and drops into the attribute editor.""",

 'gen attr input': r"""The editor is a point-buy: six attributes, a shared pool, a floor of~10 and a
ceiling of~25 per stat. The cursor index selects a 16-bit attribute word at
\texttt{PLR\_HITS} indexed by twice the cursor (so the words \texttt{PLR\_STR},
\texttt{PLR\_AGI}, \texttt{PLR\_STA}, \texttt{PLR\_CHA}, \texttt{PLR\_WIS},
\texttt{PLR\_INT}). Left and right spend and refund points; up and down move
the cursor; space finishes only once the pool is empty.""",

 'gen pick race': r"""The questionnaire follows. Each of race, sex and class is a single-key menu
that stores the choice, echoes the chosen name, and --- for race and class ---
nudges the starting attributes. The race bonuses are the canonical
\texttt{Ultima~I} ones: Human favours intelligence, Elf agility, Dwarf
strength, and the Bobbit trades strength for a large wisdom bonus.""",

 'gen pick sex': r"""Sex is cosmetic mechanically but threads through the prose elsewhere; its name
strings live in this file (\texttt{STR\_SEX}) rather than the engine's tables.""",

 'gen pick class': r"""Class layers a second set of bonuses on top of race: the Fighter raises both
strength and agility, the Cleric wisdom, the Wizard intelligence, and the
Thief agility.""",

 'gen pick name': r"""Name entry caps at thirteen letters, forcing the first upper-case and the rest
lower-case, and seeds the saved space-combat position from the RNG so a fresh
character starts somewhere definite if they ever launch into space. The
finished character falls through to the save prompt.""",

 'gen save': r"""\subsection{Saving, and the path into the formatter}

Saving writes the \texttt{\$01CA}-byte record to \texttt{/U1.PLAYER}. The
interesting branch is the failure path: the library returns a ProDOS error,
and \texttt{FMT\_OFFER} reads it. A write-protected disk or a wrong disk is
reported and retried; ``file not found'' (no player disk yet) offers to format
one. Accepting drops into the formatter; a successful format returns here to
retry the save.""",

 'gen editor draw': r"""\texttt{EDITOR\_DRAW} renders the editor each keystroke: the six named stats
with their values, the highlighted one in inverse video, and the running
``points left to distribute''.""",

 'gen chargen data': r"""The character generator's small data block holds the editor counters, the
in-file ``male''/``female'' strings, the \texttt{\$01CA} signature template,
and \texttt{PLR\_TEMPLATE} --- the default player record the new character is
built on top of (default inventory, hit points, position).""",

 'gen format entry': r"""\subsection{The disk formatter}

Everything from here serves one goal: take a blank or foreign disk and turn it
into an empty \texttt{/U1.PLAYER} ProDOS volume the game can save to. It is a
self-contained subsystem; nothing in normal play reaches it.

The front end picks a slot and drive, defaulting to the ProDOS last-used
device. Digit keys edit the fields (slot 1--7, drive 1--2), return accepts,
escape backs out, and \texttt{MLIB\_ONLINE} refuses a slot/drive with no
disk in it.""",

 'gen vol check': r"""With a target chosen, \texttt{VOL\_CHECK} confirms it is a Disk~II (other
device types are rejected), asks ProDOS whether the disk is already a known
volume so it can warn before overwriting, and requires an explicit ``Y'' to
proceed. \texttt{DO\_FORMAT} then brackets the destructive work by saving and
restoring the engine's zero-page scratch, calling first the low-level
\texttt{RWTS\_FORMAT} to write the magnetic format and then
\texttt{FORMAT\_VOLUME} to lay down the directory.""",

 'gen write voldir': r"""\texttt{WRITE\_VOLDIR} is the thin wrapper that calls the directory writer and,
on any ProDOS error, prints the code in hex so a failure is at least
diagnosable.""",

 'gen text helpers': r"""\subsection{Local text helpers}

These few routines are \texttt{GEN}'s own window furniture: a bottom-line
prompt printer that accepts inline text, a ``press space'' wait, and a couple
of line-clearing helpers used between chargen steps.""",

 'gen rdblk data': r"""The \texttt{READ\_BLOCK} parameter block and a fourteen-byte scratch buffer
(used to preserve zero page [[$D0]]--[[$DD]] across the RWTS call) sit here.""",

 'gen border': r"""\texttt{BORDER\_DRAW} strokes the decorative double-ruled frame around the
screen using the font's box glyphs.""",

 'gen image data': r"""\subsection{The initial game-state image}

\texttt{GAME\_IMAGE} is the 13-page block \texttt{LAUNCH\_GAME} copies to
\texttt{GAME\_VARS} to start a new game: the packed world variables, the player
position, and the \texttt{/U1.PLAYER} path components used to write the first
save. It is opaque data to this overlay --- the engine and \texttt{MAKE.INDATA}
give it meaning --- so it is preserved verbatim.""",

 'gen format volume': r"""\subsection{The ProDOS volume-directory writer}

\texttt{FORMAT\_VOLUME} does in code what ProDOS \texttt{FILER}'s format command
does: it writes a blank but valid volume directory and allocation bitmap onto a
disk that \texttt{RWTS\_FORMAT} has already magnetically initialised. It
patches its \texttt{WRITE\_BLOCK} paramblocks with the chosen unit, finds the
device's block count from the ProDOS device list, and writes the four directory
blocks and the bitmap through the MLI and the device driver.""",

 'gen fv write dir': r"""These helpers carry out the directory write: building and writing the key
block (the volume header), resolving the device driver address for the unit,
reading directory blocks back, and [[FV_FINISH]] allocating the bitmap
and committing the last block.""",

 'gen fv bitmap': r"""The bitmap helpers mark the boot, directory and bitmap blocks as used and
everything else free, and \texttt{FV\_DISPATCH} is the indirect jump through
the device-driver vector that actually moves blocks to and from the disk.""",

 'gen fv write block': r"""\texttt{FV\_WRITE\_BLOCK} is the MLI \texttt{WRITE\_BLOCK} call, used for every
block the directory writer commits.""",

 'gen fv init dir': r"""\texttt{FV\_INIT\_FIELDS} fills the standard ProDOS directory-header fields ---
storage type and name length, access bits, the \texttt{\$27}-byte entry length
and thirteen entries per block, the creation date from the ProDOS global page,
and the version bytes --- and the entry/block-threading helpers complete the
chain.""",

 'gen fv fill': r"""The remaining bitmap-fill primitives build the allocation map a byte and a
partial byte at a time.""",

 'gen boot image': r"""\texttt{BOOT\_IMAGE} is the ProDOS boot-loader the formatter stamps onto
block~0 of the new disk so the player save volume is itself bootable. In this
overlay's address space it is pure data --- nothing here calls into it; it runs
only after that disk boots --- so it is preserved verbatim as a block. (Its
strings ``PRODOS''/``SOS''/``UNABLE TO LOAD'' are visible in the bytes.)""",

 'gen rwts bss': r"""\subsection{The low-level Disk II formatter}

Below the directory writer sits a complete RWTS, independent of ProDOS, that
talks to the drive through the slot soft switches. This data block is its
scratch space and the ProDOS volume-name parameter block.""",

 'gen rwts format': r"""\texttt{RWTS\_FORMAT} writes the magnetic format itself. It steps the arm track
by track (35 tracks, using the \texttt{SEEK\_DELAY} tables to pace the stepper)
and writes sixteen sectors per track. Each sector is a self-synchronising
address field --- the \texttt{D5~AA~96} prologue followed by the volume, track,
sector and checksum in 4-and-4 encoding --- and a 6-and-2 GCR data field, and
each is verified by reading it straight back. This is the same job a copy
program's nibble writer or the \texttt{INIT} command does; reproducing it here
let the game ship a save-disk formatter without depending on a system disk.""",

 'gen rwts delay': r"""\texttt{RW\_WRITE\_DELAY} writes one nibble and burns the exact cycles a
4-microsecond bit cell needs, so the bitstream lands at the right density ---
the timing is the format.""",

 'gen seek tables': r"""The two seek-delay tables give the stepper settle time as a function of how far
the arm must travel, longer for the first phase and tapering as it nears the
target track.""",

 'gen rwts verify': r"""\texttt{RW\_VERIFY\_TRACK} reads back every sector of a freshly written track
to confirm the address fields took, and \texttt{RW\_LONG\_DELAY} provides the
motor and seek settle pauses. A verify miss fails the format.""",
}


def main():
    plated = Path('/tmp/gen_chunks_plated.nw').read_text()
    blocks = re.split(r'^<<(.+?)>>=$', plated, flags=re.M)
    chunk_text = {}
    order = []
    it = iter(blocks[1:])
    for name, body in zip(it, it):
        chunk_text[name] = body.strip('\n')
        order.append(name)

    out = []
    out.append(build_defines())          # opens with <<gen defines>>= ... @
    # but prose for 'gen defines' must come BEFORE the defines chunk:
    # re-do: emit prose, then defines, then collection, then chunks.
    out = []
    out.append(PROSE['gen defines'])
    out.append('')
    out.append(build_defines())
    out.append(build_collection())
    for name in order:
        if name in PROSE:
            out.append(PROSE[name])
            out.append('')
        out.append(f'<<{name}>>=')
        out.append(chunk_text[name])
        out.append('')
    Path('/tmp/gen_section.nw').write_text('\n'.join(out) + '\n')
    print('wrote /tmp/gen_section.nw with', len(order), 'chunks')


if __name__ == '__main__':
    main()
