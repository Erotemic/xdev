import argparse
import scriptconfig as scfg
from _typeshed import Incomplete


class RawDescriptionDefaultsHelpFormatter(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter):
    ...


class CodeblockCLI(scfg.Config):
    name: str
    description: str
    default: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class InfoCLI(scfg.Config):
    name: str
    description: str
    default: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class DocstrStubgenCLI(scfg.Config):
    name: str
    description: str
    default: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class SedCLI(scfg.Config):
    name: str
    description: str
    default: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class FormatQuotesCLI(scfg.Config):
    name: str
    description: str
    default: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class FindCLI(scfg.Config):
    name: str
    description: str
    default: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class TreeCLI(scfg.Config):
    name: str
    description: str
    default: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class PintCLI(scfg.Config):
    __command__: str
    description: str
    default: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class ModpathCLI(scfg.Config):
    __command__: str
    description: str
    default: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class ModalCLI:
    description: Incomplete
    sub_clis: Incomplete
    version: Incomplete

    def __init__(self,
                 description: str = ...,
                 sub_clis=...,
                 version: Incomplete | None = ...) -> None:
        ...

    def build_parser(self):
        ...

    def run(self):
        ...


def main() -> None:
    ...
