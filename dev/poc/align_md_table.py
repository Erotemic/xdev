#!/usr/bin/env python3
"""
Align the pipes in a Markdown table.

Reads a Markdown table from a positional argument, ``--file FILE``, or
stdin. Parses rows, computes per-column widths, and re-emits the table so
every pipe lines up. Recognized alignment markers (``:---``, ``---:``,
``:---:``) are preserved.

Examples:

    # from stdin
    pbpaste | align_md_table.py

    # from a string argument
    align_md_table.py "$(cat table.md)"

    # from a file
    align_md_table.py --file table.md
"""
from __future__ import annotations

import argparse
import re
import sys
from typing import List, Tuple


# Split on unescaped pipes. We allow ``\|`` to be a literal pipe within a
# cell (rare, but a real Markdown rule).
_CELL_SPLIT = re.compile(r'(?<!\\)\|')


def _strip_outer_pipes(line: str) -> str:
    """Remove the leading and trailing pipe of a table row, if present."""
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    return line


def _split_row(line: str) -> List[str]:
    """Split a row into stripped cell strings."""
    inner = _strip_outer_pipes(line)
    return [c.strip() for c in _CELL_SPLIT.split(inner)]


def _classify_align_cell(cell: str) -> Tuple[str, bool]:
    """
    Return (alignment, is_alignment_cell) for a separator-row cell.

    alignment is one of: 'left', 'right', 'center', 'default'.
    """
    s = cell.strip()
    if not re.fullmatch(r':?-{3,}:?', s):
        return 'default', False
    left = s.startswith(':')
    right = s.endswith(':')
    if left and right:
        return 'center', True
    if right:
        return 'right', True
    if left:
        return 'left', True
    return 'default', True


def _row_is_alignment(row: List[str]) -> bool:
    """A row is the alignment row iff every cell is an alignment cell."""
    return bool(row) and all(_classify_align_cell(c)[1] for c in row)


def _visible_len(s: str) -> int:
    """
    Best-effort visible length. Uses character count; treats wide characters
    as width 1 because Python's stdlib doesn't expose East Asian width
    cheaply. Good enough for the typical ASCII-heavy markdown table.
    """
    return len(s)


def _pad_cell(cell: str, width: int, alignment: str) -> str:
    pad = width - _visible_len(cell)
    if pad <= 0:
        return cell
    if alignment == 'right':
        return ' ' * pad + cell
    if alignment == 'center':
        left = pad // 2
        right = pad - left
        return ' ' * left + cell + ' ' * right
    # 'left' and 'default' both left-align
    return cell + ' ' * pad


def _format_alignment_cell(width: int, alignment: str) -> str:
    """
    Build the dashes/colons for one cell of the alignment row, sized to
    ``width``. Width here is the cell's content width (not counting the
    surrounding spaces around the pipe).
    """
    # Always emit at least three dashes per the GFM spec.
    width = max(width, 3)
    if alignment == 'left':
        return ':' + '-' * (width - 1)
    if alignment == 'right':
        return '-' * (width - 1) + ':'
    if alignment == 'center':
        return ':' + '-' * (width - 2) + ':'
    return '-' * width


def align_markdown_table(text: str) -> str:
    """
    Align the pipes in a single Markdown table.

    Lines that don't look like table rows (no ``|``) pass through verbatim,
    so a table inside a larger document survives a round-trip.
    """
    out_lines: List[str] = []
    table_buf: List[str] = []

    def flush_table():
        if table_buf:
            out_lines.append(_align_block(table_buf))
            table_buf.clear()

    for line in text.splitlines():
        if '|' in line.strip():
            table_buf.append(line)
        else:
            flush_table()
            out_lines.append(line)
    flush_table()

    return '\n'.join(out_lines)


def _align_block(lines: List[str]) -> str:
    rows = [_split_row(line) for line in lines]
    n_cols = max(len(r) for r in rows)
    # Pad ragged rows to the widest row so column indexing is uniform.
    rows = [r + [''] * (n_cols - len(r)) for r in rows]

    # Find the alignment row (typically the second row).
    align_idx = next((i for i, r in enumerate(rows) if _row_is_alignment(r)), None)
    if align_idx is not None:
        alignments = [_classify_align_cell(c)[0] for c in rows[align_idx]]
    else:
        alignments = ['default'] * n_cols

    # Compute per-column content widths (skip the alignment row when sizing
    # columns -- the markers should grow to fit, not the other way around).
    widths = [0] * n_cols
    for i, row in enumerate(rows):
        if i == align_idx:
            continue
        for c, cell in enumerate(row):
            widths[c] = max(widths[c], _visible_len(cell))
    # Alignment markers need at least 3 dashes (plus optional colons).
    for c in range(n_cols):
        markers_min = 3 + sum(
            1 for a in [alignments[c]] if a in ('left', 'right'))
        markers_min += 1 if alignments[c] == 'center' else 0
        widths[c] = max(widths[c], markers_min)

    out_rows: List[str] = []
    for i, row in enumerate(rows):
        if i == align_idx:
            cells = [_format_alignment_cell(widths[c], alignments[c])
                     for c in range(n_cols)]
        else:
            cells = [_pad_cell(row[c], widths[c], alignments[c])
                     for c in range(n_cols)]
        out_rows.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(out_rows)


def _read_input(args: argparse.Namespace) -> str:
    if args.file:
        with open(args.file, 'r') as fp:
            return fp.read()
    if args.text is not None:
        return args.text
    if sys.stdin.isatty():
        raise SystemExit(
            'No input given. Pass a string argument, --file, or pipe via stdin.'
        )
    return sys.stdin.read()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog='align_md_table',
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'text', nargs='?', default=None,
        help='markdown table (or document containing one) as a string',
    )
    parser.add_argument(
        '-f', '--file',
        help='read the markdown from this file instead of stdin / argv',
    )
    args = parser.parse_args(argv)

    text = _read_input(args)
    print(align_markdown_table(text))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
