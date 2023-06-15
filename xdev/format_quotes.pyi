from _typeshed import Incomplete

SINGLE_QUOTE: Incomplete
DOUBLE_QUOTE: Incomplete
TRIPLE_SINGLE_QUOTE: Incomplete
TRIPLE_DOUBLE_QUOTE: Incomplete


def format_quotes_in_text(text: str, backend: str = ...) -> str:
    ...


def format_quotes_in_file(fpath: str,
                          diff: bool = True,
                          write: bool = False,
                          verbose: int = 3) -> None:
    ...


def format_quotes(path,
                  diff: bool = ...,
                  write: bool = ...,
                  verbose: int = ...,
                  recursive: bool = ...) -> None:
    ...
