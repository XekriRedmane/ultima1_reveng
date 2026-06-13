#!/usr/bin/env python3
"""Emit GEN literate chunks (noweb <<...>>= blocks) from the byte-perfect map.

Reuses gen_chapter_gen's emit_code/emit_data and label maps. Splits the file
into named chunks at the boundaries in CHUNKS below; each chunk gets an ORG
and its content, with @ %def listing the global labels it defines. Output goes
to /tmp/gen_chunks.nw for hand-merge into main.nw.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen_chapter_gen as G
import gen_gen as g

BASE = g.BASE
END = g.END

# (chunk_name, start_addr, end_addr_excl). Must tile $8956..END with no gaps.
CHUNKS = [
    ('gen entry',          0x8956, 0x8A5B),
    ('gen launch',         0x8A5B, 0x8AC3),
    ('gen chargen',        0x8AC3, 0x8C00),
    ('gen attr input',     0x8C00, 0x8C7E),
    ('gen pick race',      0x8C7E, 0x8D3C),
    ('gen pick sex',       0x8D3C, 0x8D98),
    ('gen pick class',     0x8D98, 0x8E54),
    ('gen pick name',      0x8E54, 0x8EEE),
    ('gen save',           0x8EEE, 0x8FB1),
    ('gen editor draw',    0x8FB1, 0x903F),
    ('gen chargen data',   0x903F, 0x90D7),
    ('gen format entry',   0x90D7, 0x91CB),
    ('gen vol check',      0x91CB, 0x933F),
    ('gen write voldir',   0x933F, 0x9388),
    ('gen text helpers',   0x9388, 0x93E3),
    ('gen rdblk data',     0x93E3, 0x93F7),
    ('gen border',         0x93F7, 0x9440),
    ('gen image data',     0x9440, 0xA119),
    ('gen format volume',  0xA119, 0xA189),
    ('gen fv paramblocks', 0xA189, 0xA198),
    ('gen fv write dir',   0xA198, 0xA20B),
    ('gen fv bitmap ptr',  0xA20B, 0xA20D),
    ('gen fv bitmap',      0xA20D, 0xA282),
    ('gen fv vectors',     0xA282, 0xA286),
    ('gen fv write block', 0xA286, 0xA290),
    ('gen fv wr3',         0xA290, 0xA296),
    ('gen fv init dir',    0xA296, 0xA2D7),
    ('gen fv remain',      0xA2D7, 0xA2D8),
    ('gen fv fill',        0xA2D8, 0xA3C5),
    ('gen boot image',     0xA3C5, 0xA7B7),
    ('gen rwts bss',       0xA7B7, 0xA800),
    ('gen rwts format',    0xA800, 0xAB37),
    ('gen rwts pad',       0xAB37, 0xAB3A),
    ('gen rwts delay',     0xAB3A, 0xAB4B),
    ('gen seek tables',    0xAB4B, 0xAB63),
    ('gen rwts verify',    0xAB63, 0xAC1F),
    ('gen rwts tail',      0xAC1F, END),
]


def is_data(addr):
    return any(s <= addr < e for (s, e, k) in G.DATA_SPANS)


def emit_range(start, end, add_subroutine=True):
    """Emit the [start,end) range, switching between code and data spans.

    If add_subroutine and the chunk begins with code, insert a SUBROUTINE
    directive after the first global label so .L locals are chunk-scoped.
    """
    lines = []
    i = start
    while i < end:
        span = next((sp for sp in G.DATA_SPANS if sp[0] <= i < sp[1]), None)
        if span:
            s, e, k = span
            seg_end = min(e, end)
            lines += G.emit_data(i, seg_end)
            i = seg_end
        else:
            nxt = min([sp[0] for sp in G.DATA_SPANS if sp[0] > i] + [end])
            lines += G.emit_code(i, nxt)
            i = nxt
    if add_subroutine and start not in [sp[0] for sp in G.DATA_SPANS]:
        # insert SUBROUTINE after the first non-empty label line
        for j, ln in enumerate(lines):
            if ln and not ln.startswith(' ') and '=' not in ln:
                lines.insert(j + 1, '        SUBROUTINE')
                break
    return lines


# Names that are already @ %def'd elsewhere in main.nw (the shared overlay
# entry label is declared once, in the miu1 bootstrap chunk).
DEFINED_ELSEWHERE = {'OVERLAY_ENTRY'}


def defs_in(start, end):
    names = []
    for a, nm in sorted(G.labelnames.items()):
        if start <= a < end and nm not in DEFINED_ELSEWHERE:
            names.append(nm)
    for a, nm in sorted(G.DATA_LABELS.items()):
        if (start <= a < end and nm not in names and '+' not in nm
                and nm not in DEFINED_ELSEWHERE):
            names.append(nm)
    return names


if __name__ == '__main__':
    # Verify the chunks tile the file.
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
            # split into lines of <= ~6 names
            for j in range(0, len(ds), 6):
                out.append('@ %def ' + ' '.join(ds[j:j+6]))
        else:
            out.append('@')
        out.append('')
    Path('/tmp/gen_chunks.nw').write_text('\n'.join(out) + '\n')
    print('emitted', len(CHUNKS), 'chunks,', len(out), 'lines to /tmp/gen_chunks.nw')
