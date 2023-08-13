"""
Helpers to build cross-flavor regular expressions.
"""
import re


class RegexBuilder:
    """
    Notes:
        The way to have multiple negative look aheads/behinds is to change them together SO12689046

    References:
        .. [SO12689046] https://stackoverflow.com/questions/12689046/multiple-negative-lookbehind-assertions-in-python-regex

    Example:
        b = RegexBuilder.coerce('python')
        import re
        pat = re.compile('[A-Z-]+')
    """
    common_patterns = [
        {'key': 'word',      'pattern': r'\w', 'docs': r'An alphanumeric word, i.e. [a-zA-Z0-9_] (also matches unicode characters in Python)'},
        {'key': 'non-word',  'pattern': r'\W', 'docs': r'Anything not a word'},
        {'key': 'space',     'pattern': r'\s', 'docs': r'Any space character including: " " "\t", "\n", "\r"'},
        {'key': 'non-space', 'pattern': r'\S', 'docs': r'Any non-space character'},
        {'key': 'digit',     'pattern': r'\d', 'docs': r'any number 0-9'},
        {'key': 'digit',     'pattern': r'\D', 'docs': r'any non-digit'},
        {'key': 'zero_or_more', 'pattern': r'*', 'docs': r'zero or more of the pattern to the left', 'alias': ['kleene_star']},
    ]

    def __init__(self):
        raise Exception('Use ``RegexBuilder.coerce(backend=...)`` instead')

    def lookahead(self, pat, positive=True, mode='positive'):
        """
        A lookahead pattern that can be positive or negative

        looklook
        """
        if positive is not None:
            import ubelt as ub
            ub.schedule_deprecation(
                'xdev', 'positive', 'arg to lookbehind',
                migration='use mode=positive or mode=negative instead',
                deprecate='now')
            mode = 'positive' if positive else 'negative'

        if mode == 'positive':
            return self.constructs['positive_lookahead'].format(pat=pat)
        elif mode == 'negative':
            return self.constructs['negative_lookahead'].format(pat=pat)
        else:
            raise KeyError(mode)

    def lookbehind(self, pat, positive=True):
        """
        A lookbehind pattern that can be positive or negative
        """
        if positive is not None:
            import ubelt as ub
            ub.schedule_deprecation(
                'xdev', 'positive', 'arg to lookbehind',
                migration='use mode=positive or mode=negative instead',
                deprecate='now')
            mode = 'positive' if positive else 'negative'

        if mode == 'positive':
            return self.constructs['positive_lookbehind'].format(pat=pat)
        elif mode == 'negative':
            return self.constructs['negative_lookbehind'].format(pat=pat)
        else:
            raise KeyError(mode)

    def named_field(self, pat, name=None):
        if name is None:
            return self.constructs['group'].format(pat=pat)
        else:
            return self.constructs['named_field'].format(pat=pat, name=name)

    def bref_field(self, name):
        return self.constructs['backref_field'].format(name=name)

    def escape(self, pat):
        return re.escape(pat)

    def optional(self, pat):
        return r'{pat}?'.format(pat=pat)

    def group(self, pat):
        return self.constructs['group'].format(pat=pat)

    def oneof(self, *paterns):
        return self.group('|'.join(paterns))

    @classmethod
    def coerce(cls, backend='python'):
        if backend == 'python':
            cls = PythonRegexBuilder
        elif backend == 'vim':
            cls = VimRegexBuilder
        else:
            raise KeyError(backend)
        self = cls()
        return self

    @property
    def identifier(self):
        """
        A word, except it must start with a letter or underscore (not a number)

        References:
            https://stackoverflow.com/questions/5474008/regular-expression-to-confirm-whether-a-string-is-a-valid-python-identifier

        Example:
            >>> from xdev.regex_builder import *  # NOQA
            >>> b = PythonRegexBuilder()
            >>> assert re.match(b.identifier, 'hello')
            >>> assert re.match(b.identifier, 'hello')
            >>> assert re.match(b.identifier, '𝛣_ello')
            >>> assert re.match(b.identifier, 'h_1e8llo')
            >>> assert not re.match(b.identifier, '1hello')
        """
        return r'[^\d\W]\w*'
        # return '[A-Za-z_][A-Za-z_0-9]*'

    @property
    def hex(self):
        """
        A case-independent hex character
        """
        return '[0-9a-fA-F]'

    @property
    def word(self):
        return self.special['word']

    @property
    def whitespace(self):
        return self.special['space'] + '*'

    @property
    def nongreedy(self):
        return self.special['nongreedy_zero_or_more']

    @property
    def number(self):
        """
        Can match a generic floating point number

        References:
            https://www.regular-expressions.info/floatingpoint.html

        Example:
            >>> from xdev.regex_builder import *  # NOQA
            >>> b = PythonRegexBuilder()
            >>> pat = re.compile('^' + b.number + '$')
            >>> assert pat.match('3.4')
            >>> assert pat.match('3.4e-1')
            >>> assert pat.match('3.4')
            >>> assert pat.match('3.4e+1')
            >>> assert not pat.match('3.4a+1')

            >>> b = PythonRegexBuilder()
            >>> num_part = b.named_field(b.number, name='number')
            >>> space_part = b.named_field(' *', name='spaces')
            >>> unit_part = b.named_field('.*', name='unit')
            >>> pat = re.compile('^' + num_part + space_part + unit_part + '$')
            >>> pat.match('3.4').groupdict()
            >>> pat.match('3.1415 foobars').groupdict()
            >>> pat.match('3.1415foobars').groupdict()
            >>> pat.match('+3.1415e9foobars').groupdict()
        """
        exponent_part = '[eE][-+]?[0-9]+'
        decimal_part = r'[-+]?[0-9]*\.?[0-9]+'
        exponent_group = self.constructs['group'].format(pat=exponent_part)
        number_pat = decimal_part + exponent_group + '?'
        return number_pat


class VimRegexBuilder(RegexBuilder):
    """
    https://dev.to/iggredible/learning-vim-regex-26ep
    """

    vim_patterns = [
        {'key': 'nongreedy_zero_or_more', 'pattern': r'\{-}', 'docs': r'non-greedily matches zero or more of the pattern to the left', 'alias': ['nongreedy_kleene_star']},
    ]
    def __init__(self):
        self.constructs = {}
        self.constructs['positive_lookahead'] = r'\({pat}\)\@='
        self.constructs['negative_lookahead'] = r'\({pat}\)\@!'
        self.constructs['positive_lookbehind'] = r'\({pat}\)\@<='
        self.constructs['negative_lookbehind'] = r'\({pat}\)\@<!'
        self.constructs['word'] = r'\<{pat}\>'
        self.constructs['group'] = r'\({pat}\)'

        self.special = {}
        for item in self.common_patterns + self.vim_patterns:
            self.special[item['key']] = item['pattern']

    def previous(self, min=None, max=None, exact=None, greedy=True):
        r"""
        Match the previous pattern some number of times.

        Args:
            min (int | None): minimum number of matches

            max (int | None): maximum number of matches

            exact (int | None):
                Specify exact number of matches.
                Mutex with minimum and max.

            greedy (bool):
                if True match as many as possible, otherwise match as few as
                possible

        Example:
            >>> from xdev.regex_builder import *  # NOQA
            >>> b = VimRegexBuilder()
            >>> assert b.previous(exact=1) == r'\{1}'
            >>> assert b.previous(min=1, max=3) == r'\{1,3}'
            >>> assert b.previous(min=1, max=3, greedy=False) == r'\{-1,3}'
            >>> assert b.previous(max=3) == r'\{,3}'
            >>> assert b.previous(min=3) == r'\{3,}'
            >>> assert b.previous() == '*'
            >>> assert b.previous(greedy=False) == r'\{-}'
        """
        if exact is not None:
            assert min is None and max is None
            expr = f'\\{{{exact}}}'
        else:
            if min is None:
                min = 0
            if max == float('inf'):
                max = None
            if min == 0 and max is None:
                return '*' if greedy else '\\{-}'
            greed = '' if greedy else '-'
            if max is None:
                expr = f'\\{{{greed}{min},}}'
            elif min == 0:
                expr = f'\\{{{greed},{max}}}'
            else:
                expr = f'\\{{{greed}{min},{max}}}'
        return expr


class PythonRegexBuilder(RegexBuilder):
    r"""
    Contains helper methods to construct a regex

    Example:
        >>> b = PythonRegexBuilder()
        >>> pat_text = b.lookbehind('_') + r'v\d+' + b.optional(b.lookahead('_'))
        >>> pat = re.compile(pat_text)
        >>> print(pat.search('_v321_').group())
        v321
        >>> print(pat.search('_v321').group())
        v321
        >>> print(pat.search('fdsfds_v321_fdsfsd').group())
        v321
        >>> print(pat.search('fdsfds_v321fdsfsd').group())
        v321
        >>> print(pat.search('fdsfdsv321fdsfsd'))
        None

    Example:
        >>> # Test multiple negative lookbehind
        >>> b = PythonRegexBuilder()
        >>> suffix = 'foo'
        >>> neg_prefix1 = b.lookbehind('abc', positive=0)
        >>> neg_prefix2 = b.lookbehind('efg', positive=0)
        >>> pat1 = re.compile(neg_prefix1 + suffix)
        >>> pat2 = re.compile(neg_prefix2 + suffix)
        >>> patB = re.compile(neg_prefix1 + neg_prefix2 + suffix)
        >>> cases = ['abcfoo', 'efgfoo', 'hijfoo', 'foo']
        >>> print([bool(pat1.search(c)) for c in cases])
        >>> print([bool(pat2.search(c)) for c in cases])
        >>> print([bool(patB.search(c)) for c in cases])
        [False, True, True, True]
        [True, False, True, True]
        [False, False, True, True]

    References:
        https://www.dataquest.io/blog/regex-cheatsheet/
        https://docs.python.org/3/library/re.html#regular-expression-syntax
    """

    python_patterns = [
        {'key': 'nongreedy_zero_or_more', 'pattern': r'*?', 'docs': r'non-greedily matches zero or more of the pattern to the left', 'alias': ['nongreedy_kleene_star']},
        {'key': 'boundary', 'pattern': r'\b', 'docs': r'The boundary at the start or end of a word'},
        {'key': 'non-boundary', 'pattern': r'\B'},
        {'key': 'left-expr', 'pattern': r'\A'},
        {'key': 'right-expr', 'pattern': r'\Z', 'docs': 'Matches only at the end of the string'},
    ]
    def __init__(self):
        self.constructs = {}
        self.constructs['positive_lookahead'] = r'(?={pat})'
        self.constructs['negative_lookahead'] = r'(?!{pat})'
        self.constructs['positive_lookbehind'] = r'(?<={pat})'
        self.constructs['negative_lookbehind'] = r'(?<!{pat})'
        self.constructs['word'] = r'\b{pat}\b'
        self.constructs['group'] = r'({pat})'
        self.constructs['named_field'] = r'(?P<{name}>{pat})'
        self.constructs['backref_field'] = r'\g<{name}>'

        self.special = {}
        for item in self.common_patterns + self.python_patterns:
            self.special[item['key']] = item['pattern']

    def previous(self, min=None, max=None, exact=None, greedy=True):
        r"""
        Match the previous pattern some number of times.

        Args:
            min (int | None): minimum number of matches

            max (int | None): maximum number of matches

            exact (int | None):
                Specify exact number of matches.
                Mutex with minimum and max.

            greedy (bool):
                if True match as many as possible, otherwise match as few as
                possible

        Example:
            >>> from xdev.regex_builder import *  # NOQA
            >>> b = PythonRegexBuilder()
            >>> assert b.previous(exact=1) == '{1}'
            >>> assert b.previous(min=1, max=3) == '{1,3}'
            >>> assert b.previous(min=1, max=3, greedy=False) == '{1,3}?'
            >>> assert b.previous(max=3) == '{,3}'
            >>> assert b.previous(min=3) == '{3,}'
            >>> assert b.previous() == '*'
            >>> assert b.previous(greedy=False) == '*?'

        Example:
            >>> from xdev.regex_builder import *  # NOQA
            >>> b = PythonRegexBuilder()
            >>> assert re.compile('a' + b.previous(exact=2) + '$').match('aa')
            >>> assert not re.compile('a' + b.previous(exact=2) + '$').match('aaa')
            >>> assert not re.compile('a' + b.previous(exact=2) + '$').match('a')
        """
        if exact is not None:
            assert min is None and max is None
            expr = f'{{{exact}}}'
        else:
            if min is None:
                min = 0
            if max == float('inf'):
                max = None
            if min == 0 and max is None:
                return '*' if greedy else '*?'
            if max is None:
                expr = f'{{{min},}}'
            elif min == 0:
                expr = f'{{,{max}}}'
            else:
                expr = f'{{{min},{max}}}'
            if not greedy:
                expr = expr + '?'
        return expr
