r"""
Minor quality of life improvements over IPython.embed

For a full featured debugger see [PypiIPDB]_, although note that this still
suffers from issues like [IpythonIssue62]_, which this code contains
workarounds for.

The latest workaround is the "xdev.snapshot" function (new in 1.5.0).

Either when calling ``xdev.embed()`` or at any point in your code you can call
the `xdev.snapshot()` function.
This allows you to pickle your interpreter state to disk, and startup a new
IPython shell (where [IpythonIssue62]_ doesnt apply) and essentially simulates
the embedded stack frame.


export PYTHONBREAKPOINT=xdev.embed

python -c "if 1:

    def foo(arg1):
        a = 2
        b = 3 + arg1
        breakpoint()

    foo(432)
"



.. code:: bash

    echo "if 1:

        def foo(arg1):
            a = 2
            b = 3 + arg1
            import xdev
            xdev.embed()

    " > mymod.py

    # This new features does not handle __main__ modules yet, so we use this
    # workaround to demo the feature.
    python -c "import mymod; mymod.foo(23)"

This will embed you in an IPython session with the prompt:


.. code::

    ================
    ____ _  _ ___  ____ ___  ___  _ _  _ ____
    |___ |\/| |__] |___ |  \ |  \ | |\ | | __
    |___ |  | |__] |___ |__/ |__/ | | \| |__]


    ================
    [xdev.embed] embedding
    [xdev.embed] use xdev.fix_embed_globals() to address https://github.com/ipython/ipython/issues/62
    [xdev.embed] to debug in a fresh IPython context, run:

    xdev.snapshot()

                 and then follow instructions
    [xdev.embed] set EXIT_NOW or qqq=1 to hard exit on unembed
    [util] calling IPython.embed()
    In [1]:


And calling ``xdev.snapshot()`` will result in:


.. code:: python

    In [1]: xdev.snapshot()
       ...:
    not_pickleable = [
        '__builtins__',
    ]
    Could not pickle 1 variables
    # To debug in a fresh IPython session run:

    ipython -i -c "if 1:
        fpath = '/home/joncrall/.cache/xdev/states/state_2023-10-23T120433-5.pkl'
        from xdev.embeding import load_snapshot
        load_snapshot(fpath, globals())
    "


Now, executing that code in a new terminal will startup a fresh IPython session
(where issue 62 no longer applies because IPython was the entry point), and it
loads your entired state into memory as long as it is pickleable. This is very
handy for interactive development, but like all workaround it does still have
limitations - namely everything needs to be pickleable. However, it has several
advantages:

    * Quickly restart from the breakpoint state because it is saved in a pickle file.

    * Have more than one independent interpreter session looking at the same state.


References:
    .. [PypiIPDB] https://pypi.org/project/ipdb/
    .. [IpythonIssue62] https://github.com/ipython/ipython/issues/62
"""
import sys
from functools import partial
from xdoctest.dynamic_analysis import get_parent_frame, get_stack_frame
from xdev import util
import time


def _stop_rich_live_contexts():
    # Stop any rich live context.
    if 'rich' in sys.modules:
        import rich
        console = rich.get_console()
        if console._live is not None:
            console._live.__exit__(None, None, None)


def embed(parent_locals=None, parent_globals=None, exec_lines=None,
          remove_pyqt_hook=True, n=0, debug=False):
    """
    Starts interactive session. Similar to keyboard command in matlab.
    Wrapper around IPython.embed.

    Note:
        Contains helper logic to allow the developer to more easilly exit the
        program if embed is called in a loop. Specifically if you want to quit
        and not embed again, then set qqq=1 before exiting the embed session.

    SeeAlso:
        :func:`embed_on_exception`
    """
    if 1:
        _stop_rich_live_contexts()
    import os

    parent_frame = None

    if parent_globals is None:
        if parent_frame is None:
            parent_frame = get_parent_frame(n=n)
        parent_globals = parent_frame.f_globals
    if parent_locals is None:
        if parent_frame is None:
            parent_frame = get_parent_frame(n=n)
        parent_locals = parent_frame.f_locals

    if debug:
        import ubelt as ub
        print(f'parent_globals.keys = {ub.urepr(parent_globals.keys(), nl=1)}')
        print(f'parent_locals.keys = {ub.urepr(parent_locals.keys(), nl=1)}')
        print(f'parent_frame = {ub.urepr(parent_frame, nl=1)}')

    stackdepth = n  # NOQA
    getframe = partial(get_parent_frame, n=n)  # NOQA

    # exec(execstr_dict(parent_globals, 'parent_globals'))
    # exec(execstr_dict(parent_locals,  'parent_locals'))
    print('')
    print('================')
    print(util.bubbletext('EMBEDDING'))
    print('================')
    print('[xdev.embed] embedding')

    if os.environ.get('XDEV_USE_GUITOOL', ''):
        # I don't think this is needed anymore
        try:
            if remove_pyqt_hook:
                try:
                    import guitool
                    guitool.remove_pyqt_input_hook()
                except (ImportError, ValueError, AttributeError) as ex:
                    print('ex = {!r}'.format(ex))
                    pass
                # make qt not loop forever (I had qflag loop forever with this off)
        except ImportError as ex:
            print(ex)

    if 1:
        # Disable common annoyance loggers
        import logging
        logging.getLogger('parso').setLevel(logging.INFO)

    from xdev._ipython_ext import embed2
    # import IPython
    import xdev  # NOQA
    import xdev as xd  # NOQA

    #from IPython.config.loader import Config
    # cfg = Config()
    #config_dict = {}
    #if exec_lines is not None:
    #    config_dict['exec_lines'] = exec_lines
    #IPython.embed(**config_dict)
    # print('[xdev.embed]  Get stack location with: ')
    # print('[xdev.embed] get_parent_frame(n=8).f_code.co_name')
    print('[xdev.embed] use xdev.fix_embed_globals() to address https://github.com/ipython/ipython/issues/62')
    print('[xdev.embed] to debug in a fresh IPython context, run:')
    print('')
    print('xdev.snapshot()')
    print('')
    print('             and then follow instructions')
    print('[xdev.embed] set EXIT_NOW or qqq=1 to hard exit on unembed')
    #print('set iup to True to draw plottool stuff')
    # print('[util] call %pylab qt4 to get plottool stuff working')
    once = True
    # Allow user to set iup and redo the loop
    while once or vars().get('iup', False):
        if not once:
            # SUPER HACKY WAY OF GETTING FIGURES ON THE SCREEN BETWEEN UPDATES
            #vars()['iup'] = False
            # ALL YOU NEED TO DO IS %pylab qt4
            print('re-emebeding')
            #import plottool as pt
            #pt.update()
            #(pt.present())
            for _ in range(100):
                time.sleep(.01)

        once = False
        #vars().get('iup', False):
        print('[util] calling IPython.embed()')
        """
        Notes:
            /usr/local/lib/python2.7/dist-packages/IPython/terminal/embed.py
            IPython.terminal.embed.InteractiveShellEmbed

            # instance comes from  IPython.config.configurable.SingletonConfigurable.instance
        """
        #c = IPython.Config()
        #c.InteractiveShellApp.exec_lines = [
        #    '%pylab qt4',
        #    '%gui qt4',
        #    "print 'System Ready!'",
        #]
        #IPython.embed(config=c)
        parent_ns = parent_globals.copy()
        parent_ns.update(parent_locals)
        # locals().update(parent_ns)

        try:
            embed2(user_ns=parent_ns)
        except RuntimeError as ex:
            print('ex = {!r}'.format(ex))
            print('Failed to open ipython')
        #config = IPython.terminal.ipapp.load_default_config()
        #config.InteractiveShellEmbed = config.TerminalInteractiveShell
        #module = sys.modules[parent_globals['__name__']]
        #config['module'] = module
        #config['module'] = module
        #embed2(stack_depth=n + 2 + 1)
        #IPython.embed(config=config)
        #IPython.embed(config=config)
        #IPython.embed(module=module)
        # Exit python immediately if specifed
        if vars().get('EXIT_NOW', False) or vars().get('qqq', False):
            print('[xdev.embed] EXIT_NOW specified')
            sys.exit(1)


def breakpoint():
    return embed(n=1)


def _devcheck_frames():
    # TODO: how do we find the right frame when executing code directly in
    # IPython?
    import ubelt as ub
    for n in range(0, 3):
        frame = get_parent_frame(n=n)
        print(f'n={n}')
        print('frame.f_code.co_filename = {}'.format(ub.urepr(frame.f_code.co_filename, nl=1)))
        print('frame.f_code.co_name = {}'.format(ub.urepr(frame.f_code.co_name, nl=1)))
    ...


def load_snapshot(fpath, parent_globals=None):
    """
    Loads a snapshot of a local state from disk.

    Args:
        fpath (str | PathLike): the path to the snapshot file to load

        parent_globals (dict | None):
            The state dictionary to update. Should be given as ``globals()``.
            If unspecified, it is inferred via frame inspection.
    """
    import pickle
    import ubelt as ub
    if parent_globals is None:
        parent_globals = get_parent_frame(n=1).f_globals
    fpath = ub.Path(fpath)
    snapshot_state = pickle.loads(fpath.read_bytes())

    context = snapshot_state['context']
    if context['__name__'] == '__main__':
        # To work around issue where we embed on the __main__ context we import
        # the module it was associated with (which we can do because
        # make-snapshot_state recorded it) and then load its globals into the parent
        # globals (which I think will usually be a different __main__ context,
        # but I'm not 100% sure about this). Might need to update to handle
        # that case.
        modpath = context['modpath']
        if modpath is not None:
            module = ub.import_module_from_path(modpath)
            parent_globals.update(module.__dict__)

    loaded_variables = dict()
    for k, v in snapshot_state['variables'].items():
        loaded_variables[k] = pickle.loads(v)

    imports = snapshot_state.get('imports')
    for row in imports:
        modname = row['modname']
        if modname is not None:
            module = ub.import_module_from_name(modname)
            loaded_variables[row['alias']] = module

    parent_globals.update(loaded_variables)


def snapshot(parent_ns=None, n=0):
    """
    Save a snapshot of the local state to disk.

    Serialize all names in scope to a pickle and save to disk. Also print the
    command that will let the user start an IPython session with this
    namespace.

    Args:
        parent_ns (dict):
            A dictionary containing all of the available names in the scope to
            export.

        n (int):
            if ``parent_ns`` is unspecified, infer locals and globals from the
            frame ``n`` stack levels above the namespace this function is
            called in.

    TODO:
        - [ ] need to handle __main__

    References:
        .. [SO11866944] https://stackoverflow.com/questions/11866944/how-to-pickle-functions-classes-defined-in-main-python
    """
    import pickle
    import types
    import ubelt as ub
    if parent_ns is None:
        parent_globals = get_parent_frame(n=n).f_globals
        parent_locals = get_parent_frame(n=n).f_locals
        parent_ns = parent_globals.copy()
        parent_ns.update(parent_locals)

    snapshot_state = {}
    variables = snapshot_state['variables'] = {}
    not_pickleable = snapshot_state['not_pickleable'] = []
    imports = snapshot_state['imports'] = []

    for k, v in parent_ns.items():
        if isinstance(v, types.ModuleType):
            imports.append({
                'modname': getattr(v, '__name__', None),
                'modpath': getattr(v, '__file__', None),
                'alias': k,
            })
        else:
            try:
                variables[k] = pickle.dumps(v)
            except Exception:
                not_pickleable.append(k)

    context = {
        '__name__': parent_ns['__name__'],
    }
    if parent_ns['__name__'] == '__main__':
        modpath = parent_ns.get('__file__', None)
        if modpath is None:
            modname = None
        else:
            modname = parent_ns['__file__']
        context['modpath'] = modpath
        context['modname'] = modname

    snapshot_state['context'] = context

    if not_pickleable:
        if len(not_pickleable) < 20:
            print('not_pickleable = {}'.format(ub.urepr(not_pickleable, nl=1)))
        print(f'Could not pickle {len(not_pickleable)} variables')

    dpath = ub.Path.appdir('xdev', 'snapshot_states').ensuredir()
    fpath = dpath / ('state_' + ub.timestamp() + '.pkl')

    snapshot_data = pickle.dumps(snapshot_state)
    fpath.write_bytes(snapshot_data)

    print(ub.highlight_code(ub.codeblock(
        f'''
        # To debug in a fresh IPython session run:

        ipython -i -c "if 1:
            fpath = '{fpath}'
            from xdev.embeding import load_snapshot
            load_snapshot(fpath, globals())
        "
        '''), 'bash'))
    # import pickle
    # import ubelt as ub
    # fpath = ub.Path(fpath)
    # snapshot_state = pickle.loads(fpath.read_bytes())
    # loaded_variables = dict()
    # for k, v in snapshot_state['variables'].items():
    #     loaded_variables[k] = pickle.loads(v)
    # globals().update(loaded_variables)
    ...


def embed_if_requested(n=0):
    """
    Calls xdev.embed conditionally based on the environment.

    Useful in cases where you want to leave the embed call around, but you dont
    want it to trigger in normal circumstances.

    Specifically, embed is only called if the environment variable XDEV_EMBED
    exists or if --xdev-embed is in sys.argv.
    """
    import os
    import ubelt as ub
    import xdev
    if os.environ.get('XDEV_EMBED', '') or ub.argflag('--xdev-embed'):
        xdev.embed(n=n + 1)


class EmbedOnException:
    """
    Context manager which embeds in ipython if an exception is thrown

    SeeAlso:
        :func:`embed`
    """
    def __init__(self, before_embed=None):
        self.before_embed = before_embed

    def __enter__(self):
        return self

    def __call__(self, before_embed=None):
        # This is quirky behavior, but probably fine
        self.before_embed = before_embed
        return self

    def __exit__(__self, __type, __value, __trace):
        if __trace is not None:
            print('!!! EMBED ON EXCEPTION !!!')
            if __self.before_embed is not None:
                __self.before_embed()
            print('[util_dbg] %r in context manager!: %s ' % (__type, str(__value)))
            import traceback
            traceback.print_exception(__type, __value, __trace)
            # Grab the context of the frame where the failure occurred
            __trace_globals = __trace.tb_frame.f_globals
            __trace_locals = __trace.tb_frame.f_locals
            __trace_ns = __trace_globals.copy()
            __trace_ns.update(__trace_locals)
            # Hack to bring back names that we clobber
            if '__self' in __trace_ns:
                __self = __trace_ns['__self']

            # Note: this definately does nothing on 3.13+
            locals().update(__trace_ns)  # I don't think this does anything
            embed(parent_locals=__trace_locals, parent_globals=__trace_globals)


def fix_embed_globals():
    """
    HACK adds current locals() to globals().
    Can be dangerous.

    References:
        https://github.com/ipython/ipython/issues/62

    Solves the following issue:

    .. code:: python

        def foo():
            x = 5
            # You embed here
            import xdev
            xdev.embed()

            '''
            Now you try and run this line manually but you get a NameError

            result = [x + i for i in range(10)]

            No problem, just use. It changes all local variables to globals
            xdev.fix_embed_globals()

            '''
            result = [x + i for i in range(10)]

        foo()
    """
    # Get the stack frame of whoever called this function
    frame = get_stack_frame(n=1)
    # Hack all of the local variables to be global variables
    frame.f_globals.update(frame.f_locals)
    # Leave some trace that we did this
    frame.f_globals['_did_xdev_fix_embed_globals'] = True


embed_on_exception_context = EmbedOnException()
embed_on_exception = embed_on_exception_context


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdev/xdev/embeding.py
    """

    def test_embed_traceback():
        import xdev
        x = 1
        # xdev.embed()
        with xdev.EmbedOnException():
            print(x)
            raise Exception

    test_embed_traceback()
