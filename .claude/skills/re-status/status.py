#!/usr/bin/env python3
"""Aggregate done-criteria metrics for the RE loop.

Usage:
    python3 .claude/skills/re-status/status.py

Run from the project root after a build (/assemble). Prints a
scoreboard of every measurable completion criterion. The autonomous
loop uses this to decide what to do next and when it is finished.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys


def sh(cmd: list[str]) -> tuple[int, str]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main() -> None:
    try:
        with open('targets.json', encoding='utf-8') as f:
            manifest = json.load(f)
    except FileNotFoundError:
        print('NOT BOOTSTRAPPED: targets.json missing — run /bootstrap.')
        sys.exit(1)

    nw_path = manifest.get('nw_source', 'main.nw')
    nw = open(nw_path, encoding='utf-8').read()
    nw_lines = nw.splitlines()

    print('=== Coverage (byte-perfect vs reference) ===')
    all_perfect = True
    for t in manifest['targets']:
        rc, out = sh([sys.executable,
                      '.claude/skills/assemble/verify.py', t['name']])
        first = out.strip().splitlines()[0] if out.strip() else '(no output)'
        print(f'  {first}')
        if rc != 0 or 'perfect match' not in out:
            all_perfect = False

    print()
    print('=== Document hygiene ===')

    stubs = [ln for ln in nw_lines if 'STUB' in ln and 'EQU' in ln]
    stub_chunks = [ln for ln in nw_lines
                   if 'STUB' in ln and 'not yet disassembled' in ln]
    print(f'  EQU stubs (routines not yet RE\'d):      '
          f'{len(stubs)}')
    print(f'  ORG stub chunks (not yet disassembled): {len(stub_chunks)}')

    todo_sym = nw.count('TODO-SYM')
    print(f'  TODO-SYM markers:                       {todo_sym}')

    todo_other = len(re.findall(r'%\s*TODO(?!-SYM)', nw))
    print(f'  Other TODO markers in prose:            {todo_other}')

    # SUBROUTINEs lacking a header plate (no "; Behavior:" within the
    # 15 lines following the SUBROUTINE directive).
    missing_plate = 0
    for i, ln in enumerate(nw_lines):
        if ln.strip() == 'SUBROUTINE':
            window = '\n'.join(nw_lines[i:i + 15])
            if 'Behavior:' not in window:
                missing_plate += 1
    n_subs = sum(1 for ln in nw_lines if ln.strip() == 'SUBROUTINE')
    print(f'  Routines missing header plates:         '
          f'{missing_plate} / {n_subs}')

    rc, out = sh([sys.executable,
                  '.claude/skills/chunk-placement/check_placement.py'])
    m = re.search(r'(\d+) violation', out)
    viol = int(m.group(1)) if m else 0
    print(f'  Chunk-placement violations:             {viol}')

    # Raw hex JSR/JMP operands in code chunks (should be labels).
    # Only count instruction lines (leading whitespace, operand before
    # any comment); prose and comment mentions don't count.
    raw_jsr = 0
    for ln in nw_lines:
        code = ln.split(';')[0]
        if re.match(r'\s+(?:\S+:\s+)?(?:JSR|JMP)\s+\$[0-9A-Fa-f]{2,4}\s*$',
                    code):
            raw_jsr += 1
    print(f'  Raw-hex JSR/JMP operands in code:       {raw_jsr}')

    print()
    print('=== Verdict ===')
    done = (all_perfect and not stubs and not stub_chunks
            and todo_sym == 0 and missing_plate == 0 and raw_jsr == 0
            and viol == 0)
    if done:
        print('  All measurable criteria met. Remaining work is editorial:')
        print('  synthesis chapters, organization, and PDF quality.')
    else:
        print('  Work remains — pick the first failing criterion above,')
        print('  or run /find-gaps for byte-level targets.')


if __name__ == '__main__':
    main()
