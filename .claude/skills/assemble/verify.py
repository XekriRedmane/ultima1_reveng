#!/usr/bin/env python3
"""Compare assembled output against reference binaries.

Usage:
    python .claude/skills/assemble/verify.py [TARGET] [START END]

TARGET is one of the target names in targets.json, or omitted to
report on ALL targets.

With no START/END, shows overall coverage statistics and lists gaps.
With START END (hex addresses), checks just that region of one target.

Examples:
    python .claude/skills/assemble/verify.py              # all targets
    python .claude/skills/assemble/verify.py main
    python .claude/skills/assemble/verify.py main 0503 0569

Targets are defined in targets.json at the project root (the
per-project manifest). Run from the project root.
"""

from __future__ import annotations

import json
import sys


def load_targets() -> dict[str, tuple[str, str, int]]:
    try:
        with open('targets.json', encoding='utf-8') as f:
            manifest = json.load(f)
    except FileNotFoundError:
        print('ERROR: targets.json not found. Run from the project root; '
              'create it during bootstrap (see /bootstrap skill).')
        sys.exit(1)
    out_dir = manifest.get('output_dir', 'output')
    targets: dict[str, tuple[str, str, int]] = {}
    for t in manifest['targets']:
        base = int(t['base'].lstrip('$').removeprefix('0x'), 16)
        targets[t['name']] = (f"{out_dir}/{t['name']}.bin", t['reference'], base)
    return targets


TARGETS = load_targets()


def parse_addr(s: str) -> int:
    return int(s.strip().lstrip('$').removeprefix('0x').removeprefix('0X'), 16)


def main() -> None:
    args = sys.argv[1:]

    # Parse target name; with no target, report on all targets
    if args and args[0] in TARGETS:
        target = args.pop(0)
    elif args and not args[0][0].isdigit() and args[0][0] not in '$':
        print(f'ERROR: unknown target {args[0]!r}. '
              f'Known targets: {", ".join(TARGETS)}')
        sys.exit(1)
    else:
        for name in TARGETS:
            report_target(name, [])
        return

    report_target(target, args)


def report_target(target: str, args: list[str]) -> None:
    test_path, ref_path, base = TARGETS[target]

    try:
        test = open(test_path, 'rb').read()
    except FileNotFoundError:
        print(f'ERROR: {test_path} not found. Run /assemble first.')
        sys.exit(1)

    try:
        ref = open(ref_path, 'rb').read()
    except FileNotFoundError:
        print(f'ERROR: {ref_path} not found.')
        sys.exit(1)

    if len(test) != len(ref):
        print(f'WARNING: size mismatch: test={len(test)}, ref={len(ref)}')

    size = min(len(test), len(ref))

    # Region check mode
    if len(args) >= 2:
        start = parse_addr(args[0])
        end = parse_addr(args[1])
        ok = True
        for i in range(start - base, end - base):
            if i < 0 or i >= size:
                break
            if test[i] != ref[i]:
                print(f'  DIFF at ${base + i:04X}: '
                      f'expected ${ref[i]:02X}, got ${test[i]:02X}')
                ok = False
                count = 1
                for j in range(i + 1, min(i + 20, end - base)):
                    if j < size and test[j] != ref[j]:
                        print(f'  DIFF at ${base + j:04X}: '
                              f'expected ${ref[j]:02X}, got ${test[j]:02X}')
                        count += 1
                        if count >= 5:
                            print('  ...')
                            break
                break
        if ok:
            print(f'${start:04X}-${end - 1:04X}: MATCH ({end - start} bytes)')
        return

    # Full report mode
    in_diff = False
    diff_start = 0
    gaps: list[tuple[int, int]] = []
    for i in range(size):
        if test[i] != ref[i]:
            if not in_diff:
                diff_start = i
                in_diff = True
        else:
            if in_diff:
                gaps.append((diff_start, i))
                in_diff = False
    if in_diff:
        gaps.append((diff_start, size))

    total_diff = sum(e - s for s, e in gaps)
    documented = size - total_diff

    print(f'{target}: {documented}/{size} bytes '
          f'({documented * 100 / size:.1f}%) documented')
    if total_diff == 0:
        print('  No gaps — perfect match!')
        return

    print(f'  Remaining: {total_diff} bytes, {len(gaps)} gaps')
    print()

    large = [(s, e) for s, e in gaps if e - s >= 500]
    medium = [(s, e) for s, e in gaps if 100 <= e - s < 500]
    small = [(s, e) for s, e in gaps if e - s < 100]

    if large:
        print(f'Large gaps (>= 500 bytes): {len(large)}')
        for s, e in large:
            print(f'  ${base + s:04X}-${base + e - 1:04X}  {e - s:5d}B')

    if medium:
        print(f'Medium gaps (100-499 bytes): {len(medium)}')
        for s, e in medium:
            print(f'  ${base + s:04X}-${base + e - 1:04X}  {e - s:5d}B')

    if small:
        total_small = sum(e - s for s, e in small)
        print(f'Small gaps (< 100 bytes): {len(small)} '
              f'({total_small}B total)')


if __name__ == '__main__':
    main()
