#!/usr/bin/env python3
"""Generate the SPA overlay assembly from reference/spa.bin.

Twin of gen_cas.py / gen_twn.py: emits dasm-ready 6502 for a list of
(start,end) code regions, substituting spa_symmap/spa_labels for operands.
In-file branch/JSR targets that are not named become local labels .Lxxxx
(within one big SUBROUTINE scope). The only inline-arg JSR convention SPA uses
is MSG_PRINT ($8119) with inline zero-terminated text. SMC operand bytes get
`= *+N` anchor labels.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import dasm6502 as d

BASE = 0x8956
DATA = open(Path(__file__).parent.parent.parent / 'reference/spa.bin', 'rb').read()
END = BASE + len(DATA)

INLINE = {
    0x8119: ('text',),
}


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
                        elif spec == 'b':
                            i += 1
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


if __name__ == '__main__':
    print("module: import and use BASE/DATA/INLINE/collect_targets")
