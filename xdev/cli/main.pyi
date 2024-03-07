import scriptconfig as scfg
from _typeshed import Incomplete
from scriptconfig.modal import ModalCLI


class XdevCLI(ModalCLI):

    class InfoCLI(scfg.DataConfig):
        __command__: str

        @classmethod
        def main(cls, cmdline: bool = ..., **kwargs) -> None:
            ...

    class CodeblockCLI(scfg.DataConfig):
        __command__: str
        __epilog__: str
        text: Incomplete

        @classmethod
        def main(cls, cmdline: bool = ..., **kwargs) -> None:
            ...

    class SedCLI(scfg.DataConfig):
        __command__: str
        __default__: Incomplete

        @classmethod
        def main(cls, cmdline: bool = ..., **kwargs) -> None:
            ...

    class FindCLI(scfg.DataConfig):
        __command__: str
        __default__: Incomplete

        @classmethod
        def main(cls, cmdline: bool = ..., **kwargs) -> None:
            ...

    class TreeCLI(scfg.DataConfig):
        __command__: str
        __default__: Incomplete

        @classmethod
        def main(cls, cmdline: bool = ..., **kwargs) -> None:
            ...

    class PintCLI(scfg.DataConfig):
        __command__: str
        __alias__: Incomplete
        __default__: Incomplete

        @classmethod
        def main(cls, cmdline: bool = ..., **kwargs) -> None:
            ...

    class PyfileCLI(scfg.DataConfig):
        __command__: str
        __alias__: Incomplete
        __default__: Incomplete

        @classmethod
        def main(cls, cmdline: bool = ..., **kwargs) -> None:
            ...

    class PyVersionCLI(scfg.DataConfig):
        __command__: str
        __alias__: Incomplete
        __default__: Incomplete

        @classmethod
        def main(cls, cmdline: bool = ..., **kwargs):
            ...

    class EditfileCLI(scfg.DataConfig):
        __command__: str
        __alias__: Incomplete
        __default__: Incomplete

        @classmethod
        def main(cls, cmdline: bool = ..., **kwargs) -> None:
            ...

    class FormatQuotesCLI(scfg.DataConfig):
        __command__: str
        __default__: Incomplete

        @classmethod
        def main(cls, cmdline: bool = ..., **kwargs) -> None:
            ...

    class FreshPyenvCLI(scfg.DataConfig):
        __command__: str
        __default__: Incomplete

        @classmethod
        def main(cls, cmdline: bool = ..., **kwargs) -> None:
            ...

    class DocstrStubgenCLI(scfg.DataConfig):
        __command__: str
        __alias__: Incomplete
        __default__: Incomplete

        @classmethod
        def main(cls, cmdline: bool = ..., **kwargs) -> None:
            ...

    class AvailablePackageCLI(scfg.DataConfig):
        __command__: str
        __alias__: Incomplete
        __default__: Incomplete
        __doc__: Incomplete

        @classmethod
        def main(cls, cmdline: bool = ..., **kwargs) -> None:
            ...

    class RegexCLI(scfg.DataConfig):
        __command__: str
        backend: Incomplete

        @classmethod
        def main(cls, cmdline: bool = ..., **kwargs) -> None:
            ...


def rprint(*args) -> None:
    ...


def main() -> None:
    ...
