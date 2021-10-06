"""
This is Jon Crall's xdev module.

These are tools I often use in IPython, but they almost never make it into
production code, otherwise they would be in :mod:`ubelt`.
"""

__dev__ = """
CommandLine:
    # Regenerate the tail of this file
    mkinit ~/code/xdev/xdev -w

TODO:
    - [ ] Update mkinit so we can either:
        (1) blacklist specific modules from importing their attrs or
        (2) whitelist the modules that will import their attrs

    - [ ] Perhaps let submodules specify a 2-tuple with the second item
        being a dict that indicates: (nomod, noattr)?

    - [ ] Automatically add custom defined names in this file to __all__
"""

__version__ = '0.2.5'


__submodules__ = [
    'embeding',
    'interactive_iter',
    'introspect',
    'class_reloader',
    'search_replace',
    'misc',
    'autojit',
    'profiler',
]

__extra_all__ = [
    'util'
]


from xdev.embeding import util

### The following is autogenerated

from xdev import autojit
from xdev import class_reloader
from xdev import embeding
from xdev import interactive_iter
from xdev import introspect
from xdev import misc
from xdev import profiler
from xdev import search_replace

from xdev.embeding import (EmbedOnException, embed, embed_on_exception_context,
                           fix_embed_globals,)
from xdev.interactive_iter import (InteractiveIter,)
from xdev.introspect import (get_func_kwargs,)
from xdev.class_reloader import (reload_class,)
from xdev.search_replace import (GrepResult, Pattern, find, grep, grepfile,
                                 sed, sedfile,)
from xdev.misc import (byte_str, difftext, distext, edit_distance, editfile,
                       get_stack_frame, make_warnings_print_tracebacks,
                       nested_type, quantum_random, set_overlaps, startfile,
                       tree, view_directory,)
from xdev.autojit import (MAX_AUTOJIT_TRIES, NUM_AUTOJIT_TRIES,
                          import_module_from_pyx,)
from xdev.profiler import (IS_PROFILING, profile, profile_now,)

__all__ = ['EmbedOnException', 'GrepResult', 'IS_PROFILING', 'InteractiveIter',
           'MAX_AUTOJIT_TRIES', 'NUM_AUTOJIT_TRIES', 'Pattern', 'autojit',
           'byte_str', 'class_reloader', 'difftext', 'distext',
           'edit_distance', 'editfile', 'embed', 'embed_on_exception_context',
           'embeding', 'find', 'fix_embed_globals', 'get_func_kwargs',
           'get_stack_frame', 'grep', 'grepfile', 'import_module_from_pyx',
           'interactive_iter', 'introspect', 'make_warnings_print_tracebacks',
           'misc', 'nested_type', 'profile', 'profile_now', 'profiler',
           'quantum_random', 'reload_class', 'search_replace', 'sed',
           'sedfile', 'set_overlaps', 'startfile', 'tree', 'util',
           'view_directory']
