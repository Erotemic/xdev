"""
Utilities to just-in-time-cythonize a module at runtime.
"""
from collections import defaultdict
from os.path import dirname, join, basename, splitext, exists
import os
import warnings


__all__ = [
    'import_module_from_pyx',
]

# Track the number of times we've tried to autojit specific pyx files
NUM_AUTOJIT_TRIES = defaultdict(lambda: 0)
# MAX_AUTOJIT_TRIES = 1
MAX_AUTOJIT_TRIES = float('inf')
# 1


def import_module_from_pyx(fname, dpath=None, error="raise", autojit=True,
                           verbose=1, recompile=False, annotate=False):
    """
    Attempts to import a module corresponding to a pyx file.

    If the corresponding compiled module is not found, this can attempt to
    JIT-cythonize the pyx file.

    Parameters
    ----------
    fname : str
        The basename of the cython pyx file

    dpath : str
        The directory containing the cython pyx file

    error : str
        Can be "raise" or "ignore"

    autojit : bool
        If True, we will cythonize and compile the pyx file if possible.

    verbose : int
        verbosity level (higher is more verbose)

    recompile : bool
        if True force recompile

    Returns
    -------
    ModuleType | None : module
        Returns the compiled and imported module if possible, otherwise None
    """
    if dpath is None:
        dpath = dirname(fname)

    pyx_fpath = join(dpath, fname)

    if verbose > 3:
        print('[xdev.import] pyx_fpath = {!r}'.format(pyx_fpath))

    if not exists(pyx_fpath):
        raise AssertionError("pyx file {!r} does not exist".format(pyx_fpath))

    try:
        # This functionality depends on ubelt
        # TODO: the required functionality could be moved to nx.utils
        import ubelt as ub
    except Exception:
        if verbose:
            print("Autojit requires ubelt, which failed to import")
        if error == "ignore":
            module = None
        elif error == "raise":
            raise
        else:
            raise KeyError(error)
    else:

        if autojit:
            if verbose > 3:
                print('autojit = {!r}'.format(autojit))
            # Try to JIT the cython module if we ship the pyx without the compiled
            # library.
            NUM_AUTOJIT_TRIES[pyx_fpath] += 1
            if verbose > 3:
                print('NUM_AUTOJIT_TRIES = {!r}'.format(NUM_AUTOJIT_TRIES))
                print('MAX_AUTOJIT_TRIES = {!r}'.format(MAX_AUTOJIT_TRIES))
            if recompile or NUM_AUTOJIT_TRIES[pyx_fpath] <= MAX_AUTOJIT_TRIES:
                if verbose > 3:
                    print('try it')
                try:
                    _autojit_cython(pyx_fpath, verbose=verbose,
                                    recompile=recompile, annotate=annotate)
                    if verbose > 3:
                        print('got it')
                except Exception as ex:
                    warnings.warn("Cython autojit failed: ex={!r}".format(ex))
                    if error == "raise":
                        raise

        try:
            # if recompile:
            #     # Doesnt work. The module is not reloaded.
            #     modname = ub.modpath_to_modname(pyx_fpath)
            #     import sys
            #     sys.modules.pop(modname, None)
            module = ub.import_module_from_path(pyx_fpath)
        except Exception:
            if error == "ignore":
                module = None
            elif error == "raise":
                raise
            else:
                raise KeyError(error)

        return module


def _platform_pylib_exts():  # nocover
    """
    Returns .so, .pyd, or .dylib depending on linux, win or mac.  Returns the
    previous with and without abi (e.g. .cpython-35m-x86_64-linux-gnu) flags.
    """
    import sysconfig

    valid_exts = []
    # handle PEP 3149 -- ABI version tagged .so files
    base_ext = "." + sysconfig.get_config_var("EXT_SUFFIX").split(".")[-1]
    # ABI = application binary interface
    tags = [
        sysconfig.get_config_var("SOABI"),
        "abi3",  # not sure why this one is valid, but it is
    ]
    tags = [t for t in tags if t]
    for tag in tags:
        valid_exts.append("." + tag + base_ext)
    # return with and without API flags
    valid_exts.append(base_ext)
    valid_exts = tuple(valid_exts)
    return valid_exts


def _autojit_cython(pyx_fpath, verbose=1, recompile=False, annotate=False):
    """
    This idea is that given a pyx file, we try to compile it. We write a stamp
    file so subsequent calls should be very fast as long as the source pyx has
    not changed.

    Parameters
    ----------
    pyx_fpath : str
        path to the pyx file

    verbose : int
        higher is more verbose.
    """
    import shutil
    if verbose > 3:
        print('_autojit_cython')

    # TODO: move necessary ubelt utilities to nx.utils?
    # Separate this into its own util?
    if shutil.which("cythonize"):
        pyx_dpath = dirname(pyx_fpath)

        if verbose > 3:
            print('pyx_dpath = {!r}'.format(pyx_dpath))

        # Check if the compiled library exists
        pyx_base = splitext(basename(pyx_fpath))[0]

        SO_EXTS = _platform_pylib_exts()
        so_fname = False
        for fname in os.listdir(pyx_dpath):
            if fname.startswith(pyx_base) and fname.endswith(SO_EXTS):
                so_fname = fname
                break

        if verbose > 3:
            print('so_fname = {!r}'.format(so_fname))

        try:
            # Currently this functionality depends on ubelt.
            # We could replace ub.cmd with subprocess.check_call and ub.augpath
            # with os.path operations, but hash_file and CacheStamp are harder
            # to replace. We can use "liberator" to statically extract these
            # and add them to nx.utils though.
            import ubelt as ub
        except Exception:
            if verbose > 3:
                print('return false, no ubelt')
            return False
        else:
            if so_fname is False:
                # We can compute what the so_fname will be if it doesnt exist
                so_fname = pyx_base + SO_EXTS[0]

            so_fpath = join(pyx_dpath, so_fname)
            content = ub.readfrom(pyx_fpath)
            mtime = os.stat(pyx_fpath).st_mtime

            depends = [ub.hash_data(content, hasher="sha1"), mtime]
            stamp_fname = ub.augpath(so_fname, ext=".jit.stamp")
            stamp = ub.CacheStamp(
                stamp_fname,
                dpath=pyx_dpath,
                product=so_fpath,
                depends=depends,
                verbose=verbose,
            )
            if verbose > 3:
                print('stamp = {!r}'.format(stamp))
            if recompile or stamp.expired():
                # Heuristic to try and grab the numpy include dir or not
                cythonize_args = ['cythonize']
                cythonize_env = os.environ.copy()
                needs_numpy = 'numpy' in content
                if needs_numpy:
                    import numpy as np
                    import pathlib
                    numpy_include_dpath = pathlib.Path(np.get_include())
                    numpy_dpath = (numpy_include_dpath / '../..').resolve()
                    # cythonize_env['CPATH'] = numpy_include_dpath + ':' + cythonize_env.get('CPATH', '')
                    cythonize_env['CFLAGS'] = ' '.join([
                        '-I{}'.format(numpy_include_dpath),
                    ]) + cythonize_env.get('CFLAGS', '')

                    cythonize_env['LDFLAGS'] = ' '.join([
                        '-L{} -lnpyrandom'.format(numpy_dpath / 'random/lib'),
                        '-L{} -lnpymath'.format(numpy_dpath / 'core/lib'),
                    ]) + cythonize_env.get('LDFLAGS', '')
                if annotate:
                    cythonize_args.append('-a')
                cythonize_args.append('-i {}'.format(pyx_fpath))
                cythonize_cmd = ' '.join(cythonize_args)
                if needs_numpy:
                    print('CFLAGS="{}" '.format(cythonize_env['CFLAGS']) + 'LDFLAGS="{}" '.format(cythonize_env['LDFLAGS']) + cythonize_cmd)
                ub.cmd(cythonize_cmd, verbose=verbose, check=True,
                       env=cythonize_env)
                stamp.renew()
            return True
    else:
        if verbose > 2:
            print('Cythonize not found!')
