#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""
Note:
    The reason the logic is in xdev.cli.main instead of this file is because
    this file always have the name __main__ and we want to be able to import
    the various CLI constructs as packages in some instances.
"""
from xdev.cli.main import main


if __name__ == '__main__':
    """
    CommandLine:
        xdev --help
        xdev --version
        xdev info
        xdev sed "main" "MAIN" "." --dry=True --include="*_*.py"
        xdev find "*_*.py"  '.'
        xdev codeblock "
            import sys
            print(sys.argv)
            print([
                'hello world'
            ])
        "
    """
    main()
