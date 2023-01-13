#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
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
class DocstrStubgenCLI(scfg.Config):
    name = 'doctypes'
    description = 'Generate Typed Stubs from Docstrings'
    default = {
        'module': scfg.Value(None, position=1, help=ub.paragraph(
            '''
            The name of a module in the PYTHONPATH or an explicit path to that
            module.
            ''')),
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        from xdev.cli import docstr_stubgen
        import ubelt as ub
        config = cls(cmdline=cmdline, data=kwargs)
        print(f'config={config}')
        modname_or_path = config['module']
        print(f'modname_or_path={modname_or_path}')
        if modname_or_path is None:
            raise ValueError('Must specify the module')
        modpath = docstr_stubgen.modpath_coerce(modname_or_path)
        modpath = ub.Path(modpath)
        generated = docstr_stubgen.generate_typed_stubs(modpath)

        for fpath, text in generated.items():
            fpath = ub.Path(fpath)
            print(f'Write fpath={fpath}')
            fpath.write_text(text)

        # Generate a py.typed file to mark the package as typed
        if modpath.is_dir():
            pytyped_fpath = (modpath / 'py.typed')
            print(f'touch pytyped_fpath={pytyped_fpath}')
            pytyped_fpath.touch()


@_register
class SedCLI(scfg.Config):
    name = 'sed'
    description = 'Search and replace text in files'
    default = {
        'regexpr': scfg.Value('', position=1, help=ub.paragraph(
            '''
            The pattern to search for.
            ''')),
        'repl': scfg.Value('', position=2, help=ub.paragraph(
            '''
            The pattern to replace with.
            ''')),
        'dpath': scfg.Value(None, position=3, help=ub.paragraph(
            '''
            The directory to recursively search or a file pattern to match.
            '''
        )),
        'dry': scfg.Value('ask', position=4, help=ub.paragraph(
            '''
            if 1, show what would be done. if 0, execute the change, if "ask",
            then show the dry run and then ask for confirmation.
            '''
        )),
        'include': scfg.Value(None),
        'exclude': scfg.Value(None),
        'recursive': scfg.Value(True),
        'verbose': scfg.Value(1),
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        from xdev import search_replace
        config = cls(cmdline=cmdline, data=kwargs)
        if config['verbose'] > 2:
            print('config = {}'.format(ub.repr2(dict(config), nl=1, sort=0)))

        if config['dry'] in {'ask', 'auto'}:
            from rich.prompt import Confirm
            config['dry'] = True
            search_replace.sed(**config)
            flag = Confirm.ask('Do you want to execute this sed?')
            if flag:
                config['dry'] = False
                search_replace.sed(**config)
        else:
            search_replace.sed(**config)


@_register
class FormatQuotesCLI(scfg.Config):
    name = 'format_quotes'
    description = 'Use single quotes for code and double quotes for docs'
    default = {
        'path': scfg.Value('', position=1, help=ub.paragraph(
            '''
            ''')),
        'diff': scfg.Value(True, help=ub.paragraph(
            '''
            The pattern to replace with.
            ''')),
        'write': scfg.Value(False, short_alias=['-w'], help=ub.paragraph(
            '''
            The directory to recursively search or a file pattern to match.
            '''
        )),
        'verbose': scfg.Value(3, help=ub.paragraph(
            '''
            '''
        )),
        'recursive': scfg.Value(True),
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        from xdev import format_quotes
        config = cls(cmdline=cmdline, data=kwargs)
        format_quotes.format_quotes(**config)


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


@_register
class TreeCLI(scfg.Config):
    name = 'tree'
    description = 'List a directory like a tree'

    default = {
        'cwd': scfg.Value('.', position=1),
        'max_files': scfg.Value(100),
        'colors': scfg.Value(not ub.NO_COLOR, isflag=True),
        'dirblocklist': scfg.Value(None)
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        import xdev
        config = cls(cmdline=cmdline, data=kwargs)
        print(xdev.tree_repr(**config))


@_register
class PintCLI(scfg.Config):
    """
    Converts one type of unit to another via the pint library.

    Notes:

    See Also
    --------
    The pint-convert tool comes pre-installed with pint but isn't as useful for
    in-bash computation unless you munge the output. The idea here is that when
    something like GDAL wants an environ in bytes, we can specify it in
    megabytes.

    Example Usage
    -------------
    xdev pint "10 megabytes" "bytes" --precision=0

    """
    __command__ = 'pint'
    description = 'Converts one type of unit to another via the pint library.'
    # input_expr = scfg.Value(None, position=1)
    # output_expr = scfg.Value(None, position=2)
    default = {
        'input_expr': scfg.Value(None, position=1),
        'output_unit': scfg.Value(None, position=2),
        'precision': scfg.Value(0, type=int),
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        import pint
        ureg = pint.UnitRegistry()
        args = cls(cmdline=cmdline, data=kwargs)
        input = ureg.parse_expression(args['input_expr'])
        output_unit = args['output_unit']
        if output_unit is None:
            output_unit = input.unit
        output = input.to(output_unit)
        if args['precision'] == 0:
            print(int(output.magnitude))
        else:
            print(output.magnitude)


@_register
class ModpathCLI(scfg.Config):
    """
    Prints the path corresponding to a Python module

    Example Usage
    -------------
    # Simply ask where a module is stored
    xdev modpath xdev
    xdev modpath numpy

    # Use this feature in scripts for developement to avoid referencing
    # machine-specific paths.
    MODPATH=$(xdev modpath ubelt)
    echo "MODPATH = $MODPATH"
    """
    __command__ = 'modpath'
    description = 'Prints the path corresponding to a Python module'
    # input_expr = scfg.Value(None, position=1)
    # output_expr = scfg.Value(None, position=2)
    default = {
        'modname': scfg.Value(None, position=1),
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        args = cls(cmdline=cmdline, data=kwargs)
        modpath = ub.modname_to_modpath(args['modname'])
        print(modpath)


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
            cmdname = getattr(cli_cls, '__command__', getattr(cli_cls, 'name', None))
            # cmdname = cli_cls.name
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

        import os
        WATCH_LOOSE_CLI = os.environ.get('XDEV_LOOSE_CLI', '')
        if WATCH_LOOSE_CLI:
            ns = parser.parse_known_args()[0]
        else:
            ns = parser.parse_args()
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
            ret = sub_main(cmdline=False, **kw)
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
