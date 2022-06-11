import numpy
from typing import Any


def quantum_random(pure: bool = ...) -> numpy.uint32:
    ...


def byte_str(num: int, unit: str = ..., precision: int = ...) -> str:
    ...


def set_overlaps(set1, set2, s1: str = ..., s2: str = ...):
    ...


def nested_type(obj: Any, unions: bool = ...) -> str:
    ...


def difftext(text1: str,
             text2: str,
             context_lines: int = ...,
             ignore_whitespace: bool = ...,
             colored: bool = ...) -> str:
    ...


def tree_repr(cwd: Any | None = ..., max_files: int = ...) -> None:
    ...
