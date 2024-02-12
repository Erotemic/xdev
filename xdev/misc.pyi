import numpy
from typing import Iterable
from typing import Dict
from typing import Any
from os import PathLike
from _typeshed import Incomplete


def quantum_random(pure: bool = False) -> numpy.uint32:
    ...


def byte_str(num: int, unit: str = 'auto', precision: int = 2) -> str:
    ...


def set_overlaps(set1: Iterable,
                 set2: Iterable,
                 s1: str = 's1',
                 s2: str = 's2') -> Dict[str, int]:
    ...


def nested_type(obj: Any, unions: bool = False) -> str:
    ...


def difftext(text1: str,
             text2: str,
             context_lines: int = 0,
             ignore_whitespace: bool = False,
             colored: bool = False) -> str:
    ...


def tree_repr(cwd: None | str | PathLike = None,
              max_files: int | None = 100,
              dirblocklist: Incomplete | None = ...,
              show_nfiles: str = ...,
              return_text: bool = False,
              return_tree: bool = False,
              pathstyle: str = 'name',
              max_depth: Incomplete | None = ...,
              with_type: bool = ...,
              abs_root_label: bool = True,
              ignore_dotprefix: bool = ...,
              colors: bool = ...):
    ...


def textfind(text, pattern) -> None:
    ...
