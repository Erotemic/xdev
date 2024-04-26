"""

"""

__mkinit__ = """
# mkinit ~/code/xdev/xdev/cli/__init__.py  --lazy_loader -w
mkinit ~/code/xdev/xdev/cli/__init__.py  --lazy -w
"""

##


def lazy_import(module_name, submodules, submod_attrs, eager='auto'):
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

    eager_import_flag = False
    if eager == 'auto':
        # Enable eager import based on the value of the environ
        eager_import_text = os.environ.get('EAGER_IMPORT', '')
        if eager_import_text:
            eager_import_text_ = eager_import_text.lower()
            if eager_import_text_ in {'true', '1', 'on', 'yes'}:
                eager_import_flag = True
            # Could be more fancy here
            if __name__ in eager_import_text_:
                eager_import_flag = True
    else:
        eager_import_flag = eager

    if eager_import_flag:
        for name in submodules:
            __getattr__(name)

        for attrs in submod_attrs.values():
            for attr in attrs:
                __getattr__(attr)
    return __getattr__


__getattr__ = lazy_import(
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
            'main',
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


def __dir__():
    return __all__

__all__ = ['AvailablePackageConfig', 'DirectoryStatsCLI',
           'ExtendedStubGenerator', 'PythonVersions', 'ReqPythonVersionSpec',
           'Stub', 'XdevCLI', 'available_package_versions',
           'build_package_table', 'common_module_aliases',
           'common_module_names', 'common_unreferenced', 'cp_sorter',
           'delete_unpaired_pyi_files', 'demo', 'dirstats', 'docstr_stubgen',
           'generate_typed_stubs', 'grab_pypi_items', 'hacked_typing_info',
           'main', 'minimum_cross_python_versions', 'modpath_coerce',
           'parse_platform_tag', 'parse_wheel_name', 'postprocess_hacks',
           'remove_duplicate_imports', 'rprint', 'stdlib_names',
           'summarize_package_availability', 'vectorize']
