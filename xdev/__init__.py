"""
This is Jon Crall's xdev module.

These are tools I often use in IPython, but they almost never make it into
production code, otherwise they would be in :mod:`ubelt`.

+------------------+------------------------------------------+
| Read the docs    | https://xdev.readthedocs.io              |
+------------------+------------------------------------------+
| Github           | https://github.com/Erotemic/xdev         |
+------------------+------------------------------------------+
| Pypi             | https://pypi.org/project/xdev            |
+------------------+------------------------------------------+

"""

__dev__ = """
CommandLine:
    # Regenerate the tail of this file
    mkinit ~/code/xdev/xdev -w --lazy

TODO:
    - [ ] Update mkinit so we can either:
        (1) blocklist specific modules from importing their attrs or
        (2) passlist the modules that will import their attrs

    - [ ] Perhaps let submodules specify a 2-tuple with the second item
        being a dict that indicates: (nomod, noattr)?

    - [ ] Automatically add custom defined names in this file to __all__
"""

__version__ = '1.5.4'


# __submodules__ = [
#     'embeding',
#     'interactive_iter',
#     'desktop_interaction',
#     'introspect',
#     'class_reloader',
#     'search_replace',
#     'misc',
#     'util_path',
#     'patterns',
#     'autojit',
#     'profiler',
#     'tracebacks',
# ]

# __extra_all__ = [
#     'util'
# ]


from xdev import util

### The following is autogenerated


def lazy_import(module_name, submodules, submod_attrs):
    import importlib
    import os
    name_to_submod = {
        func: mod for mod, funcs in submod_attrs.items()
        for func in funcs
    }

    def __getattr__(name):
        if name in submodules:
            attr = importlib.import_module(
                '{module_name}.{name}'.format(
                    module_name=module_name, name=name)
            )
        elif name in name_to_submod:
            submodname = name_to_submod[name]
            module = importlib.import_module(
                '{module_name}.{submodname}'.format(
                    module_name=module_name, submodname=submodname)
            )
            attr = getattr(module, name)
        else:
            raise AttributeError(
                'No {module_name} attribute {name}'.format(
                    module_name=module_name, name=name))
        globals()[name] = attr
        return attr

    if os.environ.get('EAGER_IMPORT', ''):
        for name in submodules:
            __getattr__(name)

        for attrs in submod_attrs.values():
            for attr in attrs:
                __getattr__(attr)
    return __getattr__


__getattr__ = lazy_import(
    __name__,
    submodules={
        'algo',
        'autojit',
        'class_reloader',
        'cli',
        'desktop_interaction',
        'directory_walker',
        'embeding',
        'format_quotes',
        'interactive_iter',
        'introspect',
        'misc',
        'patterns',
        'profiler',
        'regex_builder',
        'search_replace',
        'tracebacks',
        'util',
        'util_networkx',
        'util_path',
        'util_random',
        'util_time',
    },
    submod_attrs={
        'algo': [
            'edit_distance',
            'knapsack',
            'knapsack_greedy',
            'knapsack_ilp',
            'knapsack_iterative',
            'knapsack_iterative_int',
            'knapsack_iterative_numpy',
            'number_of_decimals',
        ],
        'autojit': [
            'import_module_from_pyx',
        ],
        'class_reloader': [
            'reload_class',
        ],
        'cli': [
            'AvailablePackageConfig',
            'DirectoryStatsCLI',
            'DirectoryWalker',
            'ExtendedStubGenerator',
            'PythonVersions',
            'ReqPythonVersionSpec',
            'Stub',
            'XdevCLI',
            'available_package_versions',
            'build_package_table',
            'byte_str',
            'common_module_aliases',
            'common_module_names',
            'common_unreferenced',
            'cp_sorter',
            'delete_unpaired_pyi_files',
            'demo',
            'dirstats',
            'docstr_stubgen',
            'generate_typed_stubs',
            'grab_pypi_items',
            'hacked_typing_info',
            'main',
            'minimum_cross_python_versions',
            'modpath_coerce',
            'parse_file_stats',
            'parse_platform_tag',
            'parse_wheel_name',
            'postprocess_hacks',
            'remove_duplicate_imports',
            'rprint',
            'stdlib_names',
            'strip_comments_and_newlines',
            'strip_docstrings',
            'summarize_package_availability',
            'vectorize',
        ],
        'desktop_interaction': [
            'editfile',
            'startfile',
            'view_directory',
        ],
        'directory_walker': [
            'DirectoryWalker',
            'byte_str',
            'parse_file_stats',
            'strip_comments_and_newlines',
            'strip_docstrings',
        ],
        'embeding': [
            'EmbedOnException',
            'embed',
            'embed_if_requested',
            'embed_on_exception',
            'embed_on_exception_context',
            'fix_embed_globals',
            'load_snapshot',
            'snapshot',
        ],
        'format_quotes': [
            'DOUBLE_QUOTE',
            'SINGLE_QUOTE',
            'TRIPLE_DOUBLE_QUOTE',
            'TRIPLE_SINGLE_QUOTE',
            'format_quotes',
            'format_quotes_in_file',
            'format_quotes_in_text',
        ],
        'interactive_iter': [
            'InteractiveIter',
        ],
        'introspect': [
            'distext',
            'get_func_kwargs',
            'get_stack_frame',
            'iter_object_tree',
            'test_object_pickleability',
        ],
        'misc': [
            'byte_str',
            'difftext',
            'nested_type',
            'quantum_random',
            'set_overlaps',
            'textfind',
            'tree_repr',
        ],
        'patterns': [
            'MultiPattern',
            'Pattern',
            'PatternBase',
            'RE_Pattern',
        ],
        'profiler': [
            'IS_PROFILING',
            'profile',
            'profile_globals',
            'profile_now',
        ],
        'regex_builder': [
            'PythonRegexBuilder',
            'RegexBuilder',
            'VimRegexBuilder',
        ],
        'search_replace': [
            'GrepResult',
            'find',
            'grep',
            'grepfile',
            'greptext',
            'sed',
            'sedfile',
        ],
        'tracebacks': [
            'make_warnings_print_tracebacks',
        ],
        'util': [
            'bubbletext',
            'conj_phrase',
            'take_column',
        ],
        'util_networkx': [
            'AsciiDirectedGlyphs',
            'AsciiUndirectedGlyphs',
            'UtfDirectedGlyphs',
            'UtfUndirectedGlyphs',
            'generate_network_text',
            'graph_str',
            'write_network_text',
        ],
        'util_path': [
            'ChDir',
            'sidecar_glob',
            'tree',
        ],
        'util_random': [
            'ensure_rng',
        ],
        'util_time': [
            'TimeTypeError',
            'TimeValueError',
            'coerce_datetime',
            'coerce_timedelta',
            'coerce_timezone',
            'datetime',
            'ensure_timezone',
            'format_timedelta',
            'isoformat',
            'timedelta',
        ],
    },
)


def __dir__():
    return __all__

__all__ = ['AsciiDirectedGlyphs', 'AsciiUndirectedGlyphs',
           'AvailablePackageConfig', 'ChDir', 'DOUBLE_QUOTE',
           'DirectoryStatsCLI', 'DirectoryWalker', 'EmbedOnException',
           'ExtendedStubGenerator', 'GrepResult', 'IS_PROFILING',
           'InteractiveIter', 'MultiPattern', 'Pattern', 'PatternBase',
           'PythonRegexBuilder', 'PythonVersions', 'RE_Pattern',
           'RegexBuilder', 'ReqPythonVersionSpec', 'SINGLE_QUOTE', 'Stub',
           'TRIPLE_DOUBLE_QUOTE', 'TRIPLE_SINGLE_QUOTE', 'TimeTypeError',
           'TimeValueError', 'UtfDirectedGlyphs', 'UtfUndirectedGlyphs',
           'VimRegexBuilder', 'XdevCLI', 'algo', 'autojit',
           'available_package_versions', 'bubbletext', 'build_package_table',
           'byte_str', 'class_reloader', 'cli', 'coerce_datetime',
           'coerce_timedelta', 'coerce_timezone', 'common_module_aliases',
           'common_module_names', 'common_unreferenced', 'conj_phrase',
           'cp_sorter', 'datetime', 'delete_unpaired_pyi_files', 'demo',
           'desktop_interaction', 'difftext', 'directory_walker', 'dirstats',
           'distext', 'docstr_stubgen', 'edit_distance', 'editfile', 'embed',
           'embed_if_requested', 'embed_on_exception',
           'embed_on_exception_context', 'embeding', 'ensure_rng',
           'ensure_timezone', 'find', 'fix_embed_globals', 'format_quotes',
           'format_quotes_in_file', 'format_quotes_in_text',
           'format_timedelta', 'generate_network_text', 'generate_typed_stubs',
           'get_func_kwargs', 'get_stack_frame', 'grab_pypi_items',
           'graph_str', 'grep', 'grepfile', 'greptext', 'hacked_typing_info',
           'import_module_from_pyx', 'interactive_iter', 'introspect',
           'isoformat', 'iter_object_tree', 'knapsack', 'knapsack_greedy',
           'knapsack_ilp', 'knapsack_iterative', 'knapsack_iterative_int',
           'knapsack_iterative_numpy', 'load_snapshot', 'main',
           'make_warnings_print_tracebacks', 'minimum_cross_python_versions',
           'misc', 'modpath_coerce', 'nested_type', 'number_of_decimals',
           'parse_file_stats', 'parse_platform_tag', 'parse_wheel_name',
           'patterns', 'postprocess_hacks', 'profile', 'profile_globals',
           'profile_now', 'profiler', 'quantum_random', 'regex_builder',
           'reload_class', 'remove_duplicate_imports', 'rprint',
           'search_replace', 'sed', 'sedfile', 'set_overlaps', 'sidecar_glob',
           'snapshot', 'startfile', 'stdlib_names',
           'strip_comments_and_newlines', 'strip_docstrings',
           'summarize_package_availability', 'take_column',
           'test_object_pickleability', 'textfind', 'timedelta', 'tracebacks',
           'tree', 'tree_repr', 'util', 'util_networkx', 'util_path',
           'util_random', 'util_time', 'vectorize', 'view_directory',
           'write_network_text']
