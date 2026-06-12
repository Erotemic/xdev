import pytest
import ubelt as ub

from xdev import rust_analysis
from xdev.directory_walker import parse_file_stats


RUST_SAMPLE = ub.codeblock(
    r'''
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
    ''')


def test_rust_legacy_backend_preserves_aggregate_stats():
    stats = rust_analysis.parse_rust_content_stats(RUST_SAMPLE, backend='legacy')
    assert stats['code_lines'] > 0
    assert stats['comment_lines'] == 4
    assert stats['doc_lines'] == 1
    assert 'test_code_lines' not in stats
    assert 'production_code_lines' not in stats


def test_rust_treesitter_backend_splits_main_and_test_lines():
    pytest.importorskip('tree_sitter')
    pytest.importorskip('tree_sitter_rust')

    stats = rust_analysis.parse_rust_content_stats(
        RUST_SAMPLE, backend='tree-sitter')

    assert stats == {
        'main_code': 5,
        'main_comments': 2,
        'test_code': 7,
        'test_comments': 2,
    }
    assert 'doc_lines' not in stats
    assert 'comment_lines' not in stats
    assert 'code_lines' not in stats
    assert 'production_code_lines' not in stats


def test_parse_file_stats_can_use_legacy_rust_backend(tmp_path):
    fpath = tmp_path / 'main.rs'
    fpath.write_text(RUST_SAMPLE)

    stats = parse_file_stats(
        fpath, parse_content=True, rust_backend='legacy')

    assert stats['rs.files'] == 1
    assert stats['rs.total_lines'] == RUST_SAMPLE.count('\n')
    assert stats['rs.comment_lines'] == 4
    assert stats['rs.doc_lines'] == 1
    assert 'rs.test_code' not in stats


def test_parse_file_stats_treesitter_uses_short_column_names(tmp_path):
    pytest.importorskip('tree_sitter')
    pytest.importorskip('tree_sitter_rust')

    fpath = tmp_path / 'main.rs'
    fpath.write_text(RUST_SAMPLE)

    stats = parse_file_stats(
        fpath, parse_content=True, rust_backend='tree-sitter')

    assert stats['rs.files'] == 1
    assert stats['rs.total'] == RUST_SAMPLE.count('\n')
    assert stats['rs.main_code'] == 5
    assert stats['rs.main_comments'] == 2
    assert stats['rs.test_code'] == 7
    assert stats['rs.test_comments'] == 2
    assert 'rs.total_lines' not in stats
    assert 'rs.doc_lines' not in stats
    assert 'rs.production_code_lines' not in stats
