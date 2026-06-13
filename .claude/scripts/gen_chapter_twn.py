#!/usr/bin/env python3
"""Emit the complete TWN chapter .nw (chunks + SMC labels + defines + collection)."""
import sys
sys.path.insert(0, '/project/repo/.claude/scripts'); sys.path.insert(0, '/tmp')
import dasm6502 as d
import gen_twn as g
from twn_symmap import SYM as _SYM, ZP as _ZP, STATE as _STATE
from twn_labels import LBL
SYM = dict(_SYM); SYM.update(_ZP); SYM.update(_STATE)
DATA = g.DATA; BASE = g.BASE; INLINE = g.INLINE

# SMC operand sites: patch_operand_addr -> (label, insn_addr, plusN)
# SMC: operand_addr -> (label, insn_addr). The `= *+N` is planted at insn so
# the label resolves to its lowest patched operand byte; higher bytes are
# referenced as LABEL+k.
SMC_RAW = {
 0x89CD: ('MAP_SRC', 0x89CC), 0x89CE: ('MAP_SRC', 0x89CC),
 0x89D1: ('MAP_DST', 0x89CF),
 0x8A4E: ('DISP_OP', 0x8A4D), 0x8A4F: ('DISP_OP', 0x8A4D),
 0x9138: ('BUY_OP', 0x9137), 0x9139: ('BUY_OP', 0x9137),
 0x9158: ('SELL_OP', 0x9157), 0x9159: ('SELL_OP', 0x9157),
 0x918A: ('SHOPNM_OP', 0x9187), 0x918B: ('SHOPNM_OP', 0x9187),
 0x9466: ('WPRICE_OP', 0x9465), 0x9467: ('WPRICE_OP', 0x9465),
 0x97BD: ('HINT_OP', 0x97BC), 0x97BE: ('HINT_OP', 0x97BC),
 0xA1C6: ('DRAW_OP', 0xA1C5), 0xA1C7: ('DRAW_OP', 0xA1C5),
 0xA2A6: ('PROBE_OP', 0xA2A5), 0xA2A7: ('PROBE_OP', 0xA2A5),
 0x8F3A: ('PICK_TBL', 0x8F37), 0x8F3B: ('PICK_TBL', 0x8F37),
}
# anchor = lowest operand addr for each label
_anchor = {}
for opaddr, (lbl, insn) in SMC_RAW.items():
    _anchor[lbl] = min(opaddr, _anchor.get(lbl, opaddr))
_insn = {lbl: insn for opaddr, (lbl, insn) in SMC_RAW.items()}
SMC = {opaddr: (lbl, insn, opaddr - _anchor[lbl] + 1) for opaddr, (lbl, insn) in SMC_RAW.items()}
# Instruction-start addresses whose operand is self-modified (need `LABEL = *+1`).
SMC_INSN = {}
for lbl, insn in _insn.items():
    SMC_INSN.setdefault(insn, []).append((lbl, _anchor[lbl] - insn))

CODE = [(0x8956, 0x8A56), (0x8A8A, 0x8CFF), (0x8D0A, 0x8E5E), (0x8E78, 0xA50F)]
targets, starts = g.collect_targets(CODE)
labelnames = dict(LBL)


def smcname(a):
    if a in SMC and SMC[a][0]:
        lbl = SMC[a][0]
        off = a - _anchor[lbl]
        return lbl if off == 0 else lbl + f'+{off}'
    return None

def zpname(z):
    sm = smcname(z)
    if sm: return sm
    return SYM.get(z, f'${z:02X}')


def name(a16, suffix=''):
    sm = smcname(a16)
    if sm:
        return sm + suffix
    if a16 in SYM:
        return SYM[a16] + suffix
    if a16 in labelnames:
        return labelnames[a16] + suffix
    if a16 in targets:
        return f'.L{a16:04X}{suffix}'
    return f'${a16:04X}{suffix}'


DATA_SPANS = [(0x8A56, 0x8A8A, 'cmdtbl'), (0x8CFF, 0x8D0A, 'drophex'),
              (0x8E5E, 0x8E78, 'dropstr'), (0xA50F, 0xAA63, 'tail')]


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
    """Yield asm lines for a code range [start,end)."""
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
            # SMC operand of $FFFF stays as STALE_FFFF
            if a16 == 0xFFFF:
                o(f'{mn} STALE_FFFF' + (',X' if False else ''))
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
                        o(f'DC.W {name(w)}'); i += 2
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


if __name__ == '__main__':
    # quick self-test: emit whole code+data, assemble
    out = ['        PROCESSOR 6502', '        ORG $8956', 'TWN_ALL', '        SUBROUTINE']
    i = 0
    while i < len(DATA):
        addr = BASE + i
        span = next((s for s in DATA_SPANS if s[0] <= addr < s[1]), None)
        if span:
            s, e, k = span
            a = s
            while a < e:
                row = DATA[a-BASE:min(a-BASE+8, e-BASE)]
                out.append('        HEX ' + ''.join(f'{x:02x}' for x in row))
                a += len(row)
            i = e - BASE
            continue
        # find next data span or code end
        nxt = min([s[0] for s in DATA_SPANS if s[0] > addr] + [BASE+len(DATA)])
        out += emit_code(addr, nxt)
        i = nxt - BASE
    open('/tmp/chapter_test.asm', 'w').write('\n'.join(out) + '\n')
    print('self-test emitted', len(out), 'lines')
