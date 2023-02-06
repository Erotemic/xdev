from typing import Union
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


def sed(regexpr: Union[str, Pattern],
        repl: str,
        dpath: Union[str, None] = None,
        include: Union[str, List[str], MultiPattern, None] = None,
        exclude: Union[str, List[str], MultiPattern, None] = None,
        recursive: bool = True,
        dry: bool = False,
        verbose: int = 1) -> None:
    ...


def grep(regexpr: Union[str, Pattern],
         dpath: Union[str, None] = None,
         include: Union[str, List[str], MultiPattern, None] = None,
         exclude: Union[str, List[str], MultiPattern, None] = None,
         recursive: bool = True,
         verbose: int = 1) -> List[GrepResult]:
    ...


def find(pattern: Union[str, Pattern, None] = None,
         dpath: Union[str, Pattern, None] = None,
         include: Union[str, List[str], MultiPattern, None] = None,
         exclude: Union[str, List[str], MultiPattern, None] = None,
         dirblocklist: Union[str, List[str], MultiPattern, None] = None,
         type: Union[str, List[str], None] = None,
         recursive: bool = ...,
         followlinks: bool = False) -> Generator[Any, None, Any]:
    ...


def sedfile(fpath: Union[str, PathLike],
            regexpr: Union[str, Pattern],
            repl: str,
            dry: bool = False,
            verbose: int = 1) -> List[Tuple[str, str]]:
    ...


def grepfile(fpath: Union[str, PathLike],
             regexpr: Union[str, Pattern],
             verbose: int = 1) -> None | GrepResult:
    ...


def greptext(text: str,
             regexpr: Union[str, Pattern],
             fpath: Incomplete | None = ...,
             verbose: int = 1) -> None | GrepResult:
    ...
