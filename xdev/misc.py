import pipes
from os.path import normpath
import os
import six
from os.path import exists
from os.path import sys
from six import types
import ubelt as ub


def editfile(fpath, verbose=True):
    """
    Opens a file or code corresponding to a live python object in your
    preferred visual editor. This function is mainly useful in an interactive
    IPython session.

    The visual editor is determined by the `VISUAL` environment variable.  If
    this is not specified it defaults to gvim.

    Args:
        fpath (PathLike): a file path or python module / function
        verbose (int): verbosity

    DisableExample:
        >>> # This test interacts with a GUI frontend, not sure how to test.
        >>> import xdev
        >>> ub.editfile(xdev.misc.__file__)
        >>> ub.editfile(xdev)
        >>> ub.editfile(xdev.editfile)
    """
    if not isinstance(fpath, six.string_types):
        if isinstance(fpath, types.ModuleType):
            fpath = fpath.__file__
        else:
            fpath =  sys.modules[fpath.__module__].__file__
        fpath_py = fpath.replace('.pyc', '.py')
        if exists(fpath_py):
            fpath = fpath_py

    if verbose:
        print('[xdev] editfile("{}")'.format(fpath))

    editor = os.environ.get('VISUAL', 'gvim')
    if not ub.find_exe(editor):
        import warnings
        warnings.warn('Cannot find visual editor={}'.format(editor), UserWarning)
        # Try and fallback on commonly installed editor
        alt_candidates = [
            'gedit',
            'TextEdit'
            'Notepad',
        ]
        for cand in alt_candidates:
            if ub.find_exe(cand):
                editor = cand

    if not exists(fpath):
        raise IOError('Cannot start nonexistant file: %r' % fpath)
    ub.cmd([editor, fpath], fpath, detatch=True)


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

    DisableExample:
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
        fpath = pipes.quote(fpath)
    if ub.LINUX:
        info = ub.cmd(('xdg-open', fpath), detatch=True, verbose=verbose)
    elif ub.DARWIN:
        info = ub.cmd(('open', fpath), detatch=True, verbose=verbose)
    elif ub.WIN32:
        os.startfile(fpath)
        info = None
    else:
        raise RuntimeError('Unknown Platform')
    if info is not None:
        if not info['proc']:
            raise Exception('startfile failed')


def quantum_random():
    """
    Returns a quantum random number as a 32 bit unsigned integer.
    Does this by making a network request to the ANU Quantum Random Number
    Generator web service, so an internet connection is required.

    Requirements:
        quantumrandom >= 1.9.0

    Returns:
        numpy.uint32: the random number
    """
    import numpy as np
    import quantumrandom
    data16 = quantumrandom.uint16(array_length=2)
    assert data16.flags['C_CONTIGUOUS']
    data32 = data16.view(np.dtype('uint32'))[0]
    return data32


def view_directory(dpath=None, verbose=False):
    """
    View a directory in the operating system file browser. Currently supports
    windows explorer, mac open, and linux nautlius.

    Args:
        dpath (PathLike): directory name
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
        info = ub.cmd(('nautilus', dpath), detatch=True, verbose=verbose)
    elif ub.DARWIN:
        info = ub.cmd(('open', dpath), detatch=True, verbose=verbose)
    elif ub.WIN32:
        info = ub.cmd(('explorer.exe', dpath), detatch=True, verbose=verbose)
    else:
        raise RuntimeError('Unknown Platform')
    if info is not None:
        if not info['proc']:
            raise Exception('startfile failed')


def byte_str(num, unit='auto', precision=2):
    """
    Automatically chooses relevant unit (KB, MB, or GB) for displaying some
    number of bytes.

    Args:
        num (int): number of bytes
        unit (str): which unit to use, can be auto, B, KB, MB, GB, TB, PB, EB,
            ZB, or YB.

    References:
        https://en.wikipedia.org/wiki/Orders_of_magnitude_(data)

    Returns:
        str: string representing the number of bytes with appropriate units

    Example:
        >>> num_list = [1, 100, 1024,  1048576, 1073741824, 1099511627776]
        >>> result = ub.repr2(list(map(byte_str, num_list)), nl=0)
        >>> print(result)
        ['0.00 KB', '0.10 KB', '1.00 KB', '1.00 MB', '1.00 GB', '1.00 TB']
    """
    abs_num = abs(num)
    if unit == 'auto':
        if abs_num < 2.0 ** 10:
            unit = 'KB'
        elif abs_num < 2.0 ** 20:
            unit = 'KB'
        elif abs_num < 2.0 ** 30:
            unit = 'MB'
        elif abs_num < 2.0 ** 40:
            unit = 'GB'
        elif abs_num < 2.0 ** 50:
            unit = 'TB'
        elif abs_num < 2.0 ** 60:
            unit = 'PB'
        elif abs_num < 2.0 ** 70:
            unit = 'EB'
        elif abs_num < 2.0 ** 80:
            unit = 'ZB'
        else:
            unit = 'YB'
    if unit.lower().startswith('b'):
        num_unit = num
    elif unit.lower().startswith('k'):
        num_unit =  num / (2.0 ** 10)
    elif unit.lower().startswith('m'):
        num_unit =  num / (2.0 ** 20)
    elif unit.lower().startswith('g'):
        num_unit = num / (2.0 ** 30)
    elif unit.lower().startswith('t'):
        num_unit = num / (2.0 ** 40)
    elif unit.lower().startswith('p'):
        num_unit = num / (2.0 ** 50)
    elif unit.lower().startswith('e'):
        num_unit = num / (2.0 ** 60)
    elif unit.lower().startswith('z'):
        num_unit = num / (2.0 ** 70)
    elif unit.lower().startswith('y'):
        num_unit = num / (2.0 ** 80)
    else:
        raise ValueError('unknown num={!r} unit={!r}'.format(num, unit))
    return ub.repr2(num_unit, precision=precision) + ' ' + unit
