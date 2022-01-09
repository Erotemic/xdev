
def main():
    import xdev
    print('xdev.__version__ = {!r}'.format(xdev.__version__))
    print('xdev.__file__ = {!r}'.format(xdev.__file__))
    # import fire
    # fire.Fire


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdev/xdev/__main__.py
    """
    import xdoctest
    xdoctest.doctest_module(__file__)
