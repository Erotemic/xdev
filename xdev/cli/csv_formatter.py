#!/usr/bin/env python3
r"""
Simple CLI tool to take an input csv table and dump it in an aligned format.

Usage:

.. code::

    printf "a,b,c\n1,2,3\n3,5,5" | python -m xdev.cli.csv_formatter
    python -m xdev.cli.csv_formatter -- "
        col1,col2,col3
        134232,2,3
        3,5,5
    "

    python -m xdev.cli.csv_formatter -- '
        col1,col2,col3
        "1,134,232",2,3
        3,5,"32,300"
    '

"""
from __future__ import annotations
import sys
import csv
from typing import Any, List, Tuple
import ubelt as ub
import scriptconfig as scfg


class CSVFormatterCLI(scfg.DataConfig):
    """
    Read CSV from stdin and print aligned columns.
    """

    delimiter = scfg.Value(
        None, short_alias=["d"], help="CSV delimiter (overrides sniffing)."
    )
    quotechar = scfg.Value(
        None,
        short_alias=["q"],
        help=ub.paragraph(
            """
            CSV quote character (overrides sniffing).
            """
        ),
    )
    spacing = scfg.Value(
        2, type=int, short_alias=["s"], help="Spaces between columns (default: 2)."
    )
    header_rule = scfg.Value(
        False,
        isflag=True,
        help=ub.paragraph(
            """
            Draw a rule line under the first row (useful if it is a
            header).
            """
        ),
    )
    no_sniff = scfg.Value(
        False,
        isflag=True,
        help=ub.paragraph(
            """
            Do not sniff; use defaults (excel dialect) unless
            overridden.
            """
        ),
    )

    data = scfg.Value(
        None,
        position=1,
        type=str,
        help="Input text or file path to format. If not given stdin is used",
    )

    # NEW: control trimming of each parsed CSV cell (default True)
    strip_cells = scfg.Value(
        True,
        type=bool,
        help="Strip leading/trailing whitespace from each CSV cell (default: True).",
    )


def main():
    args = CSVFormatterCLI.cli(strict=True, verbose="auto")

    if args.data is None:
        # Read all stdin as text
        data = sys.stdin.read()
    else:
        data = args.data

    # If short and single-line (no newlines), treat it as a potential path.
    if len(data) < 500 and "\n" not in data.strip():
        p = ub.Path(data.strip())
        if p.exists() and p.is_file():
            data = p.read_text()

    if args.strip_cells:
        data = data.strip()

    if data == "":
        return  # nothing to do

    # Prepare CSV reader
    if args.no_sniff and not (args.delimiter or args.quotechar):
        dialect = csv.get_dialect("excel")
    else:
        sample = data[:4096]
        dialect = try_sniff(sample, args.delimiter, args.quotechar)

    # Why does excel and sniffing not work?
    class Simple(csv.Dialect):
        delimiter = ","
        quotechar = '"'
        escapechar = None
        doublequote = True
        skipinitialspace = True
        lineterminator = "\n"
        quoting = csv.QUOTE_MINIMAL

    dialect = Simple()

    lines = data.splitlines()
    # print(f'lines = {ub.urepr(lines, nl=1)}')
    reader = csv.reader(lines, dialect=dialect)
    rows = [[c if c is not None else "" for c in row] for row in reader]

    # Optionally trim each parsed cell (does NOT affect quoted content before parsing)
    if args.strip_cells:
        rows = [[c.strip() for c in row] for row in rows]

    if not rows:
        return

    # Compute widths based on how cells will LOOK once quoted/escaped.
    widths, is_numeric_col = compute_display_widths(rows, delimiter=",", quotechar='"')

    for idx, r in enumerate(rows):
        parts = [
            render_cell(
                cell, widths[i], is_numeric_col[i], delimiter=",", quotechar='"'
            )
            for i, cell in enumerate(r)
        ]
        # Join with the delimiter (no extra spaces). Cells already padded.
        line = ",".join(parts).rstrip()
        print(line)
        if idx == 0 and args.header_rule:  # draw rule after first row
            rule = ",".join(("-" * w) for w in widths).rstrip()
            print(rule)


def try_sniff(sample: str, delimiter: str | None, quotechar: str | None):
    if delimiter or quotechar:
        # User-specified settings take precedence over sniffing
        class Simple(csv.Dialect):
            delimiter = delimiter or ","  # type: ignore[name-defined]
            quotechar = quotechar or '"'  # type: ignore[name-defined]
            escapechar = None
            doublequote = True
            skipinitialspace = False
            lineterminator = "\n"
            quoting = csv.QUOTE_MINIMAL

        return Simple()

    try:
        dialect: Any = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        # Respect common CSV behaviors
        dialect.doublequote = True
        dialect.skipinitialspace = True
        dialect.skipinitialspace = False
        dialect.lineterminator = "\n"
        print(f"sniffed dialect={dialect}")
    except csv.Error:
        dialect = csv.get_dialect("excel")  # fallback
        print(f"default dialect={dialect}")
    return dialect


def is_number(s: str) -> bool:
    s = s.strip()
    if not s:
        return False
    try:
        float(s.replace(",", ""))  # allow thousands commas in input
        return True
    except ValueError:
        return False


def pad(cell: str, width: int, right_align: bool) -> str:
    # Keep cell as-is (no trimming); align with spaces
    if right_align:
        return cell.rjust(width)
    return cell.ljust(width)


def compute_display_widths(
    rows: List[List[str]], delimiter: str = ",", quotechar: str = '"'
) -> Tuple[List[int], List[bool]]:
    # Determine max number of columns across all rows
    ncols = max((len(r) for r in rows), default=0)
    # Normalize rows
    for r in rows:
        if len(r) < ncols:
            r += [""] * (ncols - len(r))

    # Column widths and numeric detection
    widths = [0] * ncols
    is_numeric_col = [True] * ncols  # start optimistic
    for r in rows:
        for i, val in enumerate(r):
            # Use the rendered length (with quoting/escaping, if needed).
            widths[i] = max(widths[i], display_len(val, delimiter, quotechar))
            if val.strip() != "" and not is_number(val):
                is_numeric_col[i] = False
    return widths, is_numeric_col


def needs_quotes(cell: str, delimiter: str, quotechar: str) -> bool:
    return (
        (delimiter in cell) or (quotechar in cell) or ("\n" in cell) or ("\r" in cell)
    )


def escape_cell(cell: str, quotechar: str) -> str:
    # Double quotes inside quoted fields per RFC 4180 / Excel behavior
    return cell.replace(quotechar, quotechar * 2)


def display_len(cell: str, delimiter: str = ",", quotechar: str = '"') -> int:
    esc = escape_cell(cell, quotechar)
    if needs_quotes(cell, delimiter, quotechar):
        return len(esc) + 2  # account for surrounding quotes
    else:
        return len(esc)


def render_cell(
    cell: str, width: int, right_align: bool, delimiter: str = ",", quotechar: str = '"'
) -> str:
    esc = escape_cell(cell, quotechar)
    inner = (
        f"{quotechar}{esc}{quotechar}"
        if needs_quotes(cell, delimiter, quotechar)
        else esc
    )
    # Align on the full rendered text
    return inner.rjust(width) if right_align else inner.ljust(width)


def align_csv_text(
    csv_text: str,
    *,
    input_delimiter: str = ",",
    input_quotechar: str = '"',
    strip_cells: bool = True,
    dedent_input: bool = False,
    # Output formatting
    output_delimiter: str = ",",
    output_quotechar: str = '"',
    header_rule: bool = False,
) -> str:
    """
    Take a CSV string (e.g. from pandas.to_csv) and return an aligned CSV string.

    - Parses with the specified *input* delimiter/quotechar.
    - Renders & aligns with the specified *output* delimiter/quotechar.
    - Quoting is MINIMAL: only when needed (delimiter/quote/newline present).
    - Numbers are right-aligned; other text is left-aligned.

    Returns a string with a trailing newline.

    Example:
        >>> # xdoctest: +REQUIRES(module:pandas)
        >>> from xdev.cli.csv_formatter import *  # NOQA
        >>> import pandas as pd
        >>> df = pd.DataFrame([
        >>>     {'col1': "my data", 'col2': 1232, 'col3': '1+2i'},
        >>>     {'col1': "my fdsfs,,ddata", 'col2': 321232, 'col3': '1+2i'},
        >>>     {'col1': 'md"da"ta', 'col2': '32,123', 'col3': '1+2i'},
        >>> ])
        >>> csv_text = df.to_csv(index=False)
        >>> new_text = align_csv_text(csv_text)
        >>> print(csv_text)
        >>> print(new_text)
    """
    import textwrap
    text = csv_text
    if dedent_input:
        text = textwrap.dedent(text).strip("\n")

    lines = text.splitlines()

    class _InDialect(csv.Dialect):
        delimiter = input_delimiter
        quotechar = input_quotechar
        escapechar = None
        doublequote = True
        skipinitialspace = True     # be lenient: a, "b", c
        lineterminator = "\n"
        quoting = csv.QUOTE_MINIMAL

    reader = csv.reader(lines, dialect=_InDialect)
    rows: List[List[str]] = [[c if c is not None else "" for c in row] for row in reader]

    if strip_cells:
        rows = [[c.strip() for c in row] for row in rows]

    if not rows:
        return ""

    widths, is_numeric_col = compute_display_widths(
        rows, delimiter=output_delimiter, quotechar=output_quotechar
    )

    out_lines: List[str] = []
    for idx, r in enumerate(rows):
        parts = [
            render_cell(cell, widths[i], is_numeric_col[i],
                        delimiter=output_delimiter, quotechar=output_quotechar)
            for i, cell in enumerate(r)
        ]
        out_lines.append(output_delimiter.join(parts).rstrip())
        if idx == 0 and header_rule:
            out_lines.append(output_delimiter.join(("-" * w) for w in widths).rstrip())
    return "\n".join(out_lines) + "\n"


if __name__ == "__main__":
    main()
