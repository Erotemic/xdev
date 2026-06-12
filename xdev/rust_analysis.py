"""
Utilities for syntax-aware Rust source analysis.

The public entrypoint for directory statistics is
:func:`parse_rust_content_stats`. The tree-sitter backend is the default and
adds main/test line breakdowns. The legacy backend keeps the previous
hand-written scanner available, but intentionally only reports the original
aggregate fields.
"""

from __future__ import annotations

import bisect
import collections
import dataclasses
import functools
from typing import Iterable, Iterator, Sequence

RUST_BACKENDS = {'tree-sitter', 'legacy'}
TEST_LIKE_ATTR_NAMES = {
    'test',
    'tokio::test',
    'async_std::test',
    'rstest',
}


@dataclasses.dataclass(frozen=True)
class ParsedRustSource:
    """A parsed Rust source buffer."""

    text: str
    source: bytes
    root: object


@dataclasses.dataclass(frozen=True)
class RustLineSets:
    """Line sets used to build Rust source statistics."""

    code_lines: set[int]
    comment_lines: set[int]
    test_code_lines: set[int]
    test_comment_lines: set[int]
    main_code_lines: set[int]
    main_comment_lines: set[int]

    def to_stats(self) -> dict[str, int]:
        return {
            'main_code': len(self.main_code_lines),
            'main_comments': len(self.main_comment_lines),
            'test_code': len(self.test_code_lines),
            'test_comments': len(self.test_comment_lines),
        }


def parse_rust_content_stats(source: str, backend: str = 'tree-sitter') -> dict[str, int]:
    """
    Count Rust lines of code and comments.

    Args:
        source: Rust source text.
        backend: Either ``'tree-sitter'`` or ``'legacy'``. The tree-sitter
            backend is the default and reports main/test breakdowns. The
            legacy backend reports only ``code_lines``, ``comment_lines``, and
            ``doc_lines``.

    Returns:
        Dict[str, int]: line count statistics.

    Example:
        >>> import ubelt as ub
        >>> source = ub.codeblock(
        >>>     r'''
        >>>     // module comment
        >>>     fn main() {
        >>>         println!("http://example.com"); // trailing comment
        >>>         let text = "/* not comment */";
        >>>         let raw = r#"// not comment"#;
        >>>         /*
        >>>           block comment
        >>>           /* nested */
        >>>         */
        >>>         /// doc comment
        >>>         pub fn documented() {}
        >>>     }
        >>>     ''')
        >>> stats = parse_rust_content_stats(source, backend='legacy')
        >>> assert stats['code_lines'] == 6
        >>> assert stats['doc_lines'] == 1
    """
    if backend not in RUST_BACKENDS:
        raise KeyError(
            f'unknown Rust parser backend={backend!r}, expected one of '
            f'{sorted(RUST_BACKENDS)!r}'
        )
    if backend == 'legacy':
        return parse_rust_content_stats_legacy(source)
    else:
        return parse_rust_content_stats_treesitter(source)


def parse_rust_content_stats_treesitter(source: str) -> dict[str, int]:
    """
    Count Rust LOC with tree-sitter-rust.

    Tree-sitter's concrete syntax keeps comment markers inside strings and raw
    strings out of comment nodes, so this backend can count code and comments
    without reimplementing Rust literal lexing. It also classifies lines under
    ``#[cfg(test)]`` or test-like attributes as test lines. Documentation
    comments are counted as comments; the tree-sitter backend does not emit a
    separate docs column.
    """
    parsed = parse_rust_source(source)
    line_sets = rust_line_sets(parsed)
    return line_sets.to_stats()


def rust_line_sets(parsed: ParsedRustSource) -> RustLineSets:
    """
    Return code/comment/doc line sets from a parsed Rust source.
    """
    source = parsed.source
    root = parsed.root
    line_starts, line_ends = byte_line_bounds(source)
    comment_spans = collect_comment_spans(source, root)
    test_spans = collect_test_spans(source, root)

    code_lines: set[int] = set()
    comment_lines: set[int] = set()
    test_code_lines: set[int] = set()
    test_comment_lines: set[int] = set()
    main_code_lines: set[int] = set()
    main_comment_lines: set[int] = set()

    comment_by_line = group_spans_by_line(comment_spans, line_starts, line_ends)

    for line_no, (line_start, line_end) in enumerate(zip(line_starts, line_ends)):
        line_comment_spans = comment_by_line.get(line_no, [])

        # Comment and doc line accounting.
        for comment_start, comment_end, is_doc in line_comment_spans:
            segment_start = max(line_start, comment_start)
            segment_end = min(line_end, comment_end)
            if segment_start >= segment_end:
                continue
            if not has_nonspace(source, segment_start, segment_end):
                continue
            comment_lines.add(line_no)
            if span_intersects_any((segment_start, segment_end), test_spans):
                test_comment_lines.add(line_no)
            else:
                main_comment_lines.add(line_no)

        # Code line accounting after removing tree-sitter comment spans.
        cursor = line_start
        code_segments = []
        for comment_start, comment_end, _is_doc in sorted(line_comment_spans):
            segment_start = max(line_start, comment_start)
            segment_end = min(line_end, comment_end)
            if cursor < segment_start:
                code_segments.append((cursor, segment_start))
            cursor = max(cursor, segment_end)
        if cursor < line_end:
            code_segments.append((cursor, line_end))

        for segment_start, segment_end in code_segments:
            if not has_nonspace(source, segment_start, segment_end):
                continue
            code_lines.add(line_no)
            if span_intersects_any((segment_start, segment_end), test_spans):
                test_code_lines.add(line_no)
            else:
                main_code_lines.add(line_no)

    return RustLineSets(
        code_lines=code_lines,
        comment_lines=comment_lines,
        test_code_lines=test_code_lines,
        test_comment_lines=test_comment_lines,
        main_code_lines=main_code_lines,
        main_comment_lines=main_comment_lines,
    )


def parse_rust_source(source: str) -> ParsedRustSource:
    """Parse Rust source text with tree-sitter-rust."""
    source_bytes = source.encode('utf-8')
    parser = make_parser()
    tree = parser.parse(source_bytes)
    return ParsedRustSource(text=source, source=source_bytes, root=tree.root_node)


@functools.lru_cache(maxsize=1)
def rust_language():
    """Return the tree-sitter Rust language, tolerant of binding variations."""
    try:
        import tree_sitter_rust as tsrust
        from tree_sitter import Language
    except ImportError as ex:  # nocover
        raise ImportError(
            'The tree-sitter Rust backend requires optional dependencies: '
            'tree-sitter and tree-sitter-rust. Install xdev[optional] or '
            'choose --rust-parser=legacy.'
        ) from ex

    raw_language = tsrust.language()
    if isinstance(raw_language, Language):
        return raw_language
    return Language(raw_language)


def make_parser():
    """Construct a parser across recent py-tree-sitter APIs."""
    try:
        from tree_sitter import Parser
    except ImportError as ex:  # nocover
        raise ImportError(
            'The tree-sitter Rust backend requires optional dependencies: '
            'tree-sitter and tree-sitter-rust. Install xdev[optional] or '
            'choose --rust-parser=legacy.'
        ) from ex

    language = rust_language()
    try:
        return Parser(language)
    except TypeError:  # pragma: no cover - older py-tree-sitter API
        parser = Parser()
        parser.set_language(language)
        return parser


def node_text(source: bytes, node: object) -> str:
    return source[node.start_byte:node.end_byte].decode('utf-8')


def child_count(node: object) -> int:
    return node.child_count


def named_child_count(node: object) -> int:
    return node.named_child_count


def child(node: object, index: int) -> object:
    return node.child(index)


def named_child(node: object, index: int) -> object:
    return node.named_child(index)


def children(node: object) -> list[object]:
    return [child(node, i) for i in range(child_count(node))]


def named_children(node: object) -> list[object]:
    return [named_child(node, i) for i in range(named_child_count(node))]


def same_node(left: object, right: object) -> bool:
    return (
        left.type == right.type and
        left.start_byte == right.start_byte and
        left.end_byte == right.end_byte
    )


def iter_descendants(node: object) -> Iterator[object]:
    yield node
    for child_ in children(node):
        yield from iter_descendants(child_)


def iter_named_descendants(node: object) -> Iterator[object]:
    yield node
    for child_ in named_children(node):
        yield from iter_named_descendants(child_)


def attrs_immediately_before(source: bytes, node: object) -> list[object]:
    """
    Return attribute-item siblings immediately preceding ``node``.
    """
    parent = node.parent
    if parent is None:
        return []
    siblings = named_children(parent)
    node_index = None
    for index, sibling in enumerate(siblings):
        if same_node(sibling, node):
            node_index = index
            break
    if node_index is None:
        return []

    attrs: list[object] = []
    index = node_index - 1
    while index >= 0 and siblings[index].type == 'attribute_item':
        attrs.append(siblings[index])
        index -= 1
    attrs.reverse()
    return attrs


def attribute_name(attr_text: str) -> str:
    """
    Return the leading attribute path from an attribute item.
    """
    dense = ''.join(attr_text.split())
    if not dense.startswith('#[') or not dense.endswith(']'):
        return ''
    inner = dense[2:-1]
    for sep in ('(', '='):
        if sep in inner:
            inner = inner.split(sep, 1)[0]
    return inner


def attr_is_cfg_test(attr_text: str) -> bool:
    """Return True for attributes that put an item in Rust test cfg."""
    dense = ''.join(attr_text.split())
    return (
        'cfg(test)' in dense or
        'cfg(any(test' in dense or
        'cfg(all(test' in dense
    )


def attr_is_test_like(attr_text: str) -> bool:
    """Return True for ``#[test]`` or common test macro attributes."""
    name = attribute_name(attr_text)
    return name in TEST_LIKE_ATTR_NAMES or name.endswith('::test')


def attrs_are_test_context(source: bytes, attrs: Sequence[object]) -> bool:
    for attr in attrs:
        text = node_text(source, attr)
        if attr_is_cfg_test(text) or attr_is_test_like(text):
            return True
    return False


def collect_test_spans(source: bytes, root: object) -> list[tuple[int, int]]:
    """
    Return byte spans for syntax items governed by test-only attributes.
    """
    spans: list[tuple[int, int]] = []
    for node in iter_named_descendants(root):
        attrs = attrs_immediately_before(source, node)
        if not attrs:
            continue
        if not attrs_are_test_context(source, attrs):
            continue
        spans.append((attrs[0].start_byte, node.end_byte))
    return merge_spans(spans)


def collect_comment_spans(source: bytes, root: object) -> list[tuple[int, int, bool]]:
    """
    Return ``(start_byte, end_byte, is_doc)`` for tree-sitter comment nodes.

    The tree-sitter dirstats backend currently folds docs into comments. The
    ``is_doc`` flag is retained for future callers that may want this
    lower-level detail from the line-set builder.
    """
    spans: list[tuple[int, int, bool]] = []
    for node in iter_descendants(root):
        if 'comment' not in node.type:
            continue
        text = node_text(source, node).lstrip()
        is_doc = (
            text.startswith('///') or
            text.startswith('//!') or
            text.startswith('/**') or
            text.startswith('/*!')
        )
        if text.startswith('/***'):
            is_doc = False
        spans.append((node.start_byte, node.end_byte, is_doc))
    return spans


def byte_line_bounds(source: bytes) -> tuple[list[int], list[int]]:
    """
    Return byte start/end offsets for each physical line.
    """
    starts = [0]
    ends: list[int] = []
    for index, byte in enumerate(source):
        if byte == 10:  # ord('\n')
            ends.append(index)
            starts.append(index + 1)
    if starts[-1] <= len(source):
        ends.append(len(source))
    if len(starts) > len(ends):
        starts = starts[:len(ends)]
    return starts, ends


def group_spans_by_line(
    spans: Iterable[tuple[int, int, bool]],
    line_starts: Sequence[int],
    line_ends: Sequence[int],
) -> dict[int, list[tuple[int, int, bool]]]:
    grouped: dict[int, list[tuple[int, int, bool]]] = collections.defaultdict(list)
    for start, end, is_doc in spans:
        if end <= start:
            continue
        start_line = max(0, bisect.bisect_right(line_starts, start) - 1)
        # Use end - 1 because byte ranges are half-open.
        end_line = max(0, bisect.bisect_right(line_starts, end - 1) - 1)
        for line_no in range(start_line, end_line + 1):
            if line_no >= len(line_ends):
                continue
            grouped[line_no].append((start, end, is_doc))
    return grouped


def has_nonspace(source: bytes, start: int, end: int) -> bool:
    return any(not chr(byte).isspace() for byte in source[start:end])


def merge_spans(spans: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    ordered = sorted(spans)
    if not ordered:
        return []
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def span_intersects_any(span: tuple[int, int], spans: Sequence[tuple[int, int]]) -> bool:
    start, end = span
    index = bisect.bisect_right(spans, (start, float('inf'))) - 1
    if index >= 0 and spans[index][1] > start:
        return True
    index += 1
    return index < len(spans) and spans[index][0] < end


def parse_rust_content_stats_legacy(source: str) -> dict[str, int]:
    """
    Count effective Rust lines of code with the historical hand-written scanner.

    This backend intentionally preserves the old aggregate-only behavior.
    """
    n = len(source)
    i = 0
    line = 0
    line_has_code = collections.defaultdict(bool)
    comment_lines = set()
    doc_lines = set()

    def mark_comment_char(ch, is_doc):
        nonlocal line
        if ch == '\n':
            line += 1
        elif not ch.isspace():
            comment_lines.add(line)
            if is_doc:
                doc_lines.add(line)

    def mark_code_span(start, stop):
        nonlocal line
        j = start
        while j < stop:
            ch = source[j]
            if ch == '\n':
                line += 1
            elif not ch.isspace():
                line_has_code[line] = True
            j += 1

    while i < n:
        ch = source[i]

        # Rust line comments: //, ///, //!
        if source.startswith('//', i):
            is_doc = source.startswith('///', i) or source.startswith('//!', i)
            while i < n and source[i] != '\n':
                mark_comment_char(source[i], is_doc)
                i += 1
            continue

        # Rust nested block comments: /* ... */, /** ... */, /*! ... */
        if source.startswith('/*', i):
            is_doc = (
                source.startswith('/**', i) and
                not source.startswith('/***', i)
            ) or source.startswith('/*!', i)
            depth = 0
            while i < n:
                if source.startswith('/*', i):
                    depth += 1
                    mark_comment_char(source[i], is_doc)
                    mark_comment_char(source[i + 1], is_doc)
                    i += 2
                    continue
                if source.startswith('*/', i):
                    mark_comment_char(source[i], is_doc)
                    mark_comment_char(source[i + 1], is_doc)
                    i += 2
                    depth -= 1
                    if depth <= 0:
                        break
                    continue
                mark_comment_char(source[i], is_doc)
                i += 1
            continue

        # Rust raw strings: r"...", r#"..."#, br"...", br#"..."#.
        close_delim = _rust_raw_string_close_delim(source, i)
        if close_delim is not None:
            open_quote = source.find('"', i)
            stop = source.find(close_delim, open_quote + 1)
            if stop < 0:
                stop = n
            else:
                stop += len(close_delim)
            mark_code_span(i, stop)
            i = stop
            continue

        # Normal string-ish literals. This avoids treating // or /* inside a
        # string as a comment.
        if (
            ch == '"' or
            (ch in {'b', 'c'} and i + 1 < n and source[i + 1] == '"')
        ):
            stop = i + 1
            if ch in {'b', 'c'} and i + 1 < n and source[i + 1] == '"':
                stop = i + 2
            escape = False
            while stop < n:
                c = source[stop]
                stop += 1
                if escape:
                    escape = False
                elif c == '\\':
                    escape = True
                elif c == '"':
                    break
            mark_code_span(i, stop)
            i = stop
            continue

        if ch == '\n':
            line += 1
            i += 1
            continue

        if not ch.isspace():
            line_has_code[line] = True

        i += 1

    return {
        'code_lines': sum(line_has_code.values()),
        'comment_lines': len(comment_lines),
        'doc_lines': len(doc_lines),
    }


def _rust_raw_string_close_delim(source: str, pos: int):
    """
    Return the closing delimiter for a Rust raw string at ``pos``, or None.
    """
    n = len(source)
    if source.startswith(('br', 'cr'), pos):
        j = pos + 2
        prefix_len = 2
    elif pos < n and source[pos] == 'r':
        j = pos + 1
        prefix_len = 1
    else:
        return None

    while j < n and source[j] == '#':
        j += 1

    if j < n and source[j] == '"':
        hashes = source[pos + prefix_len:j]
        return '"' + hashes
    return None


__all__ = [
    'ParsedRustSource',
    'RustLineSets',
    'RUST_BACKENDS',
    'parse_rust_content_stats',
    'parse_rust_content_stats_legacy',
    'parse_rust_content_stats_treesitter',
    'parse_rust_source',
    'rust_line_sets',
]
