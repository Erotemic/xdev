import re


class RegexBuilder:
    """
    Notes:
        The way to have multiple negative look aheads/behinds is to change them together SO12689046


    References:
        .. [SO12689046] https://stackoverflow.com/questions/12689046/multiple-negative-lookbehind-assertions-in-python-regex
    """

    def __init__(self):
        raise Exception('Use coerce instead')

    def lookahead(self, pat, positive=True):
        """
        A lookahead pattern that can be positive or negative
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

    def escape(pat):
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


class VimRegexBuilder(RegexBuilder):
    def __init__(self):
        self.constructs = {}
        self.constructs['positive_lookahead'] = r'\({pat}\)\@='
        self.constructs['negative_lookahead'] = r'\({pat}\)\@!'
        self.constructs['positive_lookbehind'] = r'\({pat}\)\@<='
        self.constructs['negative_lookbehind'] = r'\({pat}\)\@<!'
        self.constructs['word'] = r'\<{pat}\>'
        self.constructs['group'] = r'\({pat}\)'
        self.constructs['nongreedy_kleene_star'] = r'\{-}'


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
    """
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
        self.constructs['nongreedy_kleene_star'] = r'*?'
