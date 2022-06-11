from collections.abc import Generator
from typing import Any

get_func_kwargs: Any


def get_stack_frame(N: int = ..., strict: bool = ...):
    ...


def distext(obj) -> str:
    ...


def iter_object_tree(obj) -> Generator[Any, Any, None]:
    ...


def test_object_pickleability(obj):
    ...
