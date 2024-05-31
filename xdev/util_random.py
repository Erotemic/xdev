"""
Ported from kwutil / kwarray

This may just move to ubelt proper

Implements a version of `ensure_rng` that does not require on numpy (but allows
for it). This mirrors :kwarray:`ensure_rng`, which is a numpy-first
implementation.
"""
import random
try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

_SEED_MAX = int(2 ** 32 - 1)


def _npstate_to_pystate(npstate):
    """
    Convert state of a NumPy RandomState object to a state
    that can be used by Python's Random. Derived from [SO44313620]_.

    References:
        .. [SO44313620] https://stackoverflow.com/questions/44313620/convert-randomstate

    Example:
        >>> # xdoctest: +REQUIRES(module:numpy)
        >>> import numpy as np
        >>> py_rng = random.Random(0)
        >>> np_rng = np.random.RandomState(seed=0)
        >>> npstate = np_rng.get_state()
        >>> pystate = _npstate_to_pystate(npstate)
        >>> py_rng.setstate(pystate)
        >>> assert np_rng.rand() == py_rng.random()
    """
    PY_VERSION = 3
    version, keys, pos, has_gauss, cached_gaussian_ = npstate
    keys_pos = tuple(map(int, keys)) + (int(pos),)
    cached_gaussian_ = cached_gaussian_ if has_gauss else None
    pystate = (PY_VERSION, keys_pos, cached_gaussian_)
    return pystate


def _pystate_to_npstate(pystate):
    """
    Convert state of a Python Random object to state usable
    by NumPy RandomState. Derived from [SO44313620]_.

    References:
        .. [SO44313620] https://stackoverflow.com/questions/44313620/convert-randomstate

    Example:
        >>> # xdoctest: +REQUIRES(module:numpy)
        >>> import numpy as np
        >>> py_rng = random.Random(0)
        >>> np_rng = np.random.RandomState(seed=0)
        >>> pystate = py_rng.getstate()
        >>> npstate = _pystate_to_npstate(pystate)
        >>> np_rng.set_state(npstate)
        >>> assert np_rng.rand() == py_rng.random()
    """
    NP_VERSION = 'MT19937'
    version, keys_pos_, cached_gaussian_ = pystate
    keys, pos = keys_pos_[:-1], keys_pos_[-1]
    keys = np.array(keys, dtype=np.uint32)
    has_gauss = cached_gaussian_ is not None
    cached_gaussian = cached_gaussian_ if has_gauss else 0.0
    npstate = (NP_VERSION, keys, pos, has_gauss, cached_gaussian)
    return npstate


def _coerce_rng_type(rng):
    """
    Internal method that transforms input seeds into an integer form.
    """
    if rng is None or isinstance(rng, (random.Random, np.random.RandomState)):
        pass
    elif rng is random:
        rng = rng._inst
    elif rng is np.random:
        rng = np.random.mtrand._rand
    # elif isinstance(rng, str):
    #     # todo convert string to rng
    #     pass
    elif isinstance(rng, (float, np.floating)):
        rng = float(rng)
        # Coerce the float into an integer
        a, b = rng.as_integer_ratio()
        if b == 1:
            rng = a
        else:
            s = max(a.bit_length(), b.bit_length())
            rng = (b << s) | a
    elif isinstance(rng, (int, np.integer)):
        rng = int(rng)
    else:
        raise TypeError(
            'Cannot coerce {!r} to a random object'.format(type(rng)))
    return rng


def ensure_rng(rng=None, api='python'):
    """
    Coerces input into a random number generator.

    This function is useful for ensuring that your code uses a controlled
    internal random state that is independent of other modules.

    If the input is None, then a global random state is returned.

    If the input is a numeric value, then that is used as a seed to construct a
    random state.

    If the input is a random number generator, then another random number
    generator with the same state is returned. Depending on the api, this
    random state is either return as-is, or used to construct an equivalent
    random state with the requested api.

    Args:
        rng (int | float | None | numpy.random.RandomState | random.Random):
            if None, then defaults to the global rng. Otherwise this can
            be an integer or a RandomState class. Defaults to the global
            random.

        api (str): specify the type of random number
            generator to use. This can either be 'numpy' for a
            :class:`numpy.random.RandomState` object or 'python' for a
            :class:`random.Random` object. Defaults to numpy.

    Returns:
        (numpy.random.RandomState | random.Random) :
            rng - either a numpy or python random number generator, depending
            on the setting of ``api``.

    Example:
        >>> # xdoctest: +REQUIRES(module:numpy)
        >>> from xdev.util_random import *  # NOQA
        >>> from xdev.util_random import ensure_rng
        >>> rng = ensure_rng(None)
        >>> ensure_rng(0, 'python').randint(0, 1000)
        864
        >>> # xdoctest: +REQUIRES(module:numpy)
        >>> import numpy as np
        >>> ensure_rng(np.random.RandomState(1)).randint(0, 1000)
        427

    Example:
        >>> from xdev.util_random import *  # NOQA
        >>> from xdev.util_random import ensure_rng
        >>> num = 4
        >>> print('--- Python as PYTHON ---')
        >>> py_rng = random.Random(0)
        >>> pp_nums = [py_rng.random() for _ in range(num)]
        >>> print(pp_nums)
        >>> print('--- Numpy as PYTHON ---')
        >>> # xdoctest: +REQUIRES(module:numpy)
        >>> import numpy as np
        >>> np_rng = ensure_rng(random.Random(0), api='numpy')
        >>> np_nums = [np_rng.rand() for _ in range(num)]
        >>> print(np_nums)
        >>> print('--- Numpy as NUMPY---')
        >>> np_rng = np.random.RandomState(seed=0)
        >>> nn_nums = [np_rng.rand() for _ in range(num)]
        >>> print(nn_nums)
        >>> print('--- Python as NUMPY---')
        >>> py_rng = ensure_rng(np.random.RandomState(seed=0), api='python')
        >>> pn_nums = [py_rng.random() for _ in range(num)]
        >>> print(pn_nums)
        >>> assert np_nums == pp_nums
        >>> assert pn_nums == nn_nums

    Example:
        >>> # Test that random modules can be coerced
        >>> # xdoctest: +REQUIRES(module:numpy)
        >>> from xdev.util_random import *  # NOQA
        >>> import random
        >>> import numpy as np
        >>> ensure_rng(random, api='python')
        >>> ensure_rng(random, api='numpy')
        >>> ensure_rng(np.random, api='python')
        >>> ensure_rng(np.random, api='numpy')
    """
    rng = _coerce_rng_type(rng)

    if api == 'numpy':
        assert np is not None, 'requires numpy'
        if rng is None:
            # This is the underlying random state of the np.random module
            rng = np.random.mtrand._rand
            # Dont do this because it seeds using dev/urandom
            # rng = np.random.RandomState(seed=None)
        elif isinstance(rng, int):
            rng = np.random.RandomState(seed=rng % _SEED_MAX)
        elif isinstance(rng, random.Random):
            # Convert python to numpy random state
            py_rng = rng
            pystate = py_rng.getstate()
            npstate = _pystate_to_npstate(pystate)
            rng = np_rng = np.random.RandomState(seed=0)
            np_rng.set_state(npstate)
    elif api == 'python':
        if rng is None:
            # This is the underlying random state of the random module
            rng = random._inst
        elif isinstance(rng, int):
            rng = random.Random(rng % _SEED_MAX)
        elif np is not None and isinstance(rng, np.random.RandomState):
            # Convert numpy to python random state
            np_rng = rng
            npstate = np_rng.get_state()
            pystate = _npstate_to_pystate(npstate)
            rng = py_rng = random.Random(0)
            py_rng.setstate(pystate)
    else:
        raise KeyError('unknown rng api={}'.format(api))
    return rng
