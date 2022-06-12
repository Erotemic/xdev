"""
Script for auto-generating pyi type extension files from google-style
docstrings.

This is a work in progress, but ultimately the goal is to be able to express
concise typing information in docstrings and then explicitly expose that to
Python.


Requirements:
    pip install mypy autoflake yapf

CommandLine:
    # Run script to parse google-style docstrings and write pyi files
    python ~/code/ubelt/dev/gen_typed_stubs.py

    # Run mypy to check that type annotations are correct
    mypy ubelt
"""
from mypy.stubgen import (StubGenerator, find_self_initializers, FUNC, EMPTY,
                          METHODS_WITH_RETURN_VALUE,)
import sys

from typing import (List, Dict, Optional)
from mypy.nodes import (
    # Expression, IntExpr, UnaryExpr, StrExpr, BytesExpr, NameExpr, FloatExpr, MemberExpr,
    # TupleExpr, ListExpr, ComparisonExpr, CallExpr, IndexExpr, EllipsisExpr,
    # ClassDef, MypyFile, Decorator, AssignmentStmt, TypeInfo,
    # IfStmt, ImportAll, ImportFrom, Import,
    FuncDef,
    # FuncBase, Block,
    # Statement, OverloadedFuncDef, ARG_POS,
    ARG_STAR, ARG_STAR2,
    # ARG_NAMED,
)
# from mypy.stubgenc import generate_stub_for_c_module
# from mypy.stubutil import (
#     default_py2_interpreter, CantImport, generate_guarded,
#     walk_packages, find_module_path_and_all_py2, find_module_path_and_all_py3,
#     report_missing, fail_missing, remove_misplaced_type_comments, common_dir_prefix
# )
from mypy.types import (
    # Type, TypeStrVisitor,
    CallableType,
    # UnboundType, NoneType, TupleType, TypeList, Instance,
    AnyType,
    get_proper_type
)
from mypy.traverser import (
    all_yield_expressions,
    has_return_statement,
    has_yield_expression
)
import ubelt as ub


def generate_typed_stubs(modpath):
    """
    Attempt to use google-style docstrings, xdoctest, and mypy to generate
    typed stub files.

    Does not overwrite anything by itself.

    Args:
        modpath (PathLike): path to the module to generate types for

    Returns:
        Dict[PathLike, str]:
            A dictionary mapping the path of each file to write to the text to
            be written.

    Notes:
        FIXME: This currently requires my hacked version of mypy

    Example:
        >>> # xdoctest: +SKIP
        >>> # xdoctest: +REQUIRES(module:mypy)
        >>> # xdoctest: +REQUIRES(--hacked)
        >>> from xdev.cli.docstr_stubgen import *  # NOQA
        >>> import xdev
        >>> import ubelt as ub
        >>> from xdev.cli import docstr_stubgen
        >>> modpath = ub.Path(docstr_stubgen.__file__)
        >>> generated = generate_typed_stubs(modpath)
        >>> text = generated[ub.peek(generated.keys())]
        >>> assert 'PathLike' in text
        >>> assert 'Dict' in text
        >>> print(text)

    Ignore:
        pyfile mypy.stubgen
        # Delete compiled verisons so we can hack it

        # ls $VIRTUAL_ENV/lib/*/site-packages/mypy/*.so
        # rm $VIRTUAL_ENV/lib/*/site-packages/mypy/*.so
        # rm ~/.pyenv/versions/3.8.6/envs/pyenv3.8.6/lib/python3.8/site-packages/mypy/*.cpython-38-x86_64-linux-gnu.so

        # This works I think?
        if [[ ! -e "$HOME/code/mypy" ]];  then
            git clone https://github.com/python/mypy.git $HOME/code/mypy
        fi
        (cd $HOME/code/mypy && git pull)
        pip install -e $HOME/code/mypy


        pip install MonkeyType

        monkeytype run run_tests.py
        monkeytype stub ubelt.util_dict

        from typing import TypeVar
        from mypy.applytype import get_target_type
        z = TypeVar('Iterable')
        get_target_type(z)

        from mypy.expandtype import expand_type
        expand_type(z, env={})

        from mypy.types import get_proper_type
        get_proper_type(z)
        get_proper_type(dict)
        import typing
        get_proper_type(typing.Iterable)

        from mypy.types import deserialize_type, UnboundType
        import mypy.types as mypy_types
        z = UnboundType('Iterable')
        get_proper_type(dict)

        from mypy.fastparse import parse_type_string
        parse_type_string('dict', 'dict', 0, 0)
        z = parse_type_string('typing.Iterator', 'Any', 0, 0)
        get_proper_type(z)

    """
    # import pathlib
    # import ubelt as ub
    import os
    from mypy import stubgen
    from mypy import defaults
    from xdoctest import static_analysis
    from os.path import join
    import ubelt as ub

    # modname = 'scriptconfig'
    # module = ub.import_module_from_name(modname)
    # modpath = ub.Path(module.__file__).parent

    # for p in pathlib.Path(modpath).glob('*.pyi'):
    #     p.unlink()
    modpath = ub.Path(modpath)

    files = list(static_analysis.package_modpaths(
        modpath, recursive=True, with_libs=1, with_pkg=0))

    # files = [f for f in files if 'deprecated' not in f]
    # files = [join(ubelt_dpath, 'util_dict.py')]

    if modpath.is_file():
        output_dir = modpath.parent.parent
    else:
        output_dir = modpath.parent

    options = stubgen.Options(
        pyversion=defaults.PYTHON3_VERSION,
        no_import=True,
        doc_dir='',
        search_path=[],
        interpreter=sys.executable,
        ignore_errors=False,
        parse_only=True,
        include_private=False,
        output_dir=output_dir,
        modules=[],
        packages=[],
        files=files,
        verbose=False,
        quiet=False,
        export_less=True)
    # generate_stubs(options)

    mypy_opts = stubgen.mypy_options(options)
    py_modules, c_modules = stubgen.collect_build_targets(options, mypy_opts)

    # Collect info from docs (if given):
    sigs = class_sigs = None  # type: Optional[Dict[str, str]]
    if options.doc_dir:
        sigs, class_sigs = stubgen.collect_docs_signatures(options.doc_dir)

    # Use parsed sources to generate stubs for Python modules.
    stubgen.generate_asts_for_modules(py_modules, options.parse_only, mypy_opts, options.verbose)

    generated = {}

    for mod in py_modules:
        assert mod.path is not None, "Not found module was not skipped"
        target = mod.module.replace('.', '/')
        if os.path.basename(mod.path) == '__init__.py':
            target += '/__init__.pyi'
        else:
            target += '.pyi'
        target = join(options.output_dir, target)
        files.append(target)
        with stubgen.generate_guarded(mod.module, target, options.ignore_errors, options.verbose):
            stubgen.generate_stub_from_ast(mod, target, options.parse_only,
                                           options.pyversion,
                                           options.include_private,
                                           options.export_less)

            gen = ExtendedStubGenerator(mod.runtime_all, pyversion=options.pyversion,
                                        include_private=options.include_private,
                                        analyzed=not options.parse_only,
                                        export_less=options.export_less)
            assert mod.ast is not None, "This function must be used only with analyzed modules"
            mod.ast.accept(gen)
            # print('gen.import_tracker.required_names = {!r}'.format(gen.import_tracker.required_names))
            # print(gen.import_tracker.import_lines())

            # print('mod.path = {!r}'.format(mod.path))

            known_one_letter_types = {
                # 'T', 'K', 'A', 'B', 'C', 'V',
                'DT', 'KT', 'VT', 'T'
            }
            for type_var_name in set(gen.import_tracker.required_names) & set(known_one_letter_types):
                gen.add_typing_import('TypeVar')
                # gen.add_import_line('from typing import {}\n'.format('TypeVar'))
                gen._output = ['{} = TypeVar("{}")\n'.format(type_var_name, type_var_name)] + gen._output

            custom_types = {'Hasher'}
            for type_var_name in set(gen.import_tracker.required_names) & set(custom_types):
                gen.add_typing_import('TypeVar')
                # gen.add_import_line('from typing import {}\n'.format('TypeVar'))
                gen._output = ['{} = TypeVar("{}")\n'.format(type_var_name, type_var_name)] + gen._output

            # Hack for specific module
            # if mod.path.endswith('util_path.py'):
            #     gen.add_typing_import('TypeVar')
            #     # hack for variable inheritence
            #     gen._output = ['import pathlib\nimport os\n', "_PathBase = pathlib.WindowsPath if os.name == 'nt' else pathlib.PosixPath\n"] + gen._output

            text = ''.join(gen.output())
            text = postprocess_hacks(text, mod)

            # Write output to file.
            # subdir = ub.Path(target).parent
            # if subdir and not os.path.isdir(subdir):
            #     os.makedirs(subdir)
            generated[target] = text
            # with open(target, 'w') as file:
            #     file.write(text)
    return generated


def postprocess_hacks(text, mod):
    import autoflake
    import yapf
    # Hack to remove lines caused by Py2 compat
    text = text.replace('Generator = object\n', '')
    text = text.replace('select = NotImplemented\n', '')
    text = text.replace('iteritems: Any\n', '')
    text = text.replace('text_type = str\n', '')
    text = text.replace('text_type: Any\n', '')
    text = text.replace('string_types: Any\n', '')
    text = text.replace('PY2: Any\n', '')
    text = text.replace('__win32_can_symlink__: Any\n', '')
    # text = text.replace('odict = OrderedDict', '')
    # text = text.replace('ddict = defaultdict', '')

    if mod.path.endswith('util_path.py'):
        # hack for forward reference
        text = text.replace(' -> Path:', " -> 'Path':")
        text = text.replace('class Path(_PathBase)', "class Path")

    # Format the PYI file nicely
    text = autoflake.fix_code(text, remove_unused_variables=True,
                              remove_all_unused_imports=True)

    # import autopep8
    # text = autopep8.fix_code(text, options={
    #     'aggressive': 0,
    #     'experimental': 0,
    # })

    style = yapf.yapf_api.style.CreatePEP8Style()
    text, _ = yapf.yapf_api.FormatCode(
        text,
        filename='<stdin>',
        style_config=style,
        lines=None,
        verify=False)
    # print(text)
    return text


@ub.memoize
def stdlib_names():
    # https://stackoverflow.com/questions/6463918/how-to-get-a-list-of-all-the-python-standard-library-modules
    import sys
    try:
        names = sys.stdlib_module_names
    except AttributeError:
        from isort import stdlibs
        names = list(stdlibs.py3.stdlib)
    return names


@ub.memoize
def common_module_names():
    """
    fpath = ub.grabdata('https://raw.githubusercontent.com/hugovk/top-pypi-packages/main/top-pypi-packages-30-days.json', expires=86400)
    fpath = ub.Path(fpath)
    import json
    data = json.loads(fpath.read_text())
    for item in data['rows'][0:300]:
        pkg_name = item['project']
        if '-' not in pkg_name:
            print(f'{pkg_name!r},')
    """
    names = stdlib_names().copy()
    # https://github.com/hugovk/top-pypi-packages
    names.extend([
        'numpy',
        'torch',
        'pandas',
        'h5py',
        'networkx',

        'scipy',
        'sklearn',
        'matplotlib',
        'seaborn',
        'attrs',

        'keras',
        'ujson',
        'black',
        'mypy',
        'simplejson',
        'parso',
        'tensorflow',
        'cython',
        'git',
        'openpyxl',

        'concurrent.futures',
        'hashlib._hashlib',
    ])
    names.extend([
        'jinja2', 'boto3', 'requests', 'dateutil', 'yaml', 'boto3', 'botocore',
        'urllib3', 'requests', 'setuptools', 's3transfer', 'six', 'certifi',
        'idna', 'pyyaml', 'wheel', 'cryptography', 'awscli', 'rsa', 'pip',
        'pyparsing', 'jmespath', 'pyasn1', 'packaging', 'zipp', 'pyjwt',
        'colorama', 'pytz', 'click', 'cffi', 'protobuf', 'oauthlib', 'jinja2',
        'pycparser', 'markupsafe', 'cachetools', 'wrapt', 'docutils',
        'isodate', 'psutil', 'pyarrow', 'chardet', 'sqlalchemy', 'tomli',
        'decorator', 'werkzeug', 'msrest', 'aiohttp', 'grpcio', 'multidict',
        'scipy', 'py', 'yarl', 'pluggy', 'filelock', 'pillow', 'soupsieve',
        'aiobotocore', 'jsonschema', 'lxml', 'pytest', 'beautifulsoup4',
        'tqdm', 'greenlet', 'platformdirs', 'fsspec', 'pyopenssl', 'tabulate',
        's3fs', 'flask', 'toml', 'asn1crypto', 'future', 'frozenlist',
        'pyrsistent', 'aiosignal', 'pygments', 'pynacl', 'itsdangerous',
        'httplib2', 'iniconfig', 'docker',
    ])
    return names


@ub.memoize
def common_module_aliases():
    aliases = [
        {'modname': 'numpy', 'alias': ['np']},
        {'modname': 'scipy', 'alias': ['sp']},
        {'modname': 'matplotlib', 'alias': ['mpl']},
        {'modname': 'seaborn', 'alias': ['sns']},
        # I'm biased, what can I say?
        {'modname': 'ubelt', 'alias': ['ub']},
    ]
    return aliases


@ub.memoize
def common_unreferenced():
    unref = [
        {'name': 'PathLike', 'modname': 'os'},
        {'name': 'ModuleType', 'modname': 'types'},
        {'name': 'Callable', 'modname': 'typing'},
        {'name': 'NoParam', 'modname': 'ubelt.util_const'},
        {'name': '_NoParamType', 'modname': 'ubelt.util_const'},
        {'name': 'NoParamType', 'modname': 'ubelt.util_const'},
    ]
    return unref


def hacked_typing_info(type_name):
    result = {
        'import_lines': [],
        'typing_imports': [],
    }
    add_import_line = result['import_lines'].append
    add_typing_import = result['typing_imports'].append

    if type_name.startswith('callable'):
        # TODO: generalize, allow the "callable" func to be transformed
        # into the type if given in the docstring
        type_name = type_name.replace('callable', 'Callable')

    if '|' in type_name:
        add_typing_import('Union')
        add_import_line('from typing import {}\n'.format('Union'))

    for typing_arg in ['Iterable', 'Callable', 'Dict',
                       'List', 'Union', 'Type', 'Mapping',
                       'Tuple', 'Optional', 'Sequence',
                       'Iterator', 'Set', 'Dict']:
        if typing_arg in type_name:
            add_typing_import(typing_arg)
            add_import_line('from typing import {}\n'.format(typing_arg))

    common_modnames = common_module_names()
    common_aliases = common_module_aliases()

    for item in common_aliases:
        for alias in item['alias']:
            prefix = alias + '.'
            if prefix in type_name:
                add_import_line('import {} as {}\n'.format(item['modname'], alias))

    for modname in common_modnames:
        prefix = modname + '.'
        if prefix in type_name:
            add_import_line('import {}\n'.format(modname))

    common_unref = common_unreferenced()
    for item in common_unref:
        if item['name'] in type_name:
            add_import_line('from {} import {}\n'.format(item['modname'], item['name']))

    # types.ModuleType
    # if 'PathLike' in type_name:
    #     add_import_line('from os import {}\n'.format('PathLike'))

    # if 'hashlib._hashlib' in type_name:
    #     add_import_line('import hashlib._hashlib\n')

    # if 'concurrent.futures.Future' in type_name:
    #     add_import_line('import concurrent.futures\n')

    # if type_name.startswith('callable'):
    #     # TODO: generalize, allow the "callable" func to be transformed
    #     # into the type if given in the docstring
    #     result['type_name'] = type_name.replace('callable', 'Callable')
    #     add_typing_import('Callable')
    #     add_import_line('from typing import {}\n'.format(typing_arg))
    result['type_name'] = type_name

    return result


class ExtendedStubGenerator(StubGenerator):

    def visit_func_def(self, o: FuncDef, is_abstract: bool = False,
                       is_overload: bool = False) -> None:
        import ubelt as ub
        if (self.is_private_name(o.name, o.fullname)
                or self.is_not_in_all(o.name)
                or (self.is_recorded_name(o.name) and not is_overload)):
            self.clear_decorators()
            return
        if not self._indent and self._state not in (EMPTY, FUNC) and not o.is_awaitable_coroutine:
            self.add('\n')
        if not self.is_top_level():
            self_inits = find_self_initializers(o)
            for init, value in self_inits:
                if init in self.method_names:
                    # Can't have both an attribute and a method/property with the same name.
                    continue
                init_code = self.get_init(init, value)
                if init_code:
                    self.add(init_code)
        # dump decorators, just before "def ..."
        for s in self._decorators:
            self.add(s)
        self.clear_decorators()
        self.add("%s%sdef %s(" % (self._indent, 'async ' if o.is_coroutine else '', o.name))
        self.record_name(o.name)
        # import ubelt as ub
        # if o.name == 'dzip':
        #     import xdev
        #     xdev.embed()

        def _hack_for_info(info):
            type_name = info['type']
            if type_name is not None:
                results = hacked_typing_info(type_name)
                for typing_arg in results['typing_imports']:
                    self.add_typing_import(typing_arg)
                for line in results['import_lines']:
                    self.add_import_line(line)
                info['type'] = results['type_name']

        name_to_parsed_docstr_info = {}
        return_parsed_docstr_info = None
        fullname = o.name
        if getattr(self, '_IN_CLASS', None) is not None:
            fullname = self._IN_CLASS + '.' + o.name

        curr = ub.import_module_from_name(self.module)
        # curr = sys.modules.get(self.module)
        # print('o.name = {!r}'.format(o.name))
        # print('fullname = {!r}'.format(fullname))
        for part in fullname.split('.'):
            # print('part = {!r}'.format(part))
            # print('curr = {!r}'.format(curr))
            curr = getattr(curr, part, None)
        # print('curr = {!r}'.format(curr))
        real_func = curr
        # print('real_func = {!r}'.format(real_func))
        # if o.name == 'dict_union':
        #     import xdev
        #     xdev.embed()
        if real_func is not None and real_func.__doc__ is not None:
            from mypy import fastparse
            from xdoctest.docstr import docscrape_google
            parsed_args = None
            # parsed_ret = None

            blocks = docscrape_google.split_google_docblocks(real_func.__doc__)
            # print('blocks = {}'.format(ub.repr2(blocks, nl=1)))
            for key, block in blocks:
                # print(f'key={key}')
                lines = block[0]
                if key == 'Returns':
                    # print(f'lines={lines}')
                    for retdict in docscrape_google.parse_google_retblock(lines):
                        # print(f'retdict={retdict}')
                        _hack_for_info(retdict)
                        return_parsed_docstr_info = (key, retdict['type'])
                    if return_parsed_docstr_info is None:
                        print('Warning: return block for {} might be malformed'.format(real_func))
                if key == 'Yields':
                    for retdict in docscrape_google.parse_google_retblock(lines):
                        _hack_for_info(retdict)
                        return_parsed_docstr_info = (key, retdict['type'])
                    if return_parsed_docstr_info is None:
                        print('Warning: return block for {} might be malformed'.format(real_func))
                if key == 'Args':
                    # hack for *args
                    lines = '\n'.join([line.lstrip('*') for line in lines.split('\n')])
                    # print('lines = {!r}'.format(lines))
                    parsed_args = list(docscrape_google.parse_google_argblock(lines))
                    for info in parsed_args:
                        _hack_for_info(info)
                        name = info['name'].replace('*', '')
                        name_to_parsed_docstr_info[name] = info

            parsed_rets = list(docscrape_google.parse_google_returns(real_func.__doc__))
            ret_infos = []
            for info in parsed_rets:
                try:
                    got = fastparse.parse_type_string(info['type'], 'Any', 0, 0)

                    ret_infos.append(got)
                except Exception:
                    pass

        # print('o = {!r}'.format(o))
        # print('o.arguments = {!r}'.format(o.arguments))
        args: List[str] = []
        for i, arg_ in enumerate(o.arguments):
            var = arg_.variable
            kind = arg_.kind
            name = var.name
            annotated_type = (o.unanalyzed_type.arg_types[i]
                              if isinstance(o.unanalyzed_type, CallableType) else None)

            if annotated_type is None:
                if name in name_to_parsed_docstr_info:
                    name = name.replace('*', '')
                    doc_type_str = name_to_parsed_docstr_info[name].get('type', None)
                    if doc_type_str is not None:
                        doc_type_str = doc_type_str.split(', default')[0]
                        # annotated_type = doc_type_str
                        # import mypy.types as mypy_types
                        from mypy import fastparse
                        # globals_ = {**mypy_types.__dict__}
                        try:
                            # # got = mypy_types.deserialize_type(doc_type_str)
                            # got = eval(doc_type_str, globals_)
                            # got = mypy_types.get_proper_type(got)
                            # got = mypy_types.Iterable
                            got = fastparse.parse_type_string(doc_type_str, 'Any', 0, 0)
                        except Exception as ex:
                            print('ex = {!r}'.format(ex))
                            print('Failed to parse doc_type_str = {!r}'.format(doc_type_str))
                        else:
                            annotated_type = got
                            # print('PARSED: annotated_type = {!r}'.format(annotated_type))
                        # print('annotated_type = {!r}'.format(annotated_type))

            # I think the name check is incorrect: there are libraries which
            # name their 0th argument other than self/cls
            is_self_arg = i == 0 and name == 'self'
            is_cls_arg = i == 0 and name == 'cls'
            annotation = ""
            if annotated_type and not is_self_arg and not is_cls_arg:
                # Luckily, an argument explicitly annotated with "Any" has
                # type "UnboundType" and will not match.
                if not isinstance(get_proper_type(annotated_type), AnyType):
                    annotation = ": {}".format(self.print_annotation(annotated_type))

            # xdev change, where we try to port the defaults over to the stubs
            # as well (otherwise they dont show up in the function help text)
            XDEV_KEEP_SOME_DEFAULTS = True

            if arg_.initializer:
                if kind.is_named() and not any(arg.startswith('*') for arg in args):
                    args.append('*')
                if not annotation:
                    typename = self.get_str_type_of_node(arg_.initializer, True, False)
                    if typename == '':
                        if XDEV_KEEP_SOME_DEFAULTS:
                            # TODO
                            annotation = '=...'
                        else:
                            annotation = '=...'
                    else:
                        annotation = ': {} = ...'.format(typename)
                else:
                    if XDEV_KEEP_SOME_DEFAULTS:
                        import mypy
                        # arg_.initializer.is_special_form
                        if isinstance(arg_.initializer, (mypy.nodes.IntExpr, mypy.nodes.FloatExpr)):
                            annotation += '={!r}'.format(arg_.initializer.value)
                        elif isinstance(arg_.initializer, mypy.nodes.StrExpr):
                            annotation += '={!r}'.format(arg_.initializer.value)
                        elif isinstance(arg_.initializer, mypy.nodes.NameExpr):
                            annotation += '={}'.format(arg_.initializer.name)
                        else:
                            # fallback, unhandled default
                            print(f'todo: Unhandled arg_.initializer={type(arg_.initializer)}')
                            annotation += '=...'
                    else:
                        annotation += ' = ...'
                arg = name + annotation
            elif kind == ARG_STAR:
                arg = '*%s%s' % (name, annotation)
            elif kind == ARG_STAR2:
                arg = '**%s%s' % (name, annotation)
            else:
                arg = name + annotation
            args.append(arg)
        retname = None
        if o.name != '__init__' and isinstance(o.unanalyzed_type, CallableType):
            if isinstance(get_proper_type(o.unanalyzed_type.ret_type), AnyType):
                # Luckily, a return type explicitly annotated with "Any" has
                # type "UnboundType" and will enter the else branch.
                retname = None  # implicit Any
            else:
                retname = self.print_annotation(o.unanalyzed_type.ret_type)
        elif isinstance(o, FuncDef) and (o.is_abstract or o.name in METHODS_WITH_RETURN_VALUE):
            # Always assume abstract methods return Any unless explicitly annotated. Also
            # some dunder methods should not have a None return type.
            retname = None  # implicit Any
        elif has_yield_expression(o):
            self.add_abc_import('Generator')
            yield_name = 'None'
            send_name = 'None'
            return_name = 'None'
            for expr, in_assignment in all_yield_expressions(o):
                if expr.expr is not None and not self.is_none_expr(expr.expr):
                    self.add_typing_import('Any')
                    yield_name = 'Any'
                if in_assignment:
                    self.add_typing_import('Any')
                    send_name = 'Any'
            if has_return_statement(o):
                self.add_typing_import('Any')
                return_name = 'Any'
            generator_name = self.typing_name('Generator')
            if return_parsed_docstr_info is not None:
                print(f'return_parsed_docstr_info={return_parsed_docstr_info}')
                yield_name = return_parsed_docstr_info[1]
            retname = f'{generator_name}[{yield_name}, {send_name}, {return_name}]'
            # print('o.name = {}'.format(ub.repr2(o.name, nl=1)))
            # print('retname = {!r}'.format(retname))
            # print('retfield = {!r}'.format(retfield))
        elif not has_return_statement(o) and not is_abstract:
            retname = 'None'

        if retname is None:
            if return_parsed_docstr_info is not None:
                retname = return_parsed_docstr_info[1]

        retfield = ''
        if retname is not None:
            retfield = ' -> ' + retname

        self.add(', '.join(args))
        self.add("){}: ...\n".format(retfield))
        self._state = FUNC

    def visit_class_def(self, o) -> None:
        self._IN_CLASS = o.name
        # print('o.name = {!r}'.format(o.name))
        ret = super().visit_class_def(o)
        self._IN_CLASS = None
        return ret


def modpath_coerce(modpath_coercable):
    """
    if modpath_coercable is a name, statically converts it to a path

    Args:
        modpath_coercable (str | PathLike | ModuleType):
            something we can extract a path to a module from.

    Returns:
        str : the coerced modpath

    Example:
        >>> from xdev.cli.docstr_stubgen import *  # NOQA
        >>> import xdev
        >>> modpath_coercable = xdev
        >>> modpath = modpath_coerce(modpath_coercable)
        >>> print(f'modpath={modpath}')
        >>> assert modpath_coerce(modpath) == modpath
        >>> assert modpath_coerce(xdev.__name__) == modpath
    """
    import ubelt as ub
    import types
    from os.path import exists
    import pathlib
    if isinstance(modpath_coercable, types.ModuleType):
        modpath = modpath_coercable.__file__
    elif isinstance(modpath_coercable, pathlib.Path):
        modpath = modpath_coercable
    elif isinstance(modpath_coercable, str):
        modpath = ub.modname_to_modpath(modpath_coercable)
        if modpath is None:
            if exists(modpath_coercable):
                modpath = modpath_coercable
            else:
                raise ValueError('Cannot find module={}'.format(modpath_coercable))
    else:
        raise TypeError('{}'.format(type(modpath_coercable)))
    modpath = ub.util_import.normalize_modpath(modpath)
    return modpath

if __name__ == '__main__':
    """
    CommandLine:
        python -m xdev.cli.gen_typed_stubs
    """
    from xdev.cli.main import DocstrStubgenCLI
    DocstrStubgenCLI.main()
