#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
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
