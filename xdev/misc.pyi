import numpy
from typing import Any
from _typeshed import Incomplete
from typing import Any


def quantum_random(pure: bool = False) -> numpy.uint32:
    ...


def byte_str(num: int, unit: str = 'auto', precision: int = 2) -> str:
    ...


def set_overlaps(set1, set2, s1: str = ..., s2: str = ...):
    ...


def nested_type(obj: Any, unions: bool = False) -> str:
    ...


def difftext(text1: str,
             text2: str,
             context_lines: int = 0,
             ignore_whitespace: bool = False,
             colored: bool = False) -> str:
    ...


def tree_repr(cwd: Incomplete | None = ...,
              max_files: int = ...,
              dirblocklist: Incomplete | None = ...,
              show_nfiles: str = ...,
              return_text: bool = False,
              return_tree: bool = False,
              pathstyle: str = 'name',
              with_type: bool = ...,
              colors: bool = ...):
    ...
