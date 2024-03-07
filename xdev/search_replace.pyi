from typing import List
from os import PathLike
from typing import Tuple
import ubelt as ub
from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any
from xdev.patterns import MultiPattern, Pattern, RE_Pattern as RE_Pattern


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


def sed(regexpr: str | Pattern,
        repl: str,
        dpath: str | None = None,
        include: str | List[str] | MultiPattern | None = None,
        exclude: str | List[str] | MultiPattern | None = None,
        dirblocklist: str | List[str] | MultiPattern | None = None,
        recursive: bool = True,
        dry: bool = False,
        verbose: int = 1) -> None:
    ...


def grep(regexpr: str | Pattern,
         dpath: str | None = None,
         include: str | List[str] | MultiPattern | None = None,
         exclude: str | List[str] | MultiPattern | None = None,
         recursive: bool = True,
         dirblocklist: str | List[str] | MultiPattern | None = None,
         verbose: int = 1) -> List[GrepResult]:
    ...


def find(pattern: str | Pattern | None = None,
         dpath: str | Pattern | None = None,
         include: str | List[str] | MultiPattern | None = None,
         exclude: str | List[str] | MultiPattern | None = None,
         dirblocklist: str | List[str] | MultiPattern | None = None,
         type: str | List[str] | None = None,
         recursive: bool = ...,
         followlinks: bool = False) -> Generator[Any, None, Any]:
    ...


def sedfile(fpath: str | PathLike,
            regexpr: str | Pattern,
            repl: str,
            dry: bool = False,
            verbose: int = 1) -> List[Tuple[str, str]]:
    ...


def grepfile(fpath: str | PathLike,
             regexpr: str | Pattern,
             verbose: int = 1) -> None | GrepResult:
    ...


def greptext(text: str,
             regexpr: str | Pattern,
             fpath: Incomplete | None = ...,
             verbose: int = 1) -> None | GrepResult:
    ...
