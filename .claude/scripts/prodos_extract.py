#!/usr/bin/env python3
"""Extract reference binaries from the Ultima I (4am crack) ProDOS .dsk.

The disk is a ProDOS 1.1.1 volume (/U1) stored in a DOS-order .dsk
image. This script understands just enough of the ProDOS filesystem
(volume directory, seedling/sapling/tree storage) to pull every game
file out as a flat binary, plus the 512-byte boot block (ProDOS
block 0, physical T0 S0 + T0 S2).

Reference binaries are written to reference/ using the target names
from targets.json. Run from the project root:

    python3 .claude/scripts/prodos_extract.py

Sector math:
  - The .dsk stores sectors in DOS 3.3 logical order. Physical sector
    P of track T is at file offset T*4096 + DOS_SKEW[P]*256.
  - ProDOS block B lives on track B//8; its two 256-byte halves are
    ProDOS logical sectors 2*(B%8) and 2*(B%8)+1, which map to
    physical sectors via PRODOS_PHYS.
"""

from __future__ import annotations

import os
import sys

DSK = "Ultima I - The Beginning (4am crack).dsk"
OUTDIR = "reference"

DOS_SKEW = [0, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1, 8, 15]
PRODOS_PHYS = [0, 2, 4, 6, 8, 10, 12, 14, 1, 3, 5, 7, 9, 11, 13, 15]

# ProDOS file name -> reference binary target name.
# PRODOS itself is the stock ProDOS 1.1.1 kernel (18-SEP-84); it is
# extracted for inspection but is not an RE target.
FILE_MAP = {
    "U1.SYSTEM":   "u1system",
    "U1.INTRO":    "u1intro",
    "MI.U1":       "miu1",
    "OUT":         "out",
    "DNG":         "dng",
    "TWN":         "twn",
    "CAS":         "cas",
    "SPA":         "spa",
    "GEN":         "gen",
    "TM":          "tm",
    "MAKE.INDATA": "makeindata",
    "MAPCHARS":    "mapchars",
    "TCMAPS":      "tcmaps",
    "NIF":         "nif",
    "STUPH":       "stuph",
    "PRODOS":      "prodos111",
}


def read_block(data: bytes, n: int) -> bytes:
    track, idx = divmod(n, 8)
    out = b""
    for s in (2 * idx, 2 * idx + 1):
        p = PRODOS_PHYS[s]
        off = track * 4096 + DOS_SKEW[p] * 256
        out += data[off:off + 256]
    return out


def read_file(data: bytes, storage: int, key: int, eof: int) -> bytes:
    if storage == 1:                                    # seedling
        return read_block(data, key)[:eof]
    if storage == 2:                                    # sapling
        idx = read_block(data, key)
        out = b""
        for i in range((eof + 511) // 512):
            bn = idx[i] | (idx[256 + i] << 8)
            out += read_block(data, bn) if bn else b"\0" * 512
        return out[:eof]
    if storage == 3:                                    # tree
        master = read_block(data, key)
        out = b""
        for i in range((eof + 511) // 512):
            ii, jj = divmod(i, 256)
            ib = master[ii] | (master[256 + ii] << 8)
            idx = read_block(data, ib) if ib else b"\0" * 512
            bn = idx[jj] | (idx[256 + jj] << 8)
            out += read_block(data, bn) if bn else b"\0" * 512
        return out[:eof]
    raise ValueError(f"unsupported storage type {storage}")


def walk_volume_directory(data: bytes):
    bn = 2
    first = True
    while bn:
        blk = read_block(data, bn)
        nxt = blk[2] | (blk[3] << 8)
        for e in range(13):
            ent = blk[4 + e * 0x27: 4 + (e + 1) * 0x27]
            storage, namelen = ent[0] >> 4, ent[0] & 0x0F
            if not storage or not namelen:
                continue
            if first and e == 0:
                continue                                # volume header
            name = ent[1:1 + namelen].decode("ascii")
            ftype = ent[0x10]
            key = ent[0x11] | (ent[0x12] << 8)
            eof = ent[0x15] | (ent[0x16] << 8) | (ent[0x17] << 16)
            aux = ent[0x1F] | (ent[0x20] << 8)
            yield name, storage, ftype, key, eof, aux
        first = False
        bn = nxt


def main() -> None:
    data = open(DSK, "rb").read()
    os.makedirs(OUTDIR, exist_ok=True)

    # Boot block: ProDOS block 0, loaded by the Disk II PROM at $0800.
    boot = read_block(data, 0)
    open(os.path.join(OUTDIR, "boot1.bin"), "wb").write(boot)
    print(f"boot1.bin          512 bytes  base $0800  (T0 phys S0+S2)")

    seen = set()
    for name, storage, ftype, key, eof, aux in walk_volume_directory(data):
        if name not in FILE_MAP:
            print(f"WARNING: unmapped file {name}", file=sys.stderr)
            continue
        out = read_file(data, storage, key, eof)
        assert len(out) == eof
        target = FILE_MAP[name]
        path = os.path.join(OUTDIR, target + ".bin")
        open(path, "wb").write(out)
        seen.add(name)
        print(f"{target + '.bin':<18} {eof:5d} bytes  base ${aux:04X}  "
              f"(ProDOS {name}, type ${ftype:02X})")

    missing = set(FILE_MAP) - seen
    if missing:
        print(f"WARNING: files not found on volume: {missing}",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
