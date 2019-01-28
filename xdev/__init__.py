"""
CommandLine:
    # Regenerate the tail of this file
    mkinit ~/code/xdev/xdev


# FIXME:
# If I uncomment the following I get this error:
#       File "/home/joncrall/code/mkinit/mkinit/static_analysis.py", line 633, in _workaround_16806
#         while not is_balanced_statement(exec_source_lines[a:b]):
#       File "/home/joncrall/code/mkinit/mkinit/static_analysis.py", line 520, in is_balanced_statement
#         for t in tokenize.generate_tokens(stream.readline):
#       File "/home/joncrall/venv3.6/lib/python3.6/tokenize.py", line 578, in _tokenize
#         ("<tokenize>", lnum, pos, line))
#       File "<tokenize>", line 2
#         - [ ] Perhaps let submodules specify a 2-tuple with the second item being a dict that indicates: (nomod, noattr)?
#         ^
#     IndentationError: unindent does not match any outer indentation level

# TODO:
#     - [ ] Update mkinit so we can either:
#         (1) blacklist specific modules from importing their attrs or
#         (2) whitelist the modules that will import their attrs

#     - [ ] Perhaps let submodules specify a 2-tuple with the second item
#         being a dict that indicates: (nomod, noattr)?
#
#     - [ ] Automatically add custom defined names in this file to __all__
"""
__version__ = '0.0.4'


__submodules__ = [
    'embeding',
    'interactive_iter',
    'introspect',
    'class_reloader',
    'misc',
    'profiler',
]

__extra_all__ = [
    'util'
]


from xdev.embeding import util

### The following is autogenerated

from xdev import embeding
from xdev import interactive_iter
from xdev import introspect
from xdev import class_reloader
from xdev import misc
from xdev import profiler

from xdev.embeding import (EmbedOnException, embed, embed_on_exception_context,
                           fix_embed_globals,)
from xdev.interactive_iter import (InteractiveIter,)
from xdev.introspect import (get_func_kwargs,)
from xdev.class_reloader import (reload_class,)
from xdev.misc import (editfile, quantum_random, startfile, view_directory,)
from xdev.profiler import (IS_PROFILING, profile, profile_now,)

__all__ = ['EmbedOnException', 'IS_PROFILING', 'InteractiveIter',
           'class_reloader', 'editfile', 'embed', 'embed_on_exception_context',
           'embeding', 'fix_embed_globals', 'get_func_kwargs',
           'interactive_iter', 'introspect', 'misc', 'profile', 'profile_now',
           'profiler', 'quantum_random', 'reload_class', 'startfile', 'util',
           'view_directory']
