#!/usr/bin/env python3
"""Emit the complete GEN chapter assembly (one big SUBROUTINE) for byte-check.

Mirrors gen_chapter_spa.py. Produces /tmp/gen_all.asm which assembles to a
byte-perfect match against reference/gen.bin. The literate chunks in main.nw
are split out of this same emission by hand, keeping the SMC labels and data
spans identical.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import dasm6502 as d
import gen_gen as g
from gen_symmap import SYM as _SYM, ZP as _ZP, STATE as _STATE
from gen_labels import LBL
SYM = dict(_SYM); SYM.update(_ZP); SYM.update(_STATE)
DATA = g.DATA; BASE = g.BASE; INLINE = g.INLINE

# SMC operand sites: operand_addr -> (label, insn_addr).
SMC_RAW = {
 0x8A5C: ('DECRYPT_SRC', 0x8A5B), 0x8A5D: ('DECRYPT_SRC', 0x8A5B),
 0x8A5F: ('DECRYPT_PTR', 0x8A5E), 0x8A60: ('DECRYPT_PTR', 0x8A5E),
 0x8A84: ('COPY_SRC', 0x8A82),
 0x8A87: ('COPY_DST', 0x8A85),
 0x8B02: ('CLEAR_SRC', 0x8B01), 0x8B03: ('CLEAR_SRC', 0x8B01),
 0x8B05: ('CLEAR_DST', 0x8B04), 0x8B06: ('CLEAR_DST', 0x8B04),
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
    (0x903F, 0x904F, 'cgcount'),      # POINT_POOL/CURSOR_IDX/NAME_LEN + STR_SEX + SAVE_SIG
    (0x904F, 0x90D7, 'template'),     # PLR_TEMPLATE default player-state block
    (0x93E3, 0x93F7, 'rdblk'),        # READ_BLOCK paramblock + zp-save scratch
    (0x9440, 0xA119, 'image'),        # GAME_IMAGE 13-page $6000 init image (data)
    (0xA189, 0xA198, 'fvpb12'),       # FV saved-A2 + WRITE_BLOCK paramblocks #1/#2
    (0xA20B, 0xA20D, 'fvbm'),         # FV_BMPTR bitmap pointer
    (0xA276, 0xA277, 'fvpad'),        # pad after JMP ($A284)
    (0xA282, 0xA286, 'fvdrv'),        # drive mask + track + JMP vector
    (0xA290, 0xA296, 'fvpb3'),        # WRITE_BLOCK paramblock #3 + counter
    (0xA2D7, 0xA2D8, 'fvrem'),        # sector remainder scratch
    (0xA3C5, 0xA7B7, 'bootimg'),      # embedded ProDOS boot-loader disk image (data)
    (0xA7B7, 0xA800, 'rwbss'),        # formatter BSS + PRO param block
    (0xAB37, 0xAB3A, 'rwpad'),        # pad before RW_WRITE_DELAY
    (0xAB4B, 0xAB63, 'seekdly'),      # two seek phase-delay tables
    (0xAC1F, 0xAC3A, 'rwtail'),       # format geometry + RWTS BSS scratch tail
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

# Storage-byte labels emitted inside data spans (start an 8-byte HEX run fresh).
DATA_LABELS = {
    0x903F: 'POINT_POOL', 0x9041: 'CURSOR_IDX', 0x9042: 'NAME_LEN',
    0x9043: 'STR_SEX', 0x904D: 'SAVE_SIG',
    0x904F: 'PLR_TEMPLATE',
    0x93E3: 'RDBLK_PARAM', 0x93E4: 'FMT_UNIT', 0x93E9: 'ZP_SAVE',
    0x9440: 'GAME_IMAGE',
    0xA189: 'FV_SAVED_A2', 0xA18B: 'FV_DIRBLK', 0xA18C: 'FV_WR1', 0xA192: 'FV_WR2',
    0xA20B: 'FV_BMPTR',
    0xA282: 'FV_DRVMASK', 0xA283: 'FV_TRACK', 0xA284: 'FV_VECTOR',
    0xA290: 'FV_WR3', 0xA294: 'FV_WRCNT',
    0xA2D7: 'FV_REMAIN',
    0xA3C5: 'BOOT_IMAGE',
    0xA7B7: 'RW_BSS', 0xA7C7: 'PRO_PARAM',
    0xAB4B: 'SEEK_DELAY_A', 0xAB57: 'SEEK_DELAY_B',
    0xAC1F: 'FMT_GEOM', 0xAC23: 'RW_DRVSEL', 0xAC24: 'RW_HALFTRK',
    0xAC25: 'RW_RETRY', 0xAC26: 'RW_SECMAP', 0xAC36: 'RW_SWIDX', 0xAC38: 'RW_SEEKDLT',
}

# Auto-add every in-file SYM/STATE address that lands inside a data span and is
# referenced directly by code: it must carry a label so the HEX run breaks
# there and the operand resolves.
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
    # A target that resolves into a named data span maps to that label + offset.
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
            if a16 == 0xFFFF:
                o(f'{mn} STALE_FFFF')
            else:
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
            tgt = 'STALE_FFFF' if a16 == 0xFFFF else name(a16)
            o(f'{d.ABSOLUTE_X[b]} {tgt},X'); i += 3
        elif b in d.ABSOLUTE_Y:
            a16 = DATA[i+1] | (DATA[i+2] << 8)
            tgt = 'STALE_FFFF' if a16 == 0xFFFF else name(a16)
            o(f'{d.ABSOLUTE_Y[b]} {tgt},Y'); i += 3
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
    equs = ['STALE_FFFF EQU $FFFF']
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
    out = ['        PROCESSOR 6502'] + equs + ['        ORG $8956', 'GEN_ALL', '        SUBROUTINE']
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
    open('/tmp/gen_all.asm', 'w').write('\n'.join(out) + '\n')
    print('self-test emitted', len(out), 'lines')
