from typing import Callable
from typing import Tuple
from typing import List
import line_profiler
from _typeshed import Incomplete

IS_PROFILING: Incomplete


class DummyProfiler:

    def __call__(self, func):
        ...

    def add_module(self, mod: Incomplete | None = ...) -> None:
        ...

    def print_report(self) -> None:
        ...


class ExtendedLineProfiler(line_profiler.LineProfiler):

    def add_module(self, mod: Incomplete | None = ...):
        ...

    def print_report(self) -> None:
        ...


profile: Incomplete


def profile_now(func: Callable) -> Callable:
    ...


class KernprofParser:
    profile: Incomplete

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
                     readlines: None | Callable = None) -> str:
        ...

    def parse_timemap_from_blocks(self, profile_block_list):
        ...

    def get_summary(self,
                    profile_block_list: List[str],
                    maxlines: int = 20) -> str:
        ...

    def fix_rawprofile_blocks(self, profile_block_list):
        ...

    def clean_lprof_file(self,
                         input_fname,
                         output_fname: Incomplete | None = ...):
        ...


def profile_globals() -> None:
    ...
