import numpy
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


def tree_repr(cwd: Any | None = ..., max_files: int = ...) -> None:
    ...
