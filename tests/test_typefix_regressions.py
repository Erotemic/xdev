"""Regression checks for optional dependencies and version constraints."""

import random

import pytest


def test_python_rng_works_without_numpy(monkeypatch):
    from xdev import util_random

    monkeypatch.setattr(util_random, 'np', None)
    assert util_random.ensure_rng(None, api='python') is random._inst
    assert isinstance(util_random.ensure_rng(13, api='python'), random.Random)
    assert isinstance(util_random.ensure_rng(2.5, api='python'), random.Random)
    assert util_random.ensure_rng(random, api='python') is random._inst

    with pytest.raises(ImportError, match='numpy'):
        util_random._pystate_to_npstate(random.Random(13).getstate())


def test_explicit_python_version_bounds_are_comparable():
    from xdev.cli.available_package_versions import ReqPythonVersionSpec

    reqspec = ReqPythonVersionSpec('>=3.8, <3.12')
    assert str(reqspec.highest_explicit()) == '3.8'
    assert reqspec.matches('3.10')
    assert not reqspec.matches('3.12')

    # No minimum is a legitimate outcome: callers must handle None.
    reqspec = ReqPythonVersionSpec('<3.12')
    assert reqspec.highest_explicit() is None


def test_grep_format_text_honors_color_flag(monkeypatch):
    import re
    import ubelt as ub
    from xdev.search_replace import GrepResult

    monkeypatch.setattr(ub, 'color_text', lambda text, color: f'<{color}:{text}>')
    result = GrepResult('example.txt', pattern=re.compile('needle'))
    result.append(1, 'a needle in a haystack\n')
    assert '<red:needle>' in result.format_text(color=True)
    assert '<red:needle>' not in result.format_text(color=False)
    assert 'a needle in a haystack' in result.format_text(color=False)
