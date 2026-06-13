#!/usr/bin/env python3
"""Port of the MAKE.INDATA hi-res decompressor ($1E03 driver + $1E47 inner).

The decompressor unpacks an RLE-ish byte stream straight into a 192x40-byte
hi-res raster (page 1, $2000-$3FFF address layout). It is driven column by
column (Y = 39..0), and within each column scanline by scanline (X = 191..0),
the $1E1D math turning each row index into the canonical Apple II hi-res base
address. The inner routine $1E47 is a small state machine with two run modes:

  $08 sentinel: a (count,value) vertical run within the current column.
  $09 sentinel: a (value, repeat-rows) "background fill" that paints the
      same byte down many rows, optionally repeated across a span, and can
      restart the stream pointer (a back-reference) to repeat a region.

This Python port reproduces it exactly so we can recover every packed raster
(the title image, and -- pointed at other offsets -- the intro art frames).
"""

# Zero-page state (named after the disassembly addresses)
class ZP:
    def __init__(self):
        self.b00 = 0      # stream pointer lo ($00)
        self.b01 = 0      # stream pointer hi ($01)
        self.b02 = 0      # raster dest lo ($02)
        self.b03 = 0      # raster dest hi ($03)
        self.b04 = 0      # saved stream ptr lo ($04)
        self.b05 = 0      # saved stream ptr hi ($05)
        self.b06 = 0      # current data byte ($06)
        self.b07 = 0      # $09-run outer repeat count ($07)
        self.b08 = 0      # sentinel A ($08)
        self.b09 = 0      # sentinel B ($09)
        self.b1B = 0      # row counter X mirror ($1B)
        self.b1C = 0      # $08-run length ($1C)
        self.b1D = 0      # in-$08-run flag, bit7 ($1D)
        self.b1E = 0      # $09-run span counter ($1E)
        self.b1F = 0      # in-$09-run flag, bit7 ($1F)
        self.bF9 = 0      # $09-run inner row counter ($F9)


def rowaddr(X):
    a = 0x2000
    a += (X & 0x07) << 10
    a += ((X >> 3) & 0x07) << 7
    a += (X >> 6) * 0x28
    return a


def decompress(stream, src_off, raster):
    """Run the decompressor. stream=full file bytes, src_off=offset of the
    compressed stream within it. raster = bytearray of 0x4000 (page-1 image).
    Returns the stream offset consumed past the end."""
    zp = ZP()
    # absolute stream position as a flat index into `stream`
    pos = src_off

    def fetch():
        nonlocal pos
        b = stream[pos]
        return b

    def incptr():
        nonlocal pos
        pos += 1

    # $1E03 driver init
    zp.b1D = 0
    zp.b1F = 0
    zp.bF9 = 0
    zp.b08 = fetch(); incptr()
    zp.b09 = fetch(); incptr()

    for Y in range(0x27, -1, -1):          # LDY #$27 ; columns 39..0
        X = 0xBF                            # LDX #$BF ; row 191
        while True:
            zp.b1B = X
            base = rowaddr(X)
            zp.b02 = base & 0xFF
            zp.b03 = base >> 8
            inner(zp, stream, raster, Y, fetch, incptr, lambda: pos, set_pos)
            # the inner routine consumes the stream and stores into raster
            X = (X - 1) & 0xFF
            if X == 0xFF:
                break
    return pos


# We need a mutable closure over pos; refactor with a small object.
class Decomp:
    def __init__(self, stream, src_off, raster):
        self.s = stream
        self.pos = src_off
        self.r = raster
        self.zp = ZP()

    def fetch(self):
        return self.s[self.pos]

    def inc(self):
        self.pos += 1

    def store(self, Y, val):
        addr = (self.zp.b03 << 8) | self.zp.b02
        # raster is indexed by (addr - 0x2000) + Y
        self.r[(addr - 0x2000) + Y] = val

    def run(self):
        zp = self.zp
        zp.b1D = 0
        zp.b1F = 0
        zp.bF9 = 0
        zp.b08 = self.fetch(); self.inc()
        zp.b09 = self.fetch(); self.inc()
        for Y in range(0x27, -1, -1):
            X = 0xBF
            while True:
                zp.b1B = X
                base = rowaddr(X)
                zp.b02 = base & 0xFF
                zp.b03 = base >> 8
                self.inner(Y)
                X = (X - 1) & 0xFF
                if X == 0xFF:
                    break
        return self.pos

    def inner(self, Y):
        zp = self.zp
        s = self.s
        # $1E47: LDX #$00 (unused index for (zp,X) which is really (zp))
        # BIT $1D ; BMI .run08  ($1EB1)
        if zp.b1D & 0x80:
            self.run08(Y)
            return
        # BIT $1F ; BMI .run09  ($1EC7)
        if zp.b1F & 0x80:
            self.run09(Y)
            return
        # LDA ($00) -> $06
        b = self.fetch()
        zp.b06 = b
        # CMP $08 ; BNE .not08 ($1E78)
        if b == zp.b08:
            # INC ptr
            self.inc()
            # LDA ($00) -> $1C  (run length)
            zp.b1C = self.fetch(); self.inc()
            # LDA ($00) -> $06  (run value)
            zp.b06 = self.fetch(); self.inc()
            # SEC ; ROR $1D  (set bit7)
            zp.b1D = 0x80
            # BNE .run08
            self.run08(Y)
            return
        # .not08 ($1E78): CMP $09 ; BNE .literal ($1EA6)
        if b == zp.b09:
            self.inc()
            # LDA ($00) -> $07, $F9
            v = self.fetch(); self.inc()
            zp.b07 = v
            zp.bF9 = v
            # LDA ($00) -> $1E
            zp.b1E = self.fetch(); self.inc()
            # save stream ptr -> $04/$05
            zp.b04 = self.pos & 0xFF
            zp.b05 = (self.pos >> 8) & 0xFF
            # actually save full pos
            self._saved = self.pos
            # LDA #$80 ; STA $1F ; BNE .run09
            zp.b1F = 0x80
            self.run09(Y)
            return
        # .literal ($1EA6): LDA $06 ; STA ($02),Y ; INC ptr ; RTS
        self.store(Y, zp.b06)
        self.inc()
        return

    def run08(self, Y):
        # $1EB1: LDA $06 ; STA ($02),Y ; DEC $1C ; BNE .out ($1EB0)
        zp = self.zp
        self.store(Y, zp.b06)
        zp.b1C = (zp.b1C - 1) & 0xFF
        if zp.b1C != 0:
            return
        # LDA #$00 ; STA $1D (clear run08 flag)
        zp.b1D = 0
        # BIT $1F ; BPL .out
        if not (zp.b1F & 0x80):
            return
        # in a $09 run too: DEC $F9 ; DEC $F9 ; BNE .chk09 ($1EE3)
        zp.bF9 = (zp.bF9 - 1) & 0xFF
        zp.bF9 = (zp.bF9 - 1) & 0xFF
        if zp.bF9 != 0:
            self._after_dec_f9(Y)
            return
        # falls into $1EC7 run09 entry
        self.run09(Y)

    def run09(self, Y):
        # $1EC7: LDA ($00) ; CMP $08 ; BNE .store09 ($1EDB)
        zp = self.zp
        b = self.fetch()
        if b == zp.b08:
            # LDA $F9 ; BNE (back to $1E59 -- treat as nested $08 run)
            if zp.bF9 != 0:
                # $1E59 path: INC ptr; read $1C, $06; set run08
                self.inc()
                zp.b1C = self.fetch(); self.inc()
                zp.b06 = self.fetch(); self.inc()
                zp.b1D = 0x80
                self.run08(Y)
                return
            # restore stream ptr from $04/$05, loop
            self.pos = self._saved
            # BNE $1ECF -> re-test LDA $F9 (now from restored)... emulate by recursion
            self.run09(Y)
            return
        # .store09 ($1EDB): STA ($02),Y ; INC ptr
        self.store(Y, b)
        self.inc()
        self._after_dec_f9(Y)

    def _after_dec_f9(self, Y):
        # $1EE3: DEC $F9 ; BNE .out ($1EB0)
        zp = self.zp
        zp.bF9 = (zp.bF9 - 1) & 0xFF
        if zp.bF9 != 0:
            return
        # LDA $07 ; STA $F9 ; DEC $1E ; BEQ .end ($1EF8)
        zp.bF9 = zp.b07
        zp.b1E = (zp.b1E - 1) & 0xFF
        if zp.b1E == 0:
            # clear run09 flag
            zp.b1F = 0
            return
        # restore stream ptr, RTS
        self.pos = self._saved
        return


def run(stream, src_off):
    raster = bytearray(0x4000)
    d = Decomp(stream, src_off, raster)
    end = d.run()
    return raster, end


if __name__ == '__main__':
    import sys
    data = open('reference/makeindata.bin', 'rb').read()
    src = 0x49EC - 0x1E00
    raster, end = run(data, src)
    print('consumed to file offset', hex(end), '=> addr', hex(end + 0x1E00))
    nz = sum(1 for b in raster if b)
    print('nonzero raster bytes:', nz, '/', len(raster))
