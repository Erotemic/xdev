from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any

get_func_kwargs: Incomplete


def get_stack_frame(N: int = 0, strict: bool = True):
    ...


def distext(obj) -> str:
    ...


def iter_object_tree(obj) -> Generator[Any, Any, None]:
    ...


def test_object_pickleability(obj):
    ...
