# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import ubelt as ub


def quantum_random(pure=False):
    """
    Returns a quantum random number as a 32 bit unsigned integer.
    Does this by making a network request to the ANU Quantum Random Number
    Generator web service, so an internet connection is required.

    Args:
        pure (bool): if False, mixes this data with pseudorandom data for
            security. Otherwise returns the raw quantum numbers that were
            sent over the web (i.e. subject to MitM attacks).

    Requirements:
        quantumrandom >= 1.9.0

    Returns:
        numpy.uint32: the random number
    """
    import numpy as np
    import os
    import quantumrandom

    # Data was sent over a network
    qr_data16 = quantumrandom.uint16(array_length=2)
    nbytes = qr_data16.size * qr_data16.dtype.itemsize

    if pure:
        data16 = qr_data16
    else:
        # Cryptographically generated
        buf = memoryview(os.urandom(nbytes))
        pr_data16 = np.frombuffer(buf, dtype=qr_data16.dtype)
        # xor to mix data
        data16 = (pr_data16 ^ qr_data16)

    assert data16.flags['C_CONTIGUOUS']
    data32 = data16.view(np.dtype('uint32'))[0]
    return data32


def byte_str(num, unit='auto', precision=2):
    """
    Automatically chooses relevant unit (KB, MB, or GB) for displaying some
    number of bytes.

    Args:
        num (int): number of bytes
        unit (str): which unit to use, can be auto, B, KB, MB, GB, TB, PB, EB,
            ZB, or YB.
        precision (int): number of decimals of precision

    References:
        https://en.wikipedia.org/wiki/Orders_of_magnitude_(data)

    Returns:
        str: string representing the number of bytes with appropriate units

    Example:
        >>> num_list = [1, 100, 1024,  1048576, 1073741824, 1099511627776]
        >>> result = ub.urepr(list(map(byte_str, num_list)), nl=0)
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
    return ub.urepr(num_unit, precision=precision) + ' ' + unit


def _resolve_set(items, name='items'):
    """
    Ignore:
        items = [1, 1, 1, 2, 3, 4, 4, 5]
    """
    unique_items = set(items)
    if not isinstance(items, set):
        try:
            n_total = len(items)
        except TypeError:
            items = list(items)
            n_total = len(items)
        dup_counts = ub.udict(ub.find_duplicates(items)).map_values(len)
    else:
        dup_counts = {}
        n_total = len(unique_items)
    return unique_items, n_total, dup_counts


def set_overlaps(set1, set2, s1='s1', s2='s2'):
    """
    Return sizes about set overlaps.

    If the inputs are not sets, they will be cast to sets, and if there are
    duplicate they will be counted.

    Args:
        set1 (Iterable): the first set of items
        set2 (Iterable): the second set of items
        s1 (str): name for set1
        s2 (str): name for set2

    Returns:
        Dict[str, int]: sizes of sets intersections unions and differences

    Example:
        >>> import ubelt as ub
        >>> from xdev.misc import set_overlaps
        >>> set1 = {'a', 'b', 'c', 'd', 'e'}
        >>> set2 = {'a', 'e', 'i', 'o', 'u'}
        >>> result = set_overlaps(set1, set2, 'first5', 'vowels')
        >>> print(f'result = {ub.urepr(result, nl=1)}')
        result = {
            'first5': 5,
            'vowels': 5,
            'isect': 2,
            'union': 8,
            'first5 - vowels': 3,
            'vowels - first5': 3,
        }

    Example:
        >>> import ubelt as ub
        >>> from xdev.misc import set_overlaps
        >>> set1 = [1, 1, 2, 3, 3, 3, 4, 5,]
        >>> set2 = [2, 2, 2, 3]
        >>> result = set_overlaps(set1, set2)
        >>> print(f'result = {ub.urepr(result, nl=1)}')
    """
    set1, n_total1, dup_counts1 = _resolve_set(set1)
    set2, n_total2, dup_counts2 = _resolve_set(set2)

    overlaps = {
        s1: len(set1),
        s2: len(set2),
        'isect': len(set1.intersection(set2)),
        'union': len(set1.union(set2)),
        f'{s1} - {s2}': len(set1.difference(set2)),
        f'{s2} - {s1}': len(set2.difference(set1)),
    }
    if dup_counts1:
        overlaps[f'{s1} dupliates'] = sum(dup_counts1.values())
    if dup_counts2:
        overlaps[f'{s2} dupliates'] = sum(dup_counts2.values())
    if dup_counts1:
        overlaps[f'{s1} unique dupliates'] = len(dup_counts1)
    if dup_counts2:
        overlaps[f'{s2} unique dupliates'] = len(dup_counts2)
    if dup_counts1:
        overlaps[f'{s1} total'] = n_total1
    if dup_counts2:
        overlaps[f'{s2} total'] = n_total2
    return overlaps


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
    def _resolve(_types):
        if len(_types) == 1:
            return ub.peek(_types)
        else:
            if unions:
                return ' | '.join(sorted(_types))
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
        if hasattr(typing, '_normalize_alias'):
            objtype = typing._normalize_alias.get(objtype, objtype)
        else:
            objtype = {'list': 'List',
                       'tuple': 'Tuple',
                       'dict': 'Dict',
                       'set': 'Set',
                       'frozenset': 'FrozenSet',
                       'deque': 'Deque',
                       'defaultdict': 'DefaultDict',
                       'type': 'Type',
                       'Set': 'AbstractSet'}.get(objtype, objtype)
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


def tree_repr(cwd=None, max_files=100, dirblocklist=None, show_nfiles='auto',
              return_text=False, return_tree=False, pathstyle='name',
              max_depth=None, with_type=False, abs_root_label=True,
              ignore_dotprefix=True, colors=not ub.NO_COLOR):
    """
    Filesystem tree representation

    Like the unix util tree, but allow writing numbers of files per directory
    when given -d option

    Args:
        cwd (None | str | PathLike) : directory to print
        max_files (int | None) : maximum files to print before supressing a directory
        pathstyle (str): can be rel, name, or abs
        return_tree (bool): if True return the tree
        return_text (bool): if True return the text
        maxdepth (int | None): maximum depth to descend
        abs_root_label (bool): if True force the root to always be absolute
        colors (bool): if True use rich

    SeeAlso:
        xdev.tree - generator

    Ignore:
        >>> import xdev
        >>> import ubelt as ub
        >>> dpath = ub.Path.appdir('xdev/tests/test_tree_repr').delete().ensuredir()
        >>> outside_fpath = ((dpath / 'outside_path').ensuredir() / 'file').touch()
        >>> outside_dpath2 = ((dpath / 'outside_path/path2')).ensuredir()
        >>> outside_dpath1 = ((dpath / 'outside_path/path')).ensuredir()
        >>> (outside_dpath1 / 'file1').write_text('foo')
        >>> (outside_dpath1 / 'subdir1').ensuredir()
        >>> (outside_dpath1 / 'subdir1/file2').write_text('bar')
        >>> cwd = (dpath / 'root').ensuredir()
        >>> (cwd / 'dir1').ensuredir()
        >>> (cwd / 'dir2').ensuredir()
        >>> (cwd / 'dir3').ensuredir()
        >>> ub.symlink(link_path=(cwd / 'dir1/file_link'), real_path=outside_fpath, verbose=3)
        >>> ub.symlink(link_path=(cwd / 'dir1/dir_link1'), real_path=outside_dpath1, verbose=3)
        >>> ub.symlink(link_path=(cwd / 'dir1/dir_link2'), real_path=outside_dpath2, verbose=3)
        >>> ub.symlink(link_path=(cwd / 'dir1/broken_link'), real_path=outside_dpath1 / 'does-not-exist', verbose=3)
        >>> (cwd / 'dir1/subdir1').ensuredir()
        >>> (cwd / 'dir1/subdir2').ensuredir()
        >>> (cwd / 'dir2/subdir1').ensuredir()
        >>> (cwd / 'dir2/subdir2').ensuredir()
        >>> (cwd / 'dir1/subdir1/file1').touch()
        >>> (cwd / 'dir1/subdir1/file2').touch()
        >>> (cwd / 'dir1/subdir1/file3').touch()
        >>> (cwd / 'dir1/subdir2/file4').touch()
        >>> print('---------')
        >>> xdev.tree_repr(cwd, show_nfiles=True, with_type=True)
        >>> print('---------')
        >>> xdev.tree_repr(cwd, max_files=1)
        >>> print('---------')

        if 1:
            _ = ub.cmd('tree ' + cwd, verbose=3)
    """
    import os
    from xdev.patterns import MultiPattern

    if cwd is None:
        cwd = os.getcwd()

    from xdev.cli import dirstats

    if dirblocklist is not None:
        dirblocklist = MultiPattern.coerce(dirblocklist, hint='glob')

    if ignore_dotprefix:
        if dirblocklist is None:
            dirblocklist = MultiPattern.coerce('.*', hint='glob')
        else:
            dirblocklist = MultiPattern.coerce([dirblocklist, '.*'], hint='glob')

    walker = dirstats.DirectoryWalker(
        cwd,
        exclude_dnames=dirblocklist,
        max_files=max_files,
        abs_root_label=abs_root_label,
        pathstyle=pathstyle,
        show_nfiles=show_nfiles,
        show_progress=False,
        show_types=with_type,
        colors=colors,
    )
    walker._walk()
    walker._update_labels()
    tree = walker.graph

    from xdev.util_networkx import write_network_text
    import io
    file = io.StringIO()
    write_network_text(tree, file)
    text = file.getvalue()

    info = {}

    if return_text:
        info['text'] = text
    else:
        if colors:
            from rich import print as rprint
            rprint(text)
        else:
            print(text)

    if return_tree:
        info['tree'] = tree
        info['walker'] = walker
    return info


def textfind(text, pattern):
    """
    Return a colored text that highlights the pattern
    """
    import re
    pat = re.compile('(' + pattern + ')')
    parts = pat.split(text)
    new_text = ''.join([p if idx % 2 == 0 else ub.color_text(p, 'red') for idx, p in enumerate(parts)])
    print(new_text)
