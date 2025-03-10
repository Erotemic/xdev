"""
Functions related to interacting with data via an OS Desktop GUI.
"""
from os.path import normpath
from os.path import exists
from os.path import sys
import types
import os
import warnings
import ubelt as ub


def _coerce_editable_fpath(target):
    """
    Rules for coercing inputs to ``editfile`` into a path.

    Args:
        target (str | PathLike | ModuleType | ClassType | FunctionType):
            something coercable to a path or module path

    Returns:
        ub.Path
    """
    fpath = None
    if isinstance(target, str):
        # String inputs are ambiguous. Ambiguous case, is this a module name or a full path?
        if exists(target):
            fpath = ub.Path(target)
        else:
            # Perhaps this is a module name we want to edit?
            modpath = ub.modname_to_modpath(target)
            if modpath is not None:
                fpath = ub.Path(modpath)

    elif isinstance(target, types.ModuleType):
        fpath = ub.Path(target.__file__)
    elif isinstance(target, os.PathLike):
        fpath = ub.Path(target)
    elif hasattr(target, '__module__'):
        fpath =  ub.Path(sys.modules[target.__module__].__file__)
    else:
        raise TypeError(f"Unable to coerce {target} into a file path")

    if fpath is None:
        # Is it a package name?
        import pkg_resources
        try:
            distribution = pkg_resources.get_distribution(target)
            top_level_names = list(distribution.get_metadata_lines("top_level.txt"))
            if len(top_level_names) == 0:
                raise AssertionError('is this possible? I hope not')
            elif len(top_level_names) > 1:
                import warnings
                warnings.warn(
                    'Multiple top-level names were installed for this package, only choosing the first')
            name = top_level_names[0]
            fpath = ub.modname_to_modpath(name)
            if fpath is not None:
                fpath = ub.Path(fpath)
        except pkg_resources.DistributionNotFound:
            ...
        else:
            ...

    if fpath is None:
        raise Exception(f"Unable to interpret {target} as a module name or file path")

    # Resolve a pyc file to a py file if possible.
    if fpath.suffix == '.pyc':
        fpath_py = fpath.augment(ext='.py')
        if fpath_py.exists():
            fpath = fpath_py

    return fpath


def _find_editor():
    """
    Try to find an editor program.
    """
    editor_name = os.environ.get('VISUAL', None)
    editor_fpath = editor_name and ub.find_exe(editor_name)
    if editor_fpath is None:
        if editor_name is not None:
            warnings.warn('User specified VISUAL={editor_name}, but it does not exist.', UserWarning)
        # Try and fallback on commonly installed editor
        # TODO: add more editors in an opinionated order
        editor_candidates = [
            'gvim',
            'code',  # visual studio code
            'gedit',
            'TextEdit'
            'Notepad',
        ]
        for cand_name in editor_candidates:
            cand_fpath = ub.find_exe(cand_name)
            if cand_fpath:
                editor_fpath = cand_fpath
                break

    if editor_fpath is None:
        raise IOError('Unable to find an existing VISUAL editor')

    return editor_fpath


def editfile(fpath, verbose=True):
    """
    Opens a file or code corresponding to a live python object in your
    preferred visual editor. This function is mainly useful in an interactive
    IPython session.

    The visual editor is determined by the ``VISUAL`` environment variable.  If
    this is not specified it defaults to gvim.

    Args:
        fpath (PathLike | ModuleType | str):
            a file path or python module / function. If the input is a string
            it will interpret it either as a Path or a module name. Ambiguity
            is resolved by choosing a path if the string resolves to an
            existing path, and then checking if the string corresponds to a
            module name.

        verbose (int): verbosity

    Example:
        >>> # xdoctest: +SKIP
        >>> # This test interacts with a GUI frontend, not sure how to test.
        >>> import xdev
        >>> ub.editfile(xdev.misc.__file__)
        >>> ub.editfile(xdev)
        >>> ub.editfile(xdev.editfile)
    """
    fpath = _coerce_editable_fpath(fpath)

    if verbose:
        print('[xdev] editfile("{}")'.format(fpath))

    editor_fpath = _find_editor()
    if not exists(fpath):
        raise IOError('Cannot start nonexistant file: %r' % fpath)

    if verbose:
        print('[xdev] using "{}"'.format(editor_fpath))
    ub.cmd([editor_fpath, fpath], fpath, detach=True)


def view_directory(dpath=None, verbose=False):
    """
    View a directory in the operating system file browser. Currently supports
    windows explorer, mac open, and linux nautlius.

    Args:
        dpath (PathLike | None): directory name
        verbose (bool): verbosity
    """
    if dpath is None:
        dpath = os.getcwd()
    dpath = os.path.normpath(dpath)
    if verbose:
        print('[xdev] view_directory({!r}) '.format(dpath))
    if not exists(dpath):
        raise Exception('Cannot view nonexistant directory: {!r}'.format(dpath))
    if False:
        try:
            import vimtk.xctrl
            import vimtk.cplat_ctrl
            if vimtk.xctrl.is_directory_open(dpath):
                if verbose:
                    print('[xdev] dpath={!r} is already open'.format(dpath))
                win = vimtk.cplat_ctrl.Window.find('Nautilus.*' + os.path.basename(dpath))
                win.focus()
                return
        except Exception:
            pass
    if ub.LINUX:
        info = ub.cmd(('nautilus', dpath), detach=True, verbose=verbose)
    elif ub.DARWIN:
        info = ub.cmd(('open', dpath), detach=True, verbose=verbose)
    elif ub.WIN32:
        info = ub.cmd(('explorer.exe', dpath), detach=True, verbose=verbose)
    else:
        raise RuntimeError('Unknown Platform')
    if info is not None:
        if not info['proc']:
            raise Exception('startfile failed')


def startfile(fpath, verbose=True):
    """
    Uses default program defined by the system to open a file.
    This is done via `os.startfile` on windows, `open` on mac, and `xdg-open`
    on linux.

    Args:
        fpath (PathLike): a file to open using the program associated with the
            files extension type.
        verbose (int): verbosity

    References:
        http://stackoverflow.com/questions/2692873/quote-posix

    Example:
        >>> # xdoctest: +SKIP
        >>> # This test interacts with a GUI frontend, not sure how to test.
        >>> import ubelt as ub
        >>> base = ub.ensure_app_cache_dir('ubelt')
        >>> fpath1 = join(base, 'test_open.txt')
        >>> ub.touch(fpath1)
        >>> proc = ub.startfile(fpath1)
    """
    if verbose:
        print('[xdev] startfile("{}")'.format(fpath))
    fpath = normpath(fpath)
    if not exists(fpath):
        raise Exception('Cannot start nonexistant file: {!r}'.format(fpath))
    if not ub.WIN32:
        import shlex
        fpath = shlex.quote(fpath)
    if ub.LINUX:
        info = ub.cmd(('xdg-open', fpath), detach=True, verbose=verbose)
    elif ub.DARWIN:
        info = ub.cmd(('open', fpath), detach=True, verbose=verbose)
    elif ub.WIN32:
        os.startfile(fpath)
        info = None
    else:
        raise RuntimeError('Unknown Platform')
    if info is not None:
        if not info['proc']:
            raise Exception('startfile failed')
