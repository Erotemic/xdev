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
    """
    common_patterns = [
        {'key': 'word',      'pattern': r'\w', 'docs': r'An alphanumeric word'},
        {'key': 'non-word',  'pattern': r'\W', 'docs': r'Anything not a word'},
        {'key': 'space',     'pattern': r'\s', 'docs': r'Any space character including: " " "\t", "\n", "\r"'},
        {'key': 'non-space', 'pattern': r'\S', 'docs': r'Any non-space character'},
        {'key': 'digit',     'pattern': r'\d', 'docs': r'any number 0-9'},
        {'key': 'digit',     'pattern': r'\D', 'docs': r'any non-digit'},
        {'key': 'zero_or_more', 'pattern': r'*', 'docs': r'zero or more of the pattern to the left', 'alias': ['kleene_star']},
    ]

    def __init__(self):
        raise Exception('Use coerce instead')

    def lookahead(self, pat, positive=True):
        """
        A lookahead pattern that can be positive or negative

        looklook
        """
        if positive:
            return self.constructs['positive_lookahead'].format(pat=pat)
        else:
            return self.constructs['negative_lookahead'].format(pat=pat)

    def lookbehind(self, pat, positive=True):
        """
        A lookbehind pattern that can be positive or negative
        """
        if positive:
            return self.constructs['positive_lookbehind'].format(pat=pat)
        else:
            return self.constructs['negative_lookbehind'].format(pat=pat)

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
    def whitespace(self):
        return self.special['space'] + '*'

    @property
    def nongreedy(self):
        return self.special['nongreedy_kleene_star']

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
    """

    python_patterns = [
        {'key': 'nongreedy_zero_or_more', 'pattern': r'*?', 'docs': r'non-greedily matches zero or more of the pattern to the left', 'alias': ['nongreedy_kleene_star']},
        {'key': 'boundary', 'pattern': r'\b', 'docs': r'The boundary at the start or end of a word'},
        {'key': 'non-boundary', 'pattern': r'\B'},
        {'key': 'left-expr', 'pattern': r'\A'},
        {'key': 'right-expr', 'pattern': r'\Z'},
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
