import ubelt as ub
import os


class ChDir:
    """
    Context manager that changes the current working directory and then
    returns you to where you were.

    Args:
        dpath (PathLike | None):
            The new directory to work in.
            If None, then the context manager is disabled.

    Example:
        >>> dpath = ub.Path.appdir('xdev/tests/chdir').ensuredir()
        >>> dir1 = (dpath / 'dir1').ensuredir()
        >>> dir2 = (dpath / 'dir2').ensuredir()
        >>> with ChDir(dpath):
        >>>     assert ub.Path.cwd() == dpath
        >>>     # changes to the given directory, and then returns back
        >>>     with ChDir(dir1):
        >>>         assert ub.Path.cwd() == dir1
        >>>         with ChDir(dir2):
        >>>             assert ub.Path.cwd() == dir2
        >>>             # changes inside the context manager will be reset
        >>>             os.chdir(dpath)
        >>>         assert ub.Path.cwd() == dir1
        >>>     assert ub.Path.cwd() == dpath
        >>>     with ChDir(dir1):
        >>>         assert ub.Path.cwd() == dir1
        >>>         with ChDir(None):
        >>>             assert ub.Path.cwd() == dir1
        >>>             # When disabled, the cwd does *not* reset at context exit
        >>>             os.chdir(dir2)
        >>>         assert ub.Path.cwd() == dir2
        >>>         os.chdir(dir1)
        >>>         # Dont change dirs, but reset to your cwd at context end
        >>>         with ChDir('.'):
        >>>             os.chdir(dir2)
        >>>         assert ub.Path.cwd() == dir1
        >>>     assert ub.Path.cwd() == dpath
    """
    def __init__(self, dpath):
        self.context_dpath = dpath
        self.orig_dpath = None

    def __enter__(self):
        if self.context_dpath is not None:
            self.orig_dpath = os.getcwd()
            os.chdir(self.context_dpath)
        return self

    def __exit__(self, a, b, c):
        if self.context_dpath is not None:
            os.chdir(self.orig_dpath)


def sidecar_glob(main_pat, sidecar_ext, main_key='main', sidecar_key=None,
                 recursive=0):
    """
    Similar to a regular glob, but returns a dictionary with associated
    main-file / sidecar-file pairs.

    TODO:
        add as a general option to Pattern.paths?

    Args:
        main_pat (str | PathLike):
            glob pattern for the main non-sidecar file

    Yields:
        Dict[str, ub.Path | None]

    Notes:
        A sidecar file is defined by the sidecar extension. We usually use this
        for .dvc sidecars.

        When the pattern includes a .dvc suffix, the result will include those .dvc
        files and any matching main files they correspond to. Note: if you search
        for paths like `foo_*.dvc` this might skiped unstaged files. Therefore it
        is recommended to only include the .dvc suffix in the pattern ONLY if you
        do not want any unstaged files.

        If you want both staged and unstaged files, ensure the pattern does not
        exclude objects without a .dvc suffix (i.e. don't end the pattern with
        .dvc).

        When the pattern does not include a .dvc suffix, we include all those
        files, for other files that exist by adding a .dvc suffix.

        With the pattern matches both a dvc and non-dvc file, they are grouped
        together.

    Example:
        >>> dpath = ub.Path.appdir('xdev/tests/sidecar_glob')
        >>> dpath.delete().ensuredir()
        >>> (dpath / 'file1').touch()
        >>> (dpath / 'file1.ext').touch()
        >>> (dpath / 'file1.ext.car').touch()
        >>> (dpath / 'file2.ext').touch()
        >>> (dpath / 'file3.ext.car').touch()
        >>> (dpath / 'file4.car').touch()
        >>> (dpath / 'file5').touch()
        >>> (dpath / 'file6').touch()
        >>> (dpath / 'file6.car').touch()
        >>> (dpath / 'file7.bike').touch()
        >>> def _handle_resulst(results):
        ...     results = list(results)
        ...     for row in results:
        ...         for k, v in row.items():
        ...             if v is not None:
        ...                 row[k] = v.relative_to(dpath)
        ...     print(ub.repr2(results, sv=1))
        ...     return results
        >>> main_key = 'main',
        >>> sidecar_key = '.car'
        >>> sidecar_ext = '.car'
        >>> main_pat = dpath / '*'
        >>> _handle_resulst(sidecar_glob(main_pat, sidecar_ext))
        >>> _handle_resulst(sidecar_glob(dpath / '*.ext', '.car'))
        >>> _handle_resulst(sidecar_glob(dpath / '*.car', '.car'))
        >>> _handle_resulst(sidecar_glob(dpath / 'file*.ext', '.car'))
        >>> _handle_resulst(sidecar_glob(dpath / '*', '.ext'))
    """
    from xdev import patterns as util_pattern
    import warnings
    import os
    _len_ext = len(sidecar_ext)
    main_pat = os.fspath(main_pat)
    glob_patterns = [main_pat]
    if main_pat.endswith(sidecar_ext):
        warnings.warn(
            'The main path query should not end with the sidecar extension.'
            ' {main_pat=} {sidecar_ext=}'
        )
        # We could have a variant that removes the extension, but lets not do
        # that and document it.
        # glob_patterns.append(pat[:-_len_ext])
    else:
        if main_pat.endswith('/*'):
            # Optimization dont need an extra pattern in this case
            pass
        else:
            glob_patterns.append(main_pat + sidecar_ext)

    mpat = util_pattern.MultiPattern.coerce(glob_patterns)
    if sidecar_key is None:
        sidecar_key = sidecar_ext
    default = {main_key: None, sidecar_key: None}
    id_to_row = ub.ddict(default.copy)
    paths = mpat.paths(recursive=recursive)

    def _gen():
        for path in paths:
            parent = path.parent
            name = path.name
            if name.endswith(sidecar_ext):
                this_key = sidecar_key
                other_key = main_key
                main_path = parent / name[:-_len_ext]
                other_path = main_path
            else:
                this_key = main_key
                other_key = sidecar_key
                main_path = path
                other_path = parent / (name + sidecar_ext)
            needs_yeild = main_path not in id_to_row
            row = id_to_row[main_path]
            row[this_key] = path
            if row[other_key] is None:
                if other_path.exists():
                    row[other_key] = other_path
            if needs_yeild:
                yield row
    # without this, yilded rows might modify themselves later, that is
    # confusing for a user. Don't do it or come up with a scheme where we
    # detect if a row is "complete" and only yeild it then
    # We could more easilly do this if we used a walk-style find and pattern
    # match mechanism
    rows = list(_gen())
    yield from rows


def tree(path):
    """
    Like os.walk but yields a flat list of file and directory paths

    Args:
        path (str | os.PathLike): path to traverse

    Yields:
        str: path

    Example:
        >>> import itertools as it
        >>> import ubelt as ub
        >>> path = ub.Path('.')
        >>> gen = tree(path)
        >>> results = list(it.islice(gen, 5))
        >>> print('results = {}'.format(ub.repr2(results, nl=1)))
    """
    import os
    from os.path import join
    for r, fs, ds in os.walk(path):
        for f in fs:
            yield join(r, f)
        for d in ds:
            yield join(r, d)
