#!/usr/bin/env python3
"""Generate the TWN overlay assembly code chunks from reference/twn.bin.

Emits dasm-ready 6502 for a list of (start,end) code regions, substituting
a caller-supplied symbol map for operands. Branch/JSR/JMP targets inside the
file that are not named become local labels .Lxxxx (within one big
SUBROUTINE scope so cross-region branches resolve). Inline-arg JSR
conventions (engine text/word, MLIB paths) are consumed and rendered.

Used once to author the TWN chapter; kept for reproducibility.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import dasm6502 as d

BASE = 0x8956
DATA = open(Path(__file__).parent.parent.parent / 'reference/twn.bin', 'rb').read()
END = BASE + len(DATA)

INLINE = {
    0x8119: ('text',), 0x8115: ('text',), 0x80B8: ('w',), 0x80B6: ('w',),
    0x80B1: ('w',), 0xB733: ('text',),
}

def ascii_render(bs: bytes) -> str:
    out = []
    for b in bs:
        c = b & 0x7F
        if b == 0x7F:
            out.append('<7F>')  # tab marker; handled specially below
        elif 0x20 <= c < 0x7F:
            ch = chr(c)
            if ch == '"':
                out.append('"')
            else:
                out.append(ch)
        else:
            out.append(f'<{b:02X}>')
    return ''.join(out)


def collect_targets(regions):
    targets = set()
    starts = set()
    for (start, end) in regions:
        i = start - BASE
        while i < end - BASE:
            addr = BASE + i
            starts.add(addr)
            b = DATA[i]
            if b in (0x20, 0x4C):
                t = DATA[i+1] | (DATA[i+2] << 8)
                if BASE <= t < END:
                    targets.add(t)
                i += 3
                if b == 0x20 and t in INLINE:
                    for spec in INLINE[t]:
                        if spec == 'text':
                            while DATA[i] != 0:
                                i += 1
                            i += 1
                        elif spec == 'w':
                            i += 2
                        else:
                            i += 1
            elif b in d.BRANCH:
                off = DATA[i+1]
                t = addr + 2 + (off - 0x100 if off >= 0x80 else off)
                if BASE <= t < END:
                    targets.add(t)
                i += 2
            elif b in d.IMPLIED:
                i += 1
            elif b in (d.IMMEDIATE | d.ZEROPAGE | d.ZEROPAGE_X | d.ZEROPAGE_Y
                       | d.INDIRECT_X | d.INDIRECT_Y):
                i += 2
            elif b in (d.ABSOLUTE | d.ABSOLUTE_X | d.ABSOLUTE_Y | d.INDIRECT):
                i += 3
            else:
                i += 1
    return targets, starts


def emit(regions, symmap, targets, starts, labelnames):
    """Yield assembly lines for the given code regions."""
    def sym(a16, suffix=''):
        if a16 in symmap:
            return symmap[a16] + suffix
        if a16 in labelnames:
            return labelnames[a16] + suffix
        if a16 in targets:
            return f'.L{a16:04X}{suffix}'
        return f'${a16:04X}{suffix}'

    lines = []
    for (start, end) in regions:
        i = start - BASE
        while i < end - BASE:
            addr = BASE + i
            b = DATA[i]
            if addr in labelnames and labelnames[addr].endswith(':'):
                pass
            if addr in targets and addr not in symmap:
                lines.append(f'.L{addr:04X}:' if addr not in labelnames
                             else f'{labelnames[addr]}:')
            def out(s):
                lines.append(f'        {s}')
            if b in d.IMPLIED:
                out(d.IMPLIED[b]); i += 1
            elif b in d.IMMEDIATE:
                out(f'{d.IMMEDIATE[b]} #${DATA[i+1]:02X}'); i += 2
            elif b in d.ZEROPAGE:
                out(f'{d.ZEROPAGE[b]} ${DATA[i+1]:02X}'); i += 2
            elif b in d.ZEROPAGE_X:
                out(f'{d.ZEROPAGE_X[b]} ${DATA[i+1]:02X},X'); i += 2
            elif b in d.ZEROPAGE_Y:
                out(f'{d.ZEROPAGE_Y[b]} ${DATA[i+1]:02X},Y'); i += 2
            elif b in d.ABSOLUTE:
                a16 = DATA[i+1] | (DATA[i+2] << 8)
                out(f'{d.ABSOLUTE[b]} {sym(a16)}'); i += 3
                if b == 0x20 and a16 in INLINE:
                    for spec in INLINE[a16]:
                        if spec == 'text':
                            j = i
                            while DATA[j] != 0:
                                j += 1
                            txt = DATA[i:j]
                            lines.append(f'        DC.B "{ascii_render(txt)}",0')
                            i = j + 1
                        elif spec == 'w':
                            w = DATA[i] | (DATA[i+1] << 8)
                            out(f'DC.W {sym(w)}'); i += 2
            elif b in d.ABSOLUTE_X:
                a16 = DATA[i+1] | (DATA[i+2] << 8)
                out(f'{d.ABSOLUTE_X[b]} {sym(a16, ",X")}'); i += 3
            elif b in d.ABSOLUTE_Y:
                a16 = DATA[i+1] | (DATA[i+2] << 8)
                out(f'{d.ABSOLUTE_Y[b]} {sym(a16, ",Y")}'); i += 3
            elif b in d.INDIRECT:
                a16 = DATA[i+1] | (DATA[i+2] << 8)
                out(f'JMP ({sym(a16)})'); i += 3
            elif b in d.INDIRECT_X:
                out(f'{d.INDIRECT_X[b]} (${DATA[i+1]:02X},X)'); i += 2
            elif b in d.INDIRECT_Y:
                out(f'{d.INDIRECT_Y[b]} (${DATA[i+1]:02X}),Y'); i += 2
            elif b in d.BRANCH:
                off = DATA[i+1]
                t = addr + 2 + (off - 0x100 if off >= 0x80 else off)
                out(f'{d.BRANCH[b]} {sym(t)}'); i += 2
            else:
                out(f'DC.B ${b:02X}'); i += 1
    return lines


if __name__ == '__main__':
    print("module: import and call emit()")
