from _typeshed import Incomplete


def embed(parent_locals: Incomplete | None = ...,
          parent_globals: Incomplete | None = ...,
          exec_lines: Incomplete | None = ...,
          remove_pyqt_hook: bool = ...,
          n: int = ...) -> None:
    ...


def embed_if_requested(n: int = ...) -> None:
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


embed_on_exception_context: Incomplete
