from pathlib import Path


def test_dirstats_counts_text_total_lines(tmp_path):
    from xdev.directory_walker import parse_file_stats

    fpath = tmp_path / 'notes.md'
    fpath.write_text('# title\n\nbody', encoding='utf8')

    stats = parse_file_stats(fpath, parse_content=True)

    assert stats['md.total'] == 3
    assert 'md.main_code' not in stats


def test_dirstats_rust_analysis_is_opt_in(tmp_path):
    from xdev.directory_walker import parse_file_stats

    fpath = tmp_path / 'src' / 'lib.rs'
    fpath.parent.mkdir()
    fpath.write_text('//! module docs\nfn prod() {}\n', encoding='utf8')

    text_only = parse_file_stats(fpath, parse_content=True)
    analyzed = parse_file_stats(fpath, parse_content=True, parse_rust=True)

    assert text_only['rs.total'] == 2
    assert 'rs.main_code' not in text_only
    assert analyzed['rs.main_code'] == 1
    assert analyzed['rs.main_comments'] == 1
    assert 'rs.production_code_lines' not in analyzed


def test_dirstats_rust_test_breakdown(tmp_path):
    from xdev.directory_walker import parse_file_stats

    fpath = tmp_path / 'src' / 'lib.rs'
    fpath.parent.mkdir()
    fpath.write_text(
        '\n'.join(
            [
                'fn prod() {}',
                '#[cfg(test)]',
                'mod tests {',
                '    /// docs',
                '    #[test]',
                '    fn foo() {',
                '        assert!(true);',
                '    }',
                '}',
            ]
        )
        + '\n',
        encoding='utf8',
    )

    stats = parse_file_stats(fpath, parse_content=True, parse_rust=True)

    assert stats['rs.main_code'] == 1
    assert stats['rs.main_comments'] == 0
    assert stats['rs.test_code'] >= 4
    assert stats['rs.test_comments'] == 1
    assert not any('production' in k for k in stats)


def test_dirstats_python_uses_main_columns(tmp_path):
    from xdev.directory_walker import parse_file_stats

    fpath = tmp_path / 'tests' / 'test_demo.py'
    fpath.parent.mkdir()
    fpath.write_text(
        '"""module docs"""\n'
        '# comment\n'
        'def test_foo():\n'
        '    """function docs"""\n'
        '    assert True  # trailing\n',
        encoding='utf8',
    )

    stats = parse_file_stats(fpath, parse_content=True, parse_python=True)

    assert stats['py.total'] == 5
    assert stats['py.main_code'] >= 2
    assert stats['py.main_comments'] >= 4
    assert 'py.test_code' not in stats
    assert 'py.test_comments' not in stats


def test_dirstats_does_not_read_directories_as_text(tmp_path):
    from xdev.directory_walker import parse_file_stats

    dpath = tmp_path / 'assets'
    dpath.mkdir()

    stats = parse_file_stats(dpath, parse_content=True)

    assert stats['.files'] == 1
    assert '.total' not in stats


def test_dirstats_does_not_read_symlinked_directories_as_text(tmp_path):
    from xdev.directory_walker import parse_file_stats

    target = tmp_path / 'real_assets'
    target.mkdir()
    link = tmp_path / 'assets'
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        return

    stats = parse_file_stats(link, parse_content=True)

    assert stats['.files'] == 1
    assert '.total' not in stats


def test_dirstats_report_text_surfaces_language_breakdown(tmp_path):
    from xdev.directory_walker import dirstats_report_text

    src = tmp_path / 'src'
    src.mkdir()
    (src / 'lib.rs').write_text(
        '//! crate docs\n'
        'fn prod() {}\n'
        '#[cfg(test)]\n'
        'mod tests {\n'
        '    #[test]\n'
        '    fn demo() { assert!(true); }\n'
        '}\n',
        encoding='utf8',
    )
    (src / 'tool.py').write_text(
        '# comment\nprint("hi")\n',
        encoding='utf8',
    )
    (src / 'notes.md').write_text('# Notes\n\nbody\n', encoding='utf8')

    text = dirstats_report_text(
        tmp_path,
        max_display_depth=2,
        parse_content=True,
        python=True,
        rust=True,
    )

    assert 'main_code' in text
    assert 'main_comments' in text
    assert 'test_code' in text
    assert 'test_comments' in text
    assert 'total' in text
    assert 'src/lib.rs' in text
    assert 'src/tool.py' in text
    assert 'src/notes.md' in text
    assert 'production_code_lines' not in text
