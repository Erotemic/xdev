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


def distext(func):
    """
    Like dis.dis, but returns the text
    """
    import dis
    import io
    file = io.StringIO()
    dis.dis(func, file=file)
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
