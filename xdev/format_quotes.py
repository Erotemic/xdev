# -*- coding: utf-8 -*-
"""
Modifies Python code to roughly following quote scheme described in [1]_.
    * Single quotes (') are used for code
    * Double quotes (") are used for documentation
    * Don't touch any string that has an internal quote.

References:
    .. [1] https://github.com/google/yapf/issues/399#issuecomment-914839071

CommandLine:
    # See it in action
    FPATH=$(python -c "import six; print(six.__file__)")
    python -m xdev.format_quotes $FPATH --diff=True
"""
import redbaron
import ubelt as ub
import re
import xdev


def format_quotes_in_text(text):
    """
    Reformat text according to formatting rules

    Args:
        text (str): python source code

    Returns:
        str: modified text
    """
    # TODO: can we move to parso?
    red = redbaron.RedBaron(text)

    single_quote = chr(39)
    double_quote = chr(34)
    triple_single_quote = single_quote * 3
    triple_double_quote = double_quote * 3

    for found in red.find_all('string'):

        value = found.value
        info = {
            'quote_type': None,
            'is_docstring': None,
            'is_assigned_or_passed': None,  # TODO
            'has_internal_quote': None,
        }
        if value.startswith(triple_single_quote):
            info['quote_type'] = 'triple_single'
        elif value.startswith(triple_double_quote):
            info['quote_type'] = 'triple_double'
        elif value.startswith(single_quote):
            info['quote_type'] = 'single'
        elif value.startswith(double_quote):
            info['quote_type'] = 'double'
        else:
            raise AssertionError

        if isinstance(found.parent, redbaron.RedBaron):
            # module docstring or global string
            info['is_docstring'] = found.parent[0] == found
        elif found.parent.type in {'class', 'def'}:
            info['is_docstring'] = found.parent[0] == found
        elif isinstance(found.parent, redbaron.NodeList):
            info['is_docstring'] = '?'
            raise Exception
        else:
            info['is_docstring'] = False

        if info['quote_type'].startswith('triple'):
            content = value[3:-3]
        else:
            content = value[1:-1]

        info['has_internal_quote'] = (
            single_quote in content or double_quote in content)

        info['has_internal_triple_quote'] = (
            triple_single_quote in content or triple_double_quote in content)

        if info['quote_type'] == 'triple_single':
            if info['is_docstring']:
                if not info['has_internal_triple_quote']:
                    found.value = re.sub(
                        triple_single_quote, triple_double_quote, value)
        if info['quote_type'] == 'double':
            if not info['is_docstring']:
                if not info['has_internal_quote']:
                    found.value = re.sub(
                        double_quote, single_quote, value)

    new_text = red.dumps()
    return new_text


def format_quotes_in_file(fpath, diff=True, write=False, verbose=3):
    """
    Autoformat quotation marks in Python files

    Args:
        fpath (str): The file to format
        diff (bool): if True write the diff between old and new to stdout
        write (bool): if True write the modifications to disk
        verbose (int): verbosity level
    """
    if verbose > 1:
        print('reading fpath = {!r}'.format(fpath))

    with open(fpath, 'r') as file:
        text = file.read()

    new_text = format_quotes_in_text(text)

    difftext = xdev.difftext(text, new_text, context_lines=3, colored=True)
    did_anything = bool(difftext.strip())

    if verbose > 1:
        if not did_anything:
            print('No difference!')

    if diff:
        print(difftext)

    if write:
        # Write the file
        if did_anything:
            if verbose > 1:
                print('writing to fpath = {}'.format(ub.repr2(fpath, nl=1)))
            with open(fpath, 'w') as file:
                file.write(new_text)
    else:
        if not diff:
            if verbose > 1:
                print('dump formatted text to stdout')
            print(new_text)


def format_quotes(path, diff=True, write=False, verbose=3, recursive=True):
    # TODO:
    # Implement some sort of PathPattern that could either be a single path or
    # a pattern that indicates multiple paths
    # from xdev import search_replace
    # pat = search_replace.Pattern.coerce(str(path))

    import pathlib
    path = pathlib.Path(path)

    if path.is_file():
        if verbose:
            print('Format file')
        format_quotes_in_file(path, diff=diff, write=write, verbose=verbose)
    elif path.is_dir():
        if verbose:
            print('Format directory')
        import os
        from os.path import join
        for r, ds, fs in os.walk(path):
            for f in fs:
                if f.endswith('.py'):
                    fpath = join(r, f)
                    format_quotes_in_file(
                        fpath, diff=diff, write=write, verbose=verbose)
            if not recursive:
                break
    else:
        if verbose:
            print('Format pattern')
        raise NotImplementedError
        # if '*' in str(path):
        #     import glob
        #     for fpath in glob.glob(str(path), recursive=recursive):
        #         if pathlib.Path(fpath).is_file():
        #             pass


if __name__ == '__main__':
    import fire
    fire.Fire(format_quotes)
