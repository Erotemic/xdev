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


# if False:
#     import sys
#     import os

#     if hasattr(sys, "_getframe"):
#         def currentframe():
#             return sys._getframe(1)
#     else:  # pragma: no cover
#         def currentframe():
#             """Return the frame object for the caller's stack frame."""
#             try:
#                 raise Exception
#             except Exception:
#                 return sys.exc_info()[2].tb_frame.f_back
#     #
#     # _srcfile is used when walking the stack to check when we've got the first
#     # caller stack frame, by skipping frames whose filename is that of this
#     # module's source. It therefore should contain the filename of this module's
#     # source file.
#     #
#     # Ordinarily we would use __file__ for this, but frozen modules don't always
#     # have __file__ set, for some reason (see Issue #21736). Thus, we get the
#     # filename from a handy code object from a function defined in this module.
#     # (There's no particular reason for picking addLevelName.)
#     #

#     _srcfile = os.path.normcase(currentframe.__code__.co_filename)

#     # _srcfile is only used in conjunction with sys._getframe().
#     # Setting _srcfile to None will prevent findCaller() from being called. This
#     # way, you can avoid the overhead of fetching caller information.

#     # The following is based on warnings._is_internal_frame. It makes sure that
#     # frames of the import mechanism are skipped when logging at module level and
#     # using a stacklevel value greater than one.
#     def _is_internal_frame(frame):
#         """Signal whether the frame is a CPython or logging module internal."""
#         filename = os.path.normcase(frame.f_code.co_filename)
#         return filename == _srcfile or (
#             "importlib" in filename and "_bootstrap" in filename
#         )

#     def get_stack_frame2(stacklevel=1):
#         """
#         Based on findCaller code in stdlib logging
#         """
#         f = currentframe()
#         #On some versions of IronPython, currentframe() returns None if
#         #IronPython isn't run with -X:Frames.
#         if f is None:
#             return "(unknown file)", 0, "(unknown function)", None
#         while stacklevel > 0:
#             next_f = f.f_back
#             if next_f is None:
#                 ## We've got options here.
#                 ## If we want to use the last (deepest) frame:
#                 break
#                 ## If we want to mimic the warnings module:
#                 #return ("sys", 1, "(unknown function)", None)
#                 ## If we want to be pedantic:
#                 #raise ValueError("call stack is not deep enough")
#             f = next_f
#             if not _is_internal_frame(f):
#                 stacklevel -= 1
#         return f


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


def gen_docstr_from_context(keys, lut):
    """
    Ignore:
        keys = 'true_dets, pred_dets, iou_lookup, isvalid_lookup, cx_to_matchable_txs, bg_weight, prioritize, iou_thresh_, pdist_priority, cx_to_ancestors, bg_cidx, ignore_classes, max_dets, multiple_assignment'.split(', ')
        lut = globals()
    """
    for key in keys:
        value = lut[key]
        typestr = generate_typeannot(value)
        print(f'{key} ({typestr}): ')


def generate_typeannot(value):
    import ubelt as ub
    if isinstance(value, (set, list)):
        unique_val_types = ub.group_items(value, key=type)
        T1 = type(value).__name__
        VT = '|'.join([generate_typeannot(vs[0]) for t, vs in unique_val_types.items()])
        typestr = f'{T1}[{VT}]'
    elif isinstance(value, dict):
        unique_key_types = ub.group_items(value.keys(), key=type)
        unique_val_types = ub.group_items(value.values(), key=type)
        # Oversimplification
        kt = '|'.join([generate_typeannot(vs[0]) for t, vs  in unique_key_types.items()])
        vt = '|'.join([generate_typeannot(vs[0]) for t, vs in unique_val_types.items()])
        typestr = f'Dict[{kt}, {vt}]'
    else:
        typestr = type(value).__name__
    return typestr
