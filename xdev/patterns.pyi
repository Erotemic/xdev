import ubelt as ub
from _typeshed import Incomplete
from collections.abc import Generator

RE_Pattern: Incomplete


class FakeParseModule:

    def Parser(self, *args, **kwargs) -> None:
        ...


class PatternBase:

    def match(self, text) -> None:
        ...

    def search(self, text) -> None:
        ...

    def sub(self, repl, text) -> None:
        ...


class Pattern(PatternBase, ub.NiceRepr):
    pattern: Incomplete
    backend: Incomplete

    def __init__(self, pattern, backend) -> None:
        ...

    def __nice__(self) -> str:
        ...

    def to_regex(self) -> Pattern:
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

    @classmethod
    def coerce(cls, data, hint: str = 'auto'):
        ...

    def match(self, text):
        ...

    def search(self, text):
        ...

    def sub(self, repl: str, text: str, count: int = ...):
        ...

    def paths(self,
              cwd: Incomplete | None = ...,
              recursive: bool = ...) -> Generator[ub.Path, None, None]:
        ...


class MultiPattern(PatternBase, ub.NiceRepr):
    predicate: Incomplete
    patterns: Incomplete

    def __init__(self, patterns, predicate) -> None:
        ...

    def __nice__(self):
        ...

    def match(self, text):
        ...

    def paths(self,
              cwd: Incomplete | None = ...,
              recursive: bool = ...) -> None:
        ...

    @classmethod
    def coerce(cls,
               data,
               hint: str = 'auto',
               predicate: str = ...) -> MultiPattern:
        ...
