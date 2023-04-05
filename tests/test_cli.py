

def test_xdev_cli():
    import ubelt as ub
    import xdev

    info = ub.cmd('python3 -m xdev --help', verbose=3)
    assert 'pint' in info['out'].strip()
    assert 'codeblock' in info['out'].strip()
    assert 'tree' in info['out'].strip()

    try:
        import pint  # NOQA
    except ImportError:
        ...
    else:
        info = ub.cmd('python3 -m xdev pint 10gigabytes megabytes', verbose=3)
        assert info['out'].strip() == '10000'

    info = ub.cmd('python3 -m xdev info', verbose=3)
    assert info['ret'] == 0

    info = ub.cmd('python3 -m xdev info --help', verbose=3)
    assert info['ret'] == 0

    info = ub.cmd('python3 -m xdev pyversion xdev', verbose=3)
    assert info['out'].strip() == xdev.__version__
