import sys
from IPython.terminal.embed import InteractiveShellEmbed, load_default_config
# from IPython.terminal.ipapp import load_default_config


class InteractiveShellEmbedEnhanced(InteractiveShellEmbed):
    """
    A workaround to issue https://github.com/ipython/ipython/issues/10695
    In embedded ipython shell, new variables are created in locals() instead of globals()
    and functions do not make closures for the locals.

    Examples:

    If not embedded from a function, then nothing special needs to be done other than calling embed() defined below.
    These code will work:

        a=3; (lambda: a)()
        import time; (lambda: time.time())()

    If embedded from a function, in order to introduce new variables to global name space, we need to call
    ipy.to_global() first and then call ipy.to_local() to come back

        ipy.to_global()
        a=3  # here we cannot access the local variables
        ipy.to_local()
        (lambda: a)()

    It seems that a contextmanager to switch back automatically will not work:

        with ipy.to_global_manager():
            a=3
            print((lambda: a)())

    It may be because of that IPython compiles the whole cell and run it using exec(code, globals, locals).
    But globals and locals are calculated at the time this context manager is defined.
    """
    @property
    def user_global_ns(self):
        if getattr(self, 'embedded_outside_func', False):
            return self.user_ns
        else:
            return self.user_module.__dict__

    def init_frame(self, frame):
        if frame.f_code.co_name == '<module>':  # if embedded outside a function
            self.embedded_outside_func = True
        else:  # if embedded from a function
            self.embedded_outside_func = False

            self._saved_user_ns = None
            self._ns = {}
            # make global variables for user access to the histories
            self._ns['_ih'] = self.history_manager.input_hist_parsed
            self._ns['_oh'] = self.history_manager.output_hist
            self._ns['_dh'] = self.history_manager.dir_hist

            # user aliases to input and output histories.  These shouldn't show up
            # in %who, as they can have very large reprs.
            self._ns['In']  = self.history_manager.input_hist_parsed
            self._ns['Out'] = self.history_manager.output_hist

            # Store myself as the public api!!!
            # ns['get_ipython'] = self.get_ipython
            self._ns['exit'] = self.exiter
            self._ns['quit'] = self.exiter

            self.to_global = self._to_global
            self.to_local = self._to_local

    def _to_global(self):
        self._saved_user_ns = self.user_ns
        assert not set(self._ns).intersection(self.user_module.__dict__)
        self.user_ns = self.user_module.__dict__
        self.user_ns.update(self._ns)

    def _to_local(self):
        if self._saved_user_ns is None:
            return
        for key in self._ns:
            del self.user_ns[key]
        self.user_ns = self._saved_user_ns

    def share_locals(self):
        """
        share the locals to global manually
        """
        if (id(self.user_ns) != id(self.user_module.__dict__)):
            self.user_module.__dict__.update(self.user_ns)


def embed2(local_ns=None, **kwargs):
    """
    based on IPython.terminal.embed.embed()

    References:
        https://github.com/ipython/ipython/issues/10695
    """
    import glob
    import os
    from IPython.core.interactiveshell import InteractiveShell
    config = kwargs.get('config')
    header = kwargs.pop('header', u'')
    compile_flags = kwargs.pop('compile_flags', None)
    if config is None:
        config = load_default_config()
        config.InteractiveShellEmbedEnhanced = config.TerminalInteractiveShell
        kwargs['config'] = config
    #save ps1/ps2 if defined
    ps1 = None
    ps2 = None
    try:
        ps1 = sys.ps1
        ps2 = sys.ps2
    except AttributeError:
        pass
    #save previous instance
    saved_shell_instance = InteractiveShell._instance
    if saved_shell_instance is not None:
        cls = type(saved_shell_instance)
        cls.clear_instance()
    frame = sys._getframe(1)

    # shell is the ipython instance returned from get_ipython()
    # frame refers to the caller of this function
    shell = InteractiveShellEmbedEnhanced.instance(_init_location_id='%s:%s' % (
        frame.f_code.co_filename, frame.f_lineno), **kwargs)
    shell.init_frame(frame)

    #######################
    # load the startup files and update the local_ns
    ######################

    # if local_ns is None:
    #     local_ns = frame.f_locals
    global_ns = frame.f_globals
    global_ns['ipy'] = shell
    global_ns['share_locals'] = shell.share_locals

    startup_files = glob.glob(os.path.join(shell.profile_dir.startup_dir, '*.py'))
    startup_files += glob.glob(os.path.join(shell.profile_dir.startup_dir, '*.ipy'))

    if '__file__' in global_ns:
        hasfile = True
        cfile = global_ns['__file__']
    else:
        hasfile = False

    for filename in sorted(startup_files):
        if filename.endswith('.ipy'):
            shell.safe_execfile_ipy(filename)
        else:
            global_ns['__file__'] = filename
            shell.safe_execfile(filename, global_ns, raise_exceptions=True)  # this updates the global_ns

    if hasfile:
        global_ns['__file__'] = cfile
    else:
        del global_ns['__file__']

    ########################
    #  launch the shell
    #######################
    shell(local_ns=local_ns, header=header, stack_depth=2, compile_flags=compile_flags,
          _call_location_id='%s:%s' % (frame.f_code.co_filename, frame.f_lineno))
    InteractiveShellEmbedEnhanced.clear_instance()
    #restore previous instance
    if saved_shell_instance is not None:
        cls = type(saved_shell_instance)
        cls.clear_instance()
        for subclass in cls._walk_mro():
            subclass._instance = saved_shell_instance
    if ps1 is not None:
        sys.ps1 = ps1
        sys.ps2 = ps2
