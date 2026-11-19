#!/usr/bin/env python3
"""
Align Markdown table pipes without rewriting unrelated text.

Reads Markdown from a positional argument, ``--file FILE``, or stdin. Only
actual table blocks are reformatted: a candidate header row must be followed
immediately by a valid Markdown delimiter row. Text containing ordinary pipe
characters and fenced code blocks are left untouched.

The formatter supports:

* tables with or without leading/trailing pipes;
* left, right, center, and default delimiter-row alignment;
* ragged body rows (missing cells are padded to the table width);
* escaped pipes, including correct odd/even backslash handling;
* common blockquote prefixes and up to three spaces of indentation;
* Unicode-aware source-column widths; and
* preservation of the input newline convention and final newline.

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
import unicodedata
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple


_ALIGNMENT_CELL_RE = re.compile(r":?-{3,}:?")
_FENCE_RE = re.compile(r"^(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")
_CONTAINER_RE = re.compile(r"^(?P<prefix> {0,3}(?:> ?)+)(?P<body>.*)$")
_INDENT_RE = re.compile(r"^(?P<prefix> {0,3})(?P<body>.*)$")


@dataclass(frozen=True)
class ParsedRow:
    """One row-like Markdown source line."""

    prefix: str
    cells: List[str]


@dataclass(frozen=True)
class Fence:
    """An open fenced-code block."""

    char: str
    length: int


def _split_prefix(line: str) -> Tuple[str, str]:
    """Return a lightweight Markdown container prefix and row body."""
    match = _CONTAINER_RE.match(line)
    if match:
        return match.group("prefix"), match.group("body")

    match = _INDENT_RE.match(line)
    assert match is not None
    return match.group("prefix"), match.group("body")


def _pipe_is_escaped(text: str, index: int) -> bool:
    """Whether ``text[index]`` is preceded by an odd run of backslashes."""
    backslashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def _split_unescaped_pipes(text: str) -> Tuple[List[str], bool, bool, int]:
    """
    Split on Markdown pipe separators.

    Returns ``(parts, leading_pipe, trailing_pipe, separator_count)``. A pipe
    escaped by an odd number of immediately preceding backslashes is literal;
    a pipe preceded by an even number remains a separator.
    """
    parts: List[str] = []
    start = 0
    separator_positions: List[int] = []

    for index, char in enumerate(text):
        if char == "|" and not _pipe_is_escaped(text, index):
            parts.append(text[start:index])
            separator_positions.append(index)
            start = index + 1
    parts.append(text[start:])

    stripped_left = len(text) - len(text.lstrip())
    stripped_right = len(text.rstrip())
    first_content = stripped_left
    last_content = stripped_right - 1

    leading_pipe = bool(separator_positions and separator_positions[0] == first_content)
    trailing_pipe = bool(
        separator_positions
        and last_content >= first_content
        and separator_positions[-1] == last_content
    )

    if leading_pipe:
        parts = parts[1:]
    if trailing_pipe and parts:
        parts = parts[:-1]

    return parts, leading_pipe, trailing_pipe, len(separator_positions)


def _parse_row(line: str) -> Optional[ParsedRow]:
    """Parse a row-shaped source line, or return ``None`` if it has no separator."""
    prefix, body = _split_prefix(line)

    # Four-space indentation is an indented code block, not a table. The
    # prefix splitter intentionally consumes at most three spaces, so reject
    # a fourth one still present at the front of the body.
    if body.startswith(" ") and not prefix.rstrip().endswith(">"):
        return None

    parts, _leading, _trailing, separator_count = _split_unescaped_pipes(body)
    if separator_count == 0:
        return None

    cells = [part.strip() for part in parts]
    if not cells:
        return None
    return ParsedRow(prefix=prefix, cells=cells)


def _classify_align_cell(cell: str) -> Tuple[str, bool]:
    """
    Return ``(alignment, is_delimiter_cell)`` for a delimiter-row cell.

    ``alignment`` is one of ``left``, ``right``, ``center``, or ``default``.
    """
    value = cell.strip()
    if _ALIGNMENT_CELL_RE.fullmatch(value) is None:
        return "default", False

    left = value.startswith(":")
    right = value.endswith(":")
    if left and right:
        return "center", True
    if right:
        return "right", True
    if left:
        return "left", True
    return "default", True


def _row_is_delimiter(row: ParsedRow) -> bool:
    """A delimiter row consists entirely of valid delimiter cells."""
    return bool(row.cells) and all(_classify_align_cell(cell)[1] for cell in row.cells)


def _display_width(text: str) -> int:
    """
    Estimate monospace source width without third-party dependencies.

    Combining/control-format characters count as zero, East Asian wide/full
    width characters count as two, and tabs advance to the next 4-column stop.
    """
    width = 0
    for char in text:
        if char == "\t":
            width += 4 - (width % 4)
            continue
        if unicodedata.combining(char):
            continue
        category = unicodedata.category(char)
        if category in {"Cf", "Cc"}:
            continue
        width += 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
    return width


def _pad_cell(cell: str, width: int, alignment: str) -> str:
    pad = width - _display_width(cell)
    if pad <= 0:
        return cell
    if alignment == "right":
        return " " * pad + cell
    if alignment == "center":
        left = pad // 2
        right = pad - left
        return " " * left + cell + " " * right
    return cell + " " * pad


def _minimum_delimiter_width(alignment: str) -> int:
    """Minimum serialized width for three dashes plus alignment colons."""
    if alignment == "center":
        return 5
    if alignment in {"left", "right"}:
        return 4
    return 3


def _format_delimiter_cell(width: int, alignment: str) -> str:
    width = max(width, _minimum_delimiter_width(alignment))
    if alignment == "left":
        return ":" + "-" * (width - 1)
    if alignment == "right":
        return "-" * (width - 1) + ":"
    if alignment == "center":
        return ":" + "-" * (width - 2) + ":"
    return "-" * width


def _same_container(a: ParsedRow, b: ParsedRow) -> bool:
    """Require rows in one table to share their Markdown container prefix."""
    return a.prefix == b.prefix


def _table_start(lines: Sequence[str], index: int) -> Optional[Tuple[ParsedRow, ParsedRow]]:
    """Recognize a table only from a header immediately followed by a delimiter."""
    if index + 1 >= len(lines):
        return None

    header = _parse_row(lines[index])
    delimiter = _parse_row(lines[index + 1])
    if header is None or delimiter is None:
        return None
    if not _same_container(header, delimiter):
        return None
    if not _row_is_delimiter(delimiter):
        return None
    if len(header.cells) != len(delimiter.cells):
        return None
    return header, delimiter


def _align_table_rows(rows: Sequence[ParsedRow]) -> List[str]:
    """Format a recognized table whose second row is its delimiter row."""
    if len(rows) < 2 or not _row_is_delimiter(rows[1]):
        raise ValueError("expected header + delimiter table rows")

    n_cols = max(len(row.cells) for row in rows)
    alignments = [_classify_align_cell(cell)[0] for cell in rows[1].cells]
    alignments.extend(["default"] * (n_cols - len(alignments)))

    normalized = [row.cells + [""] * (n_cols - len(row.cells)) for row in rows]

    widths = [0] * n_cols
    for row_index, cells in enumerate(normalized):
        if row_index == 1:
            continue
        for column, cell in enumerate(cells):
            widths[column] = max(widths[column], _display_width(cell))

    for column, alignment in enumerate(alignments):
        widths[column] = max(widths[column], _minimum_delimiter_width(alignment))

    prefix = rows[0].prefix
    output: List[str] = []
    for row_index, cells in enumerate(normalized):
        if row_index == 1:
            formatted = [
                _format_delimiter_cell(widths[column], alignments[column])
                for column in range(n_cols)
            ]
        else:
            formatted = [
                _pad_cell(cells[column], widths[column], alignments[column])
                for column in range(n_cols)
            ]
        output.append(prefix + "| " + " | ".join(formatted) + " |")
    return output


def _fence_transition(line: str, open_fence: Optional[Fence]) -> Optional[Fence]:
    """Track ordinary CommonMark-style fenced code blocks."""
    _prefix, body = _split_prefix(line)
    match = _FENCE_RE.match(body)
    if match is None:
        return open_fence

    token = match.group("fence")
    char = token[0]
    length = len(token)

    if open_fence is None:
        return Fence(char=char, length=length)

    rest = match.group("rest")
    if char == open_fence.char and length >= open_fence.length and not rest.strip():
        return None
    return open_fence


def _newline_style(text: str) -> str:
    """Use the first newline sequence present, defaulting to LF."""
    match = re.search(r"\r\n|\n|\r", text)
    return match.group(0) if match else "\n"


def align_markdown_table(text: str) -> str:
    """
    Align every actual Markdown table in ``text``.

    Detection is deliberately conservative: a table begins only when a
    row-shaped header is immediately followed by a valid delimiter row with
    the same number of cells. Unrelated pipe-bearing text and fenced code are
    preserved byte-for-byte apart from the document's table replacements.
    """
    if not text:
        return text

    newline = _newline_style(text)
    had_final_newline = text.endswith(("\n", "\r"))
    lines = text.splitlines()

    output: List[str] = []
    index = 0
    open_fence: Optional[Fence] = None

    while index < len(lines):
        line = lines[index]

        next_fence = _fence_transition(line, open_fence)
        if open_fence is not None or next_fence is not None:
            output.append(line)
            open_fence = next_fence
            index += 1
            continue

        start = _table_start(lines, index)
        if start is None:
            output.append(line)
            index += 1
            continue

        header, delimiter = start
        rows: List[ParsedRow] = [header, delimiter]
        cursor = index + 2
        while cursor < len(lines):
            candidate = _parse_row(lines[cursor])
            if candidate is None or not _same_container(header, candidate):
                break

            # If this row itself begins another valid table, leave it for the
            # outer loop instead of swallowing two adjacent tables.
            if _table_start(lines, cursor) is not None:
                break

            rows.append(candidate)
            cursor += 1

        output.extend(_align_table_rows(rows))
        index = cursor

    result = newline.join(output)
    if had_final_newline:
        result += newline
    return result


def _read_input(args: argparse.Namespace) -> str:
    if args.file:
        with open(args.file, "r", newline="") as fp:
            return fp.read()
    if args.text is not None:
        return args.text
    if sys.stdin.isatty():
        raise SystemExit(
            "No input given. Pass a string argument, --file, or pipe via stdin."
        )
    return sys.stdin.read()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="align_md_table",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="markdown table (or document containing one) as a string",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="read the markdown from this file instead of stdin / argv",
    )
    args = parser.parse_args(argv)

    text = _read_input(args)
    sys.stdout.write(align_markdown_table(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
