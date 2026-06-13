#!/usr/bin/env python3
"""Tiny 6502 emulator scoped to the MAKE.INDATA decompressor.

Rather than hand-translate the tricky backward-branch control flow of the
$1E03/$1E47 decompressor, we run the actual code bytes on a small 6502 core.
The decompressor only touches zero page, the hi-res page ($2000-$3FFF), and
reads its input stream through the ($00) pointer -- all of which live in a
flat 64K memory image we preload from the reference binary.

Usage:
    from makeindata_emu import decompress_at
    raster = decompress_at(src_addr)   # returns the $2000-$3FFF bytes (0x2000 len)
"""

REF = None


def load_ref():
    global REF
    if REF is None:
        REF = open('reference/makeindata.bin', 'rb').read()
    return REF


class CPU:
    def __init__(self, mem):
        self.m = mem
        self.A = self.X = self.Y = 0
        self.SP = 0xFF
        self.PC = 0
        self.C = self.Z = self.N = self.V = 0
        self.steps = 0

    def push(self, v):
        self.m[0x100 + self.SP] = v & 0xFF
        self.SP = (self.SP - 1) & 0xFF

    def pop(self):
        self.SP = (self.SP + 1) & 0xFF
        return self.m[0x100 + self.SP]

    def setzn(self, v):
        v &= 0xFF
        self.Z = 1 if v == 0 else 0
        self.N = 1 if v & 0x80 else 0
        return v

    def rd(self, a):
        return self.m[a & 0xFFFF]

    def wr(self, a, v):
        self.m[a & 0xFFFF] = v & 0xFF

    def run(self, start, stop_sp=0xFF):
        """Run from `start` as a subroutine; stop when an RTS pops the SP back
        above the entry level (i.e. the entry RTS returns)."""
        self.PC = start
        entry_sp = self.SP
        while True:
            self.steps += 1
            if self.steps > 50_000_000:
                raise RuntimeError("runaway")
            op = self.rd(self.PC)
            self.PC = (self.PC + 1) & 0xFFFF
            done = self.exec(op, entry_sp)
            if done:
                return

    def imm(self):
        v = self.rd(self.PC); self.PC = (self.PC + 1) & 0xFFFF; return v

    def addr_abs(self):
        lo = self.rd(self.PC); hi = self.rd(self.PC + 1)
        self.PC = (self.PC + 2) & 0xFFFF
        return lo | (hi << 8)

    def addr_zp(self):
        return self.imm()

    def branch(self, cond):
        off = self.imm()
        if cond:
            if off >= 0x80:
                off -= 0x100
            self.PC = (self.PC + off) & 0xFFFF

    def exec(self, op, entry_sp):
        m = self.m
        # --- loads/stores ---
        if op == 0xA9:  # LDA #
            self.A = self.setzn(self.imm())
        elif op == 0xA2:  # LDX #
            self.X = self.setzn(self.imm())
        elif op == 0xA6:  # LDX zp
            self.X = self.setzn(self.rd(self.addr_zp()))
        elif op == 0xA4:  # LDY zp
            self.Y = self.setzn(self.rd(self.addr_zp()))
        elif op == 0xAE:  # LDX abs
            self.X = self.setzn(self.rd(self.addr_abs()))
        elif op == 0x9D:  # STA abs,X
            self.wr((self.addr_abs() + self.X) & 0xFFFF, self.A)
        elif op == 0xA0:  # LDY #
            self.Y = self.setzn(self.imm())
        elif op == 0xA5:  # LDA zp
            self.A = self.setzn(self.rd(self.addr_zp()))
        elif op == 0xAD:  # LDA abs
            self.A = self.setzn(self.rd(self.addr_abs()))
        elif op == 0xBD:  # LDA abs,X
            self.A = self.setzn(self.rd((self.addr_abs() + self.X) & 0xFFFF))
        elif op == 0xB1:  # LDA (zp),Y
            zp = self.addr_zp()
            ptr = self.rd(zp) | (self.rd((zp + 1) & 0xFF) << 8)
            self.A = self.setzn(self.rd((ptr + self.Y) & 0xFFFF))
        elif op == 0xA1:  # LDA (zp,X)
            zp = (self.addr_zp() + self.X) & 0xFF
            ptr = self.rd(zp) | (self.rd((zp + 1) & 0xFF) << 8)
            self.A = self.setzn(self.rd(ptr))
        elif op == 0x85:  # STA zp
            self.wr(self.addr_zp(), self.A)
        elif op == 0x8D:  # STA abs
            self.wr(self.addr_abs(), self.A)
        elif op == 0x91:  # STA (zp),Y
            zp = self.addr_zp()
            ptr = self.rd(zp) | (self.rd((zp + 1) & 0xFF) << 8)
            self.wr((ptr + self.Y) & 0xFFFF, self.A)
        elif op == 0x86:  # STX zp
            self.wr(self.addr_zp(), self.X)
        elif op == 0x84:  # STY zp
            self.wr(self.addr_zp(), self.Y)
        elif op == 0x8E:  # STX abs
            self.wr(self.addr_abs(), self.X)
        elif op == 0x8C:  # STY abs
            self.wr(self.addr_abs(), self.Y)
        elif op == 0x81:  # STA (zp,X)
            zp = (self.addr_zp() + self.X) & 0xFF
            ptr = self.rd(zp) | (self.rd((zp + 1) & 0xFF) << 8)
            self.wr(ptr, self.A)
        elif op == 0x95:  # STA zp,X
            self.wr((self.addr_zp() + self.X) & 0xFF, self.A)
        elif op == 0xB5:  # LDA zp,X
            self.A = self.setzn(self.rd((self.addr_zp() + self.X) & 0xFF))
        elif op == 0xB9:  # LDA abs,Y
            self.A = self.setzn(self.rd((self.addr_abs() + self.Y) & 0xFFFF))
        elif op == 0x99:  # STA abs,Y
            self.wr((self.addr_abs() + self.Y) & 0xFFFF, self.A)
        # --- inc/dec ---
        elif op == 0xE6:  # INC zp
            a = self.addr_zp(); self.wr(a, self.setzn(self.rd(a) + 1))
        elif op == 0xC6:  # DEC zp
            a = self.addr_zp(); self.wr(a, self.setzn(self.rd(a) - 1))
        elif op == 0xEE:  # INC abs
            a = self.addr_abs(); self.wr(a, self.setzn(self.rd(a) + 1))
        elif op == 0xCE:  # DEC abs
            a = self.addr_abs(); self.wr(a, self.setzn(self.rd(a) - 1))
        elif op == 0xC8:  # INY
            self.Y = self.setzn(self.Y + 1)
        elif op == 0x88:  # DEY
            self.Y = self.setzn(self.Y - 1)
        elif op == 0xE8:  # INX
            self.X = self.setzn(self.X + 1)
        elif op == 0xCA:  # DEX
            self.X = self.setzn(self.X - 1)
        # --- transfers ---
        elif op == 0xAA:  # TAX
            self.X = self.setzn(self.A)
        elif op == 0xA8:  # TAY
            self.Y = self.setzn(self.A)
        elif op == 0x8A:  # TXA
            self.A = self.setzn(self.X)
        elif op == 0x98:  # TYA
            self.A = self.setzn(self.Y)
        # --- compares ---
        elif op == 0xC9:  # CMP #
            v = self.imm(); r = (self.A - v) & 0xFF
            self.C = 1 if self.A >= v else 0; self.setzn(r)
        elif op == 0xC5:  # CMP zp
            v = self.rd(self.addr_zp()); r = (self.A - v) & 0xFF
            self.C = 1 if self.A >= v else 0; self.setzn(r)
        elif op == 0xE0:  # CPX #
            v = self.imm(); r = (self.X - v) & 0xFF
            self.C = 1 if self.X >= v else 0; self.setzn(r)
        elif op == 0xC0:  # CPY #
            v = self.imm(); r = (self.Y - v) & 0xFF
            self.C = 1 if self.Y >= v else 0; self.setzn(r)
        # --- logic/shift on A ---
        elif op == 0x29:  # AND #
            self.A = self.setzn(self.A & self.imm())
        elif op == 0x09:  # ORA #
            self.A = self.setzn(self.A | self.imm())
        elif op == 0x49:  # EOR #
            self.A = self.setzn(self.A ^ self.imm())
        elif op == 0x0A:  # ASL A
            self.C = (self.A >> 7) & 1; self.A = self.setzn((self.A << 1) & 0xFF)
        elif op == 0x4A:  # LSR A
            self.C = self.A & 1; self.A = self.setzn(self.A >> 1)
        elif op == 0x2A:  # ROL A
            c = self.C; self.C = (self.A >> 7) & 1
            self.A = self.setzn(((self.A << 1) | c) & 0xFF)
        elif op == 0x6A:  # ROR A
            c = self.C; self.C = self.A & 1
            self.A = self.setzn((self.A >> 1) | (c << 7))
        # --- shift/rotate memory zp ---
        elif op == 0x06:  # ASL zp
            a = self.addr_zp(); v = self.rd(a)
            self.C = (v >> 7) & 1; self.wr(a, self.setzn((v << 1) & 0xFF))
        elif op == 0x46:  # LSR zp
            a = self.addr_zp(); v = self.rd(a)
            self.C = v & 1; self.wr(a, self.setzn(v >> 1))
        elif op == 0x26:  # ROL zp
            a = self.addr_zp(); v = self.rd(a); c = self.C
            self.C = (v >> 7) & 1; self.wr(a, self.setzn(((v << 1) | c) & 0xFF))
        elif op == 0x66:  # ROR zp
            a = self.addr_zp(); v = self.rd(a); c = self.C
            self.C = v & 1; self.wr(a, self.setzn((v >> 1) | (c << 7)))
        # --- flags ---
        elif op == 0x18:  # CLC
            self.C = 0
        elif op == 0x38:  # SEC
            self.C = 1
        # --- branches ---
        elif op == 0xD0:  # BNE
            self.branch(self.Z == 0)
        elif op == 0xF0:  # BEQ
            self.branch(self.Z == 1)
        elif op == 0x30:  # BMI
            self.branch(self.N == 1)
        elif op == 0x10:  # BPL
            self.branch(self.N == 0)
        elif op == 0x90:  # BCC
            self.branch(self.C == 0)
        elif op == 0xB0:  # BCS
            self.branch(self.C == 1)
        # --- jumps/calls ---
        elif op == 0x4C:  # JMP abs
            self.PC = self.addr_abs()
        elif op == 0x20:  # JSR
            target = self.addr_abs()
            ret = (self.PC - 1) & 0xFFFF
            self.push(ret >> 8); self.push(ret & 0xFF)
            self.PC = target
        elif op == 0x60:  # RTS
            if self.SP == entry_sp:
                return True  # entry routine returned
            lo = self.pop(); hi = self.pop()
            self.PC = ((hi << 8) | lo) + 1 & 0xFFFF
        elif op == 0x24:  # BIT zp
            v = self.rd(self.addr_zp())
            self.Z = 1 if (self.A & v) == 0 else 0
            self.N = (v >> 7) & 1; self.V = (v >> 6) & 1
        elif op == 0x2C:  # BIT abs
            v = self.rd(self.addr_abs())
            self.Z = 1 if (self.A & v) == 0 else 0
            self.N = (v >> 7) & 1; self.V = (v >> 6) & 1
        elif op == 0x48:  # PHA
            self.push(self.A)
        elif op == 0x68:  # PLA
            self.A = self.setzn(self.pop())
        elif op == 0xEA:  # NOP
            pass
        else:
            raise RuntimeError(f"unimpl opcode ${op:02X} at ${self.PC-1:04X}")
        return False


def decompress_at(src_addr, ref=None):
    """Decompress the stream located at `src_addr` (a load address in $1E00..)
    and return the resulting hi-res page-1 raster ($2000-$3FFF, 0x2000 bytes)."""
    data = ref if ref is not None else load_ref()
    mem = bytearray(0x10000)
    mem[0x1E00:0x1E00 + len(data)] = data
    cpu = CPU(mem)
    # set decompress source pointer $00/$01 = src_addr (as the driver $1F31 does)
    mem[0x00] = src_addr & 0xFF
    mem[0x01] = (src_addr >> 8) & 0xFF
    cpu.run(0x1E03)
    # the consumed end is in $00/$01
    end = mem[0x00] | (mem[0x01] << 8)
    return bytes(mem[0x2000:0x4000]), end, cpu.steps


if __name__ == '__main__':
    raster, end, steps = decompress_at(0x49EC)
    nz = sum(1 for b in raster if b)
    print(f'decompress @ $49EC: consumed to ${end:04X}, steps={steps}, '
          f'nonzero={nz}/{len(raster)}')
