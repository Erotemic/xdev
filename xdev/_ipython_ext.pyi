from IPython.terminal.embed import InteractiveShellEmbed
from _typeshed import Incomplete


class InteractiveShellEmbedEnhanced(InteractiveShellEmbed):

    @property
    def user_global_ns(self):
        ...

    embedded_outside_func: bool
    to_global: Incomplete
    to_local: Incomplete

    def init_frame(self, frame) -> None:
        ...

    def share_locals(self) -> None:
        ...


def embed2(local_ns: Incomplete | None = ..., **kwargs) -> None:
    ...
