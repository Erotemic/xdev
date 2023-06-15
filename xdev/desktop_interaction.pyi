from os import PathLike
from types import ModuleType


def editfile(fpath: PathLike | ModuleType | str, verbose: int = True) -> None:
    ...


def view_directory(dpath: PathLike | None = None,
                   verbose: bool = False) -> None:
    ...


def startfile(fpath: PathLike, verbose: int = True) -> None:
    ...
