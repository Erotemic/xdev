#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""
Defines the subcommands for the xdev CLI.

Each subcommand is its own scriptconfig class, which is registered using a
decorator. Special "dunder" variables like ``__command__`` and ``__alias__``
are used to control subparser configurations. The normal scriptconfig
``__default__`` variable controls subparser arguments. Lastly each class must
have a ``main`` classmethod, which is the logic invoked when the subcommand is
called.
"""
import scriptconfig as scfg
import argparse
import ubelt as ub
import os
import sys
from xdev.cli import available_package_versions


class RawDescriptionDefaultsHelpFormatter(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter):
    pass


_SUB_CLIS = []


# Note: the order or registration is how it will appear in the CLI help
def _register(cli_cls):
    # Hack for older scriptconfig
    if not hasattr(cli_cls, 'default'):
        cli_cls.default = cli_cls.__default__
    _SUB_CLIS.append(cli_cls)
    return cli_cls


@_register
class InfoCLI(scfg.Config):
    """
    Info about xdev
    """
    __command__ = 'info'
    __default__ = {}

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        import xdev
        print('sys.version_info = {!r}'.format(sys.version_info))
        print('xdev.__version__ = {!r}'.format(xdev.__version__))
        print('xdev.__file__ = {!r}'.format(xdev.__file__))


@_register
class CodeblockCLI(scfg.Config):
    """
    Remove indentation from text
    """
    __command__ = 'codeblock'
    __default__ = {
        'text': scfg.Value('', position=1, help='text to dedent'),
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        config = cls(cmdline=cmdline, data=kwargs)
        print(ub.codeblock(config['text']))


@_register
class SedCLI(scfg.Config):
    """
    Search and replace text in files
    """
    __command__ = 'sed'
    __default__ = {
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
class FindCLI(scfg.Config):
    """
    Find matching files or paths in a directory.

    This is similar to the GNU find program, but written in Python.  Important
    differences are that this program is:

    * has pattern first argument and uses the cwd by default.

    * recursive by default

    * has explicit include / exclude options

    Example
    -------
    xdev find "*.py"
    """
    __command__ = 'find'
    __default__ = {
        'pattern': scfg.Value('', position=1),
        'dpath': scfg.Value(None, position=2, help='the path to search. Defaults to cwd'),
        'include': scfg.Value(None, help='If specified, only list results with matching basenames'),
        'exclude': scfg.Value(None, help='If specified, do not list results with matching basenames'),
        'type': scfg.Value('f', help="can be f and/or d"),
        'recursive': scfg.Value(True),
        'dirblocklist': scfg.Value(
            'Any directory matching this pattern will be removed from '
            'traveral.'),
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
    """
    List a directory like a tree

    See Also
    --------
    The apt-installable tree command

    Example
    -------
    xdev tree
    """
    __command__ = 'tree'

    __default__ = {
        'cwd': scfg.Value('.', position=1),
        'max_files': scfg.Value(100),
        'colors': scfg.Value(not ub.NO_COLOR, isflag=True),
        'dirblocklist': scfg.Value(None),
        'max_depth': scfg.Value(
            None, help='maximum depth to recurse', short_alias=['L']),
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        import xdev
        config = cls(cmdline=cmdline, data=kwargs)
        xdev.tree_repr(**config)
        # print()


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
    __alias__ = ['convert_unit']
    __default__ = {
        'input_expr': scfg.Value(None, position=1, help='A parsable pint expression with magnitude and units'),
        'output_unit': scfg.Value(None, position=2, help='The output unit to convert to'),
        'precision': scfg.Value(0, type=int, help='number of decimal places to use'),
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
class PyfileCLI(scfg.Config):
    """
    Prints the path corresponding to a Python module.

    This uses the ``ubelt.modname_to_modpath`` mechanism that does not require
    importing of your package.

    Alternatives
    ------------
    An alternative with no dependencies is to use the one-liner:

    python -c "import <modname>; print(<modname>.__file__)"

    Example Usage
    -------------
    xdev pyfile xdev
    xdev pyfile numpy

    # Use this feature in scripts for developement to avoid referencing
    # machine-specific paths.
    MODPATH=$(xdev pyfile ubelt)
    echo "MODPATH = $MODPATH"
    """
    __command__ = 'pyfile'
    __alias__ = ['modpath']
    # input_expr = scfg.Value(None, position=1)
    # output_expr = scfg.Value(None, position=2)
    __default__ = {
        'modname': scfg.Value(None, position=1),
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        args = cls(cmdline=cmdline, data=kwargs)
        modpath = ub.modname_to_modpath(args['modname'])
        print(modpath)


@_register
class PyVersionCLI(scfg.Config):
    """
    Detect and print the version of a Python module or package.

    Note
    ----
    Different backends may produce different results, especially for packages
    that are in development and were installed in development mode.

    Alternatives
    ------------
    An alternative with no dependencies is to use the one-liner:

    python -c "import <modname>; print(<modname>.__version__)"

    Example Usage
    -------------
    xdev pyversion xdev
    xdev pyversion numpy

    # Both the module name and the package name can be used.
    xdev pyversion cv2
    xdev pyversion opencv-python-headless

    xdev pyversion xdev --backend=import
    xdev pyversion xdev --backend=pkg_resources
    """
    __command__ = 'pyversion'
    __alias__ = ['modversion']
    __default__ = {
        'modname': scfg.Value(None, position=1, help='The name of the module or package'),
        'backend': scfg.Value('auto', help=ub.paragraph(
            '''
            The method to lookup the version. The core methods are 'import'
            which imports the module and looks for a ``__version__`` attribute
            or 'pkg_resources', which uses pip metadata. Can also be 'auto'
            which tries to find the first one that works.
            '''), choices=['auto', 'import', 'pkg_resources']),
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        args = cls(cmdline=cmdline, data=kwargs)
        modname = args['modname']

        if args['backend'] == 'auto':
            candidate_backends  = ['import', 'pkg_resources']
        else:
            candidate_backends = [args['backend']]

        def _getversion(modname, backend):
            if backend == 'import':
                module = ub.import_module_from_name(modname)
                version = module.__version__
            elif backend == 'pkg_resources':
                import pkg_resources
                version = pkg_resources.get_distribution(modname).version
            else:
                raise KeyError(backend)
            return version

        version = None
        for backend in candidate_backends:
            try:
                version = _getversion(modname, backend)
            except KeyError:
                raise
            except Exception:
                ...
            else:
                break
        print(version)
        if version is None:
            raise Exception(f'No version was found for {modname}')


@_register
class FormatQuotesCLI(scfg.Config):
    """
    Use single quotes for code and double quotes for docs.

    This is useful for "fixing" quotations after running a code formater like
    black on a module.
    """
    __command__ = 'format_quotes'
    __default__ = {
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
class FreshPyenvCLI(scfg.Config):
    """
    Create a fresh environment in a docker container to test a Python package.

    SeeAlso
    -------
    The generic freshpyenv.sh bash script also installed with this package.
    """
    __command__ = 'freshpyenv'
    __default__ = {
        'image': scfg.Value('__default__', help='The docker image to use')
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        config = cls(cmdline=cmdline, data=kwargs)
        import ubelt as ub
        ub.cmd(f'freshpyenv.sh --image={config["image"]}', system=True)


@_register
class DocstrStubgenCLI(scfg.Config):
    """
    Generate Typed Stubs from Docstrings (experimental)

    Note
    ----
    This is an experimental command and currently requires a specialized patch
    to mypy to work correctly.
    """
    __command__ = 'docstubs'
    __alias__ = ['doctypes']
    __default__ = {
        'module': scfg.Value(None, position=1, help=ub.paragraph(
            '''
            The name of a module in the PYTHONPATH or an explicit path to that
            module.
            ''')),
    }

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        from xdev.cli import docstr_stubgen
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
class AvailablePackageCLI(scfg.Config):
    __command__ = 'available_package_versions'
    __alias__ = ['availpkg']
    __default__ = available_package_versions.AvailablePackageConfig.__default__
    __doc__ = available_package_versions.AvailablePackageConfig.__doc__

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        available_package_versions.main(cmdline=cmdline, **kwargs)


class ModalCLI(object):
    """
    Contains multiple scriptconfig.Config items with corresponding `main`
    functions.
    """
    def __init__(self, description='', sub_clis=[], version=None):
        self.description = description
        self.sub_clis = sub_clis
        self.version = version

    def _build_subcmd_infos(self):
        cmdinfo_list = []
        for cli_cls in self.sub_clis:
            cmdname = getattr(cli_cls, '__command__', None)
            subconfig = cli_cls()
            parserkw = {}
            __alias__ = getattr(cli_cls, '__alias__', [])
            if __alias__:
                parserkw['aliases']  = __alias__
            parserkw.update(subconfig._parserkw())
            parserkw['help'] = parserkw['description'].split('\n')[0]
            cmdinfo_list.append({
                'cmdname': cmdname,
                'parserkw': parserkw,
                'main_func': cli_cls.main,
                'subconfig': subconfig,
            })
        return cmdinfo_list

    def build_parser(self):
        parser = argparse.ArgumentParser(
            description=self.description,
            formatter_class=RawDescriptionDefaultsHelpFormatter,
        )

        if self.version is not None:
            parser.add_argument('--version', action='store_true',
                                help='show version number and exit')

        # Prepare information to be added to the subparser before it is created
        cmdinfo_list = self._build_subcmd_infos()

        # Build a list of primary command names to display as the valid options
        # for subparsers. This avoids cluttering the screen with all aliases
        # which happens by default.
        command_choices = [d['cmdname'] for d in cmdinfo_list]
        metavar = '{' + ','.join(command_choices) + '}'

        # The subparser is what enables the modal CLI. It will redirect a
        # command to a chosen subparser.
        subparser_group = parser.add_subparsers(
            title='commands', help='specify a command to run', metavar=metavar)

        for cmdinfo in cmdinfo_list:
            # Add a new command to subparser_group
            subparser = subparser_group.add_parser(
                cmdinfo['cmdname'], **cmdinfo['parserkw'])
            subparser = cmdinfo['subconfig'].argparse(subparser)
            subparser.set_defaults(main=cmdinfo['main_func'])
        return parser

    def run(self):
        parser = self.build_parser()

        try:
            import argcomplete
            # Need to run: "$(register-python-argcomplete xdev)"
            # or activate-global-python-argcomplete --dest=-
            # activate-global-python-argcomplete --dest ~/.bash_completion.d
            # To enable this.
        except ImportError:
            argcomplete = None

        if argcomplete is not None:
            argcomplete.autocomplete(parser)

        XDEV_LOOSE_CLI = os.environ.get('XDEV_LOOSE_CLI', '')
        if XDEV_LOOSE_CLI:
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
        description=ub.codeblock(
            '''
            The XDEV CLI

            A collection of excellent developer tools for excellent developers.
            '''),
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
