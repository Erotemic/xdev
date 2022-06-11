from typing import Union
from typing import List
import ubelt as ub
from collections.abc import Generator
from typing import Any


def sed(regexpr,
        repl,
        dpath: Any | None = ...,
        include: Any | None = ...,
        exclude: Any | None = ...,
        recursive: bool = ...,
        dry: bool = ...,
        verbose: int = ...) -> None:
    ...


def grep(regexpr,
         dpath: Any | None = ...,
         include: Any | None = ...,
         exclude: Any | None = ...,
         recursive: bool = ...,
         verbose: int = ...):
    ...


def find(pattern: str = ...,
         dpath: str = ...,
         include: Union[str, List[str]] = ...,
         exclude: Union[str, List[str]] = ...,
         type: Union[str, List[str]] = ...,
         recursive: bool = ...,
         followlinks: bool = ...) -> Generator[Any, None, Any]:
    ...


def sedfile(fpath, regexpr, repl, dry: bool = ..., verbose: int = ...):
    ...


class GrepResult(ub.NiceRepr):
    pattern: Any
    fpath: Any
    found_lxs: Any
    found_lines: Any
    max_line: int

    def __init__(self, fpath, pattern: Any | None = ...) -> None:
        ...

    def __nice__(self):
        ...

    def __iter__(self):
        ...

    def __len__(self):
        ...

    def append(self, lx, line) -> None:
        ...

    def format_text(self):
        ...


def grepfile(fpath, regexpr, verbose: int = ...):
    ...
