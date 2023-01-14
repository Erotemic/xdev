from _typeshed import Incomplete


class RegexBuilder:
    common_patterns: Incomplete

    def __init__(self) -> None:
        ...

    def lookahead(self, pat, positive: bool = ...):
        ...

    def lookbehind(self, pat, positive: bool = ...):
        ...

    def named_field(self, pat, name: Incomplete | None = ...):
        ...

    def bref_field(self, name):
        ...

    def escape(self, pat):
        ...

    def optional(self, pat):
        ...

    def group(self, pat):
        ...

    def oneof(self, *paterns):
        ...

    @classmethod
    def coerce(cls, backend: str = ...):
        ...

    @property
    def whitespace(self):
        ...

    @property
    def nongreedy(self):
        ...

    @property
    def number(self):
        ...


class VimRegexBuilder(RegexBuilder):
    vim_patterns: Incomplete
    constructs: Incomplete
    special: Incomplete

    def __init__(self) -> None:
        ...


class PythonRegexBuilder(RegexBuilder):
    python_patterns: Incomplete
    constructs: Incomplete
    special: Incomplete

    def __init__(self) -> None:
        ...
