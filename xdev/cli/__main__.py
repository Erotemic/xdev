#!/usr/bin/env python
import scriptconfig as scfg
import argparse
import ubelt as ub
import sys


class RawDescriptionDefaultsHelpFormatter(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter):
    pass


_SUB_CLIS = []


def _register(cli_cls):
    _SUB_CLIS.append(cli_cls)
    return cli_cls


@_register
class CodeblockCLI(scfg.Config):
    name = 'codeblock'
    description = 'Remove indentation from text'
    default = {
        'text': scfg.Value('', position=1, help='text to dedent'),
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        config = cls(cmdline=cmdline, data=kwargs)
        print(ub.codeblock(config['text']))


@_register
class InfoCLI(scfg.Config):
    name = 'info'
    description = 'Info about xdev'
    default = {}

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        import xdev
        print('sys.version_info = {!r}'.format(sys.version_info))
        print('xdev.__version__ = {!r}'.format(xdev.__version__))
        print('xdev.__file__ = {!r}'.format(xdev.__file__))


@_register
class SedCLI(scfg.Config):
    name = 'sed'
    description = 'Search and replace text in files'
    default = {
        'regexpr': scfg.Value('', position=1),
        'repl': scfg.Value('', position=2),
        'dpath': scfg.Value(None, position=3),
        'include': scfg.Value(None),
        'exclude': scfg.Value(None),
        'recursive': scfg.Value(True),
        'dry': scfg.Value(True),
        'verbose': scfg.Value(1),
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        from xdev import search_replace
        config = cls(cmdline=cmdline, data=kwargs)
        search_replace.sed(**config)


@_register
class FindCLI(scfg.Config):
    name = 'find'
    description = 'Find files based on names'
    default = {
        'pattern': scfg.Value('', position=1),
        'dpath': scfg.Value(None, position=2),
        'include': scfg.Value(None),
        'exclude': scfg.Value(None),
        'type': scfg.Value('f', help="can be f and/or d"),
        'recursive': scfg.Value(True),
        'followlinks': scfg.Value(False),
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        from xdev import search_replace
        config = cls(cmdline=cmdline, data=kwargs)
        for found in search_replace.find(**config):
            print(found)


class ModalCLI(object):
    """
    Contains multiple scriptconfig.Config items with corresponding `main`
    functions.
    """
    def __init__(self, description='', sub_clis=[], version=None):
        self.description = description
        self.sub_clis = sub_clis
        self.version = version

    def build_parser(self):
        parser = argparse.ArgumentParser(
            description=self.description,
            formatter_class=RawDescriptionDefaultsHelpFormatter,
        )

        if self.version is not None:
            parser.add_argument('--version', action='store_true',
                                help='show version number and exit')

        subparsers = parser.add_subparsers(help='specify a command to run')
        for cli_cls in self.sub_clis:
            cmdname = cli_cls.name
            subconfig = cli_cls()
            parserkw = {}
            aliases = getattr(cli_cls, 'aliases', [])
            if aliases:
                parserkw['aliases']  = aliases
            parserkw.update(subconfig._parserkw())
            parserkw['help'] = parserkw['description'].split('\n')[0]
            subparser = subparsers.add_parser(cmdname, **parserkw)
            subparser = subconfig.argparse(subparser)
            subparser.set_defaults(main=cli_cls.main)
        return parser

    def run(self):
        parser = self.build_parser()

        ns = parser.parse_known_args()[0]
        kw = ns.__dict__

        if kw.pop('version'):
            print(self.version)
            return 0

        sub_main = kw.pop('main', None)
        if sub_main is None:
            parser.print_help()
            raise ValueError('no command given')
            return 1

        try:
            ret = sub_main(cmdline=True, **kw)
        except Exception as ex:
            print('ERROR ex = {!r}'.format(ex))
            raise
            return 1
        else:
            if ret is None:
                ret = 0
            return ret


def main():
    import xdev
    modal_cli = ModalCLI(
        description='The XDEV CLI',
        version=xdev.__version__,
        sub_clis=_SUB_CLIS,
    )
    modal_cli.run()


if __name__ == '__main__':
    """
    CommandLine:
        xdev --help
        xdev --version
        xdev info
        xdev sed "main" "MAIN" "." --dry=True --include="*_*.py"
        xdev find "*_*.py"  '.'
        xdev codeblock "
            import sys
            print(sys.argv)
            print([
                'hello world'
            ])
        "
    """
    main()
