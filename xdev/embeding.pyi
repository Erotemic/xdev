from os import PathLike
from _typeshed import Incomplete


def embed(parent_locals: Incomplete | None = ...,
          parent_globals: Incomplete | None = ...,
          exec_lines: Incomplete | None = ...,
          remove_pyqt_hook: bool = ...,
          n: int = ...) -> None:
    ...


def breakpoint():
    ...


def load_snapshot(fpath: str | PathLike,
                  parent_globals: dict | None = None) -> None:
    ...


def snapshot(parent_ns: dict | None = None, n: int = 0) -> None:
    ...


def embed_if_requested(n: int = ...) -> None:
    ...


class EmbedOnException:
    before_embed: Incomplete

    def __init__(self, before_embed: Incomplete | None = ...) -> None:
        ...

    def __enter__(self):
        ...

    def __call__(self, before_embed: Incomplete | None = ...):
        ...

    def __exit__(__self, __type, __value, __trace) -> None:
        ...


def fix_embed_globals() -> None:
    ...


embed_on_exception_context: Incomplete
embed_on_exception = embed_on_exception_context
