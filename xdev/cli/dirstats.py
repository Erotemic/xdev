#!/usr/bin/env python3
import scriptconfig as scfg
import ubelt as ub
import os

if not os.environ.get('_ARGCOMPLETE', ''):
    # Hack for backwards compat
    from xdev.directory_walker import DirectoryWalker  # NOQA


class DirectoryStatsCLI(scfg.DataConfig):
    """
    Analysis for code in a repository

    CommandLine:
        python ~/code/xdev/xdev/cli/repo_stats.py .
    """
    __command__ = 'dirstats'

    dpath = scfg.Value('.', type=str, help='path to the git repo. If prefixed with ``module:``, then treated as a python module', position=1)

    exclude_dnames = scfg.Value(None, help='A coercable multi-pattern. If "py:auto" chooses sensible defaults for a Python dev.', nargs='+', alias=['block_dnames'])

    exclude_fnames = scfg.Value(None, help='A coercable multi-pattern. If "py:auto" chooses sensible defaults for a Python dev.', nargs='+', alias=['block_fnames'])

    include_dnames = scfg.Value(None, help='A coercable multi-pattern. Only directory names matching this pattern will be considered', nargs='+')
    include_fnames = scfg.Value(None, help='A coercable multi-pattern. Only file names matching this pattern will be considered', nargs='+')

    parse_content = scfg.Value(False, isflag=True, help='if True parse stats about the content of each file')
    max_files = scfg.Value(None)
    # parse_meta_stats = scfg.Value(True, isflag=True, help='if True parse stats about the content of each file')

    max_walk_depth = scfg.Value(None, short_alias=['L'], help='maximum depth to walk')
    max_display_depth = scfg.Value(None, short_alias=['D'], help='maximum depth to display')

    verbose = scfg.Value(0, isflag=True, short_alias=['-v'])
    version = scfg.Value(False, isflag=True, short_alias=['-V'])
    python = scfg.Value(False, isflag=True, help='enable python repository defaults', alias=['pydev'])

    ignore_dotprefix = scfg.Value(True, isflag=True, help='if True ignore directories and folders with a dot prefix')

    def __post_init__(config):
        if config.dpath.startswith('module:'):
            config.dpath = ub.modname_to_modpath(config.dpath.split('module:', 1)[1])

        if config.exclude_fnames is None:
            config.exclude_fnames = []
        if config.exclude_dnames is None:
            config.exclude_dnames = []

        if config.ignore_dotprefix:
            config.exclude_fnames.append('.*')
            config.exclude_dnames.append('.*')

        if config.python:
            config.exclude_fnames += [
                '*.pyc',
                '*.pyi',
            ]
            config.exclude_dnames += [
                # '_*',
                '__pycache__',
                '_static',
                '_modules',
                'htmlcov',
                # '.*',
            ]

    @classmethod
    def _register_main(cls, func):
        cls.main = func
        return func

__cli__ = DirectoryStatsCLI


@__cli__._register_main
def main(cmdline=1, **kwargs):
    """
    Example:
        >>> # xdoctest: +SKIP
        >>> cmdline = 0
        >>> kwargs = dict(dpath='module:watch')
        >>> main(cmdline=cmdline, **kwargs)
    """
    config = DirectoryStatsCLI.cli(cmdline=cmdline, data=kwargs, strict=True)

    import rich
    if config.verbose:
        kwargs = {'dpath': ub.modname_to_modpath('kwarray')}
    rich.print('config = ' + ub.urepr(config, nl=1))

    from xdev.directory_walker import DirectoryWalker  # NOQA
    kwargs = ub.udict(config) & {
        'dpath', 'exclude_dnames', 'exclude_fnames', 'include_dnames',
        'include_fnames', 'max_walk_depth', 'parse_content', 'max_files'
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
