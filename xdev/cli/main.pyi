import kwconf
from _typeshed import Incomplete

class XdevCLI(kwconf.ModalCLI):
    class InfoCLI(kwconf.Config):
        __command__: str

        @classmethod
        def main(cls, argv: bool = ..., **kwargs) -> None: ...

    class CodeblockCLI(kwconf.Config):
        __command__: str
        __epilog__: str
        text: Incomplete

        @classmethod
        def main(cls, argv: bool = ..., **kwargs) -> None: ...

    class SedCLI(kwconf.Config):
        __command__: str
        __default__: Incomplete

        @classmethod
        def main(cls, argv: bool = ..., **kwargs) -> None: ...

    class FindCLI(kwconf.Config):
        __command__: str
        __default__: Incomplete

        @classmethod
        def main(cls, argv: bool = ..., **kwargs) -> None: ...

    class TreeCLI(kwconf.Config):
        __command__: str
        __default__: Incomplete

        @classmethod
        def main(cls, argv: bool = ..., **kwargs) -> None: ...

    class PintCLI(kwconf.Config):
        __command__: str
        __alias__: Incomplete
        __default__: Incomplete

        @classmethod
        def main(cls, argv: bool = ..., **kwargs) -> None: ...

    class PyfileCLI(kwconf.Config):
        __command__: str
        __alias__: Incomplete
        __default__: Incomplete

        @classmethod
        def main(cls, argv: bool = ..., **kwargs) -> None: ...

    class PyVersionCLI(kwconf.Config):
        __command__: str
        __alias__: Incomplete
        __default__: Incomplete

        @classmethod
        def main(cls, argv: bool = ..., **kwargs): ...

    class EditfileCLI(kwconf.Config):
        __command__: str
        __alias__: Incomplete
        __default__: Incomplete

        @classmethod
        def main(cls, argv: bool = ..., **kwargs) -> None: ...

    class FormatQuotesCLI(kwconf.Config):
        __command__: str
        __default__: Incomplete

        @classmethod
        def main(cls, argv: bool = ..., **kwargs) -> None: ...

    class FreshPyenvCLI(kwconf.Config):
        __command__: str
        __default__: Incomplete

        @classmethod
        def main(cls, argv: bool = ..., **kwargs) -> None: ...

    class DocstrStubgenCLI(kwconf.Config):
        __command__: str
        __alias__: Incomplete
        __default__: Incomplete

        @classmethod
        def main(cls, argv: bool = ..., **kwargs) -> None: ...

    class AvailablePackageCLI(kwconf.Config):
        __command__: str
        __alias__: Incomplete
        __default__: Incomplete
        __doc__: Incomplete

        @classmethod
        def main(cls, argv: bool = ..., **kwargs) -> None: ...

    class RegexCLI(kwconf.Config):
        __command__: str
        backend: Incomplete

        @classmethod
        def main(cls, argv: bool = ..., **kwargs) -> None: ...

def rprint(*args) -> None: ...
def main() -> None: ...
