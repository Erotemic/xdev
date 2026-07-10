import os
import shutil
import subprocess

import pytest
import ubelt as ub


def _git(repo, *args):
    return subprocess.run(
        ['git', '-C', os.fspath(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@pytest.mark.skipif(shutil.which('git') is None, reason='requires git')
def test_directory_walker_respects_gitignore_by_default(tmp_path):
    from xdev.directory_walker import DirectoryWalker

    repo = ub.Path(tmp_path)
    _git(repo, 'init', '-q')

    global_ignore = repo / 'global-ignore'
    global_ignore.write_text('global-only.txt\n')
    _git(repo, 'config', 'core.excludesFile', os.fspath(global_ignore))

    (repo / '.gitignore').write_text(
        'ignored-dir/\n'
        '*.tmp\n'
        '!keep.tmp\n'
    )
    info_exclude = repo / '.git' / 'info' / 'exclude'
    info_exclude.write_text(info_exclude.read_text() + '\ninfo-only.txt\n')

    (repo / 'ignored-dir').mkdir()
    (repo / 'ignored-dir' / 'payload.txt').write_text('ignored\n')
    (repo / 'drop.tmp').write_text('ignored\n')
    (repo / 'tracked-but-ignored.tmp').write_text('ignored\n')
    (repo / 'keep.tmp').write_text('kept\n')
    (repo / 'info-only.txt').write_text('ignored\n')
    (repo / 'global-only.txt').write_text('ignored\n')
    (repo / 'visible.txt').write_text('kept\n')

    nested = (repo / 'nested').ensuredir()
    (nested / '.gitignore').write_text('cache/\n')
    (nested / 'cache').mkdir()
    (nested / 'cache' / 'payload.txt').write_text('ignored\n')
    (nested / 'visible.txt').write_text('kept\n')

    # ripgrep/fd-style filtering applies ignore rules even when a matching file
    # was force-added to the index.
    _git(repo, 'add', '-f', 'tracked-but-ignored.tmp')

    walker = DirectoryWalker(
        repo,
        parse_content=False,
        show_progress=False,
    ).build()
    files = {path.relative_to(repo).as_posix() for path in walker.file_paths}
    dirs = {path.relative_to(repo).as_posix() for path in walker.dir_paths}

    assert 'visible.txt' in files
    assert 'keep.tmp' in files
    assert 'nested/visible.txt' in files
    assert 'drop.tmp' not in files
    assert 'tracked-but-ignored.tmp' not in files
    assert 'info-only.txt' not in files
    assert 'global-only.txt' not in files
    assert 'ignored-dir' not in dirs
    assert 'nested/cache' not in dirs


@pytest.mark.skipif(shutil.which('git') is None, reason='requires git')
def test_directory_walker_can_disable_gitignore(tmp_path):
    from xdev.directory_walker import DirectoryWalker

    repo = ub.Path(tmp_path)
    _git(repo, 'init', '-q')
    (repo / '.gitignore').write_text('ignored-dir/\n*.tmp\n')
    (repo / 'ignored-dir').mkdir()
    (repo / 'ignored-dir' / 'payload.txt').write_text('visible\n')
    (repo / 'drop.tmp').write_text('visible\n')

    walker = DirectoryWalker(
        repo,
        respect_gitignore=False,
        parse_content=False,
        show_progress=False,
    ).build()
    files = {path.relative_to(repo).as_posix() for path in walker.file_paths}
    dirs = {path.relative_to(repo).as_posix() for path in walker.dir_paths}

    assert 'drop.tmp' in files
    assert 'ignored-dir/payload.txt' in files
    assert 'ignored-dir' in dirs


def test_dirstats_cli_gitignore_flags():
    from xdev.cli.dirstats import DirectoryStatsCLI

    default = DirectoryStatsCLI.cli(argv=[], strict=True)
    no_ignore = DirectoryStatsCLI.cli(argv=['--no-ignore'], strict=True)
    no_ignore_vcs = DirectoryStatsCLI.cli(
        argv=['--no-ignore-vcs'], strict=True
    )
    no_gitignore = DirectoryStatsCLI.cli(
        argv=['--no-gitignore'], strict=True
    )

    assert default.respect_gitignore is True
    assert no_ignore.respect_gitignore is False
    assert no_ignore_vcs.respect_gitignore is False
    assert no_gitignore.respect_gitignore is False


@pytest.mark.skipif(shutil.which('git') is None, reason='requires git')
def test_nested_repo_ignore_with_dotdirs_hidden(tmp_path):
    from xdev.directory_walker import DirectoryWalker

    root = ub.Path(tmp_path)
    repo = (root / 'nested-repo').ensuredir()
    _git(repo, 'init', '-q')
    (repo / '.gitignore').write_text('build/\n')
    (repo / 'build').mkdir()
    (repo / 'build' / 'artifact.bin').write_text('ignored\n')
    (repo / 'source.py').write_text('visible\n')

    walker = DirectoryWalker(
        root,
        exclude_dnames=['.*'],
        exclude_fnames=['.*'],
        parse_content=False,
        show_progress=False,
    ).build()
    files = {path.relative_to(root).as_posix() for path in walker.file_paths}
    dirs = {path.relative_to(root).as_posix() for path in walker.dir_paths}

    assert 'nested-repo/source.py' in files
    assert 'nested-repo/build' not in dirs
    assert not any(path.startswith('nested-repo/.git/') for path in files)


def test_gitignore_requires_a_git_worktree(tmp_path):
    from xdev.directory_walker import DirectoryWalker

    root = ub.Path(tmp_path)
    (root / '.gitignore').write_text('*.tmp\n')
    (root / 'not-in-a-repo.tmp').write_text('visible\n')

    walker = DirectoryWalker(
        root,
        parse_content=False,
        show_progress=False,
    ).build()
    files = {path.relative_to(root).as_posix() for path in walker.file_paths}

    assert 'not-in-a-repo.tmp' in files
