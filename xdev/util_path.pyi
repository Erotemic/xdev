from os import PathLike
from typing import Dict
import ubelt as ub
import os
from _typeshed import Incomplete
from collections.abc import Generator


class ChDir:
    context_dpath: Incomplete
    orig_dpath: Incomplete

    def __init__(self, dpath) -> None:
        ...

    def __enter__(self):
        ...

    def __exit__(self, a, b, c) -> None:
        ...


def sidecar_glob(
        main_pat: str | PathLike,
        sidecar_ext,
        main_key: str = ...,
        sidecar_key: Incomplete | None = ...,
        recursive: int = ...
) -> Generator[Dict[str, ub.Path | None], None, None]:
    ...


def tree(path: str | os.PathLike) -> Generator[str, None, None]:
    ...
