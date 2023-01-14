import xinspect

get_func_kwargs = xinspect.get_func_kwargs


def get_stack_frame(N=0, strict=True):
    """
    Args:
        N (int): N=0 means the frame you called this function in.
                 N=1 is the parent frame.
        strict (bool): (default = True)
    """
    import inspect
    frame_cur = inspect.currentframe()
    for idx in range(N + 1):
        # always skip the frame of this function
        frame_next = frame_cur.f_back
        if frame_next is None:
            if strict:
                raise AssertionError('Frame level {:!r} is root'.format(idx))
            else:
                break
        frame_cur = frame_next
    return frame_cur


def distext(obj):
    """
    Like dis.dis, but returns the text

    Args:
        obj : a compiled object (e.g. a function, class, generator, etc...)

    Returns:
        str: text of the python byte code

    Example:
        >>> from xdev.introspect import *  # NOQA
        >>> import ubelt as ub
        >>> code = ub.codeblock(
            '''
            def foo(a, b):
                print('hello')
                if __debug__:
                    if a is None or b is None:
                        raise ValueError
                print('world')
                # This is not entirely optimized away
                if __debug__ and (a is None or b is None):
                    raise ValueError
                return a + b
            ''')
        >>> obj = compile(code, filename='<memory>', mode='exec', dont_inherit=True, optimize=0)
        >>> print(' ** UNOPTIMIZED')
        >>> text = distext(obj)
        >>> print(text)
        >>> print(' ** OPTIMIZED')
        >>> obj = compile(code, filename='<memory>', mode='exec', dont_inherit=True, optimize=1)
        >>> text = distext(obj)
        >>> print(text)
    """
    import dis
    import io
    file = io.StringIO()
    dis.dis(obj, file=file)
    file.seek(0)
    text = file.read()
    return text


# def import_star(module):
#     """
#     This is the unholy grail

#     Import all contents of the module into the global scope

#     Args:
#         module (str | module): a path, module name, or module itself

#     Example:
#         >>> # xdoctest: +DISABLE_DOCTEST
#         >>> from xdev.misc import import_star
#         >>> module = 'ubelt'
#         >>> print(import_star(module).keys())
#     """
#     import ubelt as ub
#     if isinstance(module, str):
#         if exists(module):
#             module = ub.import_module_from_path(module)
#         else:
#             module = ub.import_module_from_name(module)

#     mod_attrs = {
#         key: val for key, val in module.__dict__.items()
#         if not key.startswith('_')
#     }
#     parent_frame = get_stack_frame(N=2)
#     print('parent_frame.f_code.co_names = {!r}'.format(parent_frame.f_code.co_names))
#     print('parent_frame.f_code.co_name = {!r}'.format(parent_frame.f_code.co_name))
#     # Note: locals is usually read only
#     # parent_frame.f_locals.update(mod_attrs)
#     parent_frame.f_globals.update(mod_attrs)
#     return mod_attrs


def iter_object_tree(obj):
    # ub.IndexableWalker
    data = obj.__dict__
    prefix = []

    list_cls = (list, tuple)
    dict_cls = (dict,)
    indexable_cls = dict_cls + list_cls

    seen_ = set()
    stack = [(data, prefix)]
    while stack:
        _data, _prefix = stack.pop()
        # Create an items iterable of depending on the indexable data type
        if hasattr(_data, '__dict__'):
            items = _data.__dict__.items()
        elif isinstance(_data, list_cls):
            items = enumerate(_data)
        elif isinstance(_data, dict_cls):
            items = _data.items()
        else:
            raise TypeError(type(_data))

        for key, value in items:
            # Yield the full path to this position and its value
            path = _prefix + [key]

            message = yield path, value
            # If the value at this path is also indexable, then continue
            # the traversal, unless the False message was explicitly sent
            # by the caller.
            if message is False:
                # Because the `send` method will return the next value,
                # we yield a dummy value so we don't clobber the next
                # item in the traversal.
                yield None
            else:
                if isinstance(value, indexable_cls) or hasattr(value, '__dict__'):
                    objid = id(value)
                    if objid not in seen_:
                        seen_.add(objid)
                        stack.append((value, path))


def test_object_pickleability(obj):
    # ub.IndexableWalker

    import pickle
    serialized = pickle.dumps(obj)
    recon = pickle.loads(serialized)  # NOQA

    data = obj.__dict__
    prefix = []

    list_cls = (list, tuple)
    dict_cls = (dict,)
    indexable_cls = dict_cls + list_cls

    def condition(path, value):
        import pickle
        dumped = pickle.dumps(value)
        try:
            recon = pickle.loads(dumped)  # NOQA
        except Exception:
            return True
        else:
            return False
        ignore_types = (float, int, bool, type(None))
        return not isinstance(value, ignore_types)

    walker = iter_object_tree(obj)
    for path, value in walker:
        flag = condition(path, value)
        if flag:
            print('BAD FLAG path = {!r}'.format(path))
            walker.send(False)

    found = []

    keyfn = type

    seen_ = set()

    stack = [(data, prefix)]
    while stack:
        _data, _prefix = stack.pop()
        # Create an items iterable of depending on the indexable data type
        if isinstance(_data, list_cls):
            items = enumerate(_data)
        elif isinstance(_data, dict_cls):
            items = _data.items()
        elif hasattr(_data, '__dict__'):
            items = _data.__dict__.items()
        else:
            raise TypeError(type(_data))

        for key, value in items:
            # Yield the full path to this position and its value
            path = _prefix + [key]
            flag = condition(path, value)
            if flag:
                store = keyfn(value)
                found.append((path, store))

                if isinstance(value, indexable_cls) or hasattr(value, '__dict__'):
                    objid = id(value)
                    if objid not in seen_:
                        seen_.add(objid)
                        stack.append((value, path))
