
def make_warnings_print_tracebacks():
    """
    Makes warnings show tracebacks when displayed.

    Applies a monkeypatch to warnings.formatwarning that includes a traceback
    in the displayed warning message.
    """
    import warnings
    import traceback
    _orig_formatwarning = warnings.formatwarning
    warnings._orig_formatwarning = _orig_formatwarning
    def _monkeypatch_formatwarning_tb(*args, **kwargs):
        s = _orig_formatwarning(*args, **kwargs)
        if len(s.strip()):
            tb = traceback.format_stack()
            s += ''.join(tb[:-1])
        return s
    warnings.formatwarning = _monkeypatch_formatwarning_tb
