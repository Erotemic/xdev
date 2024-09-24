

def test_xdev_cli():
    import ubelt as ub
    import xdev
    import sys
    py_exe = sys.executable

    info = ub.cmd(f'{py_exe} -m xdev --help', verbose=3)
    assert 'pint' in info['out'].strip()
    assert 'codeblock' in info['out'].strip()
    assert 'tree' in info['out'].strip()

    try:
        import pint  # NOQA
    except ImportError:
        ...
    else:
        info = ub.cmd(f'{py_exe} -m xdev pint 10gigabytes megabytes', verbose=3)
        assert float(info['out'].strip()) == 10000

    info = ub.cmd(f'{py_exe} -m xdev info', verbose=3)
    assert info['ret'] == 0

    info = ub.cmd(f'{py_exe} -m xdev info --help', verbose=3)
    assert info['ret'] == 0

    info = ub.cmd(f'{py_exe} -m xdev pyversion xdev', verbose=3)
    assert info['out'].strip() == xdev.__version__
