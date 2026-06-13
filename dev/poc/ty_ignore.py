#!/usr/bin/env python3
"""
Run:

    ty check --output-format=concise FILE

Then append:

    # type: ignore

to each line in FILE that ty reports as offending.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


TY_CONCISE_PATTERNS = [
    # Current observed ty format:
    #
    #   kwimage/structs/heatmap.py:1745:16: error[not-subscriptable] ...
    #
    re.compile(
        r'^(?P<path>.*):(?P<line>\d+):(?P<col>\d+):\s+'
        r'(?P<level>error|warning|warn|info|note)'
        r'(?:\[[^\]]+\])?\b'
    ),
    # Older / alternate format:
    #
    #   error[not-subscriptable] kwimage/structs/heatmap.py:1745:16: ...
    #
    re.compile(
        r'^(?P<level>error|warning|warn|info|note)'
        r'(?:\[[^\]]+\])?\s+'
        r'(?P<path>.*):(?P<line>\d+):(?P<col>\d+):'
    ),
]


def normalize_path(path: Path) -> str:
    return os.path.normcase(os.path.normpath(str(path)))


def paths_refer_to_same_file(diagnostic_path: str, target: Path) -> bool:
    diag = Path(diagnostic_path)

    candidates = {
        normalize_path(diag),
        normalize_path(Path.cwd() / diag),
    }

    target_candidates = {
        normalize_path(target),
        normalize_path(target.resolve()),
    }

    return bool(candidates & target_candidates)


def parse_ty_lines(output: str, target: Path) -> set[int]:
    line_numbers: set[int] = set()

    for raw_line in output.splitlines():
        text = raw_line.strip()

        for pattern in TY_CONCISE_PATTERNS:
            match = pattern.match(text)
            if match is None:
                continue

            if paths_refer_to_same_file(match.group('path'), target):
                line_numbers.add(int(match.group('line')))

            break

    return line_numbers


def add_type_ignores(path: Path, line_numbers: set[int]) -> int:
    lines = path.read_text(encoding='utf-8').splitlines(keepends=True)

    changed = 0

    for line_number in sorted(line_numbers):
        index = line_number - 1
        if not (0 <= index < len(lines)):
            continue

        line = lines[index]

        if line.endswith('\r\n'):
            body = line[:-2]
            newline = '\r\n'
        elif line.endswith('\n'):
            body = line[:-1]
            newline = '\n'
        else:
            body = line
            newline = ''

        if '# type: ignore' in body:
            continue

        lines[index] = f'{body}  # type: ignore{newline}'
        changed += 1

    if changed:
        path.write_text(''.join(lines), encoding='utf-8')

    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=Path)
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print the lines that would be changed, but do not edit the file.',
    )
    args = parser.parse_args()

    path = args.file

    if not path.exists():
        print(f'error: file does not exist: {path}', file=sys.stderr)
        return 2

    cmd = ['ty', 'check', '--output-format=concise', str(path)]
    result = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    combined_output = result.stdout
    if result.stderr:
        combined_output += '\n' + result.stderr

    line_numbers = parse_ty_lines(combined_output, path)

    if not line_numbers:
        print('No ty diagnostics found for this file.')
        return result.returncode

    if args.dry_run:
        print(
            'Would add # type: ignore to lines: '
            + ', '.join(map(str, sorted(line_numbers)))
        )
        return result.returncode

    changed = add_type_ignores(path, line_numbers)
    print(f'Added # type: ignore to {changed} line(s) in {path}')

    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
