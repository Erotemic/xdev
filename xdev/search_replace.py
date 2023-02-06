"""
Python implementations of sed, grep, and find

Porting from ~/local/rob/rob/rob_nav.py / ubelt
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import os
import ubelt as ub
from os.path import relpath, split, join, abspath
from xdev.patterns import Pattern, RE_Pattern  # NOQA
from xdev.patterns import MultiPattern

# try:
#     from packaging.version import parse as parse_version
# except Exception:
#     from distutils.version import LooseVersion as parse_version


class GrepResult(ub.NiceRepr):
    """
    Manage and format results from grep
    """
    def __init__(self, fpath, pattern=None):
        self.pattern = pattern
        self.fpath = fpath
        self.found_lxs = []
        self.found_lines = []
        self.max_line = 100

    def __nice__(self):
        return '{} in {}'.format(len(self), self.fpath)

    def __iter__(self):
        return iter(self.found_lines)

    def __len__(self):
        return len(self.found_lines)

    def append(self, lx, line):
        self.found_lines.append(line)
        self.found_lxs.append(lx)

    def format_text(self, color=True):
        summary = []
        app = summary.append
        fname = ub.Path(self.fpath).name
        ndigits = str(len(str(self.max_line)))

        fmt_str = '{} : {:' + ndigits + 'd} |{}'
        ret = 'Found {} line(s) in {!r}: '.format(len(self), self.fpath)
        app('----------------------')
        color = 'red'
        app(ret)
        for (lx, line) in zip(self.found_lxs, self.found_lines):
            line = line.replace('\n', '')
            if color and self.pattern:
                found = self.pattern.search(line)
                s, t = found.span()
                line = line[:s] + ub.color_text(line[s:t], color) + line[t:]
            app(fmt_str.format(fname, lx, line))

        return '\n'.join(summary)


def sed(regexpr, repl, dpath=None, include=None, exclude=None, recursive=True,
        dry=False, verbose=1):
    r"""
    Execute a sed on multiple files.

    Args:
        regexpr (str | Pattern): pattern to find
        repl (str): the text to replace the found pattern with
        dpath (str | None): passed to :func:`find`.
        include (str | List[str] | MultiPattern | None): passed to :func:`find`.
        exclude (str | List[str] | MultiPattern | None): passed to :func:`find`.
        recursive (bool): passed to :func:`find`.
        dry (bool): if True does not apply edits
        verbose (int): verbosity level

    Example:
        >>> from xdev.search_replace import *  # NOQA
        >>> from xdev.search_replace import _create_test_filesystem
        >>> dpath = _create_test_filesystem()['root']
        >>> sed('a', 'x', dpath=dpath, dry=True)
    """
    num_changed = 0
    num_files_checked = 0
    num_skipped = 0
    fpaths_changed = []

    fpath_generator = find(dpath=dpath, type='f', include=include,
                           exclude=exclude, recursive=recursive)
    for fpath in fpath_generator:
        try:
            changed_lines = sedfile(fpath, regexpr, repl, dry=dry)
        except UnicodeDecodeError:
            num_skipped += 1
        else:
            num_files_checked += 1
            if len(changed_lines) > 0:
                fpaths_changed.append(fpath)
                num_changed += len(changed_lines)

    if verbose:
        print('num_files_checked = {}'.format(num_files_checked))
        print('num probable binary files skipped = {}'.format(num_skipped))
        print('fpaths_changed = {}'.format(ub.repr2(sorted(fpaths_changed))))
        print('total lines changed = {!r}'.format(num_changed))


def grep(regexpr, dpath=None, include=None, exclude=None, recursive=True,
         verbose=1):
    r"""
    Execute a grep on multiple files.

    Args:
        regexpr (str | Pattern): pattern to find
        dpath (str | None): passed to :func:`find`.
        include (str | List[str] | MultiPattern | None): passed to :func:`find`.
        exclude (str | List[str] | MultiPattern | None): passed to :func:`find`.
        recursive (bool): passed to :func:`find`.
        verbose (int): verbosity level

    Returns:
        List[GrepResult]:

    Example:
        >>> from xdev.search_replace import *  # NOQA
        >>> from xdev.search_replace import _create_test_filesystem
        >>> dpath = _create_test_filesystem()['root']
        >>> grep('a', dpath=dpath)
    """
    grep_results = []

    fpath_generator = find(dpath=dpath, type='f', include=include,
                           exclude=exclude, recursive=recursive)

    for fpath in fpath_generator:
        grepres = grepfile(fpath, regexpr, verbose=verbose)
        if grepres:
            grep_results.append(grepres)

    if verbose:
        print('====================')
        print('====================')
        found_fpaths = [r.fpath for r in grep_results]
        print('\n'.join(found_fpaths))

    return grep_results


def find(pattern=None, dpath=None, include=None, exclude=None, dirblocklist=None,
         type=None, recursive=True, followlinks=False):
    """
    Find all paths in a root subject to a search criterion

    Args:
        pattern (str | Pattern | None):
            The glob pattern the path name must match to be returned

        dpath (str | Pattern | None):
            The root directory to search. Default to cwd.

        include (str | List[str] | MultiPattern | None):
            Pattern or list of patterns. If specified, search only files whose
            base name matches this pattern. By default the pattern is GLOB.
            This only applies to the final name. Directories that do not match
            this name will still be traversed.

        exclude (str | List[str] | MultiPattern | None):
            Pattern or list of patterns. Skip any file with a name suffix that
            matches the pattern. By default the pattern is GLOB. This ONLY
            applies to the final name. Directories that match an exclude
            pattern will still be traversed.  Use ``dirblocklist`` to specify
            patterns to exclude intermediate directories from traversal.

        dirblocklist (str | List[str] | MultiPattern | None):
            Any directory name matching this pattern will be removed from
            traversal.

        type (str | List[str] | None):
            A list of 1 character codes indicating what types of file can be
            returned. Currently we only allow either "f" for file or "d" for
            directory. Symbolic links are not currently distinguished. In the
            future we may support posix codes, see [1]_ for details.

        recursive:
            search all subdirectories recursively

        followlinks (bool, default=False):
            if True will follow directory symlinks

    References:
        _[1] https://linuxconfig.org/identifying-file-types-in-linux

    TODO:
        mindepth

        maxdepth

        ignore_case

        regex_match


    Example:
        >>> from xdev.search_replace import *  # NOQA
        >>> from xdev.search_replace import _create_test_filesystem
        >>> dpath = _create_test_filesystem()['root']
        >>> paths = list(find(pattern='*', dpath=dpath))
        >>> assert len(paths) == 5
        >>> paths = list(find(pattern='*', dpath=dpath, type='f'))
        >>> assert len(paths) == 4
    """

    if pattern is None:
        pattern = '*'

    if type is None:
        with_dirs = True
        with_files = True
    else:
        with_dirs = False
        with_files = False
        if 'd' in type:
            with_dirs = True
        if 'f' in type:
            with_files = True

    if dpath is None:
        dpath = '.'  # os.getcwd()

    # Define helper for checking inclusion / exclusion
    include = None if include is None else MultiPattern.coerce(include, hint='glob')
    exclude = None if exclude is None else MultiPattern.coerce(exclude, hint='glob')
    dirblocklist = None if dirblocklist is None else MultiPattern.coerce(dirblocklist, hint='glob')
    main_pattern = Pattern.coerce(pattern, hint='glob')

    def is_included(name):
        if not main_pattern.match(name):
            return False

        if exclude is not None and exclude.match(name):
            return False

        if include is None or include.match(name):
            return True

        return False

    for root, dnames, fnames in os.walk(dpath, followlinks=followlinks):

        if dirblocklist is not None:
            dnames[:] = [
                dname for dname in dnames if not dirblocklist.match(dname)]

        if with_files:
            for fname in fnames:
                if is_included(fname):
                    yield join(root, fname)

        if with_dirs:
            for dname in dnames:
                if is_included(dname):
                    yield join(root, dname)

        if not recursive:
            break


def sedfile(fpath, regexpr, repl, dry=False, verbose=1):
    r"""
    Execute a search and replace on a particular file

    Args:
        fpath (str | PathLike): file to search / replace on
        regexpr (str | Pattern): pattern to find
        repl (str): the text to replace the found pattern with
        dry (bool): if True does not apply edits
        verbose (int): verbosity level

    Returns:
        List[Tuple[str, str]]: changed lines

    TODO:
        - [ ] Store "SedResult" class, with lazy execution

    Example:
        >>> from xdev.search_replace import *  # NOQA
        >>> from xdev.search_replace import _create_test_filesystem
        >>> fpath = _create_test_filesystem()['contents'][1]
        >>> changed_lines1 = sedfile(fpath, 'a', 'x', dry=True, verbose=1)
        >>> changed_lines2 = sedfile(fpath, 'a', 'x', dry=False, verbose=0)
        >>> assert changed_lines2 == changed_lines1
        >>> changed_lines3 = sedfile(fpath, 'a', 'x', dry=False, verbose=0)
        >>> assert changed_lines3 != changed_lines2
    """
    import xdev
    mode_text = ['(real-run)', '(dry-run)'][dry]

    pattern = Pattern.coerce(regexpr, hint='regex')
    # print(f'regexpr={regexpr}')
    # print(f'pattern={pattern!r}')

    path, name = split(fpath)
    new_file_lines = []
    try:
        with open(fpath, 'r') as file:
            file_lines = file.readlines()
            # Search each line for the desired regexpr
            new_file_lines = [pattern.sub(repl, line) for line in file_lines]
    except UnicodeDecodeError as ex:
        # Add the file name into the exception
        new_last_arg = ex.args[-1] + ' in fpath={!r}'.format(fpath)
        new_args = ex.args[:-1] + (new_last_arg,)
        raise UnicodeDecodeError(*new_args) from ex
    except Exception:
        raise
        # This does not preserve exception type
        # raise Exception('Failed to sedfile fpath = {!r}'.format(fpath)) from ex

    changed_lines = [(newline, line)
                     for newline, line in zip(new_file_lines, file_lines)
                     if  newline != line]
    nChanged = len(changed_lines)
    if nChanged > 0:
        try:
            rel_fpath = relpath(fpath, os.getcwd())
        except ValueError:
            # windows issues
            rel_fpath = abspath(fpath)

        if verbose:
            print(' * {} changed {} lines in {!r} '.format(
                mode_text, nChanged, rel_fpath))
            print(' * --------------------')
        new_file = ''.join(new_file_lines)
        old_file = ub.ensure_unicode(
            ''.join(list(map(ub.ensure_unicode, file_lines))))
        if verbose:
            print(xdev.difftext(old_file, new_file, colored=True))
        if not dry:
            if verbose:
                print(' ! WRITING CHANGES')
            with open(fpath, 'w') as file:
                file.write(new_file)
        return changed_lines
    return []


def grepfile(fpath, regexpr, verbose=1):
    r"""
    Exceute grep on a single file

    Args:
        fpath (str | PathLike): file to search
        regexpr (str | Pattern): pattern to find
        verbose (int): verbosity level

    Returns:
        None | GrepResult

    Example:
        >>> from xdev.search_replace import *  # NOQA
        >>> from xdev.search_replace import _create_test_filesystem
        >>> fpath = _create_test_filesystem()['contents'][1]
        >>> grep_result = grepfile(fpath, r'\bb\b')
        >>> print('grep_result = {}'.format(grep_result))
    """
    grep_result = None
    pattern = Pattern.coerce(regexpr, hint='regex')
    with open(fpath, 'r') as file:
        try:
            lines = file.readlines()
        except UnicodeDecodeError:
            print("UNABLE TO READ fpath={}".format(fpath))
        else:
            grep_result = GrepResult(fpath, pattern)
            grep_result.max_line = len(lines)

            # Search each line for the desired pattern
            for lx, line in enumerate(lines):
                match_object = pattern.search(line)
                if match_object:
                    grep_result.append(lx, line)

            # Print the results (if any)
            if verbose:
                if len(grep_result):
                    print(grep_result.format_text())

    return grep_result


def greptext(text, regexpr, fpath=None, verbose=1):
    r"""
    Exceute grep on text

    Args:
        text (str): text to search
        regexpr (str | Pattern): pattern to find
        verbose (int): verbosity level

    Returns:
        None | GrepResult
    """
    from xdev.patterns import Pattern
    # from xdev.search_replace import GrepResult
    grep_result = None
    pattern = Pattern.coerce(regexpr, hint='regex')
    fpath = '<text>'
    try:
        lines = text.splitlines()
    except UnicodeDecodeError:
        print("UNABLE TO READ fpath={}".format(fpath))
    else:
        grep_result = GrepResult(fpath, pattern)
        grep_result.max_line = len(lines)

        # Search each line for the desired pattern
        for lx, line in enumerate(lines):
            match_object = pattern.search(line)
            if match_object:
                grep_result.append(lx, line)

        # Print the results (if any)
        if verbose:
            if len(grep_result):
                print(grep_result.format_text())
    return grep_result


def _create_test_filesystem():
    dpath = ub.ensure_app_cache_dir('xdev/test_search_replace')
    text1 = ub.paragraph(
        '''
        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
        tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
        veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
        commodo consequat. Duis aute irure dolor in reprehenderit in voluptate
        velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint
        occaecat cupidatat non proident, sunt in culpa qui officia deserunt
        mollit anim id est laborum.
        ''')

    text2 = ub.codeblock(
        '''
        def fib(n):
            a, b = 0, 1
            while a < n:
                print(a, end=' ')
                a, b = b, a+b
                print()

        fib(1000)
        ''')

    text3 = ub.codeblock(
        '''
        This file contains Lorem and fib

        Newlines

        fib

        lorem

        fib
        ''')

    text4 = ''

    fpath1 = join(dpath, 'lorium.txt')
    fpath2 = join(dpath, 'fib.py')
    fpath3 = join(dpath, 'foo.txt')
    fpath4 = join(ub.ensuredir((dpath, 'subdir')), 'foo.txt')
    with open(fpath1, 'w') as file:
        file.write(text1)
    with open(fpath2, 'w') as file:
        file.write(text2)
    with open(fpath3, 'w') as file:
        file.write(text3)
    with open(fpath4, 'w') as file:
        file.write(text4)

    info = {
        'root': dpath,
        'contents': [fpath1, fpath2, fpath3],
    }

    return info

if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdev/xdev/search_replace.py
        xdoctest ~/code/xdev/xdev/search_replace.py
    """
    import xdoctest
    xdoctest.doctest_module(__file__)
