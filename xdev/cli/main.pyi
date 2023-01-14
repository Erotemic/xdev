import argparse
import scriptconfig as scfg
from _typeshed import Incomplete


class RawDescriptionDefaultsHelpFormatter(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter):
    ...


class InfoCLI(scfg.Config):
    __command__: str
    __default__: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class CodeblockCLI(scfg.Config):
    __command__: str
    __default__: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class SedCLI(scfg.Config):
    __command__: str
    __default__: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class FindCLI(scfg.Config):
    __command__: str
    __default__: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class TreeCLI(scfg.Config):
    __command__: str
    __default__: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class PintCLI(scfg.Config):
    __command__: str
    __alias__: Incomplete
    __default__: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class PyfileCLI(scfg.Config):
    __command__: str
    __alias__: Incomplete
    __default__: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class PyVersionCLI(scfg.Config):
    __command__: str
    __alias__: Incomplete
    __default__: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs):
        ...


class FormatQuotesCLI(scfg.Config):
    __command__: str
    __default__: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class FreshPyenvCLI(scfg.Config):
    __command__: str
    __default__: Incomplete

    @classmethod
    def main(cls, cmdline: bool = ..., **kwargs) -> None:
        ...


class DocstrStubgenCLI(scfg.Config):
    __command__: str
    __alias__: Incomplete
    __default__: Incomplete

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
