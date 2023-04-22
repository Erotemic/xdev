Xdev - Excellent Developer
--------------------------

|GithubActions| |Codecov| |Pypi| |Downloads| |ReadTheDocs|

Xdev is an excellent developer tool for excellent developers.
It contains miscellaneous and/or interactive debugging tools.

I mostly maintain this for myself, but I could see polishing it up in the
future.


Remarks
-------

Perhaps I should just use `ipdb` but I often just like to directly embed with
IPython whenever I want:


.. code:: python

    import xdev
    xdev.embed()


Or wherever I want whenever there is an exception.

.. code:: python

    import xdev
    with xdev.embed_on_exception:
        some_code()


I don't feel like I need  `ipdb <https://github.com/gotcha/ipdb>`_'s other features.


I also like to


.. code:: python

    def func(a=1, b=2, c=3):
        """
        Example:
            >>> from this.module import *  # import contextual namespace
            >>> import xinspect
            >>> globals().update(xinspect.get_func_kwargs(func))  # populates globals with default kwarg value
            >>> print(a + b + c)
            6
        """

But I know these things are a little dirty.

But these aren't production practices. These are development tricks and life
hacks to make working faster.


Also see ``xinspect`` for things like ``autogen_imports``


.. code:: python

    >>> import ubelt as ub
    >>> source = ub.codeblock(
    >>>     '''
    >>>     p = os.path.dirname(join('a', 'b'))
    >>>     glob.glob(p)
    >>>     ''')
    >>> # Generate a list of lines to fix the name errors
    >>> lines = autogen_imports(source=source)
    >>> print(lines)
    ['import glob', 'from os.path import join', 'import os']


The CLI
-------

The xdev CLI is getting kinda nice, although it is a bit of a hodgepodge of
functionality (much like this library).

.. code::

    usage: xdev [-h] [--version] {info,codeblock,sed,find,tree,pint,pyfile,pyversion,format_quotes,freshpyenv,docstubs,available_package_versions} ...

    The XDEV CLI

    A collection of excellent developer tools for excellent developers.

    options:
      -h, --help            show this help message and exit
      --version             show version number and exit (default: False)

    commands:
      {info,codeblock,sed,find,tree,pint,pyfile,pyversion,format_quotes,freshpyenv,docstubs,available_package_versions}
                            specify a command to run
        info                Info about xdev
        codeblock           Remove indentation from text.
        sed                 Search and replace text in files
        find                Find matching files or paths in a directory.
        tree                List a directory like a tree
        pint (convert_unit)
                            Converts one type of unit to another via the pint library.
        pyfile (modpath)    Prints the path corresponding to a Python module.
        pyversion (modversion)
                            Detect and print the version of a Python module or package.
        format_quotes       Use single quotes for code and double quotes for docs.
        freshpyenv          Create a fresh environment in a docker container to test a Python package.
        docstubs (doctypes)
                            Generate Typed Stubs from Docstrings (experimental)
        available_package_versions (availpkg)
                            Print a table of available versions of a python package on Pypi


It contains functionality that I generally use when developing on my setup, but
I often find lacking in the setup of others.

For instance the `tree <https://en.wikipedia.org/wiki/Tree_(command)>`_ UNIX
command is amazing, but not everyone has it installed, and getting it via
``apt`` requires sudo privileges. Meanwhile xdev can be installed in user space
via pip, so this provides me with an easy way to get ``tree`` on someone's
system while helping them debug.

Other examples are ``sed``, ``find``, ``pyfile``, and ``pyversion``. Look at
the ``--help`` for more info on them.


The ``availpkg`` command has been indispensable for me when writing
requirements.txt files. If you need to find good versions of a package ---
especially a binary one, e.g. numpy --- for different versions of Python and
would like the appropirate requirements.txt syntax to be generated for you,
take a look at ``availpkg``. It also provides an overview of what versions of a
package are available for what operating systems / CPU architectures.


The ``docstubs`` command is designed to turn google-style docstrings into
proper type annotation stubs.  It "works on my machine" and currently requires
a custom monkey patched mypy. See the code for details, it is possible to use,
but it is still very raw. I do think it can evolve into a tool.


.. |Appveyor| image:: https://ci.appveyor.com/api/projects/status/github/Erotemic/xdev?branch=master&svg=True
   :target: https://ci.appveyor.com/project/Erotemic/xdev/branch/master
.. |Codecov| image:: https://codecov.io/github/Erotemic/xdev/badge.svg?branch=master&service=github
   :target: https://codecov.io/github/Erotemic/xdev?branch=master
.. |Pypi| image:: https://img.shields.io/pypi/v/xdev.svg
   :target: https://pypi.python.org/pypi/xdev
.. |Downloads| image:: https://img.shields.io/pypi/dm/xdev.svg
   :target: https://pypistats.org/packages/xdev
.. |ReadTheDocs| image:: https://readthedocs.org/projects/xdev/badge/?version=latest
    :target: http://xdev.readthedocs.io/en/latest/
.. |GithubActions| image:: https://github.com/Erotemic/xdev/actions/workflows/tests.yml/badge.svg?branch=main
    :target: https://github.com/Erotemic/xdev/actions?query=branch%3Amain
