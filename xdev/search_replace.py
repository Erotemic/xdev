"""
Python implementations of sed, grep, and find

Porting from ~/local/rob/rob/rob_nav.py / ubelt
"""
import re
import os
import fnmatch
import ubelt as ub
from os.path import relpath, split, join, basename


class Pattern(ub.NiceRepr):
    """
    A general patterns class, which can be strict, regex, or glob.

    Example:
        >>> from xdev.search_replace import *  # NOQA
        >>> repat = Pattern.coerce('foo.*', 'regex')
        >>> assert repat.match('foobar')
        >>> assert not repat.match('barfoo')

        >>> globpat = Pattern.coerce('foo*', 'glob')
        >>> assert globpat.match('foobar')
        >>> assert not globpat.match('barfoo')
    """
    def __init__(self, pattern, backend):
        if backend == 'regex' and isinstance(pattern, str):
            pattern = re.compile(pattern)
        self.pattern = pattern
        self.backend = backend

    def __nice__(self):
        return '{}, {}'.format(self.pattern, self.backend)

    @classmethod
    def coerce(cls, data, hint='glob'):
        """
        from xdev.search_replace import *  # NOQA
        pat = Pattern.coerce('foo*', 'glob')
        pat2 = Pattern.coerce(pat, 'regex')
        print('pat = {}'.format(ub.repr2(pat, nl=1)))
        print('pat2 = {}'.format(ub.repr2(pat2, nl=1)))
        """
        if isinstance(data, cls) or type(data).__name__ == cls.__name__:
            self = data
        else:
            backend = cls.coerce_backend(data, hint=hint)
            self = cls(data, backend)
        return self

    @classmethod
    def coerce_backend(cls, data, hint='glob'):
        if isinstance(data, re.Pattern):
            backend = 'regex'
        elif isinstance(data, cls) or type(data).__name__ == cls.__name__:
            backend = data.backend
        else:
            backend = hint
        return backend

    def match(self, text):
        if self.backend == 'regex':
            return self.pattern.match(text)
        elif self.backend == 'glob':
            return fnmatch.fnmatch(text, self.pattern)
        elif self.backend == 'strict':
            return self.pattern == text
        else:
            raise KeyError(self.backend)

    def search(self, text):
        if self.backend == 'regex':
            return self.pattern.search(text)
        elif self.backend == 'glob':
            return fnmatch.fnmatch(text, '*{}*'.format(self.pattern))
        elif self.backend == 'strict':
            return self.pattern in text
        else:
            raise KeyError(self.backend)

    def sub(self, repl, text):
        if self.backend == 'regex':
            return self.pattern.sub(repl, text)
        elif self.backend == 'glob':
            raise NotImplementedError
        elif self.backend == 'strict':
            return text.replace(self.pattern, repl)
        else:
            raise KeyError(self.backend)


def sed(regexpr, repl, dpath=None, include=None, exclude=None, recursive=True, dry=False, verbose=1):
    r"""
    Execute a sed on multiple files.

    Example:
        >>> from xdev.search_replace import *  # NOQA
        >>> from xdev.search_replace import _create_test_filesystem
        >>> dpath = _create_test_filesystem()['root']
        >>> sed('a', 'x', dpath=dpath, dry=True)
    """
    num_changed = 0
    num_files_checked = 0
    fpaths_changed = []

    fpath_generator = find(dpath=dpath, type='f', include=include,
                           exclude=exclude, recursive=recursive)
    for fpath in fpath_generator:
        num_files_checked += 1
        changed_lines = sedfile(fpath, regexpr, repl, dry=dry)
        if len(changed_lines) > 0:
            fpaths_changed.append(fpath)
            num_changed += len(changed_lines)

    if verbose:
        print('num_files_checked = %r' % (num_files_checked,))
        print('fpaths_changed = %s' % (ub.repr2(sorted(fpaths_changed)),))
        print('total lines changed = %r' % (num_changed,))


def grep(regexpr, dpath=None, include=None, exclude=None, dry=False,
         recursive=True, verbose=1):
    r"""
    Execute a grep on multiple files.

    Example:
        >>> from xdev.search_replace import *  # NOQA
        >>> from xdev.search_replace import _create_test_filesystem
        >>> dpath = _create_test_filesystem()['root']
        >>> grep('a', dpath=dpath, dry=True)
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


def _coerce_multipattern(pattern):
    if pattern is None:
        pattern_ = None
    else:
        if not ub.iterable(pattern):
            pattern_ = [pattern]
        else:
            pattern_ = pattern
        pattern_ = [Pattern.coerce(pat, hint='glob') for pat in pattern_]
    return pattern_


def find(pattern=None, dpath=None, include=None, exclude=None, type=None,
         recursive=True, followlinks=False):
    """
    Find all paths in a root subject to a search criterion

    Args:
        pattern (str):
            The glob pattern the path name must match to be returned

        dpath (str):
            The root direcotry to search. Default to cwd.

        include (str | List[str]):
            Pattern or list of patterns. If specified, search only files whose
            base name matches this pattern. By default the pattern is GLOB.

        exclude (str | List[str]):
            Pattern or list of patterns. Skip any file with a name suffix that
            matches the pattern. By default the pattern is GLOB.

        type (str | List[str]):
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
        dpath = os.getcwd()

    # Define helper for checking inclusion / exclusion
    include_ = _coerce_multipattern(include)
    exclude_ = _coerce_multipattern(exclude)

    def is_included(name):
        if exclude_ is not None:
            if any(pat.match(name) for pat in exclude_):
                return False

        if include_ is not None:
            if any(pat.match(name) for pat in include_):
                return True
            else:
                return False
        return True

    for root, dnames, fnames in os.walk(dpath, followlinks=followlinks):

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

    path, name = split(fpath)
    new_file_lines = []
    with open(fpath, 'r') as file:
        file_lines = file.readlines()
        # Search each line for the desired regexpr
        new_file_lines = [pattern.sub(repl, line) for line in file_lines]

    changed_lines = [(newline, line)
                     for newline, line in zip(new_file_lines, file_lines)
                     if  newline != line]
    nChanged = len(changed_lines)
    if nChanged > 0:
        rel_fpath = relpath(fpath, os.getcwd())
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

    def format_text(self):
        summary = []
        app = summary.append
        fname = basename(self.fpath)
        ndigits = str(len(str(self.max_line)))

        fmt_str = '{} : {:' + ndigits + 'd} |{}'
        ret = 'Found {} line(s) in {!r}: '.format(len(self), self.fpath)
        app('----------------------')
        app(ret)
        for (lx, line) in zip(self.found_lxs, self.found_lines):
            line = line.replace('\n', '')
            app(fmt_str.format(fname, lx, line))

        return '\n'.join(summary)


def grepfile(fpath, regexpr, verbose=1):
    r"""
    Exceute grep on a single file

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
