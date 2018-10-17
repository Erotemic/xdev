import sys
from functools import partial
from xdoctest.dynamic_analysis import get_parent_frame, get_stack_frame
from . import util
import time


def embed(parent_locals=None, parent_globals=None, exec_lines=None,
          remove_pyqt_hook=True, n=0):
    """
    Starts interactive session. Similar to keyboard command in matlab.
    Wrapper around IPython.embed

    """
    import IPython

    if parent_globals is None:
        parent_globals = get_parent_frame(n=n).f_globals
    if parent_locals is None:
        parent_locals = get_parent_frame(n=n).f_locals

    stackdepth = n  # NOQA
    getframe = partial(get_parent_frame, n=n)  # NOQA

    # exec(execstr_dict(parent_globals, 'parent_globals'))
    # exec(execstr_dict(parent_locals,  'parent_locals'))
    print('')
    print('================')
    print(util.bubbletext('EMBEDDING'))
    print('================')
    print('[util] embedding')
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

    #from IPython.config.loader import Config
    # cfg = Config()
    #config_dict = {}
    #if exec_lines is not None:
    #    config_dict['exec_lines'] = exec_lines
    #IPython.embed(**config_dict)
    print('[util]  Get stack location with: ')
    print('[util] get_parent_frame(n=8).f_code.co_name')
    print('[util] set EXIT_NOW or qqq to True(ish) to hard exit on unembed')
    #print('set iup to True to draw plottool stuff')
    print('[util] call %pylab qt4 to get plottool stuff working')
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
        locals().update(parent_ns)
        try:
            IPython.embed()
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


class EmbedOnException(object):
    """
    Context manager which embeds in ipython if an exception is thrown
    """
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __call__(self):
        return self

    def __exit__(__self, __type, __value, __trace):
        if __trace is not None:
            print('!!! EMBED ON EXCEPTION !!!')
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
            locals().update(__trace_ns)  # I don't think this does anythign
            embed()


def fix_embed_globals():
    """
    HACK adds current locals() to globals().
    Can be dangerous.

    Solves the following issue:

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
