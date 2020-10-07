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


def set_overlaps(set1, set2, s1='s1', s2='s2'):
    """
    return info about set overlaps
    """
    set1 = set(set1)
    set2 = set(set2)
    overlaps = ub.odict([
        (s1, len(set1)),
        (s2, len(set2)),
        ('isect', len(set1.intersection(set2))),
        ('union', len(set1.union(set2))),
        ('%s - %s' % (s1, s2), len(set1.difference(set2))),
        ('%s - %s' % (s2, s1), len(set2.difference(set1))),
    ])
    return overlaps


def edit_distance(string1, string2):
    """
    Edit distance algorithm. String1 and string2 can be either
    strings or lists of strings

    Args:
        string1 (str | List[str]):
        string2 (str | List[str]):

    Requirements:
        pip install python-Levenshtein

    Example:
        >>> # xdoctest: +REQUIRES(module:Levenshtein)
        >>> string1 = 'hello world'
        >>> string2 = ['goodbye world', 'rofl', 'hello', 'world', 'lowo']
        >>> edit_distance(['hello', 'one'], ['goodbye', 'two'])
        >>> edit_distance('hello', ['goodbye', 'two'])
        >>> edit_distance(['hello', 'one'], 'goodbye')
        >>> edit_distance('hello', 'goodbye')
        >>> distmat = edit_distance(string1, string2)
        >>> result = ('distmat = %s' % (ub.repr2(distmat),))
        >>> print(result)
        >>> [7, 9, 6, 6, 7]
    """

    import Levenshtein
    isiter1 = ub.iterable(string1)
    isiter2 = ub.iterable(string2)
    strs1 = string1 if isiter1 else [string1]
    strs2 = string2 if isiter2 else [string2]
    distmat = [
        [Levenshtein.distance(str1, str2) for str2 in strs2]
        for str1 in strs1
    ]
    # broadcast
    if not isiter2:
        distmat = [row[0] for row in distmat]
    if not isiter1:
        distmat = distmat[0]
    return distmat


def nested_type(obj, unions=False):
    """
    Compute the :module:`typing` compatible annotation type.

    Args:
        obj (Any): a typing template based on a specific object
        unions (bool): if True use unions, otherwise use Any

    Returns:
        str: type code (might change to return actual type)

    Example:
        >>> obj = {'a': [1, 2], 'b': [3, 4, 5]}
        >>> print(nested_type(obj))
        Dict[str, List[int]]

        >>> import numpy as np
        >>> obj = {'b': {'a': 1.0, 'b': 'foo', 'c': np.array([1, 2])}}
        >>> print(nested_type(obj, unions=True))
        Dict[str, Dict[str, float | ndarray | str]]
    """
    def _resolve(types):
        if len(types) == 1:
            return ub.peek(types)
        else:
            if unions:
                return ' | '.join(sorted(types))
            else:
                return 'Any'

    from functools  import partial
    _nested = partial(nested_type, unions=unions)
    if isinstance(obj, dict):
        keytypes = {_nested(k) for k in obj.keys()}
        valtypes = {_nested(v) for v in obj.values()}
        keytype = _resolve(keytypes)
        valtype = _resolve(valtypes)
        objtype = 'Dict[{}, {}]'.format(keytype, valtype)
    elif isinstance(obj, list):
        itemtypes = {_nested(item) for item in obj}
        itemtype = _resolve(itemtypes)
        objtype = 'List[{}]'.format(itemtype)
    elif isinstance(obj, set):
        itemtypes = [_nested(item) for item in obj]
        itemtype = _resolve(itemtypes)
        objtype = 'Set[{}]'.format(itemtype)
    elif isinstance(obj, tuple):
        itemtypes = [_nested(item) for item in obj]
        objtype = 'Tuple[{}]'.format(', '.join(itemtypes))
    else:
        import typing
        objtype = type(obj).__name__
        objtype = typing._normalize_alias.get(objtype, objtype)
        # objtype = 'Any'
        return objtype
    return objtype


def difftext(text1, text2, context_lines=0, ignore_whitespace=False,
             colored=False):
    r"""
    Uses difflib to return a difference string between two similar texts

    Args:
        text1 (str): old text
        text2 (str): new text
        context_lines (int): number of lines of unchanged context
        ignore_whitespace (bool):
        colored (bool): if true highlight the diff

    Returns:
        str: formatted difference text message

    References:
        http://www.java2s.com/Code/Python/Utility/IntelligentdiffbetweentextfilesTimPeters.htm

    Example:
        >>> # build test data
        >>> text1 = 'one\ntwo\nthree'
        >>> text2 = 'one\ntwo\nfive'
        >>> # execute function
        >>> result = difftext(text1, text2)
        >>> # verify results
        >>> print(result)
        - three
        + five

    Example:
        >>> # build test data
        >>> text1 = 'one\ntwo\nthree\n3.1\n3.14\n3.1415\npi\n3.4\n3.5\n4'
        >>> text2 = 'one\ntwo\nfive\n3.1\n3.14\n3.1415\npi\n3.4\n4'
        >>> # execute function
        >>> context_lines = 1
        >>> result = difftext(text1, text2, context_lines, colored=True)
        >>> # verify results
        >>> print(result)
    """
    import ubelt as ub
    import difflib
    text1 = ub.ensure_unicode(text1)
    text2 = ub.ensure_unicode(text2)
    text1_lines = text1.splitlines()
    text2_lines = text2.splitlines()
    if ignore_whitespace:
        text1_lines = [t.rstrip() for t in text1_lines]
        text2_lines = [t.rstrip() for t in text2_lines]
        ndiff_kw = dict(linejunk=difflib.IS_LINE_JUNK,
                        charjunk=difflib.IS_CHARACTER_JUNK)
    else:
        ndiff_kw = {}
    all_diff_lines = list(difflib.ndiff(text1_lines, text2_lines, **ndiff_kw))

    if context_lines is None:
        diff_lines = all_diff_lines
    else:
        # boolean for every line if it is marked or not
        ismarked_list = [len(line) > 0 and line[0] in '+-?'
                         for line in all_diff_lines]
        # flag lines that are within context_lines away from a diff line
        isvalid_list = ismarked_list[:]
        for i in range(1, context_lines + 1):
            isvalid_list[:-i] = list(map(any, zip(
                isvalid_list[:-i], ismarked_list[i:])))
            isvalid_list[i:] = list(map(any, zip(
                isvalid_list[i:], ismarked_list[:-i])))

        USE_BREAK_LINE = True
        if USE_BREAK_LINE:
            # insert a visual break when there is a break in context
            diff_lines = []
            prev = False
            visual_break = '\n <... FILTERED CONTEXT ...> \n'
            #print(isvalid_list)
            for line, valid in zip(all_diff_lines, isvalid_list):
                if valid:
                    diff_lines.append(line)
                elif prev:
                    if False:
                        diff_lines.append(visual_break)
                prev = valid
        else:
            diff_lines = list(ub.compress(all_diff_lines, isvalid_list))
    text = '\n'.join(diff_lines)
    if colored:
        text = ub.highlight_code(text, lexer_name='diff')
    return text


def tree(cwd=None):
    """
    Like the unix util tree, but allow writing numbers of files per directory
    when given -d option

    cwd = '/data/public/Aerial/US_ALASKA_MML_SEALION'
    """
    import os
    from os.path import join, relpath
    if cwd is None:
        cwd = os.getcwd()

    import networkx as nx
    tree = nx.OrderedDiGraph()

    for root, dnames, fnames in os.walk(cwd):
        dnames[:] = sorted(dnames)
        tree.add_node(root)

        num_files = len(fnames)
        prefix = '[ {} ]'.format(num_files)

        pathrep = relpath(root, cwd)

        label = '{} {}'.format(prefix, pathrep)

        tree.nodes[root]['label'] = label

        for dname in dnames:
            dpath = join(root, dname)
            tree.add_edge(root, dpath)

    _print_forest(tree)


def _print_forest(graph):
    """
    Nice ascii representation of a forest

    Ignore:
        graph = nx.balanced_tree(r=2, h=3, create_using=nx.DiGraph)
        _print_forest(graph)

        graph = CategoryTree.demo('coco').graph
        _print_forest(graph)
    """
    if len(graph.nodes) == 0:
        print('--')
        return

    import networkx as nx
    assert nx.is_forest(graph)

    def _recurse(node, indent='', islast=False):
        if islast:
            this_prefix = indent + '└── '
            next_prefix = indent + '    '
        else:
            this_prefix = indent + '├── '
            next_prefix = indent + '│   '
        label = graph.nodes[node].get('label', node)
        print(this_prefix + str(label))
        graph.succ[node]
        children = graph.succ[node]
        for idx, child in enumerate(children, start=1):
            islast_next = (idx == len(children))
            _recurse(child, indent=next_prefix, islast=islast_next)

    sources = [n for n in graph.nodes if graph.in_degree[n] == 0]
    for idx, node in enumerate(sources, start=1):
        islast_next = (idx == len(sources))
        _recurse(node, indent='', islast=islast_next)


def make_warnings_print_tracebacks():
    import warnings
    import traceback
    _orig_formatwarning = warnings.formatwarning
    warnings._orig_formatwarning = _orig_formatwarning
    def _monkeypatch_formatwarning_tb(*args, **kwargs):
        s = _orig_formatwarning(*args, **kwargs)
        if len(s.strip()):
            tb = traceback.format_stack()
            s += ''.join(tb[:-1])
        return s
    warnings.formatwarning = _monkeypatch_formatwarning_tb
