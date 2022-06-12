import argparse
import scriptconfig as scfg
from typing import Any


class RawDescriptionDefaultsHelpFormatter(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter):
    ...


class CodeblockCLI(scfg.Config):
    name: str
    description: str
    default: Any

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class InfoCLI(scfg.Config):
    name: str
    description: str
    default: Any

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class DocstrStubgenCLI(scfg.Config):
    name: str
    description: str
    default: Any

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class SedCLI(scfg.Config):
    name: str
    description: str
    default: Any

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class FindCLI(scfg.Config):
    name: str
    description: str
    default: Any

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class ModalCLI:
    description: Any
    sub_clis: Any
    version: Any

    def __init__(self,
                 description: str = ...,
                 sub_clis=...,
                 version: Any | None = ...) -> None:
        ...

    def build_parser(self):
        ...

    def run(self):
        ...


def main() -> None:
    ...
