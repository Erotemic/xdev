import sys
import os

__all__ = [
    'profile',
    'profile_now',
    'profile_globals',
    'IS_PROFILING',
]

_FALSY_STRINGS = {'', '0', 'off', 'false', 'no'}
IS_PROFILING = os.environ.get('XDEV_PROFILE', '').lower() not in _FALSY_STRINGS
IS_PROFILING |= os.environ.get('LINE_PROFILE', '').lower() not in _FALSY_STRINGS
IS_PROFILING |= '--line-profile' in sys.argv
IS_PROFILING |= '--profile' in sys.argv


class DummyProfiler:
    """
    A profiler that does nothing.
    """

    def __call__(self, func):
        return func

    def add_module(self, mod=None):
        ...

    def print_report(self):
        print('Profiling was not enabled')

if IS_PROFILING:
    import line_profiler
    profile = line_profiler.profile
    profile.enable()
else:
    profile = DummyProfiler()


def profile_now(func):
    """
    Wrap a function to print profile information after it is called.

    Args:
        func (Callable): function to profile

    Returns:
        Callable: the wrapped function

    Example:
        >>> # xdoctest: +SKIP
        >>> from xdev.profiler import *  # NOQA
        >>> def func_to_profile():
        >>>     list(range(10))
        >>>     tuple(range(100))
        >>>     set(range(1000))
        >>> profile_now(func_to_profile)()  # xdoctest: +IGNORE_WANT

        Timer unit: 1e-09 s

        Total time: 2.7767e-05 s
        File: <ipython-input-11-049a3440df03>
        Function: func_to_profile at line 3

        Line #      Hits         Time  Per Hit   % Time  Line Contents
        ==============================================================
             3                                           def func_to_profile():
             4         1       3200.0   3200.0     11.5      list(range(10))
             5         1       1949.0   1949.0      7.0      tuple(range(100))
             6         1      22618.0  22618.0     81.5      set(range(1000))
    """
    import line_profiler
    profile = line_profiler.LineProfiler()
    new_func = profile(func)
    new_func.profile = profile

    def print_report():
        profile.print_stats(rich=1)

    new_func.print_report = print_report

    def wraper(*args, **kwargs):
        try:
            return new_func(*args, **kwargs)
        except Exception:
            pass
        finally:
            new_func.print_report()
    wraper.new_func = new_func
    return wraper


def profile_globals():
    """
    Adds the profile decorator to all global functions
    """
    import inspect
    parent_frame = inspect.currentframe().f_back

    parent_frame.f_globals
    name = parent_frame.f_globals['__name__']
    module = sys.modules[name]

    from xdoctest.dynamic_analysis import is_defined_by_module
    import xdev
    for k, v in module.__dict__.items():
        if is_defined_by_module(v, module):
            if callable(v):
                v = xdev.profile(v)
                parent_frame.f_globals[k] = v


if __name__ == '__main__':
    """
    CommandLine:
        python -m xdev.profiler all
    """
    import xdoctest
    xdoctest.doctest_module(__file__)
