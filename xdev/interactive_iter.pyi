from _typeshed import Incomplete

INDEXABLE_TYPES: Incomplete


class InteractiveIter:

    def __init__(iiter,
                 iterable: None = None,
                 enabled: bool = True,
                 startx: int = 0,
                 default_action: str = 'next',
                 custom_actions: list = ...,
                 wraparound: bool = False,
                 display_item: bool = False,
                 verbose: bool = True) -> None:
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

    def __call__(iiter, iterable: Incomplete | None = ...) -> None:
        ...

    @classmethod
    def draw(iiter) -> None:
        ...
