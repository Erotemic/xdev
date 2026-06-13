import pytest
import ubelt as ub

from xdev import rust_analysis
from xdev.directory_walker import parse_file_stats


RUST_SAMPLE = ub.codeblock(
    r"""
    #[cfg(test)]
    mod tests {
        // test comment
        #[test]
        fn it_works() {
            assert_eq!(1 + 1, 2); // inline test
        }
    }

    fn main() {
        println!("http://example.com"); // prod trailing comment
        let raw = r#"// not a comment"#;
    }

    /// main docs
    pub fn documented() {}
    """
)


MIXED_COMMENT_RUST_SAMPLE = ub.codeblock(
    r"""
    fn trailing_block() {} /* trailing block comment */
    /* leading block comment */ fn leading_block() {}
    fn trailing_line() {} // trailing line comment
    /* comment-only block */
    """
)


def _assert_rust_breakdown_is_partition(stats, source):
    breakdown_total = (
        stats.get('main_code', 0)
        + stats.get('main_comments', 0)
        + stats.get('test_code', 0)
        + stats.get('test_comments', 0)
    )
    # Blank lines are excluded from the code/comment breakdown, but no
    # physical line should be counted in more than one breakdown bucket.
    assert breakdown_total <= len(source.splitlines())


def test_rust_legacy_backend_preserves_aggregate_stats():
    stats = rust_analysis.parse_rust_content_stats(
        RUST_SAMPLE, backend='legacy'
    )
    assert stats['code_lines'] > 0
    assert stats['comment_lines'] == 2
    assert stats['doc_lines'] == 1
    assert 'test_code_lines' not in stats
    assert 'production_code_lines' not in stats


def test_rust_treesitter_backend_splits_main_and_test_lines():
    pytest.importorskip('tree_sitter')
    pytest.importorskip('tree_sitter_rust')

    stats = rust_analysis.parse_rust_content_stats(
        RUST_SAMPLE, backend='tree-sitter'
    )

    assert stats == {
        'main_code': 5,
        'main_comments': 1,
        'test_code': 7,
        'test_comments': 1,
    }
    assert 'doc_lines' not in stats
    assert 'comment_lines' not in stats
    assert 'code_lines' not in stats
    assert 'production_code_lines' not in stats
    _assert_rust_breakdown_is_partition(stats, RUST_SAMPLE)


def test_parse_file_stats_can_use_legacy_rust_backend(tmp_path):
    fpath = tmp_path / 'main.rs'
    fpath.write_text(RUST_SAMPLE)

    stats = parse_file_stats(fpath, parse_content=True, rust_backend='legacy')

    assert stats['rs.files'] == 1
    assert stats['rs.total'] == len(RUST_SAMPLE.splitlines())
    assert stats['rs.comment_lines'] == 2
    assert stats['rs.doc_lines'] == 1
    assert 'rs.test_code' not in stats
    assert 'rs.total_lines' not in stats


def test_parse_file_stats_treesitter_uses_short_column_names(tmp_path):
    pytest.importorskip('tree_sitter')
    pytest.importorskip('tree_sitter_rust')

    fpath = tmp_path / 'main.rs'
    fpath.write_text(RUST_SAMPLE)

    stats = parse_file_stats(
        fpath, parse_content=True, rust_backend='tree-sitter'
    )

    assert stats['rs.files'] == 1
    assert stats['rs.total'] == len(RUST_SAMPLE.splitlines())
    assert stats['rs.main_code'] == 5
    assert stats['rs.main_comments'] == 1
    assert stats['rs.test_code'] == 7
    assert stats['rs.test_comments'] == 1
    assert 'rs.total_lines' not in stats
    assert 'rs.doc_lines' not in stats
    assert 'rs.production_code_lines' not in stats
    assert (
        stats['rs.main_code']
        + stats['rs.main_comments']
        + stats['rs.test_code']
        + stats['rs.test_comments']
    ) <= stats['rs.total']



def test_parse_file_stats_rust_does_not_probe_generic_text_by_default(tmp_path):
    rs_fpath = tmp_path / 'lib.rs'
    rs_fpath.write_text(RUST_SAMPLE)
    md_fpath = tmp_path / 'README.md'
    readme_lines = ['# docs'] + [f'line {idx}' for idx in range(5)]
    md_fpath.write_text('\n'.join(readme_lines))

    rs_stats = parse_file_stats(
        rs_fpath, parse_content=True, parse_rust=True
    )
    md_stats = parse_file_stats(
        md_fpath, parse_content=True, parse_rust=True
    )

    assert rs_stats['rs.total'] == len(RUST_SAMPLE.splitlines())
    assert md_stats['md.files'] == 1
    assert 'md.total' not in md_stats

    md_stats_with_opt_in = parse_file_stats(
        md_fpath,
        parse_content=True,
        parse_rust=True,
        textline_exts='md,rst',
    )
    assert md_stats_with_opt_in['md.total'] == len(readme_lines)



def test_coerce_textline_exts_uses_csv_strings():
    from xdev.directory_walker import _coerce_textline_exts

    assert _coerce_textline_exts('md,rst') == {'.md', '.rst'}
    assert _coerce_textline_exts(' .md, .rst , "txt" ') == {
        '.md',
        '.rst',
        '.txt',
    }
    assert _coerce_textline_exts('') == set()



def test_rust_dirstats_does_not_probe_every_text_file_by_default(tmp_path):
    from xdev.directory_walker import DirectoryWalker

    crate = tmp_path / 'crate'
    src = crate / 'src'
    src.mkdir(parents=True)
    (src / 'lib.rs').write_text(RUST_SAMPLE)
    readme_lines = ['# docs'] + [f'line {idx}' for idx in range(30)]
    (crate / 'README.md').write_text('\n'.join(readme_lines))

    walker = DirectoryWalker(
        tmp_path, parse_content=True, rust=True, show_progress=False
    )
    walker.build()

    row = walker._summary_row_for_node(crate, humanize=False)
    rust_total = len(RUST_SAMPLE.splitlines())
    assert row['files'] == 1
    assert row['total'] == rust_total
    assert (
        row['main_code']
        + row['main_comments']
        + row['test_code']
        + row['test_comments']
    ) <= row['total']

    ext_table = walker._stats_table_for_node(crate, humanize=False)
    assert ext_table.loc['rs', 'total'] == rust_total
    assert ext_table.loc['md', 'files'] == 1
    assert ext_table.loc['md', 'total'] == 0
    assert ext_table.loc['∑ total', 'total'] == rust_total



def test_textlines_option_adds_generic_text_to_rust_summary(tmp_path):
    from xdev.directory_walker import DirectoryWalker

    crate = tmp_path / 'crate'
    src = crate / 'src'
    src.mkdir(parents=True)
    (src / 'lib.rs').write_text(RUST_SAMPLE)
    readme_lines = ['# docs'] + [f'line {idx}' for idx in range(30)]
    (crate / 'README.md').write_text('\n'.join(readme_lines))

    walker = DirectoryWalker(
        tmp_path,
        parse_content=True,
        rust=True,
        textlines='md,rst',
        show_progress=False,
    )
    walker.build()

    row = walker._summary_row_for_node(crate, humanize=False)
    rust_total = len(RUST_SAMPLE.splitlines())
    assert row['files'] == 2
    assert row['total'] == rust_total + len(readme_lines)
    assert (
        row['main_code']
        + row['main_comments']
        + row['test_code']
        + row['test_comments']
    ) <= row['total']

    ext_table = walker._stats_table_for_node(crate, humanize=False)
    assert ext_table.loc['rs', 'total'] == rust_total
    assert ext_table.loc['md', 'total'] == len(readme_lines)
    assert ext_table.loc['∑ total', 'total'] == rust_total + len(readme_lines)


def test_mixed_comment_lines_are_not_double_counted_by_legacy_backend():
    stats = rust_analysis.parse_rust_content_stats(
        MIXED_COMMENT_RUST_SAMPLE, backend='legacy'
    )
    assert stats['code_lines'] == 3
    assert stats['comment_lines'] == 1
    assert stats['doc_lines'] == 0


def test_mixed_comment_lines_are_not_double_counted_by_dirstats_backend():
    from xdev.directory_walker import parse_rust_content_stats

    stats = parse_rust_content_stats(MIXED_COMMENT_RUST_SAMPLE)
    assert stats == {
        'main_code': 3,
        'main_comments': 1,
        'test_code': 0,
        'test_comments': 0,
    }
    _assert_rust_breakdown_is_partition(stats, MIXED_COMMENT_RUST_SAMPLE)


def test_mixed_comment_lines_are_not_double_counted_by_treesitter_backend():
    pytest.importorskip('tree_sitter')
    pytest.importorskip('tree_sitter_rust')

    stats = rust_analysis.parse_rust_content_stats(
        MIXED_COMMENT_RUST_SAMPLE, backend='tree-sitter'
    )
    assert stats == {
        'main_code': 3,
        'main_comments': 1,
        'test_code': 0,
        'test_comments': 0,
    }
    _assert_rust_breakdown_is_partition(stats, MIXED_COMMENT_RUST_SAMPLE)


def test_treesitter_line_sets_partition_mixed_physical_lines(monkeypatch):
    source = (
        b'/* c */ fn a() {}\n'
        b'fn b() {} // c\n'
        b'// only\n'
        b'#[test] fn t() {} fn main() {}\n'
    )

    class Root:
        pass

    parsed = rust_analysis.ParsedRustSource(
        text=source.decode('utf8'), source=source, root=Root()
    )
    comment_spans = [
        (0, 7, False),    # leading comment before code: code line
        (28, 32, False),  # trailing comment after code: code line
        (33, 40, False),  # comment-only line: comment line
    ]
    test_spans = [(41, 58)]
    monkeypatch.setattr(
        rust_analysis,
        'collect_comment_spans',
        lambda source, root: comment_spans,
    )
    monkeypatch.setattr(
        rust_analysis,
        'collect_test_spans',
        lambda source, root: test_spans,
    )

    line_sets = rust_analysis.rust_line_sets(parsed)
    stats = line_sets.to_stats()

    assert stats == {
        'main_code': 2,
        'main_comments': 1,
        'test_code': 1,
        'test_comments': 0,
    }
    partitions = [
        line_sets.main_code_lines,
        line_sets.main_comment_lines,
        line_sets.test_code_lines,
        line_sets.test_comment_lines,
    ]
    assert sum(map(len, partitions)) == len(set().union(*partitions))
