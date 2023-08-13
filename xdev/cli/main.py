#!/usr/bin/env python3
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
import ubelt as ub
import os
import sys
from scriptconfig.modal import ModalCLI
from xdev.cli import available_package_versions


class XdevCLI(ModalCLI):
    """
    The XDEV CLI

    A collection of excellent developer tools for excellent developers.
    """

    class InfoCLI(scfg.DataConfig):
        """
        Info about xdev
        """
        __command__ = 'info'

        @classmethod
        def main(cls, cmdline=False, **kwargs):
            import xdev
            print('sys.version_info = {!r}'.format(sys.version_info))
            print('xdev.__version__ = {!r}'.format(xdev.__version__))
            print('xdev.__file__ = {!r}'.format(xdev.__file__))

    class CodeblockCLI(scfg.DataConfig):
        """
        Remove indentation from text.

        Useful for writing subscripts (e.g. python -c code) in shell files without
        having to resort to ugly indentation.
        """
        __command__ = 'codeblock'
        __epilog__ = """
        Example Usage
        -------------

        python -c "$(xdev codeblock "
            import pathlib
            print(list(pathlib.Path('.').glob('*')))
            ")"
        """
        text = scfg.Value('', type=str, position=1,
                          help='text to remove indentation from (i.e. dedent)')

        @classmethod
        def main(cls, cmdline=False, **kwargs):
            """
            Example:
                >>> from xdev.cli.main import *  # NOQA
                >>> CodeblockCLI.main(cmdline=0, text='foobar')
            """
            config = cls.cli(cmdline=cmdline, data=kwargs)
            print(ub.codeblock(config['text']))

    class SedCLI(scfg.DataConfig):
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
            'include': scfg.Value(None, help='If specified, only consider results with matching basenames'),
            'exclude': scfg.Value(None, help='If specified, do not consider results with matching basenames'),
            'dirblocklist': scfg.Value(None, help=(
                'Any directory matching this pattern will be removed from '
                'traveral.')),
            'recursive': scfg.Value(True),
            'verbose': scfg.Value(1),
        }

        @classmethod
        def main(cls, cmdline=False, **kwargs):
            from xdev import search_replace
            config = cls.cli(cmdline=cmdline, data=kwargs)
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

    class FindCLI(scfg.DataConfig):
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
            'include': scfg.Value(None, help='If specified, only consider results with matching basenames'),
            'exclude': scfg.Value(None, help='If specified, do not consider results with matching basenames'),
            'dirblocklist': scfg.Value(None, help=(
                'Any directory matching this pattern will be removed from '
                'traveral.')),
            'type': scfg.Value('f', help="can be f and/or d"),
            'recursive': scfg.Value(True),
            'followlinks': scfg.Value(False),
        }

        @classmethod
        def main(cls, cmdline=False, **kwargs):
            from xdev import search_replace
            config = cls.cli(cmdline=cmdline, data=kwargs)
            for found in search_replace.find(**config):
                print(found)

    class TreeCLI(scfg.DataConfig):
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
            'ignore_dotprefix': scfg.Value(True, isflag=True),
            'max_depth': scfg.Value(
                None, help='maximum depth to recurse', short_alias=['L']),
        }

        @classmethod
        def main(cls, cmdline=False, **kwargs):
            import xdev
            config = cls.cli(cmdline=cmdline, data=kwargs)
            xdev.tree_repr(**config)
            # print()

    class PintCLI(scfg.DataConfig):
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
            args = cls.cli(cmdline=cmdline, data=kwargs)
            input = ureg.parse_expression(args['input_expr'])
            output_unit = args['output_unit']
            if output_unit is None:
                output_unit = input.unit
            output = input.to(output_unit)
            if args['precision'] == 0:
                print(int(output.magnitude))
            else:
                print(output.magnitude)

    class PyfileCLI(scfg.DataConfig):
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
            args = cls.cli(cmdline=cmdline, data=kwargs)
            modpath = ub.modname_to_modpath(args['modname'])
            print(modpath)

    class PyVersionCLI(scfg.DataConfig):
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
            args = cls.cli(cmdline=cmdline, data=kwargs)
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

    class EditfileCLI(scfg.DataConfig):
        """
        Opens a file in your visual editor determined by the ``VISUAL``
        environment variable.

        If ``VISUAL`` is unspecified it attempts to default to the first known
        existing editor.

        Example Usage
        -------------
        xdev edit xdev
        xdev edit numpy
        """
        __command__ = 'editfile'
        __alias__ = ['edit']
        __default__ = {
            'target': scfg.Value(None, position=1, help='a path or a module name'),
        }

        @classmethod
        def main(cls, cmdline=False, **kwargs):
            import xdev
            args = cls.cli(cmdline=cmdline, data=kwargs)
            xdev.editfile(args.target)

    class FormatQuotesCLI(scfg.DataConfig):
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
            'write': scfg.Value(False, isflag=True, short_alias=['w'], help=ub.paragraph(
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
            config = cls.cli(cmdline=cmdline, data=kwargs)
            format_quotes.format_quotes(**config)

    class FreshPyenvCLI(scfg.DataConfig):
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
            config = cls.cli(cmdline=cmdline, data=kwargs)
            import ubelt as ub
            ub.cmd(f'freshpyenv.sh --image={config["image"]}', system=True)

    class DocstrStubgenCLI(scfg.DataConfig):
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
            config = cls.cli(cmdline=cmdline, data=kwargs)
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

    class AvailablePackageCLI(scfg.DataConfig):
        __command__ = 'available_package_versions'
        __alias__ = ['availpkg']
        __default__ = available_package_versions.AvailablePackageConfig.__default__
        __doc__ = available_package_versions.AvailablePackageConfig.__doc__

        @classmethod
        def main(cls, cmdline=False, **kwargs):
            available_package_versions.main(cmdline=cmdline, **kwargs)

    from xdev.cli.dirstats import DirectoryStatsCLI


def main():
    import xdev
    cli = XdevCLI()
    cli.version = xdev.__version__
    XDEV_LOOSE_CLI = os.environ.get('XDEV_LOOSE_CLI', '')
    cli.main(strict=not XDEV_LOOSE_CLI)


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
