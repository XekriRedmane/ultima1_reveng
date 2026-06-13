#!/usr/bin/env python3
"""Emit the complete SPA chapter assembly (one big SUBROUTINE) for byte-check.

Mirrors gen_chapter_cas.py. Produces /tmp/spa_all.asm which assembles to a
byte-perfect match against reference/spa.bin. The literate chunks in main.nw
are split out of this same emission by hand, keeping the SMC labels and data
spans identical.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import dasm6502 as d
import gen_spa as g
from spa_symmap import SYM as _SYM, ZP as _ZP, STATE as _STATE
from spa_labels import LBL
SYM = dict(_SYM); SYM.update(_ZP); SYM.update(_STATE)
DATA = g.DATA; BASE = g.BASE; INLINE = g.INLINE

# SMC operand sites: operand_addr -> (label, insn_addr).
SMC_RAW = {
 0x8AB1: ('DISP_OP', 0x8AB0), 0x8AB2: ('DISP_OP', 0x8AB0),
 0x9E9A: ('SHAPE_SMC', 0x9E99), 0x9E9B: ('SHAPE_SMC', 0x9E99),
 0x9F02: ('SHAPE_SMC2', 0x9F01), 0x9F03: ('SHAPE_SMC2', 0x9F01),
 0x9F0C: ('BLIT_EOR', 0x9F0B),
 0x9F0D: ('BLIT_OP', 0x9F0D),
 0x93D9: ('INFORM_JSR', 0x93D8), 0x93DA: ('INFORM_JSR', 0x93D8),
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
    (0x8C47, 0x8C4F, 'basegeom'),     # BASE_RADIUS / BASE_AXIS collision geometry
    (0x8F40, 0x8F4C, 'shiptbl'),      # SHIP_FUEL / SHIP_SHIELD per craft type
    (0x8FF4, 0x8FFC, 'thrust'),       # THRUST_DX / THRUST_DY deltas by heading
    (0x9046, 0x904E, 'retro'),        # RETRO_DX / RETRO_DY deltas by heading
    (0x91B6, 0x9207, 'scan_disp'),    # scan state + SCAN_CELLGLYPH + DISPATCH_TBL
    (0x9219, 0x9243, 'dirstr'),       # DIR_STR_FLIGHT names + tail bytes
    (0x9243, 0x9298, 'physbss'),      # physics/actor BSS band (zeroed on disk)
    (0x93DE, 0x93FE, 'speedstr'),     # DIR_STR_SPEED names + reticle scratch
    (0x9496, 0x9497, 'scantmo'),      # SCAN_TIMEOUT init byte
    (0x98F1, 0x98F2, 'hyperspd'),     # HYPER_SPEED storage byte
    (0x9BCA, 0x9C53, 'star_bss'),     # AI_FIXED + INFORM_TBL + starfield BSS
    (0x9C87, 0x9C92, 'gridoff'),      # GRID_ROW_OFF_DATA
    (0x9D87, 0x9D89, 'distidx'),      # DIST_A / DIST_B storage
    (0x9D9A, 0x9D9E, 'blitstor'),     # BLIT_SHAPE storage (stale $FF)
    (0x9F7D, 0x9F7F, 'shiftstor'),    # SHAPE_PRESHIFT scratch
    (0xA0FE, 0xA107, 'xport'),        # XPORT_FRAME / CRAFT_TYPE
    (0xA1CF, 0xB020, 'sprites'),      # all projection/sprite tables + pixel data
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
    0x8C47: 'BASE_RADIUS', 0x8C4B: 'BASE_AXIS',
    0x8F40: 'SHIP_FUEL', 0x8F46: 'SHIP_SHIELD',
    0x8FF4: 'THRUST_DX', 0x8FF8: 'THRUST_DY',
    0x9046: 'RETRO_DX', 0x904A: 'RETRO_DY',
    0x91B6: 'SCAN_GLYPH', 0x91B9: 'SCAN_CELLGLYPH', 0x91D3: 'DISPATCH_TBL',
    0x9219: 'DIR_STR_FLIGHT',
    0x9243: 'ENEMY_INIT_LO', 0x924D: 'ENEMY_INIT_HI', 0x9257: 'ACTOR_SHAPE',
    0x9261: 'ACTOR_HEAD', 0x926B: 'ACTOR_X', 0x9275: 'ACTOR_Y',
    0x927F: 'CELL_NW', 0x9287: 'RND_MOD', 0x9288: 'SHIP_X',
    0x928A: 'REL_X', 0x928C: 'DRAW_FLAG',
    0x93DE: 'DIR_STR_SPEED', 0x93F0: 'DRAW_MODE',
    0x9496: 'SCAN_TIMEOUT',
    0x9BCA: 'AI_FIXED', 0x9BCB: 'INFORM_TBL', 0x9BD3: 'INFORM_CODE',
    0x9BFF: 'STAR_X', 0x9C29: 'STAR_Y',
    0x9C87: 'GRID_ROW_OFF_DATA',
    0x9D87: 'DIST_A',
    0x9D9A: 'BLIT_SHAPE',
    0x9F7D: 'SHIFT_SCRATCH',
    0xA0FE: 'XPORT_FRAME', 0xA104: 'CRAFT_TYPE',
    0xA1CF: 'SHAPE_PTR_LO', 0xA1F3: 'SHAPE_PTR_HI',
    0xA217: 'SHAPE_XOFF', 0xA23B: 'SHAPE_YOFF', 0xA25F: 'SHAPE_WID',
    0xA283: 'SHAPE_DX', 0xA2A7: 'SHAPE_HGT', 0xA2CB: 'SHAPE_PIXELS',
}

# Auto-add every in-file SYM/STATE address that lands inside a data span and is
# referenced directly by code: it must carry a label so the HEX run breaks
# there and the operand resolves. (These are BSS/storage cells embedded in the
# data bands -- HEAD_CUR, BASE_X, SPEED, the reticle scratch, etc.)
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
        # In-file labels (code or data) are defined by chunk labels, not EQUs.
        if 0x8956 <= a < g.END:
            continue
        base_a = a - (int(nm.split('+')[1]) if '+' in nm else 0)
        equs.append(f'{base_nm} EQU ${base_a:04X}')
        seen.add(base_nm)
    out = ['        PROCESSOR 6502'] + equs + ['        ORG $8956', 'SPA_ALL', '        SUBROUTINE']
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
    open('/tmp/spa_all.asm', 'w').write('\n'.join(out) + '\n')
    print('self-test emitted', len(out), 'lines')
