#!/usr/bin/env python3
"""Emit TM literate chunks (noweb <<...>>= blocks) from the byte-perfect map.

Reuses tm_chapter_tm's emit_code/emit_data and label maps. Splits the file into
named chunks at the boundaries in CHUNKS below; each chunk gets an ORG and its
content, with @ %def listing the global labels it defines. Output -> /tmp.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import tm_chapter_tm as T
import tm_gen as g

BASE = g.BASE
END = g.END

# (chunk_name, start_addr, end_addr_excl). Must tile $8956..END with no gaps.
CHUNKS = [
    ('tm mul',             0x8956, 0x89FE),  # OVERLAY_ENTRY + MUL8/MUL16/MUL16B/DIV16
    ('tm bcd',             0x89FE, 0x8AD7),  # BCD conversion helpers + weight tables
    ('tm entry',           0x8AD7, 0x8C25),  # TM_ENTRY: gem-socket setup + intro narration
    ('tm launch',          0x8C25, 0x8E07),  # the launch / time-travel narration sequence
    ('tm scene setup',     0x8E07, 0x8E5E),  # combat-scene setup (Mondain + gem cells)
    ('tm main loop',       0x8E5E, 0x8EA8),  # MAIN_LOOP + DISPATCH
    ('tm dispatch tbl',    0x8EA8, 0x8EDC),  # DISPATCH_TBL (26 words)
    ('tm attack',          0x8EDC, 0x91FB),  # CMD_ATTACK: strike Mondain / the gem
    ('tm cast',            0x91FB, 0x9249),  # CMD_CAST: spell dispatch
    ('tm spell tbl',       0x9249, 0x925F),  # SPELL_TBL (11 words)
    ('tm spell helpers',   0x925F, 0x92D9),  # spell range/target helpers + Not-applicable
    ('tm spell missile',   0x92D9, 0x934A),  # magic missile spell at Mondain
    ('tm spell band2',     0x934A, 0x9475),  # spells 7/8/9 (status/aura effects)
    ('tm spell kill',      0x9475, 0x94D6),  # spell 10: INTERFICIO-NUNC! (backfires)
    ('tm get',             0x94D6, 0x95AC),  # CMD_GET: attack the gem directly
    ('tm inform',          0x95AC, 0x963F),  # CMD_INFORM / examine
    ('tm misc cmds',       0x963F, 0x96B8),  # Quit/Ready/Steal/Transact/Ztats stubs
    ('tm move',            0x96B8, 0x9801),  # the four move handlers + collision
    ('tm pass',            0x9801, 0x9815),  # CMD_PASS + TURN_END
    ('tm idle',            0x9815, 0x98C1),  # IDLE_POLL / IDLE_FRAME / SCENE_TICK
    ('tm mondain',         0x98C1, 0x9A0F),  # MONDAIN_TURN: approach / melee / cast pick
    ('tm mondain spell tbl', 0x9A0F, 0x9A15),  # MONDAIN_SPELL_TBL (3 words)
    ('tm mondain spells',  0x9A15, 0x9B61),  # his 3 spells + hit/damage resolution
    ('tm death',           0x9B61, 0x9BDF),  # THOU ART DEAD / defeat ending
    ('tm scene tick',      0x9BDF, 0x9D2A),  # per-turn scene redraw + cell helpers
    ('tm proj tbl',        0x9D2A, 0x9D5C),  # PROJ_TBL projection/coordinate tables
    ('tm dist',            0x9D5C, 0x9DCB),  # distance / coordinate-delta helpers
    ('tm craft redraw',    0x9DCB, 0x9E31),  # CRAFT_REDRAW + scene draw entry
    ('tm rend bss',        0x9E31, 0x9E45),  # REND_BSS (renderer scratch)
    ('tm rend helpers',    0x9E45, 0x9EE5),  # renderer setup/clear helpers
    ('tm shape step',      0x9EE5, 0xA16E),  # vector-shape stepper + hi-res blitter
    ('tm blit vec',        0xA16E, 0xA174),  # BLIT_VEC jump table
    ('tm blit',            0xA174, 0xA2FC),  # the line/segment blitter routines
    ('tm cell state',      0xA2FC, 0xA3EE),  # CELL_STATE grid + CELL_COL column table
    ('tm cell helpers',    0xA3EE, 0xA436),  # cell-state read/write + BITMASK_TBL
    ('tm popup text',      0xA436, 0xA470),  # POPUP_TEXT trampoline + gem-socket drawer
    ('tm craft gfx',       0xA470, END),     # CRAFT_GFX graphics blob
]


def is_data(addr):
    return any(s <= addr < e for (s, e, k) in T.DATA_SPANS)


def emit_range(start, end, add_subroutine=True):
    lines = []
    i = start
    while i < end:
        span = next((sp for sp in T.DATA_SPANS if sp[0] <= i < sp[1]), None)
        if span:
            s, e, k = span
            seg_end = min(e, end)
            lines += T.emit_data(i, seg_end)
            i = seg_end
        else:
            nxt = min([sp[0] for sp in T.DATA_SPANS if sp[0] > i] + [end])
            lines += T.emit_code(i, nxt)
            i = nxt
    if add_subroutine and start not in [sp[0] for sp in T.DATA_SPANS]:
        for j, ln in enumerate(lines):
            if ln and not ln.startswith(' ') and '=' not in ln:
                lines.insert(j + 1, '        SUBROUTINE')
                break
    return lines


DEFINED_ELSEWHERE = {'OVERLAY_ENTRY'}


def defs_in(start, end):
    names = []
    for a, nm in sorted(T.labelnames.items()):
        if start <= a < end and nm not in DEFINED_ELSEWHERE:
            names.append(nm)
    for a, nm in sorted(T.DATA_LABELS.items()):
        if (start <= a < end and nm not in names and '+' not in nm
                and nm not in DEFINED_ELSEWHERE):
            names.append(nm)
    return names


if __name__ == '__main__':
    prev = BASE
    for (nm, s, e) in CHUNKS:
        assert s == prev, f'gap/overlap at {nm}: {s:04X} != {prev:04X}'
        prev = e
    assert prev == END, f'chunks end at {prev:04X}, file ends at {END:04X}'

    out = []
    for (nm, s, e) in CHUNKS:
        out.append(f'<<{nm}>>=')
        out.append(f'        ORG ${s:04X}')
        out += emit_range(s, e)
        ds = defs_in(s, e)
        if ds:
            for j in range(0, len(ds), 6):
                out.append('@ %def ' + ' '.join(ds[j:j+6]))
        else:
            out.append('@')
        out.append('')
    Path('/tmp/tm_chunks.nw').write_text('\n'.join(out) + '\n')
    print('emitted', len(CHUNKS), 'chunks to /tmp/tm_chunks.nw')
