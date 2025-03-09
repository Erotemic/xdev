import warnings


def make_warnings_print_tracebacks():
    """
    Makes warnings show tracebacks when displayed.

    Applies a monkeypatch to warnings.formatwarning that includes a traceback
    in the displayed warning message.

    NOTE:
        Use the context manager `:class:WarningsWithTracebacks` instead, or
        :func:`WarningsWithTracebacks.apply()` if global modification is
        needed.

    Example:
        >>> # xdoctest: +SKIP
        >>> make_warnings_print_tracebacks()
        >>> warnings.warn('This is a test warning')
    """
    WarningsWithTracebacks.apply()


class WarningsWithTracebacks:
    """
    Makes warnings show tracebacks when displayed.

    Applies a monkeypatch to warnings.formatwarning that includes a traceback
    in the displayed warning message.

    CommandLine:
        xdoctest -m xdev.tracebacks WarningsWithTracebacks:0
        xdoctest -m xdev.tracebacks WarningsWithTracebacks:1

    Example:
        >>> # xdoctest: +IGNORE_WANT
        >>> from xdev.tracebacks import *  # NOQA
        >>> import warnings
        >>> with WarningsWithTracebacks():
        ...     warnings.warn('This is a test warning')
        <string>:1: UserWarning: This is a test warning
        Traceback (most recent call last):
        ...

    Example:
        >>> from xdev.tracebacks import *  # NOQA
        >>> import warnings
        >>> warnings.warn('This warning1 has no traceback')
        >>> with WarningsWithTracebacks():
        >>>     warnings.warn('This warning2 has a traceback')
        >>> warnings.warn('This warning3 has no traceback')

    Example:
        >>> import warnings
        >>> def my_function():
        ...     with WarningsWithTracebacks():
        ...         warnings.warn('This is a test warning')
        >>> def driver():
        >>>     my_function()
        >>> driver()
    """
    _enter_count = 0

    def __init__(self, thread_safe=True):
        if thread_safe:
            import threading
            self._lock = threading.Lock()
        else:
            from contextlib import nullcontext
            self._lock = nullcontext()

    def __enter__(self):
        with self._lock:
            # Apply patching if it's the first entry in this thread
            if self._enter_count == 0:
                print("ENTER")
                self._orig_formatwarning = warnings.formatwarning
                warnings.formatwarning = self._monkeypatch_formatwarning_tb
            else:
                print("NOT ENTER")
            self._enter_count += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._enter_count -= 1
        if self._enter_count == 0:
            warnings.formatwarning = self._orig_formatwarning

    def _monkeypatch_formatwarning_tb(self, *args, **kwargs):
        import traceback
        s = self._orig_formatwarning(*args, **kwargs)
        if len(s.strip()):
            tb = traceback.format_stack()
            s += ''.join(tb[:-1])
        return s

    @classmethod
    def apply(cls):
        """
        Apply this warnings traceback patch globaly. It will not be undone.
        """
        cls().__enter__()


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdev/xdev/tracebacks.py
    """
    # Test, as xdoctest doesn't work correctly for patched warning testing.
    def main():
        warnings.warn('This warning1 has no traceback')
        with WarningsWithTracebacks():
            warnings.warn('This warning2 has a traceback')
        warnings.warn('This warning3 has no traceback')

    main()
