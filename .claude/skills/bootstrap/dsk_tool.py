#!/usr/bin/env python3
"""General Apple II .dsk image tool for reverse-engineering bootstrap.

A 140K .dsk is 35 tracks x 16 sectors x 256 bytes. The file stores
sectors in a *logical* order; the game's RWTS addresses them in
*physical* order. The mapping between the two is the sector skew.

Usage (all addresses/sectors in hex or decimal; hex needs $ or 0x):

    dsk_tool.py info IMAGE
        Image size, track count, quick non-zero-track summary.

    dsk_tool.py dump IMAGE TRACK SECTOR [--order dos33|physical]
        Hexdump one 256-byte sector. TRACK/SECTOR are the *physical*
        track/sector the game's RWTS would request; --order says how
        the .dsk file is laid out (default dos33, the common case
        for .dsk/.do images).

    dsk_tool.py extract IMAGE TRACK SECTOR COUNT OUT [--order ...]
        Extract COUNT consecutive physical sectors (in PROM read
        order 0,1,2,...,15 then next track) to a flat binary OUT.

    dsk_tool.py extractmap IMAGE MAPFILE OUT
        Build a reference binary from a page map. MAPFILE lines:
        "track sector dest_page" (all hex, # comments allowed).
        OUT is sized to span the min..max dest pages; unmapped
        pages are zero-filled. Use this once the loader's page
        table has been reverse engineered.

    dsk_tool.py search IMAGE HEXBYTES [--order ...]
        Find a byte pattern (e.g. "4C 00 60") anywhere on the disk;
        reports physical track/sector/offset for each hit.

Exit non-zero on errors. No third-party dependencies.
"""

from __future__ import annotations

import argparse
import sys

SECTOR = 256
SECTORS_PER_TRACK = 16
TRACK = SECTOR * SECTORS_PER_TRACK

# DOS 3.3 skew: physical sector -> logical sector position in the .dsk
DOS_SKEW = [0, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1, 8, 15]

ORDERS = {
    'dos33': DOS_SKEW,
    'physical': list(range(16)),
}


def parse_num(s: str) -> int:
    s = s.strip()
    if s.startswith('$'):
        return int(s[1:], 16)
    if s.lower().startswith('0x'):
        return int(s, 16)
    return int(s)


def sector_offset(track: int, phys_sector: int, order: str) -> int:
    return track * TRACK + ORDERS[order][phys_sector] * SECTOR


def read_image(path: str) -> bytes:
    with open(path, 'rb') as f:
        data = f.read()
    if len(data) % TRACK != 0:
        print(f'WARNING: image size {len(data)} is not a whole number '
              f'of {TRACK}-byte tracks', file=sys.stderr)
    return data


def hexdump(data: bytes, base: int = 0) -> None:
    for i in range(0, len(data), 16):
        row = data[i:i + 16]
        hexs = ' '.join(f'{b:02X}' for b in row)
        text = ''.join(chr(b & 0x7F) if 0x20 <= (b & 0x7F) < 0x7F else '.'
                       for b in row)
        print(f'{base + i:04X}: {hexs:<47}  {text}')


def cmd_info(args: argparse.Namespace) -> None:
    data = read_image(args.image)
    n_tracks = len(data) // TRACK
    print(f'{args.image}: {len(data)} bytes, {n_tracks} tracks')
    for t in range(n_tracks):
        td = data[t * TRACK:(t + 1) * TRACK]
        used = sum(1 for s in range(SECTORS_PER_TRACK)
                   if any(td[s * SECTOR:(s + 1) * SECTOR]))
        print(f'  track ${t:02X}: {used:2d}/16 non-zero sectors')


def cmd_dump(args: argparse.Namespace) -> None:
    data = read_image(args.image)
    off = sector_offset(parse_num(args.track), parse_num(args.sector),
                        args.order)
    print(f'physical T{parse_num(args.track):02X} '
          f'S{parse_num(args.sector):X} (file offset ${off:05X}, '
          f'order={args.order}):')
    hexdump(data[off:off + SECTOR])


def cmd_extract(args: argparse.Namespace) -> None:
    data = read_image(args.image)
    track, sector = parse_num(args.track), parse_num(args.sector)
    count = parse_num(args.count)
    out = bytearray()
    for i in range(count):
        s = sector + i
        t = track + s // SECTORS_PER_TRACK
        s %= SECTORS_PER_TRACK
        off = sector_offset(t, s, args.order)
        out += data[off:off + SECTOR]
    with open(args.out, 'wb') as f:
        f.write(out)
    print(f'wrote {len(out)} bytes to {args.out}')


def cmd_extractmap(args: argparse.Namespace) -> None:
    data = read_image(args.image)
    entries: list[tuple[int, int, int]] = []
    with open(args.mapfile, encoding='utf-8') as f:
        for line in f:
            line = line.split('#')[0].strip()
            if not line:
                continue
            t, s, page = (int(x, 16) for x in line.split())
            entries.append((t, s, page))
    if not entries:
        print('ERROR: empty map file', file=sys.stderr)
        sys.exit(1)
    lo = min(p for _, _, p in entries)
    hi = max(p for _, _, p in entries)
    out = bytearray(SECTOR * (hi - lo + 1))
    for t, s, page in entries:
        off = sector_offset(t, s, args.order)
        dst = (page - lo) * SECTOR
        out[dst:dst + SECTOR] = data[off:off + SECTOR]
    with open(args.out, 'wb') as f:
        f.write(out)
    print(f'wrote {len(out)} bytes to {args.out} '
          f'(base address ${lo:02X}00)')


def cmd_search(args: argparse.Namespace) -> None:
    data = read_image(args.image)
    pattern = bytes.fromhex(args.hexbytes.replace(' ', ''))
    # Invert: logical .dsk position -> physical sector
    inv = [0] * 16
    for phys, logical in enumerate(ORDERS[args.order]):
        inv[logical] = phys
    start = 0
    found = 0
    while True:
        i = data.find(pattern, start)
        if i < 0:
            break
        t, rem = divmod(i, TRACK)
        logical_s, off = divmod(rem, SECTOR)
        print(f'physical T{t:02X} S{inv[logical_s]:X} +${off:02X} '
              f'(file offset ${i:05X})')
        found += 1
        start = i + 1
    print(f'{found} match(es)')


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)

    def add(name, fn, *params):
        sp = sub.add_parser(name)
        for prm in params:
            sp.add_argument(prm)
        sp.add_argument('--order', choices=ORDERS, default='dos33')
        sp.set_defaults(fn=fn)

    add('info', cmd_info, 'image')
    add('dump', cmd_dump, 'image', 'track', 'sector')
    add('extract', cmd_extract, 'image', 'track', 'sector', 'count', 'out')
    add('extractmap', cmd_extractmap, 'image', 'mapfile', 'out')
    add('search', cmd_search, 'image', 'hexbytes')

    args = p.parse_args()
    args.fn(args)


if __name__ == '__main__':
    main()
