import re
import os
import ubelt as ub
from os.path import relpath, split


def sedfile(fpath, regexpr, repl, dry=False, verbose=1):
    """
    Execute a search and replace on a particular file
    """
    path, name = split(fpath)
    new_file_lines = []
    with open(fpath, 'r') as file:
        file_lines = file.readlines()
        # Search each line for the desired regexpr
        new_file_lines = [re.sub(regexpr, repl, line) for line in file_lines]

    changed_lines = [(newline, line)
                     for newline, line in zip(new_file_lines, file_lines)
                     if  newline != line]
    nChanged = len(changed_lines)
    if nChanged > 0:
        rel_fpath = relpath(fpath, os.getcwd())
        if verbose:
            print(' * %s changed %d lines in %r ' %
                  (['(real-run)', '(dry-run)'][dry], nChanged, rel_fpath))
            print(' * --------------------')
        new_file = ''.join(new_file_lines)
        old_file = ub.ensure_unicode(
            ''.join(list(map(ub.ensure_unicode, file_lines))))
        format_difftext(old_file, new_file)
        if not dry:
            if verbose:
                print(' ! WRITING CHANGES')
            with open(fpath, 'w') as file:
                file.write(new_file)
        return changed_lines
    return []


def grepfile(fpath, regexpr, verbose=1):
    """
    Exceute grep on a single file
    """
    ret = None
    with open(fpath, 'r') as file:
        try:
            lines = file.readlines()
        except UnicodeDecodeError:
            print("UNABLE TO READ fpath={}".format(fpath))
        else:
            found_lines = []
            found_lxs = []
            # Search each line for the desired regexpr
            for lx, line in enumerate(lines):
                match_object = re.search(regexpr, line)
                if match_object is not None:
                    found_lines.append(line)
                    found_lxs.append(lx)
            found = list(zip(found_lxs, found_lines))
            # Print the results (if any)
            if len(found) > 0:
                rel_fpath = relpath(fpath, os.getcwd())
                ret = 'Found %d line(s) in %r: ' % (len(found), rel_fpath)
                if verbose:
                    print('----------------------')
                    print(ret)
                name = split(fpath)[1]
                max_line = len(lines)
                ndigits = str(len(str(max_line)))
                fmt_str = '%s : %' + ndigits + 'd |%s'
                for (lx, line) in iter(found):
                    line = line.replace('\n', '')
                    if verbose:
                        print(fmt_str % (name, lx, line))
    return ret


def format_difftext(text1, text2, num_context_lines=0, ignore_whitespace=False):
    r"""
    Uses difflib to return a difference string between two similar texts

    Args:
        text1 (str):
        text2 (str):

    Returns:
        str: formatted difference text message

    References:
        http://www.java2s.com/Code/Python/Utility/IntelligentdiffbetweentextfilesTimPeters.htm

    Example:
        >>> # DISABLE_DOCTEST
        >>> # build test data
        >>> text1 = 'one\ntwo\nthree'
        >>> text2 = 'one\ntwo\nfive'
        >>> # execute function
        >>> result = format_difftext(text1, text2)
        >>> # verify results
        >>> print(result)
        - three
        + five

    Example2:
        >>> # DISABLE_DOCTEST
        >>> # build test data
        >>> text1 = 'one\ntwo\nthree\n3.1\n3.14\n3.1415\npi\n3.4\n3.5\n4'
        >>> text2 = 'one\ntwo\nfive\n3.1\n3.14\n3.1415\npi\n3.4\n4'
        >>> # execute function
        >>> num_context_lines = 1
        >>> result = format_difftext(text1, text2, num_context_lines)
        >>> # verify results
        >>> print(result)
    """
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

    if num_context_lines is None:
        diff_lines = all_diff_lines
    else:
        # boolean for every line if it is marked or not
        ismarked_list = [len(line) > 0 and line[0] in '+-?'
                         for line in all_diff_lines]
        # flag lines that are within num_context_lines away from a diff line
        isvalid_list = ismarked_list[:]
        for i in range(1, num_context_lines + 1):
            def or_lists(*args):
                return [any(tup) for tup in zip(*args)]
            isvalid_list[:-i] = or_lists(isvalid_list[:-i], ismarked_list[i:])
            isvalid_list[i:]  = or_lists(isvalid_list[i:], ismarked_list[:-i])
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
    return '\n'.join(diff_lines)
