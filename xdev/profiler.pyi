from typing import Callable
from typing import Tuple
from typing import List
from typing import Union
from typing import Any

IS_PROFILING: Any
profile: Any


def __dummy_profile__(func):
    ...


profile = __dummy_profile__


def profile_now(func: Callable) -> Callable:
    ...


class KernprofParser:
    profile: Any

    def __init__(self, profile) -> None:
        ...

    def raw_text(self) -> str:
        ...

    def print_report(self) -> None:
        ...

    def get_text(self) -> Tuple[str, str]:
        ...

    def dump_text(self) -> None:
        ...

    def parse_rawprofile_blocks(self, text: str) -> List[str]:
        ...

    def clean_line_profile_text(self, text):
        ...

    def get_block_totaltime(self, block: str) -> str | None:
        ...

    def get_block_id(self,
                     block: str,
                     readlines: Union[None, Callable] = None) -> str:
        ...

    def parse_timemap_from_blocks(self, profile_block_list):
        ...

    def get_summary(self,
                    profile_block_list: List[str],
                    maxlines: int = 20) -> str:
        ...

    def fix_rawprofile_blocks(self, profile_block_list):
        ...

    def clean_lprof_file(self, input_fname, output_fname: Any | None = ...):
        ...


def profile_globals() -> None:
    ...
