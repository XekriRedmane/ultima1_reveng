#!/usr/bin/env python3
"""Reorder chunk references in assembly files by ORG address.

Usage:
    python .claude/skills/assemble/reorder_chunks.py [TARGET] [-v]

TARGET is one of the target names in targets.json, or 'all' (default)
to reorder every target's collection chunk.

Reads the noweb source, finds the <<TARGET.asm>>= chunk, resolves each
chunk reference's first ORG address, and reorders them in ascending
order.

Comments and blank lines are attached to the chunk reference that
follows them and move together during reordering.

Use -v for verbose output showing all chunks with their addresses.
Run from the project root (reads targets.json).
"""

from __future__ import annotations

import json
import re
import sys


def load_manifest() -> tuple[str, dict[str, str]]:
    """Return (nw_source, {target_name: collection_chunk_name})."""
    try:
        with open('targets.json', encoding='utf-8') as f:
            manifest = json.load(f)
    except FileNotFoundError:
        print('ERROR: targets.json not found. Run from the project root.')
        sys.exit(1)
    names = {t['name']: f"{t['name']}.asm" for t in manifest['targets']}
    return manifest.get('nw_source', 'main.nw'), names


FILE, CHUNK_NAMES = load_manifest()


def find_chunk_org(chunk_name: str, lines: list[str]) -> int | None:
    """Find the first ORG address in a chunk definition."""
    target = f'<<{chunk_name}>>='
    in_chunk = False
    for line in lines:
        stripped = line.strip()
        if stripped == target:
            in_chunk = True
            continue
        if in_chunk:
            m = re.match(r'\s+ORG\s+\$([0-9A-Fa-f]+)', line)
            if m:
                return int(m.group(1), 16)
            if stripped.startswith('<<') and stripped.endswith('>>='):
                if stripped == target:
                    continue
                in_chunk = False
            if stripped == '@' or stripped.startswith('@ %def'):
                in_chunk = False
    return None


def reorder_target(target: str, lines: list[str]) -> list[str]:
    """Reorder chunk refs in one <<target.asm>>= chunk. Returns modified lines."""
    asm_chunk = f'<<{CHUNK_NAMES[target]}>>='
    chunk_ref_pattern = re.compile(r'^<<(.+)>>$')

    # Find the chunk boundaries
    start = -1
    end = -1
    for i, line in enumerate(lines):
        if line.strip() == asm_chunk:
            start = i
        elif start >= 0 and end < 0:
            if line.strip() == '@' or (
                line.strip().startswith('<<') and line.strip().endswith('>>=')
                and line.strip() != asm_chunk
            ):
                end = i
                break
    if start < 0:
        print(f'  {target}: <<{CHUNK_NAMES[target]}>>= not found')
        return lines
    if end < 0:
        end = len(lines)

    # Parse the chunk body into groups.
    # Each group is: (chunk_name | None, [lines])
    # A group with chunk_name is a chunk reference preceded by its
    # associated comment/blank lines.  A group with chunk_name=None
    # is a preamble (PROCESSOR, macros, defines, etc.) before the
    # first ORG-bearing chunk.
    groups: list[tuple[str | None, list[str]]] = []
    pending_lines: list[str] = []

    for i in range(start + 1, end):
        line = lines[i]
        m = chunk_ref_pattern.match(line.strip())
        if m:
            name = m.group(1)
            # Check if this chunk has an ORG (is reorderable)
            org = find_chunk_org(name, lines)
            if org is not None:
                # This is a reorderable chunk ref; pending lines are its prefix
                groups.append((name, pending_lines + [line]))
                pending_lines = []
            else:
                # Non-ORG chunk (macros, defines, etc.) — keep in preamble
                pending_lines.append(line)
        else:
            # Comment, blank line, or directive — accumulate
            pending_lines.append(line)

    # Any trailing pending lines (comments/blanks after last ref)
    trailing: list[str] = pending_lines

    # Separate preamble (groups before first ORG ref) from reorderable groups
    preamble: list[str] = []
    reorderable: list[tuple[str, list[str]]] = []

    for name, group_lines in groups:
        if name is not None:
            reorderable.append((name, group_lines))
        else:
            preamble.extend(group_lines)

    # Resolve ORGs for sorting
    chunk_orgs: dict[str, int] = {}
    for name, _ in reorderable:
        org = find_chunk_org(name, lines)
        if org is not None:
            chunk_orgs[name] = org

    # Sort reorderable groups by ORG address
    old_order = [name for name, _ in reorderable]
    reorderable.sort(key=lambda x: chunk_orgs.get(x[0], 0))
    new_order = [name for name, _ in reorderable]

    changes = sum(1 for a, b in zip(old_order, new_order) if a != b)

    # Rebuild
    new_chunk = [lines[start]]
    new_chunk.extend(preamble)
    for name, group_lines in reorderable:
        new_chunk.extend(group_lines)
    new_chunk.extend(trailing)

    result = lines[:start] + new_chunk + lines[end:]

    n_no_org = len([name for name, _ in groups if name is None])
    print(f'  {target}: {len(reorderable)} chunks, {changes} reordered'
          + (f', {n_no_org} without ORG' if n_no_org else ''))

    if '-v' in sys.argv or '--verbose' in sys.argv:
        for name, _ in reorderable:
            org = chunk_orgs.get(name)
            addr = f'${org:04X}' if org is not None else '????'
            print(f'    {addr}  <<{name}>>')

    return result


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    target = args[0] if args else 'all'

    with open(FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if target == 'all':
        targets = list(CHUNK_NAMES)
    elif target in CHUNK_NAMES:
        targets = [target]
    else:
        print(f'ERROR: unknown target {target!r}. '
              f'Known targets: {", ".join(CHUNK_NAMES)}, all')
        sys.exit(1)

    for t in targets:
        lines = reorder_target(t, lines)

    with open(FILE, 'w', encoding='utf-8') as f:
        f.writelines(lines)


if __name__ == '__main__':
    main()
