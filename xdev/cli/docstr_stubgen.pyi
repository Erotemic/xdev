from os import PathLike
from typing import Dict
from types import ModuleType
from _typeshed import Incomplete
from mypy.nodes import FuncDef
from mypy.stubgen import StubGenerator
from typing import Dict

StubStub: Incomplete


def generate_typed_stubs(modpath: PathLike) -> Dict[PathLike, str]:
    ...


def postprocess_hacks(text, mod):
    ...


def stdlib_names():
    ...


def common_module_names():
    ...


def common_module_aliases():
    ...


def common_unreferenced():
    ...


def hacked_typing_info(type_name):
    ...


class ExtendedStubGenerator(StubGenerator):

    def visit_func_def(self,
                       o: FuncDef,
                       is_abstract: bool = False,
                       is_overload: bool = False) -> None:
        ...

    def visit_class_def(self, o) -> None:
        ...


def modpath_coerce(modpath_coercable: str | PathLike | ModuleType) -> str:
    ...
