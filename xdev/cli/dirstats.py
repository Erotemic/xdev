#!/usr/bin/env python3
import os

import kwconf
import ubelt as ub

if not os.environ.get('_ARGCOMPLETE', ''):
    # Hack for backwards compat
    from xdev.directory_walker import DirectoryWalker  # NOQA


class DirectoryStatsCLI(kwconf.Config):
    """
    Analysis for code in a repository

    CommandLine:
        python ~/code/xdev/xdev/cli/repo_stats.py .
    """

    __command__ = 'dirstats'

    dpath = kwconf.Value(
        '.',
        parser=str,
        help='path to the git repo. If prefixed with ``module:``, then treated as a python module',
        position=1,
    )

    exclude_dnames = kwconf.Value(
        None,
        help='A coercable multi-pattern. If "py:auto" chooses sensible defaults for a Python dev.',
        nargs='+',
        alias=['block_dnames'],
    )

    exclude_fnames = kwconf.Value(
        None,
        help='A coercable multi-pattern. If "py:auto" chooses sensible defaults for a Python dev.',
        nargs='+',
        alias=['block_fnames'],
    )

    include_dnames = kwconf.Value(
        None,
        help='A coercable multi-pattern. Only directory names matching this pattern will be considered',
        nargs='+',
    )
    include_fnames = kwconf.Value(
        None,
        help='A coercable multi-pattern. Only file names matching this pattern will be considered',
        nargs='+',
    )

    parse_content = kwconf.Flag(
        True,
        help='if True count total lines for text-like files. Language flags add richer parsers.',
    )
    max_files = kwconf.Value(None)
    # parse_meta_stats = kwconf.Value(True, isflag=True, help='if True parse stats about the content of each file')

    max_walk_depth = kwconf.Value(
        None, short_alias=['L'], help='maximum depth to walk'
    )
    max_display_depth = kwconf.Value(
        None, short_alias=['D'], help='maximum depth to display'
    )

    verbose = kwconf.Value(0, isflag='counter', short_alias=['v'])
    version = kwconf.Flag(False, short_alias=['V'])
    python = kwconf.Flag(
        False,
        help='enable Python defaults and code/doc line analysis',
        alias=['pydev'],
    )
    rust = kwconf.Flag(
        False,
        help='enable Rust defaults and code/comment/test line analysis',
        alias=['rsdev'],
    )
    textlines = kwconf.Value(
        None,
        parser=str,
        help=(
            'Optional comma-separated generic text extensions to count raw '
            'total lines for when language analyzers are active, e.g. '
            '--textlines=md,rst. Without --python/--rust, omitted preserves '
            'broad UTF-8 text probing.'
        ),
        alias=['text_lines'],
    )

    respect_gitignore = kwconf.Flag(
        True,
        alias=['ignore', 'ignore_vcs', 'gitignore'],
        help=(
            'respect Git ignore rules from .gitignore, .git/info/exclude, '
            'and the configured global excludes file. Disable with '
            '--no-ignore or --no-ignore-vcs.'
        ),
    )

    ignore_dotprefix = kwconf.Flag(
        True,
        help='if True ignore directories and folders with a dot prefix',
    )

    def __post_init__(config):
        def _flatten_pattern_args(values):
            """Preserve the historical comma-or-space list syntax."""
            if values is None:
                return []
            if isinstance(values, str):
                values = [values]
            flattened = []
            for value in values:
                if isinstance(value, str):
                    flattened.extend(value.split(','))
                else:
                    flattened.append(value)
            return flattened

        if config.dpath.startswith('module:'):  # type: ignore
            config.dpath = ub.modname_to_modpath(
                config.dpath.split('module:', 1)[1]
            )  # type: ignore

        config.exclude_fnames = _flatten_pattern_args(config.exclude_fnames)
        config.exclude_dnames = _flatten_pattern_args(config.exclude_dnames)
        if config.include_fnames is not None:
            config.include_fnames = _flatten_pattern_args(
                config.include_fnames
            )
        if config.include_dnames is not None:
            config.include_dnames = _flatten_pattern_args(
                config.include_dnames
            )

        if config.ignore_dotprefix:
            config.exclude_fnames.append('.*')  # type: ignore
            config.exclude_dnames.append('.*')  # type: ignore

        if config.python:
            config.exclude_fnames += [  # type: ignore
                '*.pyc',
                '*.pyi',
            ]
            config.exclude_dnames += [  # type: ignore
                # '_*',
                '__pycache__',
                '_static',
                '_modules',
                'htmlcov',
                # '.*',
            ]

        if config.rust:
            # Effective Rust LOC requires content parsing. Generic text line
            # totals are intentionally opt-in via --textlines when language
            # analyzers are active.
            config.parse_content = True  # type: ignore

            config.exclude_fnames += [  # type: ignore
                'Cargo.lock',
            ]
            config.exclude_dnames += [  # type: ignore
                'target',
            ]

    @classmethod
    def _register_main(cls, func):
        cls.main = func
        return func


__cli__ = DirectoryStatsCLI


@__cli__._register_main
def main(argv=1, **kwargs):
    """
    Example:
        >>> # xdoctest: +SKIP
        >>> argv = 0
        >>> kwargs = dict(dpath='module:watch')
        >>> main(argv=argv, **kwargs)
    """
    config = DirectoryStatsCLI.cli(argv=argv, data=kwargs, strict=True)  # type: ignore

    import rich

    if config.verbose:
        kwargs = {'dpath': ub.modname_to_modpath('kwarray')}
    rich.print('config = ' + ub.urepr(config, nl=1))

    from xdev.directory_walker import DirectoryWalker  # NOQA

    kwargs = ub.udict(config) & {  # type: ignore
        'dpath',
        'exclude_dnames',
        'exclude_fnames',
        'include_dnames',
        'include_fnames',
        'max_walk_depth',
        'parse_content',
        'max_files',
        'python',
        'rust',
        'textlines',
        'respect_gitignore',
    }
    self = DirectoryWalker(**kwargs)
    self.build()
    nxtxt_kwargs = {'max_depth': config['max_display_depth']}
    self.write_report(**nxtxt_kwargs)


if __name__ == '__main__':
    """

    CommandLine:
        python ~/code/xdev/xdev/cli/repo_stats.py
        python -m repo_analysis
    """
    main()
