from typing import Union
from os import PathLike
from collections.abc import Generator
from typing import Any


class ChDir:
    context_dpath: Any
    orig_dpath: Any

    def __init__(self, dpath) -> None:
        ...

    def __enter__(self):
        ...

    def __exit__(self, a, b, c) -> None:
        ...


def sidecar_glob(main_pat: Union[str, PathLike],
                 sidecar_ext,
                 main_key: str = ...,
                 sidecar_key: Any | None = ...,
                 recursive: int = ...) -> Generator[None, None, None]:
    ...


def tree(path) -> Generator[str, None, None]:
    ...
