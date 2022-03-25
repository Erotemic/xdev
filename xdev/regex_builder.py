import re


class _AbstractRegexBuilder:

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


class VimRegexBuilder(_AbstractRegexBuilder):
    def __init__(self):
        self.constructs = {}
        self.constructs['positive_lookahead'] = r'\({pat}\)\@='
        self.constructs['negative_lookahead'] = r'\({pat}\)\@!'
        self.constructs['positive_lookbehind'] = r'\({pat}\)\@<='
        self.constructs['negative_lookbehind'] = r'\({pat}\)\@<!'
        self.constructs['word'] = r'\<{pat}\>'
        self.constructs['group'] = r'\({pat}\)'
        self.constructs['nongreedy_kleene_star'] = r'\{-}'


class PythonRegexBuilder(_AbstractRegexBuilder):
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
