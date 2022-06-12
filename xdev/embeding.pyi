from typing import Any


def embed(parent_locals: Any | None = ...,
          parent_globals: Any | None = ...,
          exec_lines: Any | None = ...,
          remove_pyqt_hook: bool = ...,
          n: int = ...) -> None:
    ...


class EmbedOnException:

    def __init__(self) -> None:
        ...

    def __enter__(self):
        ...

    def __call__(self):
        ...

    def __exit__(__self, __type, __value, __trace) -> None:
        ...


def fix_embed_globals() -> None:
    ...


embed_on_exception_context: Any
