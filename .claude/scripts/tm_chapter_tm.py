#!/usr/bin/env python3
"""Emit the complete TM chapter assembly (one big SUBROUTINE) for byte-check.

Mirrors gen_chapter_gen.py. Produces /tmp/tm_all.asm which must assemble to a
byte-perfect match against reference/tm.bin. The literate chunks in main.nw are
split out of this same emission by hand, keeping SMC labels and data spans
identical.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import dasm6502 as d
import tm_gen as g
from tm_symmap import SYM as _SYM, ZP as _ZP, STATE as _STATE, SCENE as _SCENE
from tm_labels import LBL
SYM = dict(_SYM); SYM.update(_ZP); SYM.update(_STATE); SYM.update(_SCENE)
DATA = g.DATA; BASE = g.BASE; INLINE = g.INLINE

# SMC operand sites: operand_addr -> (label, insn_addr).
SMC_RAW = {
 # patched-JSR dispatch: STA $8EA0 / STA $8EA1 patch the JSR operand at $8E9F.
 0x8EA0: ('DISPATCH_JSR', 0x8E9F), 0x8EA1: ('DISPATCH_JSR', 0x8E9F),
 # patched-JMP spell dispatch: STA $9247 / STA $9248 patch JMP operand at $9246.
 0x9247: ('SPELL_JMP', 0x9246), 0x9248: ('SPELL_JMP', 0x9246),
}
_anchor = {}
for opaddr, (lbl, insn) in SMC_RAW.items():
    _anchor[lbl] = min(opaddr, _anchor.get(lbl, opaddr))
_insn = {lbl: insn for opaddr, (lbl, insn) in SMC_RAW.items()}
SMC = {opaddr: (lbl, insn, opaddr - _anchor[lbl] + 1) for opaddr, (lbl, insn) in SMC_RAW.items()}
SMC_INSN = {}
for lbl, insn in _insn.items():
    SMC_INSN.setdefault(insn, []).append((lbl, _anchor[lbl] - insn))

# Data spans: (start, end, kind). Everything else is code.
DATA_SPANS = [
    (0x8A5D, 0x8A61, 'bcdwt'),        # BCD_WEIGHTS digit-weight table
    (0x8ACF, 0x8AD7, 'bcdwt2'),       # BCD_WEIGHTS2 + entry pad
    (0x8EA8, 0x8EDC, 'disp'),         # DISPATCH_TBL (26 words)
    (0x9150, 0x916F, 'restart'),      # "Press Control-RESET to restart." string
    (0x9249, 0x925F, 'spelltbl'),     # SPELL_TBL (11 words)
    (0x95AB, 0x95AC, 'gemgone'),      # GEM_GONE flag byte (1 byte BSS)
    (0x9826, 0x9827, 'idlecnt'),      # IDLE_CNT byte (1 byte BSS)
    (0x9843, 0x9844, 'animcnt'),      # ANIM_CNT byte (1 byte BSS)
    (0x9A0F, 0x9A15, 'mspelltbl'),    # MONDAIN_SPELL_TBL (3 words)
    (0x9D2A, 0x9D5C, 'sincoord'),     # coordinate/projection tables
    (0x9E31, 0x9E45, 'rbss1'),        # renderer BSS (zeros)
    (0x9EB3, 0x9EB5, 'shptbl'),       # 2-byte table read by LDA SHAPE_TBL2,X
    (0xA16E, 0xA174, 'blitvec'),      # 3-entry blitter jump-vector table
    (0xA2FC, 0xA3EE, 'gfx3'),         # renderer cell-state array + column table
    (0xA42E, 0xA436, 'bitmask'),      # bitmask table ff bf df ef f7 fb fd fe
    (0xA470, 0xA911, 'craftgfx'),     # gem-craft graphics blob
]

CODE = []
prev = BASE
for (s, e, k) in DATA_SPANS:
    if s > prev:
        CODE.append((prev, s))
    prev = e
if prev < g.END:
    CODE.append((prev, g.END))
targets, starts = g.collect_targets(CODE)
labelnames = dict(LBL)

DATA_LABELS = {
    0x8A5D: 'BCD_WEIGHTS', 0x8ACF: 'BCD_WEIGHTS2',
    0x8EA8: 'DISPATCH_TBL',
    0x9150: 'STR_RESTART',
    0x9249: 'TM_SPELL_TBL',
    0x95AB: 'GEM_GONE',
    0x9826: 'IDLE_CNT',
    0x9843: 'ANIM_CNT',
    0x9A0F: 'MONDAIN_SPELL_TBL',
    0x9D2A: 'PROJ_TBL',
    0x9E31: 'REND_BSS',
    0x9EB3: 'SHAPE_TBL2',
    0xA16E: 'BLIT_VEC',
    0xA2FC: 'CELL_STATE',
    0xA3E3: 'CELL_COL',
    0xA42E: 'BITMASK_TBL',
    0xA470: 'CRAFT_GFX',
}

for _a, _nm in SYM.items():
    if '+' in _nm:
        continue
    if not (BASE <= _a < g.END):
        continue
    if any(s <= _a < e for (s, e, k) in DATA_SPANS) and _a not in DATA_LABELS and _a not in LBL:
        DATA_LABELS[_a] = _nm


def smcname(a):
    if a in SMC and SMC[a][0]:
        lbl = SMC[a][0]
        off = a - _anchor[lbl]
        return lbl if off == 0 else lbl + f'+{off}'
    return None


def zpname(z):
    sm = smcname(z)
    if sm:
        return sm
    return SYM.get(z, f'${z:02X}')


def in_data_span(a16):
    return any(s <= a16 < e for (s, e, k) in DATA_SPANS)


def name(a16, suffix=''):
    sm = smcname(a16)
    if sm:
        return sm + suffix
    if a16 in SYM:
        return SYM[a16] + suffix
    if a16 in labelnames:
        return labelnames[a16] + suffix
    if a16 in DATA_LABELS:
        return DATA_LABELS[a16] + suffix
    if in_data_span(a16):
        base = max([la for la in DATA_LABELS if la <= a16], default=None)
        if base is not None and in_data_span(base):
            off = a16 - base
            return (DATA_LABELS[base] + (f'+{off}' if off else '')) + suffix
        return f'${a16:04X}{suffix}'
    if a16 in targets and a16 in starts:
        return f'.L{a16:04X}{suffix}'
    return f'${a16:04X}{suffix}'


def emit_text(bs):
    segs = []; cur = ''
    for b in bs:
        if 0x20 <= b < 0x7F and b != 0x22:
            cur += chr(b)
        else:
            if cur:
                segs.append('"' + cur + '"'); cur = ''
            segs.append(f'${b:02X}')
    if cur:
        segs.append('"' + cur + '"')
    segs.append('0')
    return 'DC.B ' + ','.join(segs)


def emit_code(start, end):
    lines = []
    i = start - BASE
    while i < end - BASE:
        addr = BASE + i
        b = DATA[i]
        if addr in labelnames:
            lines.append(f'{labelnames[addr]}')
        elif addr in targets:
            lines.append(f'.L{addr:04X}')
        if addr in SMC_INSN:
            for (lbl, n) in sorted(SMC_INSN[addr], key=lambda x: x[1]):
                lines.append(f'{lbl} = *+{n}')

        def o(s):
            lines.append(f'        {s}')
        if b in d.IMPLIED:
            o(d.IMPLIED[b].replace(' A', '')); i += 1
        elif b in d.IMMEDIATE:
            o(f'{d.IMMEDIATE[b]} #${DATA[i+1]:02X}'); i += 2
        elif b in d.ZEROPAGE:
            o(f'{d.ZEROPAGE[b]} {zpname(DATA[i+1])}'); i += 2
        elif b in d.ZEROPAGE_X:
            o(f'{d.ZEROPAGE_X[b]} {zpname(DATA[i+1])},X'); i += 2
        elif b in d.ZEROPAGE_Y:
            o(f'{d.ZEROPAGE_Y[b]} {zpname(DATA[i+1])},Y'); i += 2
        elif b in d.ABSOLUTE:
            a16 = DATA[i+1] | (DATA[i+2] << 8)
            mn = d.ABSOLUTE[b]
            o(f'{mn} {name(a16)}')
            i += 3
            if b == 0x20 and a16 in INLINE:
                for spec in INLINE[a16]:
                    if spec == 'text':
                        j = i
                        while DATA[j] != 0:
                            j += 1
                        lines.append('        ' + emit_text(DATA[i:j]))
                        i = j + 1
                    elif spec == 'w':
                        w = DATA[i] | (DATA[i+1] << 8)
                        lines.append(f'        DC.W {name(w)}')
                        i += 2
        elif b in d.ABSOLUTE_X:
            a16 = DATA[i+1] | (DATA[i+2] << 8)
            o(f'{d.ABSOLUTE_X[b]} {name(a16)},X'); i += 3
        elif b in d.ABSOLUTE_Y:
            a16 = DATA[i+1] | (DATA[i+2] << 8)
            o(f'{d.ABSOLUTE_Y[b]} {name(a16)},Y'); i += 3
        elif b in d.INDIRECT:
            a16 = DATA[i+1] | (DATA[i+2] << 8)
            o(f'JMP ({name(a16)})'); i += 3
        elif b in d.INDIRECT_X:
            o(f'{d.INDIRECT_X[b]} ({zpname(DATA[i+1])},X)'); i += 2
        elif b in d.INDIRECT_Y:
            o(f'{d.INDIRECT_Y[b]} ({zpname(DATA[i+1])}),Y'); i += 2
        elif b in d.BRANCH:
            off = DATA[i+1]
            t = addr + 2 + (off - 0x100 if off >= 0x80 else off)
            o(f'{d.BRANCH[b]} {name(t)}'); i += 2
        else:
            o(f'DC.B ${b:02X}'); i += 1
    return lines


def emit_data(s, e):
    lines = []
    a = s
    while a < e:
        nxt_lbl = min([la for la in DATA_LABELS if a < la < e] + [e])
        if a in DATA_LABELS:
            lines.append(DATA_LABELS[a])
        run_end = min(nxt_lbl, e)
        while a < run_end:
            row = DATA[a-BASE:min(a-BASE+8, run_end-BASE)]
            lines.append('        HEX ' + ''.join(f'{x:02x}' for x in row))
            a += len(row)
    return lines


if __name__ == '__main__':
    equs = []
    seen = set()
    for a, nm in sorted({**SYM}.items()):
        base_nm = nm.split('+')[0]
        if base_nm in seen:
            continue
        if 0x8956 <= a < g.END:
            continue
        base_a = a - (int(nm.split('+')[1]) if '+' in nm else 0)
        equs.append(f'{base_nm} EQU ${base_a:04X}')
        seen.add(base_nm)
    out = ['        PROCESSOR 6502'] + equs + ['        ORG $8956', 'TM_ALL', '        SUBROUTINE']
    i = 0
    while i < len(DATA):
        addr = BASE + i
        span = next((sp for sp in DATA_SPANS if sp[0] <= addr < sp[1]), None)
        if span:
            s, e, k = span
            out += emit_data(s, e)
            i = e - BASE
            continue
        nxt = min([sp[0] for sp in DATA_SPANS if sp[0] > addr] + [g.END])
        out += emit_code(addr, nxt)
        i = nxt - BASE
    open('/tmp/tm_all.asm', 'w').write('\n'.join(out) + '\n')
    print('self-test emitted', len(out), 'lines')
