#!/usr/bin/env python3
"""Emit the complete CAS chapter assembly (one big SUBROUTINE) for byte-check.

Mirrors gen_chapter_twn.py. Produces /tmp/cas_all.asm which assembles to a
byte-perfect match against reference/cas.bin. The literate chunks in main.nw
are split out of this same emission by hand, keeping the SMC labels and data
spans identical.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import dasm6502 as d
import gen_cas as g
from cas_symmap import SYM as _SYM, ZP as _ZP, STATE as _STATE
from cas_labels import LBL
SYM = dict(_SYM); SYM.update(_ZP); SYM.update(_STATE)
DATA = g.DATA; BASE = g.BASE; INLINE = g.INLINE

# SMC operand sites: operand_addr -> (label, insn_addr). The `= *+N` is planted
# at the instruction so the label resolves to its lowest patched operand byte;
# higher bytes are referenced as LABEL+k.
SMC_RAW = {
 0x89CF: ('MAP_SRC', 0x89CE), 0x89D0: ('MAP_SRC', 0x89CE),
 0x89D2: ('MAP_DST', 0x89D1), 0x89D3: ('MAP_DST', 0x89D1),
 0x8A57: ('DISP_OP', 0x8A56), 0x8A58: ('DISP_OP', 0x8A56),
 0x9084: ('PICK_ALPHA', 0x9081),
 0x90CF: ('PICK_TBL', 0x90CC), 0x90D0: ('PICK_TBL', 0x90CC),
 0x95CE: ('HINT_OP', 0x95CD), 0x95CF: ('HINT_OP', 0x95CD),
 0x97DC: ('DOOR_OP', 0x97DB), 0x97DD: ('DOOR_OP', 0x97DB),
 0x9B1A: ('DRAW_SRC', 0x9B19), 0x9B1B: ('DRAW_SRC', 0x9B19),
 0x9BF7: ('PROBE_OP', 0x9BF6), 0x9BF8: ('PROBE_OP', 0x9BF6),
}
_anchor = {}
for opaddr, (lbl, insn) in SMC_RAW.items():
    _anchor[lbl] = min(opaddr, _anchor.get(lbl, opaddr))
_insn = {lbl: insn for opaddr, (lbl, insn) in SMC_RAW.items()}
SMC = {opaddr: (lbl, insn, opaddr - _anchor[lbl] + 1) for opaddr, (lbl, insn) in SMC_RAW.items()}
SMC_INSN = {}
for lbl, insn in _insn.items():
    SMC_INSN.setdefault(insn, []).append((lbl, _anchor[lbl] - insn))

# Code regions (everything that is not a data span).
CODE = [(0x8956, 0x8A5F), (0x8A93, 0x8E9B), (0x8EA7, 0x8FF3), (0x900D, 0x9E24)]
targets, starts = g.collect_targets(CODE)
labelnames = dict(LBL)
# PICK_CNT is a self-modified storage byte that sits in the code stream just
# past DROP_PICK's RTS (a dead ASL opcode used as a counter cell).
labelnames[0x90D3] = 'PICK_CNT'

# Data spans: (start, end, kind).
DATA_SPANS = [
    (0x8A5F, 0x8A93, 'cmdtbl'),
    (0x8E9B, 0x8EA7, 'dropdisp'),
    (0x8FF3, 0x900D, 'dropstr'),
    (0x95D6, 0x95DE, 'hinttbl'),
    (0x9E24, 0x9EEA, 'tail'),
]


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
                        o(f'DC.W {name(w)}'); i += 2
                    elif spec == 'b':
                        o(f'DC.B ${DATA[i]:02X}'); i += 1
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


# Labels emitted inside data spans (start an 8-byte HEX run fresh).
DATA_LABELS = {
    0x8A5F: 'CMD_TBL', 0x8E9B: 'DROP_KEYS', 0x8E9F: 'DROP_JMP',
    0x8FF3: 'DROP_STRINGS', 0x9E3F: 'STR_NPCS', 0x9E63: 'STR_PRINCESS',
    0x9EA8: 'MAP_ROW_LO', 0x9EBA: 'MAP_ROW_HI', 0x9ECC: 'WEAPON_HITKIND',
    0x9EDC: 'NPC_GLYPH', 0x9EE2: 'CASTLE_COL',
}


def emit_data(s, e):
    lines = []
    # GEM_HINT_TBL: a word table of in-file handler addresses.
    if s == 0x95D6:
        lines.append('GEM_HINT_TBL')
        a = s
        while a < e:
            w = DATA[a-BASE] | (DATA[a-BASE+1] << 8)
            lines.append(f'        DC.W {name(w)}')
            a += 2
        return lines
    a = s
    while a < e:
        # break a HEX run at any labeled boundary
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
    # EQU block for all external (non-in-file) symbols referenced by operands.
    equs = ['STALE_FFFF EQU $FFFF']
    seen = set()
    for a, nm in sorted({**SYM}.items()):
        base_nm = nm.split('+')[0]
        if base_nm in seen:
            continue
        # In-file data-table labels ($9E3F..end) are emitted as labels by the
        # tail data chunk, so don't EQU them. Everything else that lands inside
        # the file but is NOT an emitted code/data label (the BSS band
        # $9E24-$9E3E) gets an EQU here.
        if 0x9E3F <= a < 0x9EEA:
            continue  # named data table — labeled in the tail chunk
        if 0x8956 <= a < 0x9E24:
            continue  # in-file code label, defined by a chunk label
        # strip any +N offset: define the base address
        base_a = a - (int(nm.split('+')[1]) if '+' in nm else 0)
        equs.append(f'{base_nm} EQU ${base_a:04X}')
        seen.add(base_nm)
    out = ['        PROCESSOR 6502'] + equs + ['        ORG $8956', 'CAS_ALL', '        SUBROUTINE']
    i = 0
    while i < len(DATA):
        addr = BASE + i
        span = next((sp for sp in DATA_SPANS if sp[0] <= addr < sp[1]), None)
        if span:
            s, e, k = span
            out += emit_data(s, e)
            i = e - BASE
            continue
        nxt = min([sp[0] for sp in DATA_SPANS if sp[0] > addr] + [BASE+len(DATA)])
        out += emit_code(addr, nxt)
        i = nxt - BASE
    open('/tmp/cas_all.asm', 'w').write('\n'.join(out) + '\n')
    print('self-test emitted', len(out), 'lines')
