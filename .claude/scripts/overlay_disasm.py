#!/usr/bin/env python3
"""Convention-aware disassembler for Ultima I overlay files.

Improves on dasm6502.py for the game overlays by:
  * consuming the inline arguments of the engine/MLIB JSR conventions
    (MSG_PRINT inline text, STR_NTH inline table pointer, MLIB paths,
    MENU_PICK 5-byte block, ITEM_LINE word) so the sweep stays aligned;
  * substituting known symbols (from a dasm .sym file, default
    output/miu1.sym) for operands;
  * rendering inline text as ASCII;
  * collecting branch/JSR/JMP targets inside the swept range and
    printing labels.

Usage:
    python .claude/scripts/overlay_disasm.py --file reference/out.bin \
        --base 8956 [--sym output/miu1.sym] START [END]

Inline-text caveat: a $7F (tab) inside MSG text takes a count byte;
the scan treats text as zero-terminated, which is correct because tab
counts are never zero.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dasm6502 as d  # opcode tables

# JSR targets with inline arguments. Value is a tuple of arg specs
# consumed in order: 'text' = zero-terminated text, 'w' = 16-bit word,
# 'b' = one byte.
INLINE_CONVENTIONS: dict[int, tuple[str, ...]] = {
    0x8119: ('text',),                  # MSG_PRINT
    0x8115: ('text',),                  # MSG_AT
    0x80B8: ('w',),                     # STR_NTH
    0x80B6: ('w',),                     # STR_FIRST
    0x80B1: ('w',),                     # STR_NTH_CAP
    0x87BB: ('w',),                     # ITEM_LINE
    0x87B8: ('w',),                     # ITEM_LINE_A
    0x84DF: ('b', 'w', 'w'),            # MENU_PICK: count, owned, names
    0xB703: ('text',),                  # MLIB_BLOAD
    0xB706: ('w', 'text'),              # MLIB_BLOAD_AT
    0xB709: ('w', 'w', 'text'),         # MLIB_BSAVE
    0xB70C: ('text',),                  # MLIB_BRUN
    0xB70F: ('text',),                  # MLIB_SET_PREFIX
    0xB715: ('w',),                     # MLIB_READ_BLOCK
    0xB718: ('w',),                     # MLIB_WRITE_BLOCK
    0xB71E: ('w',),                     # MLIB_BLOAD_P
    0xB721: ('w', 'w'),                 # MLIB_BLOAD_AT_P
    0xB724: ('w', 'w', 'w'),            # MLIB_BSAVE_P
    0xB727: ('w',),                     # MLIB_BRUN_P
    0xB72A: ('w',),                     # MLIB_SET_PREFIX_P
    0xB72D: ('text',),                  # MLIB_DESTROY
    0xB730: ('w',),                     # MLIB_DESTROY_P
    0xB733: ('text',),                  # MLIB_PARSE_PATH
    0xB736: ('w',),                     # MLIB_PARSE_PATH_P
}


def load_syms(path: str) -> dict[int, str]:
    syms: dict[int, str] = {}
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2 and not parts[0].startswith(('-', 'End', 'Symbol')):
            name = parts[0]
            if '.' in name:               # skip dasm local labels
                continue
            try:
                addr = int(parts[1], 16)
            except ValueError:
                continue
            syms.setdefault(addr, name)
    return syms


def ascii_render(bs: bytes) -> str:
    out = []
    for b in bs:
        c = b & 0x7F
        out.append(chr(c) if 0x20 <= c < 0x7F else f'<{b:02X}>')
    return ''.join(out)


def disassemble(data: bytes, base: int, start: int, end: int,
                syms: dict[int, str]) -> None:
    # Pass 1: sweep to collect instruction starts and targets.
    targets: set[int] = set()
    i = start - base
    starts: set[int] = set()
    while i < end - base and i < len(data):
        addr = base + i
        starts.add(addr)
        b = data[i]
        if b in d.ABSOLUTE and b in (0x20, 0x4C):
            t = data[i+1] | (data[i+2] << 8)
            if start <= t < end:
                targets.add(t)
            i += 3
            if b == 0x20 and t in INLINE_CONVENTIONS:
                for spec in INLINE_CONVENTIONS[t]:
                    if spec == 'text':
                        while i < len(data) and data[i] != 0:
                            i += 1
                        i += 1
                    elif spec == 'w':
                        i += 2
                    else:
                        i += 1
        elif b in d.BRANCH:
            off = data[i+1]
            t = addr + 2 + (off - 0x100 if off >= 0x80 else off)
            if start <= t < end:
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

    def sym(a16: int, suffix: str = '') -> str:
        if a16 in syms:
            return syms[a16] + suffix
        if a16 in targets:
            return f'L{a16:04X}{suffix}'
        return f'${a16:04X}{suffix}'

    # Pass 2: print.
    i = start - base
    while i < end - base and i < len(data):
        addr = base + i
        b = data[i]
        label = ''
        if addr in targets or addr in syms:
            label = f'{sym(addr)}:'
            print(label)

        def out(s: str, note: str = '') -> None:
            print(f'    {s:40s}; ${addr:04X}{note}')

        if b in d.IMPLIED:
            out(d.IMPLIED[b]); i += 1
        elif b in d.IMMEDIATE:
            out(f'{d.IMMEDIATE[b]} #${data[i+1]:02X}'); i += 2
        elif b in d.ZEROPAGE:
            out(f'{d.ZEROPAGE[b]} ${data[i+1]:02X}'); i += 2
        elif b in d.ZEROPAGE_X:
            out(f'{d.ZEROPAGE_X[b]} ${data[i+1]:02X},X'); i += 2
        elif b in d.ZEROPAGE_Y:
            out(f'{d.ZEROPAGE_Y[b]} ${data[i+1]:02X},Y'); i += 2
        elif b in d.ABSOLUTE:
            a16 = data[i+1] | (data[i+2] << 8)
            out(f'{d.ABSOLUTE[b]} {sym(a16)}')
            i += 3
            if b == 0x20 and a16 in INLINE_CONVENTIONS:
                for spec in INLINE_CONVENTIONS[a16]:
                    iaddr = base + i
                    if spec == 'text':
                        j = i
                        while j < len(data) and data[j] != 0:
                            j += 1
                        txt = data[i:j]
                        print(f'    .text "{ascii_render(txt)}",0'
                              f'{"":12s}; ${iaddr:04X} inline text')
                        i = j + 1
                    elif spec == 'w':
                        w = data[i] | (data[i+1] << 8)
                        print(f'    .word {sym(w):34s}; ${iaddr:04X} '
                              f'inline word')
                        i += 2
                    else:
                        print(f'    .byte ${data[i]:02X}{"":29s}; '
                              f'${iaddr:04X} inline byte')
                        i += 1
        elif b in d.ABSOLUTE_X:
            a16 = data[i+1] | (data[i+2] << 8)
            out(f'{d.ABSOLUTE_X[b]} {sym(a16, ",X")}'); i += 3
        elif b in d.ABSOLUTE_Y:
            a16 = data[i+1] | (data[i+2] << 8)
            out(f'{d.ABSOLUTE_Y[b]} {sym(a16, ",Y")}'); i += 3
        elif b in d.INDIRECT:
            a16 = data[i+1] | (data[i+2] << 8)
            out(f'JMP ({sym(a16)})'); i += 3
        elif b in d.INDIRECT_X:
            out(f'{d.INDIRECT_X[b]} (${data[i+1]:02X},X)'); i += 2
        elif b in d.INDIRECT_Y:
            out(f'{d.INDIRECT_Y[b]} (${data[i+1]:02X}),Y'); i += 2
        elif b in d.BRANCH:
            off = data[i+1]
            t = addr + 2 + (off - 0x100 if off >= 0x80 else off)
            note = '' if t in starts else '  *** target not an insn start'
            out(f'{d.BRANCH[b]} {sym(t)}', note); i += 2
        else:
            c = b & 0x7F
            ch = chr(c) if 0x20 <= c < 0x7F else ''
            out(f".byte ${b:02X}", f"  '{ch}'" if ch else '')
            i += 1


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--file', required=True)
    p.add_argument('--base', required=True)
    p.add_argument('--sym', default='output/miu1.sym')
    p.add_argument('start')
    p.add_argument('end', nargs='?')
    a = p.parse_args()
    base = d.parse_addr(a.base)
    start = d.parse_addr(a.start)
    data = Path(a.file).read_bytes()
    end = d.parse_addr(a.end) if a.end else base + len(data)
    syms = load_syms(a.sym)
    disassemble(data, base, start, end, syms)


if __name__ == '__main__':
    main()
