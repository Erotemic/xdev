from typing import Union
from typing import List
import ubelt as ub
from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any
from xdev.patterns import MultiPattern, RE_Pattern as RE_Pattern


def sed(regexpr,
        repl,
        dpath: Incomplete | None = ...,
        include: Incomplete | None = ...,
        exclude: Incomplete | None = ...,
        recursive: bool = ...,
        dry: bool = ...,
        verbose: int = ...) -> None:
    ...


def grep(regexpr,
         dpath: Incomplete | None = ...,
         include: Incomplete | None = ...,
         exclude: Incomplete | None = ...,
         recursive: bool = ...,
         verbose: int = ...):
    ...


def find(pattern: Union[str, None] = None,
         dpath: Union[str, None] = None,
         include: Union[str, List[str], MultiPattern, None] = None,
         exclude: Union[str, List[str], MultiPattern, None] = None,
         dirblocklist: Union[str, List[str], MultiPattern, None] = None,
         type: Union[str, List[str], None] = None,
         recursive: bool = ...,
         followlinks: bool = False) -> Generator[Any, None, Any]:
    ...


def sedfile(fpath, regexpr, repl, dry: bool = ..., verbose: int = ...):
    ...


class GrepResult(ub.NiceRepr):
    pattern: Incomplete
    fpath: Incomplete
    found_lxs: Incomplete
    found_lines: Incomplete
    max_line: int

    def __init__(self, fpath, pattern: Incomplete | None = ...) -> None:
        ...

    def __nice__(self):
        ...

    def __iter__(self):
        ...

    def __len__(self):
        ...

    def append(self, lx, line) -> None:
        ...

    def format_text(self, color: bool = ...):
        ...


def grepfile(fpath, regexpr, verbose: int = ...):
    ...


def greptext(text,
             regexpr,
             fpath: Incomplete | None = ...,
             verbose: int = ...):
    ...
