from os import PathLike
from typing import Union


def editfile(fpath: PathLike, verbose: int = True) -> None:
    ...


def view_directory(dpath: Union[PathLike, None] = None,
                   verbose: bool = False) -> None:
    ...


def startfile(fpath: PathLike, verbose: int = True) -> None:
    ...
