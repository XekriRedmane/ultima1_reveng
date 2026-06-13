#!/usr/bin/env python3
"""Generate the GEN overlay assembly from reference/gen.bin.

Twin of gen_spa.py / gen_cas.py: emits dasm-ready 6502 for a list of
(start,end) code regions, substituting gen_symmap/gen_labels for operands.
In-file branch/JSR targets that are not named become local labels .Lxxxx
(within one big SUBROUTINE scope).

Inline-arg JSR conventions GEN uses:
  * MSG_PRINT ($8119) and MSG_AT ($8115): inline zero-terminated text.
  * PROMPT_LINE ($9388): a GEN-local trampoline that homes the cursor to
    the bottom prompt line and falls into MSG_PRINT -- also inline text.
  * STR_NTH_CAP ($80B1): one inline word (name-table pointer).
  * MLIB pointer paths $B721 (w,w) and $B724 (w,w,w): addr(+len) + path ptr.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import dasm6502 as d

BASE = 0x8956
DATA = open(Path(__file__).parent.parent.parent / 'reference/gen.bin', 'rb').read()
END = BASE + len(DATA)

INLINE = {
    0x8119: ('text',),          # MSG_PRINT
    0x8115: ('text',),          # MSG_AT
    0x9388: ('text',),          # PROMPT_LINE (GEN-local) -> MSG_PRINT
    0x80B1: ('w',),             # STR_NTH_CAP: inline name-table word
    0xB721: ('w', 'w'),         # MLIB_BLOAD_AT_P: addr, path ptr
    0xB724: ('w', 'w', 'w'),    # MLIB_BSAVE_P: addr, len, path ptr
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
