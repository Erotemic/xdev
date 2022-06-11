from typing import Any

INDEXABLE_TYPES: Any


class InteractiveIter:

    def __init__(iiter,
                 iterable: None = ...,
                 enabled: bool = ...,
                 startx: int = ...,
                 default_action: str = ...,
                 custom_actions: list = ...,
                 wraparound: bool = ...,
                 display_item: bool = ...,
                 verbose: bool = ...) -> None:
        ...

    @classmethod
    def eventloop(cls, custom_actions=...):
        ...

    def __iter__(iiter):
        ...

    def handle_ans(iiter, ans_):
        ...

    def prompt(iiter):
        ...

    def wait_for_input(iiter):
        ...

    def __call__(iiter, iterable: Any | None = ...) -> None:
        ...

    @classmethod
    def draw(iiter) -> None:
        ...
