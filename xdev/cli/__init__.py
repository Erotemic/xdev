__autogen__ = """
mkinit ~/code/xdev/xdev/cli/__init__.py  --lazy_loader -w
"""
import lazy_loader  # NOQA


__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules={
        'available_package_versions',
        'dirstats',
        'docstr_stubgen',
        'main',
    },
    submod_attrs={
        'available_package_versions': [
            'AvailablePackageConfig',
            'PythonVersions',
            'ReqPythonVersionSpec',
            'build_package_table',
            'cp_sorter',
            'demo',
            'grab_pypi_items',
            'main',
            'minimum_cross_python_versions',
            'parse_platform_tag',
            'parse_wheel_name',
            'summarize_package_availability',
            'vectorize',
        ],
        'dirstats': [
            'DirectoryStatsCLI',
            'DirectoryWalker',
            'byte_str',
            'main',
            'parse_file_stats',
            'strip_comments_and_newlines',
            'strip_docstrings',
        ],
        'docstr_stubgen': [
            'ExtendedStubGenerator',
            'Stub',
            'common_module_aliases',
            'common_module_names',
            'common_unreferenced',
            'delete_unpaired_pyi_files',
            'generate_typed_stubs',
            'hacked_typing_info',
            'modpath_coerce',
            'postprocess_hacks',
            'remove_duplicate_imports',
            'stdlib_names',
        ],
        'main': [
            'XdevCLI',
            'main',
            'rprint',
        ],
    },
)

__all__ = ['AvailablePackageConfig', 'DirectoryStatsCLI', 'DirectoryWalker',
           'ExtendedStubGenerator', 'PythonVersions', 'ReqPythonVersionSpec',
           'Stub', 'XdevCLI', 'available_package_versions',
           'build_package_table', 'byte_str', 'common_module_aliases',
           'common_module_names', 'common_unreferenced', 'cp_sorter',
           'delete_unpaired_pyi_files', 'demo', 'dirstats', 'docstr_stubgen',
           'generate_typed_stubs', 'grab_pypi_items', 'hacked_typing_info',
           'main', 'minimum_cross_python_versions', 'modpath_coerce',
           'parse_file_stats', 'parse_platform_tag', 'parse_wheel_name',
           'postprocess_hacks', 'remove_duplicate_imports', 'rprint',
           'stdlib_names', 'strip_comments_and_newlines', 'strip_docstrings',
           'summarize_package_availability', 'vectorize']
