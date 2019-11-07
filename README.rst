xdev
----

|CircleCI| |Travis| |Appveyor| |Codecov| |Pypi| |Downloads| |ReadTheDocs|


Miscellaneous interactive debugging tools for developers


Perhaps I should just use `ipdb` but I often just like to directly embed with IPython whenever I want:


.. code:: python

    import xdev
    xdev.embed()


Or wherever I want whenever there is an exception.

.. code:: python

    import xdev
    with xdev.embed_on_exception_context:
        some_code()


I don't feel like I need  ``ipdb``'s other features. 


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


https://github.com/Erotemic/xinspect


.. |CircleCI| image:: https://circleci.com/gh/Erotemic/xdev.svg?style=svg
    :target: https://circleci.com/gh/Erotemic/xdev
.. |Travis| image:: https://img.shields.io/travis/Erotemic/xdev/master.svg?label=Travis%20CI
   :target: https://travis-ci.org/Erotemic/xdev?branch=master
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
