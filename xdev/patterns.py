import re
import fnmatch
import ubelt as ub

if hasattr(re, 'Pattern'):
    RE_Pattern = re.Pattern
else:
    # sys.version_info[0:2] <= 3.6
    RE_Pattern = type(re.compile('.*'))


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
    def from_regex(cls, data, flags=0, multiline=False, dotall=False,
                   ignorecase=False):
        if multiline:
            flags |= re.MULTILINE
        if dotall:
            flags |= re.DOTALL
        if multiline:
            flags |= re.DOTALL
        if ignorecase:
            flags |= re.IGNORECASE
        pat = re.compile(data, flags=flags)
        self = cls(pat, 'regex')
        return self

    @classmethod
    def from_glob(cls, data):
        self = cls(data, 'glob')
        return self

    @classmethod
    def coerce_backend(cls, data, hint='glob'):
        if isinstance(data, RE_Pattern):
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
