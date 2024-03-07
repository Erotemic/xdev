from typing import Callable
from _typeshed import Incomplete

IS_PROFILING: Incomplete


class DummyProfiler:

    def __call__(self, func):
        ...

    def add_module(self, mod: Incomplete | None = ...) -> None:
        ...

    def print_report(self) -> None:
        ...


profile: Incomplete


def profile_now(func: Callable) -> Callable:
    ...


def profile_globals() -> None:
    ...
