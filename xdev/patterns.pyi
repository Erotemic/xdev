import ubelt as ub
from typing import Any

RE_Pattern: Any


class PatternBase:

    def match(self, text) -> None:
        ...

    def search(self, text) -> None:
        ...

    def sub(self, repl, text) -> None:
        ...


class Pattern(PatternBase, ub.NiceRepr):
    pattern: Any
    backend: Any

    def __init__(self, pattern, backend) -> None:
        ...

    def __nice__(self):
        ...

    @classmethod
    def from_regex(cls,
                   data,
                   flags: int = ...,
                   multiline: bool = ...,
                   dotall: bool = ...,
                   ignorecase: bool = ...):
        ...

    @classmethod
    def from_glob(cls, data):
        ...

    @classmethod
    def coerce_backend(cls, data, hint: str = ...):
        ...

    def match(self, text):
        ...

    def search(self, text):
        ...

    def sub(self, repl: str, text: str, count: int = ...):
        ...

    @classmethod
    def coerce(cls, data, hint: str = ...):
        ...

    def paths(self, cwd: Any | None = ..., recursive: bool = ...) -> None:
        ...


class MultiPattern(PatternBase, ub.NiceRepr):
    predicate: Any
    patterns: Any

    def __init__(self, patterns, predicate) -> None:
        ...

    def __nice__(self):
        ...

    def match(self, text):
        ...

    def paths(self, cwd: Any | None = ..., recursive: bool = ...) -> None:
        ...

    @classmethod
    def coerce(cls, data, hint: str = ..., predicate: str = ...):
        ...
