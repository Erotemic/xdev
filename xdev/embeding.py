import sys
from functools import partial
from xdoctest.dynamic_analysis import get_parent_frame
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

    def __exit__(self, type_, value, trace):
        if trace is not None:
            print('!!! EMBED ON EXCEPTION !!!')
            print('[util_dbg] %r in context manager!: %s ' % (type_, str(value)))
            import traceback
            traceback.print_exception(type_, value, trace)
            # Grab the context of the frame where the failure occurred
            trace_globals = trace.tb_frame.f_globals
            trace_locals = trace.tb_frame.f_locals
            trace_ns = trace_globals.copy()
            trace_ns.update(trace_locals)
            # Hack to bring back self
            if 'self' in trace_ns:
                self = trace_ns['self']
            # execstr_trace_g = ut.execstr_dict(trace_globals, 'trace_globals')
            # execstr_trace_l = ut.execstr_dict(trace_locals, 'trace_locals')
            # execstr_trace = execstr_trace_g + '\n' + execstr_trace_l
            # exec(execstr_trace)
            locals().update(trace_ns)
            embed()


embed_on_exception_context = EmbedOnException()
