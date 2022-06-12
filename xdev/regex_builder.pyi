from typing import Any


class _AbstractRegexBuilder:

    def lookahead(self, pat, positive: bool = ...):
        ...

    def lookbehind(self, pat, positive: bool = ...):
        ...

    def named_field(self, pat, name: Any | None = ...):
        ...

    def bref_field(self, name):
        ...

    def escape(pat):
        ...

    def optional(self, pat):
        ...

    def group(self, pat):
        ...

    def oneof(self, *paterns):
        ...


class VimRegexBuilder(_AbstractRegexBuilder):
    constructs: Any

    def __init__(self) -> None:
        ...


class PythonRegexBuilder(_AbstractRegexBuilder):
    constructs: Any

    def __init__(self) -> None:
        ...
