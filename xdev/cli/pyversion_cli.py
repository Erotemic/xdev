#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import scriptconfig as scfg
import ubelt as ub


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

    # For more verbose information add the verbose flag
    xdev pyversion opencv-python-headless --verbose

    xdev pyversion xdev --backend=import
    xdev pyversion xdev --backend=importlib
    """
    __command__ = 'pyversion'
    __alias__ = ['modversion']

    modname = scfg.Value(None, position=1, help='The name of the module or package')

    backend = scfg.Value('auto', help=ub.paragraph(
        '''
        The method to lookup the version. The core methods are 'import'
        which imports the module and looks for a ``__version__`` attribute
        or 'importlib', which uses pip metadata. Can also be 'auto'
        which tries to find the first one that works.
        '''), choices=['auto', 'import', 'importlib', 'pkg_resources'])

    verbose = scfg.Value(False, isflag=True, help='if 1 prints out more info')

    @classmethod
    def main(cls, cmdline=False, **kwargs):
        args = cls.cli(cmdline=cmdline, data=kwargs)
        if args.verbose:
            from rich.markup import escape
            import rich
            rich.print(f'args = {escape(ub.urepr(args, nl=1))}')

        modname = args['modname']

        if args['backend'] == 'auto':
            candidate_backends  = ['import', 'pkg_resources']
        else:
            candidate_backends = [args['backend']]

        def _getversion(modname, backend):
            if backend == 'import':
                module = ub.import_module_from_name(modname)
                version = module.__version__
                if args.verbose:
                    one_liner = ub.codeblock(
                        f'''
                        python -c "import {modname}; print({modname}.__version__)"
                        '''
                    )
                    print('One Liner:')
                    print(one_liner)
            elif backend == 'importlib':
                # import importlib.resources
                import importlib.metadata
                version = importlib.metadata.distribution(modname).version
                if args.verbose:
                    one_liner = ub.codeblock(
                        f'''
                        python -c "import importlib.metadata; print(importlib.metadata.distribution({modname!r}).version)"
                        '''
                    )
                    print('One Liner:')
                    print(one_liner)
            elif backend == 'pkg_resources':
                # pkg resources is deprecated.
                import pkg_resources
                version = pkg_resources.get_distribution(modname).version
                if args.verbose:
                    one_liner = ub.codeblock(
                        f'''
                        python -c "import pkg_resources; print(pkg_resources.get_distribution({modname!r}).version)"
                        '''
                    )
                    print('One Liner:')
                    print(one_liner)
            else:
                raise KeyError(backend)
            return version

        version = None
        for backend in candidate_backends:
            try:
                version = _getversion(modname, backend)
            except KeyError:
                raise
            except Exception as ex:
                if args.verbose:
                    print(f'Unable to use backend {backend}')
                    if args.verbose > 1:
                        print(f'ex = {ub.urepr(ex, nl=1)}')
            else:
                if args.verbose:
                    print(f'Used backend {backend}')
                break
        print(version)
        if version is None:
            raise Exception(f'No version was found for {modname}')


__cli__ = PyVersionCLI

if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdev/xdev/cli/pyversion_cli.py
    """
    __cli__.main()
