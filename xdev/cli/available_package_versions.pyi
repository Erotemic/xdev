import scriptconfig as scfg
from _typeshed import Incomplete


class AvailablePackageConfig(scfg.DataConfig):
    package_name: Incomplete
    request_min: Incomplete
    refresh: Incomplete


def main(cmdline: int = ..., **kwargs) -> None:
    ...


class ReqPythonVersionSpec:
    pattern: Incomplete
    parts: Incomplete
    specifier: Incomplete
    constraints: Incomplete

    def __init__(self, pattern) -> None:
        ...

    def highest_explicit(self):
        ...

    def matches(self, other):
        ...


def parse_platform_tag(platform_tag):
    ...


def parse_wheel_name(fname):
    ...


def grab_pypi_items(package_name, refresh: bool = ...):
    ...


def vectorize(func):
    ...


def cp_sorter(v):
    ...


def summarize_package_availability(package_name):
    ...


class PythonVersions:
    latest: Incomplete
    cp_codes: Incomplete
    table: Incomplete
    python_vstrings: Incomplete
    python_version_rows: Incomplete

    def __init__(self) -> None:
        ...

    def resolve_pyversion(self, pyver, maximize: bool = ...):
        ...


def build_package_table(package_name, refresh: bool = ...):
    ...


def minimum_cross_python_versions(package_name,
                                  request_min: Incomplete | None = ...,
                                  refresh: bool = ...):
    ...


def demo() -> None:
    ...
