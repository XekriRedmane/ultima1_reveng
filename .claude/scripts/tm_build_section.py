#!/usr/bin/env python3
"""Assemble the complete TM chapter for main.nw.

Twin of gen_build_section.py.  Combines authored prose, the defines (EQU)
chunk, the collection chunk, and the byte-perfect code/data chunks --- with a
header-plate comment block injected after each chunk's SUBROUTINE --- into
/tmp/tm_section.nw, ready to splice into main.nw as the TM chapter.

All assembly content comes from the byte-perfect emission in tm_emit_chunks
(via /tmp/tm_chunks.nw); this script only authors prose and the per-routine
header plates and wraps them in the defines/collection scaffolding.  Run:

    cd /project/repo && python3 .claude/scripts/tm_build_section.py
"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import tm_chapter_tm as T
import tm_gen as g
import tm_emit_chunks as E

# --- defines (EQU) block, grouped with comments -----------------------------
DEFINES_HEAD = """<<tm defines>>=
        PROCESSOR 6502
;
; TM runs at the shared overlay base ($8956) and calls into the resident STUPH
; library ($15xx), the MI.U1 engine API ($80xx-$88xx), and the MLIB file
; library ($B7xx).  It owns Mondain's gem hit-point counter (GEM_HP) and the
; combat-state byte (CUR_MON) in the shared player-state block, and drives the
; hi-res renderer directly through the HGR row pointers in zero page.
;
"""

# Group EQUs by address band with a section comment (mirrors gen_build_section).
BANDS = [
    (0x0000, 0x0100, '; --- zero page ---'),
    (0x1100, 0x1600, '; --- STUPH resident library + stale SMC operands ---'),
    (0x2000, 0x7000, '; --- hi-res pages + buffers + soft-switch shadows ---'),
    (0x7000, 0x7F00, '; --- MI.U1 player state + gem HP ---'),
    (0x8000, 0x8956, '; --- MI.U1 engine API ---'),
    (0xB000, 0xC000, '; --- MLIB file library + scene buffers/state ---'),
    (0xC000, 0xF500, '; --- soft switches ---'),
]


def build_defines():
    lines = [DEFINES_HEAD.rstrip('\n')]
    seen = set()
    items = sorted(T.SYM.items())

    def base_of(a, nm):
        return a - (int(nm.split('+')[1]) if '+' in nm else 0)

    for (lo, hi, comment) in BANDS:
        band = []
        for a, nm in items:
            base_nm = nm.split('+')[0]
            if base_nm in seen:
                continue
            if 0x8956 <= a < g.END:
                continue
            if not (lo <= base_of(a, nm) < hi):
                continue
            seen.add(base_nm)
            band.append(f'{base_nm:16s}EQU ${base_of(a, nm):04X}')
        if band:
            lines.append(comment)
            lines += band
    # Catch-all: any out-of-file SYM not captured by a band (guards against a
    # new EQU silently dropping out of the defines and failing the tangle).
    extra = []
    for a, nm in items:
        base_nm = nm.split('+')[0]
        if base_nm in seen or (0x8956 <= a < g.END):
            continue
        seen.add(base_nm)
        extra.append(f'{base_nm:16s}EQU ${base_of(a, nm):04X}')
    if extra:
        lines.append('; --- other ---')
        lines += extra
    lines.append('')
    return '\n'.join(lines)


# --- collection chunk -------------------------------------------------------
def build_collection():
    refs = '\n'.join(f'<<{nm}>>' for (nm, s, e) in E.CHUNKS)
    return f"""<<tm.asm>>=
        PROCESSOR 6502
<<tm defines>>
{refs}
@
"""


# --- header plates, keyed by chunk name -------------------------------------
# Injected right after the chunk's "        SUBROUTINE" line.  ASCII only;
# comment the purpose, not the mechanics.  "Behavior:" within 15 lines.
PLATE = {
 'tm mul': """        ; Overlay entry, then a small suite of fixed-point arithmetic helpers.
        ;
        ; Behavior:
        ;   OVERLAY_ENTRY is the loader's jump-in point and immediately jumps to
        ;   TM_ENTRY.  The rest are shift-add long-multiply / restoring-divide
        ;   primitives the renderer and combat code lean on: MUL8 (A*ZP_M0 ->
        ;   ZP_M2), MUL16 (ZP_PTR*A -> ZP_M2..ZP_M4), MUL16B (ZP_PTR*ZP_M0/M1
        ;   -> ZP_M2..ZP_M5), and DIV16 (16-bit ZP_M2/M3 by ZP_M0/M1, quotient
        ;   in ZP_M2/M3, remainder in ZP_M4/M5).  Each saves the decimal flag
        ;   and forces binary mode, so callers in SED mode stay safe.
        ;
        ; Modifies:
        ;   ZP_M0..ZP_M5, ZP_MCNT, ZP_MREM
        ; Clobbers: A""",
 'tm bcd': """        ; Binary-to-BCD conversion helpers for printing 16-bit numbers.
        ;
        ; Behavior:
        ;   BCD_DBL doubles a packed-BCD byte; BIN2BCD16 converts the 16-bit
        ;   value at (ZP_PTR) to packed BCD in place by repeated weighted adds
        ;   from the BCD_WEIGHTS digit-weight table; BCD_FROM8 / BCD_FROM16 are
        ;   the byte / word entry points using BCD_WEIGHTS2 and decimal-mode
        ;   adds (BCD_W_HI / BCD_W_LO).  These are generic math support shared
        ;   with the stats display.
        ;
        ; Modifies:
        ;   ZP_M0..ZP_M3, and the word at (ZP_PTR) for the in-place converters
        ; Clobbers: A, X, Y""",
 'tm entry': """        ; Endgame entry: arm Mondain's gem, draw the craft, run the intro.
        ;
        ; Behavior:
        ;   Set GEM_HP <- #$03E8 (1000 = the gem-of-immortality hit points that
        ;   gate Mondain's life) and CUR_MON <- #$00.  Build the interior scene
        ;   (the .L9E95 / .L9E50 / .L9E6C renderer setup), print the framed
        ;   intro narration ("Entering the craft... four holes marked R G B W
        ;   ... a button marked LAUNCH ... press it!"), and draw the four
        ;   colored gem-socket markers at x = $5E/$73/$88/$9D in colors
        ;   5/1/6/7 (R/G/B/W) via the LA44B socket drawer.
        ;
        ; Modifies:
        ;   GEM_HP, CUR_MON
        ; Clobbers: A, X, Y""",
 'tm main loop': """        ; The combat turn loop: tick the scene, poll, dispatch a command.
        ;
        ; Behavior:
        ;   Reset the stack and print the prompt, then TURN_TOP ticks the scene
        ;   (SCENE_TICK), refreshes the stats, and checks for death -- food or
        ;   hits at zero jumps to RESPAWN.  IDLE_POLL animates while waiting for
        ;   a key; with no key it runs Mondain's turn (TURN_END + .L9BDF) and
        ;   loops.  On a key, DISPATCH reads the command, copies its handler
        ;   address from DISPATCH_TBL over the self-modified JSR operand
        ;   (DISPATCH_JSR), calls it, clears the keyboard, and repeats.
        ;
        ; Modifies:
        ;   DISPATCH_JSR (self-modified call target)
        ; Clobbers: A, X, Y""",
 'tm attack': """        ; ATTACK command: strike Mondain (or his gem) in melee.
        ;
        ; Behavior:
        ;   Require a sword-class weapon (READY_WEAPON = 4 or 8..10, else fall
        ;   to QUERY_MARK "Huh?").  Pick a direction with .L916F and demand it
        ;   face Mondain.  Hit chance gates PLR_AGI against RND; on a hit,
        ;   damage = weapon*3 + PLR_STR (via RND_MOD) and DMG_AMT is subtracted
        ;   from the 16-bit GEM_HP.  As GEM_HP crosses 500 then 0 Mondain's
        ;   sprite advances (CRAFT_GFX+6 -> 7 then 8) and CUR_MON steps.  When
        ;   GEM_HP reaches 0 with the $95AB victory flag set, run the
        ;   "THOU ART VICTORIOUS!" win sequence (NIF screen, Control-RESET
        ;   hook, screen-melt, STR_RESTART, hang); if the gem was never
        ;   destroyed, only " ...or is he?" -- the gem-destroy gate.
        ;
        ; Modifies:
        ;   GEM_HP, CUR_MON, DMG_AMT, CRAFT_GFX+6, CRAFT_GFX+10/+11
        ; Clobbers: A, X, Y""",
 'tm cast': """        ; CAST command: dispatch the readied spell.
        ;
        ; Behavior:
        ;   Print the spell name (PRINT_SPELL), refuse a used-up spell
        ;   ("Thou hast used up that spell!" via OWNED_SPELLS), then index
        ;   TM_SPELL_TBL by 2*READY_SPELL and copy the handler address over the
        ;   self-modified JMP operand (SPELL_JMP) before jumping to it.
        ;
        ; Modifies:
        ;   SPELL_JMP (self-modified jump target), CUR_MON
        ; Clobbers: A, X, Y""",
 'tm spell helpers': """        ; Cast-success check and the shared failure / not-applicable tails.
        ;
        ; Behavior:
        ;   .L925F consumes one charge of the readied spell (OWNED_SPELLS),
        ;   then decides success: a Cleric (PLR_CLASS = 2) auto-passes, others
        ;   roll against RND; range is gated through .L9D5C and PLR_INT is
        ;   rolled against RND.  Carry clear = success, set = failure.  .L929F
        ;   prints " failed!" and beeps; the fall-through entries print
        ;   "Not applicable!" / route to NO_EFFECT_MSG for the inert spells.
        ;
        ; Outputs:
        ;   Carry clear on success, set on failure.
        ; Clobbers: A, X, Y""",
 'tm spell missile': """        ; Magic-missile spell aimed at Mondain.
        ;
        ; Behavior:
        ;   Prompt for a direction (.L916F); on a valid cast (.L925F) and a
        ;   facing of Mondain, roll base damage from PLR_INT and scale it by
        ;   the readied weapon class (8 -> 1.5x, 9 -> 2x, 10..11 -> 3x), store
        ;   DMG_AMT, then jump into the shared hit-resolution path (.L8F80,
        ;   the "Hit Mondain!" / GEM_HP-drain code).
        ;
        ; Modifies:
        ;   DMG_AMT
        ; Clobbers: A, X, Y""",
 'tm spell band2': """        ; Spells 7/8/9: place, summon, and clear cells on the interior grid.
        ;
        ; Behavior:
        ;   .L934A picks a random empty cell and writes a force-field marker
        ;   into CELL_STATE there (re-rolling until empty), drawing it into the
        ;   scene.  The two later entries take a direction (.L916F), resolve a
        ;   target cell offset (.L9436 against the projection tables), and
        ;   either set or clear that CELL_STATE entry with the matching sprite,
        ;   printing "Done".
        ;
        ; Modifies:
        ;   CELL_STATE, ZP_PTR, $B62C/$B62D (target cell)
        ; Clobbers: A, X, Y""",
 'tm spell kill': """        ; Spell 10, "INTERFICIO-NUNC!" -- the kill spell that backfires.
        ;
        ; Behavior:
        ;   A designed trap: announce the incantation, print "The spell doth
        ;   seem to make him stronger!", then DOUBLE the remaining GEM_HP
        ;   (16-bit add of GEM_HP to itself) instead of harming Mondain --
        ;   unless the gem is already destroyed ($7EF5 negative), in which case
        ;   it does nothing.
        ;
        ; Modifies:
        ;   GEM_HP
        ; Clobbers: A""",
 'tm get': """        ; GET command: destroy Mondain's gem directly -- the true win gate.
        ;
        ; Behavior:
        ;   If the gem still stands ($95AB clear) and the player stands
        ;   adjacent to its cell (distance < 2 via .LA26E), set the victory
        ;   flag (INC $95AB), clear the gem sprite, and compute self-damage of
        ;   about 3/8 of PLR_HITS (the blast hurts the player), subtracting it
        ;   from PLR_HITS.  Print "The Gem is DESTROYED!"; if Mondain is
        ;   already dying (CUR_MON negative) chain straight into the victory
        ;   sequence.  Otherwise "...'tis nothing here!?!".
        ;
        ; Modifies:
        ;   $95AB (victory flag), PLR_HITS, DMG_AMT, CELL_STATE
        ; Clobbers: A, X, Y""",
 'tm inform': """        ; INFORM command: describe the scene to the player.
        ;
        ; Behavior:
        ;   If the gem is destroyed ($95AB set) print "Mondain's magical aura
        ;   doth seem substantially diminished in the absence of the gem.";
        ;   otherwise print "...it looks as if he is creating the evil gem?!"
        ;   (the high-bit text is the engine's inverse-video encoding).
        ;
        ; Clobbers: A, X, Y""",
 'tm misc cmds': """        ; The short stub command handlers: Quit, Ready, Steal, Transact, Ztats.
        ;
        ; Behavior:
        ;   Quit prints "is not allowed!" (no escape from the final battle);
        ;   Ready re-equips via READY_CMD then redraws; Steal and Transact are
        ;   refused in-character ("he's watching" / "Mondain will not
        ;   negotiate!"); Ztats shows the inventory (INVENTORY) and redraws the
        ;   craft.  Each is a separate entry reached through DISPATCH_TBL.
        ;
        ; Clobbers: A, X, Y""",
 'tm move': """        ; The four MOVE handlers (N/S/E/W) and the shared step routine.
        ;
        ; Behavior:
        ;   Each direction entry loads a signed (dx,dy) and falls into .L96CE,
        ;   which computes the destination cell = player pos +/- dir and reads
        ;   CELL_STATE (CELL_COL[row] base + column).  An empty cell walks the
        ;   player there (.L97BA); a force field ($03) prints "Blocked!"; any
        ;   other obstacle "Burned!" -- a field zaps the player for PLR_HITS/10
        ;   points with an XOR screen-flash (.L9791).  Stepping adjacent to
        ;   Mondain advances CUR_MON.
        ;
        ; Modifies:
        ;   ZP_PTR (player cell), PLR_HITS, CELL_STATE, CUR_MON
        ; Clobbers: A, X, Y""",
 'tm pass': """        ; PASS command and the end-of-turn tail.
        ;
        ; Behavior:
        ;   TM_PASS ticks the clock (TICK with Y=1, A=$10) and returns.
        ;   TURN_END runs the sound tick (TICK_SND) and drains the SFX queue
        ;   (SFX_DRAIN) before each of Mondain's turns.
        ;
        ; Clobbers: A, Y""",
 'tm idle': """        ; Idle keyboard poll, animated frame, and per-turn scene tick.
        ;
        ; Behavior:
        ;   IDLE_POLL spins ~$23 frames waiting for a key, animating each frame
        ;   via IDLE_FRAME (LA07B shape step + ACCEL_NUDGE + CURSOR_FLASH) and
        ;   returning the key (zero = none).  SCENE_TICK runs once per turn:
        ;   while the fight is idle it may print a "Your hear a strange
        ;   chanting" flavour line, and while Mondain's gem is regenerating it
        ;   heals GEM_HP toward 500 and cycles his sprite/CUR_MON state.
        ;
        ; Modifies:
        ;   GEM_HP, CUR_MON, CRAFT_GFX+6
        ; Clobbers: A, X, Y""",
 'tm mondain': """        ; MONDAIN_TURN: Mondain's AI -- choose melee, spell, or a step.
        ;
        ; Behavior:
        ;   By distance to the player (.L9D5C): adjacent -> MONDAIN_MELEE; at
        ;   mid range a 1/2 chance picks MONDAIN_CAST, else he steps; far ->
        ;   MONDAIN_STEP (a biased wander toward the player).  When his gem is
        ;   regenerating he heals GEM_HP by 5 per turn toward 500 and advances
        ;   his sprite/state.  MONDAIN_STEP moves him into an empty cell and
        ;   returns carry = blocked.  MONDAIN_CAST rolls one of three spells
        ;   from MONDAIN_SPELL_TBL and patches its dispatcher.
        ;
        ; Modifies:
        ;   GEM_HP, CUR_MON, CRAFT_GFX+6, $B628/$B629 (Mondain cell)
        ; Clobbers: A, X, Y""",
 'tm mondain spells': """        ; Mondain's three spells and the shared player-hit resolution.
        ;
        ; Behavior:
        ;   Magic missile (armour-gated hit, damage = (hits>>5)+RND_MOD($14)),
        ;   mind blaster ("Stats are reduced." -- drains each PLR_STR..PLR_INT
        ;   attribute), and psionic shock (a screen-flash plus shifted-hits
        ;   damage).  All converge on MONDAIN_HIT, which prints "Hit! N
        ;   damage", subtracts the 16-bit DMG_AMT from PLR_HITS, and jumps to
        ;   TM_DEATH if that would reach zero.
        ;
        ; Modifies:
        ;   PLR_HITS, PLR_STR..PLR_INT, DMG_AMT
        ; Clobbers: A, X, Y""",
 'tm death': """        ; TM_DEATH: the player's defeat ending.
        ;
        ; Behavior:
        ;   Print "THOU ART DEAD!", zero PLR_HITS, refresh the stats, and pop
        ;   up "Thou hast been defeated by Mondain the Wizard!  THE UNIVERSE IS
        ;   DOOMED!!" before restoring the window and jumping to RESPAWN.
        ;
        ; Modifies:
        ;   PLR_HITS
        ; Clobbers: A, X, Y""",
 'tm scene tick': """        ; Per-turn scene redraw plus the cell place/clear/draw helpers.
        ;
        ; Behavior:
        ;   .L9BDF, when Mondain is active, occasionally spawns a random
        ;   obstacle into an empty CELL_STATE cell and draws it.  The helper
        ;   block below (.L9C1F place, .L9C47 clear, .L9C64 / .L9C93 / .L9CB5 /
        ;   .L9CE4 draw/erase Mondain and the gem, .L9D15 the shape-into-cell
        ;   primitive) maintains the wireframe interior as pieces move.
        ;
        ; Modifies:
        ;   CELL_STATE, the scene shape arrays
        ; Clobbers: A, X, Y""",
 'tm dist': """        ; Distance and signed coordinate-delta helpers on the grid.
        ;
        ; Behavior:
        ;   .L9D5C returns in ZP_C3 the distance from the player cell (ZP_PTR)
        ;   to Mondain's cell ($B628/$B629), computed through the squared-sum
        ;   helper .LA26E.  .L9D74 and .L9D98 apply a signed step to Mondain's
        ;   cell, writing the new target into $B62C/$B62D and reading the
        ;   destination CELL_STATE.
        ;
        ; Outputs:
        ;   ZP_C3 = distance (.L9D5C); $B62C/$B62D = stepped cell, A = its state
        ; Clobbers: A, X, Y""",
 'tm craft redraw': """        ; CRAFT_REDRAW: redraw the whole wireframe interior scene.
        ;
        ; Behavior:
        ;   Clear the view, prime the shape walker (SHAPE_NEXT), save and zero
        ;   the active shape's bytes into REND_BSS, then sweep every grid cell
        ;   ($13 columns x 9 rows): wherever CELL_STATE holds a gem marker (2),
        ;   project its coordinates through PROJ_TBL into the shape pointers and
        ;   stroke it (.LA084).  Finally restore the saved shape bytes.
        ;
        ; Modifies:
        ;   REND_BSS, the shape pointer arrays
        ; Clobbers: A, X, Y""",
 'tm rend helpers': """        ; Renderer setup/clear helpers and the shape-pointer advance.
        ;
        ; Behavior:
        ;   NEGATE_SIGN returns a sign token ($01 / $81 / 0) for a value.
        ;   .L9E50 fills the $B400/$B500 row-coordinate scratch tables; .L9E6C
        ;   writes one byte into the active shape array (or fills it); .L9E95
        ;   resolves a shape's data pointer from SHAPE_TBL2; SHAPE_NEXT copies
        ;   the working NPC array (00D6) to/from the $B600 backing store and
        ;   advances the shape pointer to the next vertex list.
        ;
        ; Modifies:
        ;   $B400/$B500 tables, the shape pointer arrays, 00D6 scratch
        ; Clobbers: A, X, Y""",
 'tm shape step': """        ; The vector-shape stepper and hi-res line stroker.
        ;
        ; Behavior:
        ;   Walk a shape's (dx,dy,pen) vertex list from the self-modified
        ;   pointer ($B2), set up the per-row HGR pointers ($B8/$BB from the
        ;   $1200/$12C0 row tables), and plot each segment of the figure into
        ;   the hi-res page, honouring the pen byte (draw / skip / colour).
        ;   This is the stroker that renders the craft, Mondain, and the gem;
        ;   it dispatches the actual pixel work through BLIT_VEC.
        ;
        ; Clobbers: A, X, Y""",
 'tm blit': """        ; The three line/segment blitters BLIT_VEC selects among.
        ;
        ; Behavior:
        ;   .LA176 copies a run of bytes along a scan line (plot), .LA1C0 XOR-
        ;   merges a run (erase/flash), and the third entry advances to the
        ;   next vertex.  Each walks the HGR row pointers ($1200/$12C0 tables)
        ;   and writes into the hi-res page byte by byte; the shared tail
        ;   (.LA206) steps the run counters and fetches the next pen command.
        ;
        ; Clobbers: A, X, Y""",
 'tm cell helpers': """        ; Cell-state read/write helper (a hi-res address descrambler).
        ;
        ; Behavior:
        ;   Walk the hi-res page applying the BITMASK_TBL pixel masks: shift the
        ;   16-bit address (ZP_PTR) with an EOR #$B4 feedback (a Galois LFSR
        ;   walk of the page), derive the byte address (ZP_M0/M1) and pixel
        ;   column, and AND the mask into each touched byte.  Used to clear or
        ;   stipple the interior backdrop.
        ;
        ; Modifies:
        ;   ZP_PTR, ZP_M0/M1, the hi-res page
        ; Clobbers: A, X, Y""",
 'tm popup text': """        ; Popup-text trampolines and the gem-socket marker drawer.
        ;
        ; Behavior:
        ;   .LA436 frames a popup then prints inline text; .LA43C saves the
        ;   window, clears the view, and prints inline text without a frame --
        ;   both fall into MSG_PRINT so callers pass zero-terminated text in
        ;   line.  .LA44B draws one colored gem socket: set the color and
        ;   stroke three short lines from base X to make a small filled hole.
        ;
        ; Clobbers: A, X, Y""",
}


# --- prose blocks, keyed by the chunk they precede --------------------------
# The section opener is keyed by 'tm defines' (emitted before the defines
# chunk).  Other entries are 1-3 sentences of context before their chunk.
PROSE = {
 'tm defines': r"""\section{TM: the time machine and the final battle}
\label{ch:tm}

\texttt{TM} is the last overlay the engine ever loads --- the endgame. The
overworld's \texttt{CAS} chapter ends by setting \texttt{TM\_REVEAL} once the
space ace has rescued the princess; travelling to the time machine then loads
this file and jumps to [[TM_ENTRY]]. Everything here happens inside Mondain's
craft, face to face with the wizard himself, and winning here wins the whole
game.

The fight has one subtlety that the whole overlay is built around. Mondain is
shielded by his Gem of Immortality, modelled as a 16-bit hit-point counter
[[GEM_HP]] seeded to $1000$ on entry. Striking Mondain drains the gem, but
\emph{killing Mondain while the gem still stands does not win} --- the code
prints only `` \ldots or is he?'' and he regenerates. The player must first
\texttt{GET} the gem to destroy it (which sets the victory flag at [[$95AB]]
and weakens Mondain's aura), and \emph{then} reduce [[GEM_HP]] to zero. Only
that order triggers ``THOU ART VICTORIOUS!'', the \texttt{NIF} victory screen,
and the Control-RESET restart hook. The order of the two acts is the puzzle the
endgame poses.

Structurally the overlay is three things layered together: a small combat
engine (a turn loop, a command dispatcher, and Mondain's AI), a pseudo-3D
wireframe renderer that draws the craft interior and animates the figures on a
grid of cells, and the shared fixed-point and BCD math the rest of the file
leans on. It reuses the engine's calling conventions throughout ---
\texttt{MSG\_PRINT} for inline text, the \texttt{POPUP\_TEXT} trampolines for
framed narration, and \texttt{RND}/\texttt{RND\_MOD} for every roll.

\subsection{Arithmetic and number formatting}

The file opens with its math toolbox: the overlay entry point (a jump to
[[TM_ENTRY]]) sits in front of a set of shift-add multiply and restoring-divide
routines, followed by the binary-to-BCD converters the stats display uses to
print decimal numbers.""",

 'tm entry': r"""\subsection{Entering the craft}

[[TM_ENTRY]] is where the loader lands. It arms the boss fight --- seeding
[[GEM_HP]] to $1000$ and clearing [[CUR_MON]] --- draws the craft interior, and
runs the framed intro narration that establishes the four gem sockets and the
\textsc{launch} button.""",

 'tm launch': r"""The launch sequence is pure narration: three framed panels carry the player
from pressing the black \textsc{launch} button, through the journey ``through
time,'' to coming ``face to face with the evil Mondain himself.'' Each panel is
a \texttt{POPUP\_TEXT\_NF} call followed by [[POPUP_REDRAW]] and an
[[MON_CV]] bump to step down the screen.""",

 'tm scene setup': r"""With the narration done, the scene is built: Mondain and the Gem are placed as
cells on the small interior grid (their positions cached in
[[$B628]]/[[$B629]] and [[$B62A]]/[[$B62B]]), the victory flag at [[$95AB]] is
cleared, and Mondain's starting sprite/frame are written into [[CRAFT_GFX]]$+6$
and $+7$ before control falls into the turn loop.""",

 'tm main loop': r"""\subsection{The turn loop and command dispatch}

[[MAIN_LOOP]] is the heart of the fight. It is a classic Ultima command loop:
tick the scene, check for the player's death, wait (animating) for a key, and
dispatch the command through a jump table. The dispatch is a self-modified
\texttt{JSR}: the handler address is copied from [[DISPATCH_TBL]] over the
operand at [[DISPATCH_JSR]] each turn.""",

 'tm dispatch tbl': r"""[[DISPATCH_TBL]] is the command jump table, indexed by twice the command code.
Most commands route to [[QUERY_MARK]] (the ``Huh?'' beep); the live ones are
the four moves, Pass, Attack, Cast, Get, Inform, Quit, Ready, Steal, Transact,
Ztats, and the two sound-toggle controls.""",

 'tm attack': r"""\subsection{Attacking Mondain and his gem}

[[TM_ATTACK]] is the melee strike --- the bread-and-butter way to drain
[[GEM_HP]]. It checks for a sword-class weapon, makes the player face Mondain,
rolls to hit, and on success subtracts the damage from the gem. The interesting
part is the threshold logic at the bottom: as the gem crosses $500$ and then
$0$, Mondain's sprite changes and, once the gem is at zero \emph{and} the
victory flag is set, it runs the entire win sequence inline --- the
``THOU ART VICTORIOUS!'' popup, loading the \texttt{NIF} screen, hooking
Control-RESET, a screen-melt dissolve, and the [[STR_RESTART]] prompt --- then
hangs waiting for the reset.""",

 'tm cast': r"""\subsection{Spells}

[[TM_CAST]] mirrors the attack path for magic: it validates the readied spell
against [[OWNED_SPELLS]] and dispatches through [[TM_SPELL_TBL]] via another
self-modified jump ([[SPELL_JMP]]).""",

 'tm spell tbl': r"""[[TM_SPELL_TBL]] holds the eleven spell-handler addresses indexed by
[[READY_SPELL]]; most point at the not-applicable tail, with magic missile and
a handful of grid effects being the spells that actually do something here.""",

 'tm spell missile': r"""The one offensive spell that matters against the gem is magic missile: it rolls
damage from [[PLR_INT]], scales it by the readied weapon class, and feeds the
result into the same hit-resolution code [[TM_ATTACK]] uses.""",

 'tm spell kill': r"""The kill spell is a deliberate trap. Casting ``\texttt{INTERFICIO-NUNC!}'' at
Mondain --- the obvious thing to try --- backfires: it prints that the spell
makes him \emph{stronger} and doubles the remaining [[GEM_HP]]. The designers
are steering the player away from the brute-force solution and toward
destroying the gem.""",

 'tm get': r"""\subsection{Destroying the gem --- the win gate}

[[CMD_GET]] is the true solution to the puzzle. Standing adjacent to the gem
cell and issuing \texttt{Get} destroys it: the victory flag [[$95AB]] is set
(so a later kill actually wins), Mondain's aura is described as diminished, and
the blast costs the player a chunk of [[PLR_HITS]]. Only after this does
reducing [[GEM_HP]] to zero in [[TM_ATTACK]] produce victory rather than
`` \ldots or is he?''""",

 'tm move': r"""\subsection{Movement on the interior grid}

The four [[CMD_MOVE_N]]/\texttt{S}/\texttt{E}/\texttt{W} handlers all funnel
into one step routine. It resolves the destination cell, reads its
[[CELL_STATE]], and acts: an empty cell is walked into, a force field prints
``Blocked!'', and anything else burns the player for a tenth of their
[[PLR_HITS]] with a full-screen XOR flash. Walking next to Mondain wakes him
([[CUR_MON]] advances).""",

 'tm idle': r"""\subsection{Idle animation and Mondain's turn}

[[IDLE_POLL]] is what makes the scene feel alive between keystrokes: it polls
the keyboard for a few dozen frames, animating the wireframe each frame.
[[SCENE_TICK]] runs the per-turn upkeep --- flavour text and, crucially, the
gem's slow regeneration of [[GEM_HP]] while Mondain is recovering.""",

 'tm mondain': r"""[[MONDAIN_TURN]] is the wizard's AI. It chooses an action by distance to the
player: adjacent he attacks in melee, at middle range he may cast, and far away
he steps toward the player. His gem regenerates as he acts, healing [[GEM_HP]]
back toward $500$ and cycling his sprite state --- which is why the player must
keep up the pressure once the gem is destroyed.""",

 'tm mondain spell tbl': r"""[[MONDAIN_SPELL_TBL]] gives the three spells Mondain rolls between: magic
missile, mind blaster, and psionic shock.""",

 'tm mondain spells': r"""His three spells resolve through a common path. Magic missile and psionic shock
deal scaled damage; mind blaster instead drains the player's attributes. All
three converge on [[MONDAIN_HIT]], which subtracts the damage from [[PLR_HITS]]
and sends the player to [[TM_DEATH]] if it reaches zero.""",

 'tm death': r"""[[TM_DEATH]] is the losing ending --- ``THOU ART DEAD!'' and the popup that the
universe is doomed --- before the engine respawns the player.""",

 'tm scene tick': r"""\subsection{The renderer}

The remaining chunks draw the craft. The scene is a pseudo-3D wireframe of the
craft interior on a grid of cells; the helpers here place, clear, and redraw
the player, Mondain, and the gem as they move from cell to cell.""",

 'tm proj tbl': r"""[[PROJ_TBL]] holds the projection tables --- the screen X and Y of each grid
cell --- that turn a cell coordinate into a position in the pseudo-3D interior
view.""",

 'tm rend bss': r"""[[REND_BSS]] is the renderer's scratch area, stored zeroed on disk; the redraw
code saves and restores shape bytes through it.""",

 'tm shape step': r"""The vector-shape stepper is the core of the renderer: it walks a shape's
list of $(dx, dy, \mathrm{pen})$ vertices from a self-modified pointer and
strokes line segments into the hi-res page through the row-pointer tables. It is
what actually draws the craft, the wizard, and the gem.""",

 'tm blit vec': r"""[[BLIT_VEC]] is the three-entry jump table the stepper indexes by a shape's pen
mode to choose which blitter draws the next segment.""",

 'tm cell state': r"""[[CELL_STATE]] is the interior grid itself --- one byte per cell recording what
occupies it (empty, Mondain, the gem, or a force field) --- and [[CELL_COL]]
the per-row base offsets into it.""",

 'tm craft gfx': r"""\subsection{The shape data}

[[CRAFT_GFX]] is the vector-shape graphics blob: a pool of $(dx, dy,
\mathrm{pen})$ vertex lists, addressed by the shape stepper, that define the
craft interior, the Mondain figure, the gem, and the socket markers. To this
overlay it is opaque data, preserved verbatim.""",
}


def main():
    plated = Path('/tmp/tm_chunks.nw').read_text()
    blocks = re.split(r'^<<(.+?)>>=$', plated, flags=re.M)
    chunk_text = {}
    order = []
    it = iter(blocks[1:])
    for name, body in zip(it, it):
        chunk_text[name] = body.strip('\n').split('\n')
        order.append(name)

    # Inject the header plates right after each chunk's SUBROUTINE line.
    for name, plate in PLATE.items():
        body = chunk_text[name]
        for i, ln in enumerate(body):
            if ln.strip() == 'SUBROUTINE':
                chunk_text[name] = body[:i+1] + plate.split('\n') + body[i+1:]
                break
        else:
            raise SystemExit(f'no SUBROUTINE in chunk {name}')

    out = []
    out.append(PROSE['tm defines'])
    out.append('')
    out.append(build_defines())
    out.append(build_collection())
    for name in order:
        if name in PROSE:
            out.append(PROSE[name])
            out.append('')
        out.append(f'<<{name}>>=')
        out += chunk_text[name]
        out.append('')
    Path('/tmp/tm_section.nw').write_text('\n'.join(out) + '\n')
    print('wrote /tmp/tm_section.nw with', len(order), 'chunks,',
          len(PLATE), 'plates')


if __name__ == '__main__':
    main()
