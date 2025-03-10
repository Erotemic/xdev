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

TODO:
    * rope: https://github.com/python-rope/rope or parso
    * Make tool that fixes specific classes of issues, this handles quotes, but we should also hand:

        * Spaces between operators and commas: `autopep8 --select E225,E226,E231 --in-place <fpath>`
"""
import ubelt as ub
import re
import xdev


SINGLE_QUOTE = chr(39)
DOUBLE_QUOTE = chr(34)
TRIPLE_SINGLE_QUOTE = SINGLE_QUOTE * 3
TRIPLE_DOUBLE_QUOTE = DOUBLE_QUOTE * 3


def format_quotes_in_text(text, backend='parso'):
    """
    Reformat text according to formatting rules

    Args:
        text (str): python source code

    Returns:
        str: modified text

    Example:
        >>> # xdoctest: +REQUIRES(module:parso)
        >>> from xdev.format_quotes import *  # NOQA
        >>> text = ub.codeblock(
        ...     f'''
        ...     def func1():
        ...         {TRIPLE_SINGLE_QUOTE}
        ...         Fix this.
        ...         {TRIPLE_SINGLE_QUOTE}
        ...
        ...     def func2():
        ...         {TRIPLE_DOUBLE_QUOTE}
        ...         Leave the doctests alone!
        ...         {TRIPLE_DOUBLE_QUOTE}
        ...
        ...     string1 = "fix these"
        ...     string2 = "don't fix these"
        ...     string3 = {TRIPLE_SINGLE_QUOTE}this is ok{TRIPLE_SINGLE_QUOTE}
        ...     string4 = {TRIPLE_DOUBLE_QUOTE}fix this{TRIPLE_DOUBLE_QUOTE}
        ...
        ...     def func3():
        ...         inside_string1 = "fix these"
        ...         inside_string2 = "don't fix these"
        ...         inside_string3 = {TRIPLE_SINGLE_QUOTE}this is ok{TRIPLE_SINGLE_QUOTE}
        ...         inside_string4 = {TRIPLE_DOUBLE_QUOTE}fix this{TRIPLE_DOUBLE_QUOTE}
        ...     ''')
        >>> print(text)
        >>> fixed = format_quotes_in_text(text)
        >>> print(fixed)
        >>> import xdev
        >>> fixed = format_quotes_in_text(text, backend='parso')
        >>> print('----')
        >>> print(xdev.difftext(text, fixed, colored=True))
        >>> # xdoctest: +REQUIRES(module:redbaron)
        >>> print('----')
        >>> fixed = format_quotes_in_text(text, backend='redbaron')
        >>> print('----')
        >>> print(xdev.difftext(text, fixed, colored=True))
        >>> print('----')
    """

    def fix_string_value(value, is_docstring=False):
        info = {
            'quote_type': None,
            'is_docstring': is_docstring,
            'is_assigned_or_passed': None,  # TODO
            'has_internal_quote': None,
        }

        def quote_variants(quote):
            prefixes = ['', 'r', 'f', 'rf']
            return tuple([p + quote for p in prefixes])

        if value.startswith(quote_variants(TRIPLE_SINGLE_QUOTE)):
            info['quote_type'] = 'triple_single'
        elif value.startswith(quote_variants(TRIPLE_DOUBLE_QUOTE)):
            info['quote_type'] = 'triple_double'
        elif value.startswith(quote_variants(SINGLE_QUOTE)):
            info['quote_type'] = 'single'
        elif value.startswith(quote_variants(DOUBLE_QUOTE)):
            info['quote_type'] = 'double'
        else:
            raise AssertionError(value)

        if info['quote_type'].startswith('triple'):
            content = value[3:-3]
        else:
            content = value[1:-1]

        info['has_internal_quote'] = (
            SINGLE_QUOTE in content or DOUBLE_QUOTE in content)

        info['has_internal_triple_quote'] = (
            TRIPLE_SINGLE_QUOTE in content or TRIPLE_DOUBLE_QUOTE in content)

        new_value = value

        # print('info = {}'.format(ub.urepr(info, nl=1)))
        if info['quote_type'] == 'triple_single':
            if info['is_docstring']:
                if not info['has_internal_triple_quote']:
                    new_value = re.sub(
                        TRIPLE_SINGLE_QUOTE, TRIPLE_DOUBLE_QUOTE, value)
        if info['quote_type'] == 'double':
            if not info['is_docstring']:
                if not info['has_internal_quote']:
                    new_value = re.sub(
                        DOUBLE_QUOTE, SINGLE_QUOTE, value)
        return new_value

    if backend == 'parso':
        import parso
        from parso.normalizer import Normalizer

        class MyNormalizer(Normalizer):
            def visit(self, node):
                if node.type == 'string':

                    try:
                        is_docstring = node.parent.parent.parent.type in {
                            'funcdef', 'classdef'}
                    except Exception:
                        is_docstring = False
                        ...
                    # print('----')
                    # print('node = {}'.format(ub.urepr(node, nl=1)))
                    # print(f'is_docstring={is_docstring}')
                    # print(f'node.type={node.type}')
                    # print(f'node.value={node.value}')
                    new_value = fix_string_value(node.value, is_docstring=is_docstring)
                    node.value = new_value
                    # print(f'new_value={new_value}')
                return super().visit(node)

        module = parso.parse(text)
        normalizer = MyNormalizer(None, None)
        normalizer.walk(module)
        new_text = module.get_code()
    elif backend == 'redbaron':
        # TODO: deprecate, redbaron is no longer maintained
        import redbaron
        red = redbaron.RedBaron(text)

        for found in red.find_all('string'):

            value = found.value
            if isinstance(found.parent, redbaron.RedBaron):
                # module docstring or global string
                is_docstring = found.parent[0] == found
            elif found.parent.type in {'class', 'def'}:
                is_docstring = found.parent[0] == found
            elif isinstance(found.parent, redbaron.NodeList):
                is_docstring = '?'
                raise Exception
            else:
                is_docstring = False
            new_value = fix_string_value(value, is_docstring=is_docstring)
            found.value = new_value
        new_text = red.dumps()
    else:
        raise KeyError(backend)

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
