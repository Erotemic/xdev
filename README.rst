Xdev - Excellent Developer
--------------------------

|GithubActions| |Codecov| |Pypi| |Downloads| |ReadTheDocs|


+------------------+------------------------------------------+
| Read the docs    | https://xdev.readthedocs.io              |
+------------------+------------------------------------------+
| Github           | https://github.com/Erotemic/xdev         |
+------------------+------------------------------------------+
| Pypi             | https://pypi.org/project/xdev            |
+------------------+------------------------------------------+

Xdev is an excellent developer tool for excellent developers.
It contains miscellaneous and/or interactive debugging tools.

This started as a project for myself to contain development related tools that
I wouldn't want to ship with a package itself (where as `ubelt
<https://github.com/Erotemic/ubelt>`_ contains the tools used in programs
themselves). I've polished it up over the years, and it's become a reasonably
useful package with tools I could see others making use of.


This is the CLI:

.. code::

    usage: xdev [-h] [--version] {info,codeblock,sed,find,tree,pint,pyfile,pyversion,editfile,format_quotes,freshpyenv,docstubs,available_package_versions,dirstats} ...

    The XDEV CLI

    A collection of excellent developer tools for excellent developers.

    options:
      -h, --help            show this help message and exit
      --version             show version number and exit (default: False)

    commands:
      {info,codeblock,sed,find,tree,pint,pyfile,pyversion,editfile,format_quotes,freshpyenv,docstubs,available_package_versions,dirstats}
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
        editfile (edit)     Opens a file in your visual editor determined by the ``VISUAL``
        format_quotes       Use single quotes for code and double quotes for docs.
        freshpyenv          Create a fresh environment in a docker container to test a Python package.
        docstubs (doctypes)
                            Generate Typed Stubs from Docstrings (experimental)
        available_package_versions (availpkg)
                            Print a table of available versions of a python package on Pypi
        dirstats            Analysis for code in a repository


.. .... mkinit xdev

This is the top level API:

.. code:: python

    from xdev import algo
    from xdev import autojit
    from xdev import class_reloader
    from xdev import cli
    from xdev import desktop_interaction
    from xdev import embeding
    from xdev import format_quotes
    from xdev import interactive_iter
    from xdev import introspect
    from xdev import misc
    from xdev import patterns
    from xdev import profiler
    from xdev import regex_builder
    from xdev import search_replace
    from xdev import tracebacks
    from xdev import util
    from xdev import util_networkx
    from xdev import util_path

    from xdev.algo import (edit_distance, knapsack, knapsack_greedy, knapsack_ilp,
                           knapsack_iterative, knapsack_iterative_int,
                           knapsack_iterative_numpy, number_of_decimals,)
    from xdev.autojit import (import_module_from_pyx,)
    from xdev.class_reloader import (reload_class,)
    from xdev.desktop_interaction import (editfile, startfile, view_directory,)
    from xdev.embeding import (EmbedOnException, embed, embed_if_requested,
                               embed_on_exception, embed_on_exception_context,
                               fix_embed_globals,)
    from xdev.format_quotes import (DOUBLE_QUOTE, SINGLE_QUOTE,
                                    TRIPLE_DOUBLE_QUOTE, TRIPLE_SINGLE_QUOTE,
                                    format_quotes, format_quotes_in_file,
                                    format_quotes_in_text,)
    from xdev.interactive_iter import (InteractiveIter,)
    from xdev.introspect import (distext, get_func_kwargs, get_stack_frame,
                                 iter_object_tree, test_object_pickleability,)
    from xdev.misc import (byte_str, difftext, nested_type, quantum_random,
                           set_overlaps, textfind, tree_repr,)
    from xdev.patterns import (MultiPattern, Pattern, PatternBase, RE_Pattern,
                               our_extended_regex_compile,)
    from xdev.profiler import (IS_PROFILING, profile, profile_globals,
                               profile_now,)
    from xdev.regex_builder import (PythonRegexBuilder, RegexBuilder,
                                    VimRegexBuilder,)
    from xdev.search_replace import (GrepResult, find, grep, grepfile, greptext,
                                     sed, sedfile,)
    from xdev.tracebacks import (make_warnings_print_tracebacks,)
    from xdev.util import (bubbletext, conj_phrase, take_column,)
    from xdev.util_networkx import (AsciiDirectedGlyphs, AsciiUndirectedGlyphs,
                                    UtfDirectedGlyphs, UtfUndirectedGlyphs,
                                    generate_network_text, graph_str,
                                    write_network_text,)
    from xdev.util_path import (ChDir, sidecar_glob, tree,)

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

   pip install xdev
   xdev --help


It contains functionality that I generally use when developing on my setup, but
I often find lacking in the setup of others.

For instance the `tree <https://en.wikipedia.org/wiki/Tree_(command)>`_ UNIX
command is amazing, but not everyone has it installed, and getting it via
``apt`` requires sudo privileges. Meanwhile xdev can be installed in user space
via pip, so this provides me with an easy way to get ``tree`` on someone's
system while helping them debug.

Other examples are ``sed``, ``find``, ``pyfile``, and ``pyversion``. Look at
the ``--help`` for more info on them.

The ``dirstats`` function is like a buffed up ``tree``. In addition to printing
the directory tree structure it inspects the contents of the tree and
summarizes things like: number of lines per type of file. For Python files it
breaks up the analysis into code-lines and docstring lines to give a better
sense of project complexity.


For repo maintence I use this package in conjunction with `xcookie
<https://github.com/Erotemic/xcookie>`_. I use xcookie to generate the package
structure and then xdev helps fill in the details. Specifically the
``availpkg`` and ``docstubs`` commands.


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
