"""
Ported from kwutil

This may just move to ubelt proper? Some of the pint integration is sus though.
"""
import datetime as datetime_mod
import numbers
import time
import ubelt as ub
import math
from datetime import datetime as datetime_cls


__docstubs__ = """
import pint
from datetime import tzinfo
"""


class TimeValueError(ValueError):
    ...


class TimeTypeError(TypeError):
    ...


class datetime(datetime_cls):
    """
    An enriched datetime class

    Example:
        >>> # xdoctest: +REQUIRES(module:pint)
        >>> # xdoctest: +REQUIRES(module:pytimeparse)
        >>> import xdev
        >>> self = xdev.util_time.datetime.random()
        >>> print(f'self = {self!s}')
        >>> print(f'self = {self!r}')
    """

    def __str__(self):
        return self.isoformat()

    def __repr__(self):
        return f'DT({self.isoformat()})'

    def isoformat(self, pathsafe=False):
        if pathsafe:
            return isoformat(pathsafe=pathsafe)
        else:
            return super().isoformat()

    @classmethod
    def coerce(cls, data, **kwargs):
        """
        Args:
            data: passed to `func`:coerce_datetime
            **kwargs: passed to `func`:coerce_datetime

        Example:
            data = '1970-01-01'
            cls = datetime
        """
        dt = coerce_datetime(data, **kwargs)
        try:
            self = cls(dt.year, dt.month, dt.day, dt.hour, dt.minute,
                       dt.second, dt.microsecond, dt.tzinfo)
        except AttributeError:
            self = dt
        return self

    @classmethod
    def random(cls, start=None, end=None, rng=None):
        """
        Example:
            datetime.random(start='2010-01-01', end='2020-01-01')
            data = '1970-01-01'
            cls = datetime
            rng = 0
            start = None
            end = None
        """
        from xdev.util_random import ensure_rng
        rng = ensure_rng(rng)
        min_dt = None
        max_dt = None
        if start is not None:
            min_dt = coerce_datetime(start)
        if end is not None:
            max_dt = coerce_datetime(end)
        if min_dt is None:
            # min_dt = datetime_cls(1, 1, 2, 0, 0)
            # min_dt = min_dt.replace(tzinfo=datetime_mod.timezone.utf)  # work around win32 issue
            min_dt = coerce_datetime('1980-01-01')
        if max_dt is None:
            # max_dt = cls.max
            # https://stackoverflow.com/questions/71680355/oserror-errno-22-invalid-argument-when-using-datetime-strptime
            # max_dt = max_dt.replace(tzinfo=datetime_mod.timezone.utf)  # work around win32 issue
            max_dt = coerce_datetime('2980-01-01')
        try:
            min_ts = min_dt.timestamp()
            max_ts = max_dt.timestamp()
        except Exception as ex:
            print(f'min_dt: {type(min_dt)} = {min_dt}')
            print(f'max_dt: {type(max_dt)} = {max_dt}')
            print(f'ex={ex}')
            raise

        ts = rng.randint(int(min_ts), int(max_ts))
        default_timezone = 'utc'
        tz = coerce_timezone(default_timezone)
        self = cls.fromtimestamp(ts, tz=tz)
        return self


class timedelta(datetime_mod.timedelta):
    """
    An enriched timedelta class

    Example:
        >>> # xdoctest: +REQUIRES(module:pint)
        >>> # xdoctest: +REQUIRES(module:pytimeparse)
        >>> import xdev
        >>> self = xdev.timedelta.random()
        >>> print(f'self={self}')
    """

    @classmethod
    def random(cls, rng=None):
        """
        Create a random time delta

        Returns:
            Self
        """
        from xdev.util_random import ensure_rng
        rng = ensure_rng(rng)
        max_range = int(timedelta.max.total_seconds() // 100)
        seconds = rng.randint(-max_range, max_range)
        self = cls.coerce(seconds)
        return self

    @classmethod
    def coerce(cls, data):
        """
        Args:
            data (str | int | float):
                If given as a string, attempt to parse out a time duration.
                Otherwise, interpret pure magnitudes in seconds.

            none_policy (str):
                Can be: 'return-None', 'return-nan', or 'raise'.
                See :func:`_handle_null_policy` for details.

            nan_policy (str):
                Can be: 'return-None', 'return-nan', or 'raise'.
                See :func:`_handle_null_policy` for details.

        Returns:
            Self | float | None

        Example:
            >>> # xdoctest: +REQUIRES(module:pint)
            >>> # xdoctest: +REQUIRES(module:pytimeparse)
            >>> from xdev.util_time import *  # NOQA
            >>> data = '3.141592653589793 years'
            >>> cls = timedelta
            >>> self = cls.coerce(data)
            >>> print('self = {}'.format(ub.urepr(self, nl=1)))
        """
        delta = coerce_timedelta(data)
        self = cls(seconds=delta.total_seconds())
        return self

    def to_pint(self):
        """
        Convert the time delta to a pint-based representation of duration

        Returns:
            pint.util.Quantity

        Example:
            >>> # xdoctest: +REQUIRES(module:pint)
            >>> # xdoctest: +REQUIRES(module:pytimeparse)
            >>> import xdev
            >>> self = xdev.timedelta.random()
            >>> quantity = self.to_pint()
        """
        ureg = _time_unit_registery()
        quantity = self.total_seconds() * ureg.seconds
        return quantity

    def to_pandas(self):
        """
        Returns:
            pd.Timedelta
        """
        import pandas as pd
        return pd.Timedelta(self)

    def isoformat(self):
        """
        ISO 8601 time deltas.

        Format is ``P[n]Y[n]M[n]DT[n]H[n]M[n]S``

        Returns:
            str

        References:
            https://en.wikipedia.org/wiki/ISO_8601#Durations.
        """
        return self.to_pandas().isoformat()


def isoformat(dt, sep='T', timespec='seconds', pathsafe=True):
    """
    A path-safe version of datetime_cls.isotime() that returns a
    path-friendlier version of a ISO 8601 timestamp.

    Args:
        dt (datetime_cls): datetime to format

        pathsafe (bool):
            if True, uses only path safe characters, otherwise
            adds extra delimeters for better readability

    References:
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes

    SeeAlso:
        :func:`ubelt.timestamp`

    Example:
        >>> # xdoctest: +REQUIRES(module:pint)
        >>> from xdev.util_time import *  # NOQA
        >>> items = []
        >>> dt = datetime_cls.now()
        >>> dt = ensure_timezone(dt, datetime_mod.timezone(datetime_mod.timedelta(hours=+5)))
        >>> items.append(dt)
        >>> dt = datetime_cls.utcnow()
        >>> items.append(dt)
        >>> dt = dt.replace(tzinfo=datetime_mod.timezone.utc)
        >>> items.append(dt)
        >>> dt = ensure_timezone(datetime_cls.now(), datetime_mod.timezone(datetime_mod.timedelta(hours=-5)))
        >>> items.append(dt)
        >>> dt = ensure_timezone(datetime_cls.now(), datetime_mod.timezone(datetime_mod.timedelta(hours=+5)))
        >>> items.append(dt)
        >>> print('items = {!r}'.format(items))
        >>> for dt in items:
        >>>     print('----')
        >>>     print('dt = {!r}'.format(dt))
        >>>     # ISO format is cool, but it doesnt give much control
        >>>     print(dt.isoformat())
        >>>     # Need a better version
        >>>     print(isoformat(dt))
        >>>     print(isoformat(dt, pathsafe=False))
    """
    if not pathsafe:
        return dt.isoformat(sep=sep, timespec=timespec)

    date_fmt = '%Y%m%d'
    if timespec == 'seconds':
        time_tmf = '%H%M%S'
    else:
        raise NotImplementedError(timespec)

    text = dt.strftime(''.join([date_fmt, sep, time_tmf]))
    if dt.tzinfo is not None:
        off = dt.utcoffset()
        off_seconds = off.total_seconds()
        if off_seconds == 0:
            # TODO: use codes for offsets to remove the plus sign if possible
            suffix = 'Z'
        elif off_seconds % 3600 == 0:
            tz_hour = int(off_seconds // 3600)
            suffix = '{:02d}'.format(tz_hour) if tz_hour < 0 else '+{:02d}'.format(tz_hour)
        else:
            suffix = _format_offset(off)
        text += suffix
    return text


def _format_offset(off):
    """
    Taken from CPython:
        https://github.com/python/cpython/blob/main/Lib/datetime_mod.py
    """
    s = ''
    if off is not None:
        if off.days < 0:
            sign = "-"
            off = -off
        else:
            sign = "+"
        hh, mm = divmod(off, datetime_mod.timedelta(hours=1))
        mm, ss = divmod(mm, datetime_mod.timedelta(minutes=1))
        s += "%s%02d:%02d" % (sign, hh, mm)
        if ss or ss.microseconds:
            s += ":%02d" % ss.seconds

            if ss.microseconds:
                s += '.%06d' % ss.microseconds
    return s


def coerce_datetime(data, default_timezone='utc', nan_policy='return-None',
                    none_policy='return-None'):
    """
    Parses a timestamp and always returns a timestamp with a timezone.
    If only a date is specified, the time is defaulted to 00:00:00
    If one is not discoverable a specified default is used.
    A nan or None input depends on nan_policy and none_policy.

    Args:
        data (None | str | datetime_mod.datetime | datetime_mod.date)

        default_timezone (str): defaults to utc.

        none_policy (str):
            Can be: 'return-None', 'return-nan', or 'raise'.
            See :func:`_handle_null_policy` for details.

        nan_policy (str):
            Can be: 'return-None', 'return-nan', or 'raise'.
            See :func:`_handle_null_policy` for details.

    Returns:
        datetime_mod.datetime | None

    Example:
        >>> # xdoctest: +REQUIRES(module:pint)
        >>> # xdoctest: +REQUIRES(module:dateutil)
        >>> from xdev.util_time import *  # NOQA
        >>> assert coerce_datetime(None) is None
        >>> assert coerce_datetime(float('nan')) is None
        >>> assert coerce_datetime('2020-01-01') == datetime_cls(2020, 1, 1, 0, 0, tzinfo=datetime_mod.timezone.utc)
        >>> assert coerce_datetime(datetime_cls(2020, 1, 1, 0, 0)) == datetime_cls(2020, 1, 1, 0, 0, tzinfo=datetime_mod.timezone.utc)
        >>> assert coerce_datetime(datetime_cls(2020, 1, 1, 0, 0).date()) == datetime_cls(2020, 1, 1, 0, 0, tzinfo=datetime_mod.timezone.utc)
        >>> dt = coerce_datetime('2020-01-01')
        >>> stamp = dt.timestamp()
        >>> assert stamp == 1577836800.0
        >>> assert coerce_datetime(stamp) == dt
        >>> assert dt.isoformat() == '2020-01-01T00:00:00+00:00'
    """
    from dateutil import parser as date_parser
    if data is None:
        return _handle_null_policy(
            none_policy, TimeTypeError,
            'cannot coerce None to a datetime')
    elif isinstance(data, str):
        # Canse use ubelt.timeparse(data, default_timezone=default_timezone) here.
        if data == 'now':
            dt = datetime_cls.utcnow()
        else:
            dt = date_parser.parse(data)
    elif isinstance(data, datetime_cls):
        dt = data
    elif isinstance(data, datetime_mod.date):
        dt = date_parser.parse(data.isoformat())
    elif isinstance(data, numbers.Number):
        if math.isnan(data):
            return _handle_null_policy(
                nan_policy, TimeTypeError,
                'cannot coerce nan to a datetime')

        tz = coerce_timezone(default_timezone)
        dt = datetime_cls.fromtimestamp(data, tz=tz)
        # OLD INCORRECT IMPLEMENTATION:
        # dt = datetime_cls.fromtimestamp(data)
    else:
        raise TimeTypeError('unhandled {}'.format(data))
    dt = ensure_timezone(dt, default=default_timezone)
    return dt


def _handle_null_policy(policy, ex_type=TypeError,
                        ex_msg='cannot accept null input'):
    """
    For handling a nan or None policy.

    Args:
        policy (str):
            How null inputs are handled. Can be:
                'return-None': returns None
                'return-nan': returns nan
                'raise': raises an error

        ex_type (type): Exception type to raise if policy is raise

        ex_msg (msg): Exception arguments
    """
    if policy == 'return-None':
        return None
    elif policy == 'return-nan':
        return float('nan')
    elif policy == 'raise':
        raise ex_type(ex_msg)
    else:
        raise KeyError(policy)


def coerce_timedelta(delta, nan_policy='raise', none_policy='raise'):
    """
    Parses data that could be associated with a time delta

    Args:
        delta (str | int | float):
            If given as a string, attempt to parse out a time duration.
            Otherwise, interpret pure magnitudes in seconds.

        none_policy (str):
            Can be: 'return-None', 'return-nan', or 'raise'.
            See :func:`_handle_null_policy` for details.

        nan_policy (str):
            Can be: 'return-None', 'return-nan', or 'raise'.
            See :func:`_handle_null_policy` for details.

    Returns:
        datetime_mod.timedelta | None

    Example:
        >>> # xdoctest: +REQUIRES(module:pint)
        >>> # xdoctest: +REQUIRES(module:pytimeparse)
        >>> from xdev.util_time import *  # NOQA
        >>> variants = [
        >>>     ['year', 'y'],
        >>>     ['month', 'm', 'mon'],
        >>>     ['day', 'd', 'days'],
        >>>     ['hours', 'hour', 'h'],
        >>>     ['minutes', 'min', 'M'],
        >>>     ['second', 'S', 's', 'secs'],
        >>> ]
        >>> for vs in variants:
        >>>     print('vs = {!r}'.format(vs))
        >>>     ds = []
        >>>     for v in vs:
        >>>         d = coerce_timedelta(f'1{v}')
        >>>         ds.append(d)
        >>>         d = coerce_timedelta(f'1 {v}')
        >>>         ds.append(d)
        >>>     assert ub.allsame(ds)
        >>>     print('ds = {!r}'.format(ds))
        >>> print(coerce_timedelta(10.3))
        >>> print(coerce_timedelta('1y'))
        >>> print(coerce_timedelta('1m'))
        >>> print(coerce_timedelta('1d'))
        >>> print(coerce_timedelta('1H'))
        >>> print(coerce_timedelta('1M'))
        >>> print(coerce_timedelta('1S'))
        >>> print(coerce_timedelta('1year'))
        >>> print(coerce_timedelta('1month'))
        >>> print(coerce_timedelta('1day'))
        >>> print(coerce_timedelta('1hour'))
        >>> print(coerce_timedelta('1min'))
        >>> print(coerce_timedelta('1sec'))
        >>> print(coerce_timedelta('1microsecond'))
        >>> print(coerce_timedelta('1milliseconds'))
        >>> print(coerce_timedelta('1ms'))
        >>> print(coerce_timedelta('1us'))

    Example:
        >>> # xdoctest: +REQUIRES(module:pint)
        >>> # xdoctest: +REQUIRES(module:numpy)
        >>> # xdoctest: +REQUIRES(module:pytimeparse)
        >>> from xdev.util_time import *  # NOQA
        >>> import numpy as np
        >>> print(coerce_timedelta(int(30)))
        >>> print(coerce_timedelta(float(30)))
        >>> print(coerce_timedelta(np.int32(30)))
        >>> print(coerce_timedelta(np.int64(30)))
        >>> print(coerce_timedelta(np.float32(30)))
        >>> print(coerce_timedelta(np.float64(30)))

    References:
        https://docs.python.org/3.4/library/datetime_mod.html#strftime-strptime-behavior
    """
    if isinstance(delta, str):
        try:
            delta = float(delta)
        except ValueError:
            ...

    if isinstance(delta, datetime_mod.timedelta):
        ...
    elif isinstance(delta, numbers.Number):
        try:
            delta = datetime_mod.timedelta(seconds=delta)
        except TypeError:
            import sys
            np = sys.modules.get('numpy', None)
            if np is None:
                raise
            else:
                if isinstance(delta, np.integer):
                    delta = datetime_mod.timedelta(seconds=int(delta))
                elif isinstance(delta, np.floating):
                    delta = datetime_mod.timedelta(seconds=float(delta))
                else:
                    raise
        except ValueError:
            if isinstance(delta, float) and math.isnan(delta):
                return _handle_null_policy(
                    nan_policy, TimeTypeError,
                    'cannot coerce nan to a timedelta')
            raise
    elif isinstance(delta, str):
        # TODO: handle isoformat
        try:
            ureg = _time_unit_registery()
            seconds = ureg.parse_expression(delta).to('seconds').m
            # timedelta apparently does not have resolution higher than
            # microseconds.
            # https://stackoverflow.com/questions/10611328/strings-ns
            # https://bugs.python.org/issue15443
            delta = datetime_mod.timedelta(seconds=seconds)
        except Exception:
            # Separate the expression into a magnitude and a unit
            import re
            expr_pat = re.compile(
                r'^(?P<magnitude>[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)'
                '(?P<spaces> *)'
                '(?P<unit>.*)$')
            match = expr_pat.match(delta.strip())
            if match:
                parsed = match.groupdict()
                unit = parsed.get('unit', '')
                magnitude = parsed.get('magnitude', '')
            else:
                unit = None
                magnitude = None

            if unit in {'y', 'year', 'years'}:
                delta = datetime_mod.timedelta(days=365 * float(magnitude))
            elif unit in {'d', 'day', 'days'}:
                delta = datetime_mod.timedelta(days=1 * float(magnitude))
            elif unit in {'w', 'week', 'weeks'}:
                delta = datetime_mod.timedelta(days=7 * float(magnitude))
            elif unit == {'m', 'month', 'months'}:
                delta = datetime_mod.timedelta(days=30.437 * float(magnitude))
            elif unit == {'H', 'hour', 'hours'}:
                delta = datetime_mod.timedelta(hours=float(magnitude))
            elif unit == {'M', 'min', 'mins', 'minute', 'minutes'}:
                delta = datetime_mod.timedelta(minutes=float(magnitude))
            elif unit == {'S', 'sec', 'secs', 'second', 'seconds'}:
                delta = datetime_mod.timedelta(seconds=float(magnitude))
            else:
                import pytimeparse  #
                import warnings
                warnings.warn('warning: pytimeparse fallback')
                seconds = pytimeparse.parse(delta)
                if seconds is None:
                    raise Exception(delta)
                delta = datetime_mod.timedelta(seconds=seconds)
                return delta
    else:
        if delta is None:
            return _handle_null_policy(
                none_policy, TimeTypeError,
                'cannot coerce None to a timedelta')
        raise TimeTypeError(f'cannot coerce {type(delta)} to a timedelta')
    return delta


def coerce_timezone(tz):
    """
    Converts input to a valid timezone object
    Args:
        tz (str | tzinfo):

    Returns:
        tzinfo: timezone object
    """
    if isinstance(tz, datetime_mod.timezone):
        tzinfo = tz
    else:
        if tz == 'utc':
            tzinfo = datetime_mod.timezone.utc
        elif tz == 'local':
            tzinfo = datetime_mod.timezone(datetime_mod.timedelta(seconds=-time.timezone))
        else:
            raise NotImplementedError
    return tzinfo


def ensure_timezone(dt, default='utc'):
    """
    Gives a datetime_mod a timezone (utc by default) if it doesnt have one

    Arguments:
        dt (datetime_mod.datetime): the datetime to fix
        default (str): the timezone to use if it does not have one.

    Returns:
        datetime_mod.datetime

    Example:
        >>> # xdoctest: +REQUIRES(module:pint)
        >>> from xdev.util_time import *  # NOQA
        >>> dt = ensure_timezone(datetime_cls.now(), datetime_mod.timezone(datetime_mod.timedelta(hours=+5)))
        >>> print('dt = {!r}'.format(dt))
        >>> dt = ensure_timezone(datetime_cls.utcnow())
        >>> print('dt = {!r}'.format(dt))
        >>> ensure_timezone(datetime_cls.utcnow(), 'utc')
        >>> ensure_timezone(datetime_cls.utcnow(), 'local')
    """
    if dt.tzinfo is not None:
        return dt
    else:
        tzinfo = coerce_timezone(default)
        return dt.replace(tzinfo=tzinfo)


@ub.memoize
def _time_unit_registery():
    import pint
    # Empty registry
    ureg = pint.UnitRegistry(None)
    ureg.define('second = []')
    ureg.define('minute = 60 * second')
    ureg.define('hour = 60 * minute')

    ureg.define('day = 24 * hour')
    ureg.define('week = 7 * day')
    ureg.define('month = 30.437 * day')
    ureg.define('year = 365 * day')

    ureg.define('min = minute')
    ureg.define('mon = month')
    ureg.define('sec = second')

    ureg.define('S = second')
    ureg.define('M = minute')
    ureg.define('H = hour')

    ureg.define('d = day')
    ureg.define('m = month')
    ureg.define('y = year')

    ureg.define('s = second')

    ureg.define('millisecond = second / 1000')
    ureg.define('microsecond = second / 1000000')

    ureg.define('ms = millisecond')
    ureg.define('us = microsecond')

    @ ub.urepr.extensions.register(pint.Unit)
    def format_unit(data, **kwargs):
        numer = [k for k, v in data._units.items() if v > 0]
        denom = [k for k, v in data._units.items() if v < 0]
        numer_str = ' '.join(numer)
        if len(denom) == 0:
            return numer_str
        elif len(denom) > 1:
            denom_str = '({})'.format(' '.join(denom))
        elif len(denom) == 1:
            denom_str = ' '.join(denom)
        else:
            raise AssertionError
        if len(numer) == 0:
            return '/ ' + denom_str
        else:
            return numer_str + ' / ' + denom_str

    @ub.urepr.extensions.register(pint.Quantity)
    def format_quantity(data, _return_info=None, **kwargs):
        return ub.repr2(data.magnitude, **kwargs) + ' ' + ub.repr2(data.u)

    return ureg

_time_unit_registery()


def format_timedelta(delta, resolution=None, unit=None, precision=None):
    """
    TODO format time deltas at some resolution granularity

    Args:
        delta (datetime_mod.timedelta): The timedelta to format

        unit (str | None | pint.Unit):
            if specified, express the time delta in terms of this unit.

        precision (int):
            number of decimal places when a single unit is given

        resolution (datetime_mod.timedelta | str | None):
            minimum temporal resolution. If unspecified returns
            an isoformat

    Returns:
        str: formatted text

    References:
        https://gist.github.com/thatalextaylor/7408395
        https://en.wikipedia.org/wiki/ISO_8601#Durations

    CommandLine:
        xdoctest -m xdev.util_time format_timedelta

    Example:
        >>> # xdoctest: +REQUIRES(module:pint)
        >>> from xdev.util_time import *  # NOQA
        >>> resolution = coerce_timedelta('year')
        >>> resolution = 'year'
        >>> delta = coerce_timedelta('13months')
        >>> print(format_timedelta(delta))
        >>> print(format_timedelta(delta, unit='year', precision=2))

        >>> print(format_timedelta('.000003 days', unit='auto', precision=0))
        >>> print(format_timedelta('.03 days', unit='auto', precision=0))
        >>> print(format_timedelta('39 days', unit='auto', precision=0))
        >>> print(format_timedelta('3900 days', unit='auto', precision=0))

    """
    if resolution is None and unit is None:
        return str(delta)
    else:
        ureg = _time_unit_registery()
        delta = coerce_timedelta(delta)
        delta_sec = delta.total_seconds()

        if unit == 'auto':
            # Figure out the "best" unit to express the delta in
            seconds = int(delta_sec)
            years, seconds = divmod(seconds, 31536000)
            week, seconds = divmod(seconds, 604800)
            days, seconds = divmod(seconds, 86400)
            hours, seconds = divmod(seconds, 3600)
            minutes, seconds = divmod(seconds, 60)
            if years > 0:
                unit = 'year'
            elif week > 0:
                unit = 'week'
            elif days > 0:
                unit = 'day'
            elif hours > 0:
                unit = 'hour'
            elif minutes > 0:
                unit = 'min'
            else:
                unit = 'sec'
                # TOOD: ms, us, ns

        if isinstance(unit, str):
            unit = ureg.parse_units(unit)
        elif isinstance(unit, ureg.Unit):
            ...
        else:
            raise TypeError(type(unit))

        if unit is not None:
            pint_sec = delta_sec * ureg.sec
            new_unit = pint_sec.to(unit)
            text = ub.repr2(new_unit, precision=precision)
            return text

        raise NotImplementedError

        # resolution = coerce_timedelta(resolution)
        # res_seconds = resolution.total_seconds()
        # del_seconds = delta.total_seconds()
        # n, r = divmod(del_seconds, res_seconds)
        # floor = n * res_seconds
        # floor_delta = coerce_timedelta(floor)

        # # TODO: unit, precision?
        # delta / resolution
        # # s = 13420
        # # hours, remainder = divmod(s, 3600)
        # # minutes, seconds = divmod(remainder, 60)
        # # print('{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)))
        # # # result: 03:43:40
        # # ...


def _devcheck_portion():
    """
    Portion seems like a good library to build a TimeInterval class with.
    Could also check PyInterval
    """
    import xdev
    import portion
    delta = abs(xdev.util_time.timedelta.coerce('1 year'))
    start = xdev.util_time.datetime.coerce('2020-01-01')
    interval1 = portion.Interval.from_atomic(portion.CLOSED, start, start + delta, portion.CLOSED)
    interval2 = portion.Interval.from_atomic(portion.CLOSED, start + delta * 0.5, start + delta * 1.5, portion.CLOSED)
    interval3 = portion.Interval.from_atomic(portion.CLOSED, start + delta * 3, start + delta * 4, portion.CLOSED)

    interval1 & interval2
    interval1 & interval3
    interval1 | interval3
    interval1 | interval2
    print(f'interval1={interval1}')
    print(f'interval2={interval2}')
    print(f'interval3={interval3}')
    # See Also:
    # https://pyinterval.readthedocs.io/en/latest/api.html#interval-interval-arithmetic
