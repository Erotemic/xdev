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

    xdev doctypes --module=xdev
    python ~/code/xdev/xdev/cli/docstr_stubgen.py

    See:
    ~/code/mypy/mypy/stubgen.py

    # Run mypy to check that type annotations are correct
    mypy ubelt


Ignore:
    # Can we use liberator to help automatically extract some of these imports?

    # The idea is check if the name is defined, and if not try to define it.
    # Very similar to how liberator works.
    import liberator

    from kwcoco.util.delayed_poc import delayed_nodes
    modpath = delayed_nodes.__file__
    name = 'DelayedVisionOperation'
    lib = liberator.Liberator()
    lib.add_static(name, modpath)
    print(lib.current_sourcecode())
"""

try:
    from mypy.stubgen import (StubGenerator, find_self_initializers, FUNC, EMPTY,
                              METHODS_WITH_RETURN_VALUE,)
    from mypy.nodes import (
        # Expression, IntExpr, UnaryExpr, StrExpr, BytesExpr, NameExpr, FloatExpr, MemberExpr,
        # TupleExpr, ListExpr, ComparisonExpr, CallExpr, IndexExpr, EllipsisExpr,
        # ClassDef, MypyFile, Decorator, AssignmentStmt, TypeInfo,
        # IfStmt, ImportAll, ImportFrom, Import,
        IS_ABSTRACT,
        FuncDef,
        # FuncBase, Block,
        # Statement, OverloadedFuncDef, ARG_POS,
        ARG_STAR, ARG_STAR2,
        # ARG_NAMED,
    )
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
except Exception:
    StubGenerator = object
    FuncDef = None
    METHODS_WITH_RETURN_VALUE = []

import sys
from typing import (List, Dict, Optional)
# from mypy.stubgenc import generate_stub_for_c_module
# from mypy.stubutil import (
#     default_py2_interpreter, CantImport, generate_guarded,
#     walk_packages, find_module_path_and_all_py2, find_module_path_and_all_py3,
#     report_missing, fail_missing, remove_misplaced_type_comments, common_dir_prefix
# )
import ubelt as ub


Stub = ...  # hack for mypy. Not sure why it is generated in the first place.


def _hack_away_compiled_mypy():
    """
    Worked with: mypy-0.970+dev.ddbea6988c0913c70ed16cd2fda6064e301b4b63
    """
    # This doesn't seem to work. The only thing that has worked so far is a
    # custom checkout and developer install. Not sure why that is the case.
    modpath = ub.Path(ub.modname_to_modpath('mypy'))
    print(f'modpath={modpath}')
    compiled_modules = list(modpath.glob('*.so'))
    print(f'compiled_modules={compiled_modules}')
    for p in compiled_modules:
        p.delete()


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

    CommandLine:
        xdoctest -m /home/joncrall/code/xdev/xdev/cli/docstr_stubgen.py generate_typed_stubs --hacked

    Example:
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
        # This was done with mypy version:
        # 0.920+dev.5c4aea39ab6a14eeef85cc849d6057bebf2147a3

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
    # from os.path import join
    import ubelt as ub

    # modname = 'scriptconfig'
    # module = ub.import_module_from_name(modname)
    # modpath = ub.Path(module.__file__).parent

    # for p in pathlib.Path(modpath).glob('*.pyi'):
    #     p.unlink()
    modpath = ub.Path(modpath)

    files = list(static_analysis.package_modpaths(
        modpath, recursive=True, with_libs=0, with_pkg=0))

    # print('files = {}'.format(ub.repr2(files, nl=1)))
    # files = [f for f in files if 'deprecated' not in f]
    # files = [join(ubelt_dpath, 'util_dict.py')]

    if modpath.is_file():
        output_dir = modpath.parent.parent
    else:
        output_dir = modpath.parent
    # print(f'output_dir={output_dir}')

    options = stubgen.Options(
        pyversion=defaults.PYTHON3_VERSION,
        no_import=True,
        doc_dir='',
        search_path=[],
        interpreter=sys.executable,
        ignore_errors=False,
        parse_only=True,
        include_private=False,
        output_dir=os.fspath(output_dir),
        modules=[],
        packages=[],
        files=[os.fspath(p) for p in files],
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

    verbose = 3

    for mod in py_modules:
        assert mod.path is not None, "Not found module was not skipped"
        # print(f'mod.module={mod.module}')
        # import xdev
        # xdev.embed()
        target = mod.path + 'i'
        # target = mod.module.replace('.', '/')
        # if os.path.basename(mod.path) == '__init__.py':
        #     target += '/__init__.pyi'
        # else:
        #     target += '.pyi'
        # target = join(options.output_dir, target)
        if verbose > 1:
            print(f'target={target}')
        # print(f'options.output_dir={options.output_dir}')
        # print(f'target={target}')
        files.append(target)
        with stubgen.generate_guarded(mod.module, target, options.ignore_errors, options.verbose):
            stubgen.generate_stub_from_ast(mod, target, options.parse_only,
                                           # options.pyversion,
                                           options.include_private,
                                           options.export_less)

            gen = ExtendedStubGenerator(mod.runtime_all,
                                        # pyversion=options.pyversion,
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
                'DT', 'KT', 'VT', 'T', 'T1', 'T2', 'T3', 'T4', 'T5',
                # Hack for kwcoco
                'ObjT',
            }
            for type_var_name in sorted(set(gen.import_tracker.required_names) & set(known_one_letter_types)):
                gen.add_typing_import('TypeVar')
                # gen.add_import_line('from typing import {}\n'.format('TypeVar'))
                gen._output = ['{} = TypeVar("{}")\n'.format(type_var_name, type_var_name)] + gen._output

            custom_types = {'Hasher', 'Sliceable'}
            for type_var_name in sorted(set(gen.import_tracker.required_names) & set(custom_types)):
                gen.add_typing_import('TypeVar')
                # gen.add_import_line('from typing import {}\n'.format('TypeVar'))
                gen._output = ['{} = TypeVar("{}")\n'.format(type_var_name, type_var_name)] + gen._output

            # Check for a special user header variable we pull in verbatim
            import mypy
            user_header = None
            for d in mod.ast.defs:
                if isinstance(d, mypy.nodes.AssignmentStmt):
                    try:
                        if len(d.lvalues) == 1 and d.lvalues[0].name == '__docstubs__':
                            user_header = d.rvalue.value
                    except AttributeError:
                        ...

            if user_header is not None:
                gen._output = [user_header] + gen._output

            # Hack for specific module
            # if mod.path.endswith('coco_objects1d.py'):
            #     import xdev
            #     xdev.embed()

            text = ''.join(gen.output())
            text = postprocess_hacks(text, mod)

            # Write output to file.
            # subdir = ub.Path(target).parent
            # if subdir and not os.path.isdir(subdir):
            #     os.makedirs(subdir)
            generated[target] = text
            if verbose > 1:
                print(f'generated target={target}')
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

    # FIXME: does ubelt still need this?
    if mod.path.endswith('util_dict.py'):
        # hack for util_dict
        text = 'import sys\n' + text

    if mod.path.endswith('util_path.py'):
        # hack for forward reference
        text = text.replace(' -> Path:', " -> 'Path':")
        text = text.replace('class Path(_PathBase)', "class Path")

    # Not sure why this happens
    text = text.replace('from io import io\n', '')
    text = text.replace('from datetime import datetime\n', '')

    # Ubelt hack
    if 'DictBase' in text:
        # Hack for util_dict
        text = text.replace('DictBase = OrderedDict\n', '')
        text = text.replace('DictBase = dict\n', 'DictBase = OrderedDict if sys.version_info[0:2] <= (3, 6) else dict')

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
    names = list(names)
    # https://github.com/hugovk/top-pypi-packages
    names.extend([
        'numpy', 'torch', 'pandas', 'h5py', 'networkx', 'torch.nn',

        'shapely',

        # Hack: determine this from env
        'kwcoco',
        'kwimage',
        'kwarray',

        'xdoctest',
        'xdoctest.doctest_part',

        'scipy', 'sklearn', 'matplotlib', 'seaborn', 'attrs',

        'keras', 'ujson', 'black', 'mypy', 'simplejson', 'parso', 'tensorflow',
        'cython', 'git', 'openpyxl',

        'concurrent.futures',
        'hashlib._hashlib',

        'kwcoco.util.delayed_poc.delayed_nodes',
        'kwcoco.coco_objects1d',
        'kwcoco.metrics.confusion_measures',
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
        'aiobotocore', 'jsonschema', 'lxml', 'pytest', '_pytest', 'beautifulsoup4',
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
        {'modname': 'pandas', 'alias': ['pd']},
        {'modname': 'matplotlib', 'alias': ['mpl']},
        {'modname': 'seaborn', 'alias': ['sns']},
        # I'm biased, what can I say?
        {'modname': 'ubelt', 'alias': ['ub']},
    ]
    return aliases


@ub.memoize
def common_unreferenced():

    modname_to_refs = {
        'numpy': [
            'ndarray',
        ],

        'numbers': [
            'Number', 'Real', 'Integral', 'Rational', 'Complex',
        ],

        'numpy.random': [
            'RandomState',
        ],

        # https://github.com/ramonhagenaars/nptyping/blob/master/USERDOCS.md#Shape-expressions
        'numpy.typing': [
            'ArrayLike',
        ],

        'torch': [
            'Tensor',
        ],

        'typing': [
            'Callable',
            'Any',
            'IO',
        ],

        'collections': [
            'OrderedDict', 'defaultdict'
        ]
    }

    try:
        import nptyping
        modname_to_refs['nptyping'] = ['NDArray', 'Shape', 'DType'] + list(set(nptyping.typing_.dtype_per_name.keys()) - {'Number'})
    except ModuleNotFoundError:
        pass

    unref = [
        {'name': 'datetime', 'modname': 'datetime'},
        {'name': 'io', 'modname': 'io'},
        {'name': 'PathLike', 'modname': 'os'},
        {'name': 'ModuleType', 'modname': 'types'},
        {'name': 'FrameType', 'modname': 'types'},
        {'name': 'NoParam', 'modname': 'ubelt.util_const'},
        {'name': '_NoParamType', 'modname': 'ubelt.util_const'},
        {'name': 'NoParamType', 'modname': 'ubelt.util_const'},
        {'name': 'GeometricTransform', 'modname': 'skimage.transform._geometric'},
    ]
    for modname, refs in modname_to_refs.items():
        for ref in refs:
            unref.append({'name': ref, 'modname': modname})
    return unref


def hacked_typing_info(type_name):
    result = {
        'import_lines': [],
        'typing_imports': [],
        'hacks': [],
    }
    add_import_line = result['import_lines'].append
    add_typing_import = result['typing_imports'].append

    # TODO: do a real parsing of the type names with a node transformer

    if 'callable' in type_name:
        # TODO: generalize, allow the "callable" func to be transformed
        # into the type if given in the docstring
        type_name = type_name.replace('callable', 'Callable')

    import re
    type_name = re.sub(r'\bor\b', '|', type_name)

    if type_name == '?':
        type_name = 'Any'

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

    if 'Float32' in type_name:
        add_import_line('from nptyping import {}\n'.format('Float32'))

    if 'Int64' in type_name:
        add_import_line('from nptyping import {}\n'.format('Int64'))

    if 'Shape' in type_name:
        add_import_line('from nptyping import {}\n'.format('Shape'))

    if 'UInt8' in type_name:
        add_import_line('from nptyping import {}\n'.format('UInt8'))

    if 'Bool' in type_name:
        add_import_line('from nptyping import {}\n'.format('Bool'))

    if 'Integer' in type_name:
        add_import_line('from nptyping import {}\n'.format('Integer'))

    if 'skimage.transform.AffineTransform' == type_name:
        add_import_line('import skimage.transform\n')

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

    if 1:
        # HACKS
        # if type_name == 'Sliceable':
        #     result['hacks'].append('sliceable')
        hack_to_any = {
            'imgaug.augmenters.Augmenter',
            'imgaug.KeypointsOnImage',
            'ia.BoundingBoxesOnImage',
            'Sliceable',
            'Augmenter',
        }
        for h in hack_to_any:
            if h in type_name:
                add_import_line('from typing import {}\n'.format('Any'))
                break

        for h in hack_to_any:
            if h in type_name:
                type_name = type_name.replace(h, 'Any')

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

    def _hack_for_info(self, info):
        type_name = info['type']
        if type_name is not None:
            results = hacked_typing_info(type_name)
            for typing_arg in results['typing_imports']:
                self.add_typing_import(typing_arg)
            for line in results['import_lines']:
                self.add_import_line(line)
            for hack in results['hacks']:
                if hack == 'sliceable':
                    hacked = ub.codeblock(
                        '''
                        from typing import Any
                        from typing_extensions import Protocol

                        class Sliceable(Protocol):
                            def __getitem__(self: 'Sliceable', key: Any) -> Any:
                                ...
                        ''') + '\n'

                    self.add_import_line(hacked)
                else:
                    raise NotImplementedError(hack)
            info['type'] = results['type_name']

    def visit_func_def(self, o: FuncDef, is_abstract: bool = False,
                       is_overload: bool = False) -> None:

        from mypy import fastparse
        DEBUG = 0
        if DEBUG:
            print('o.name = {!r}'.format(o.name))

        import ubelt as ub
        # Parse extra information out of the docstring
        name_to_parsed_docstr_info = {}
        return_parsed_docstr_info = None
        fullname = o.name
        if getattr(self, '_IN_CLASS', None) is not None:
            fullname = self._IN_CLASS + '.' + o.name
        parent_mod = ub.import_module_from_name(self.module)
        if DEBUG:
            print('fullname = {!r}'.format(fullname))
        curr = parent_mod
        for part in fullname.split('.'):
            curr = getattr(curr, part, None)
        real_func = curr
        force_yield = False
        if real_func is not None and real_func.__doc__ is not None:
            from xdoctest.docstr import docscrape_google
            parsed_args = None
            # parsed_ret = None

            blocks = docscrape_google.split_google_docblocks(real_func.__doc__)
            # print('blocks = {}'.format(ub.repr2(blocks, nl=1)))
            for key, block in blocks:
                # print(f'block key={key}')
                lines = block[0]
                if key == 'Returns':
                    # print(f'lines={lines}')
                    for retdict in docscrape_google.parse_google_retblock(lines):
                        # print(f'retdict={retdict}')
                        self._hack_for_info(retdict)
                        return_parsed_docstr_info = (key, retdict['type'])
                    if return_parsed_docstr_info is None:
                        print('Warning: return block for {} might be malformed'.format(real_func))
                if key == 'Yields':
                    for retdict in docscrape_google.parse_google_retblock(lines):
                        self._hack_for_info(retdict)
                        return_parsed_docstr_info = (key, retdict['type'])
                        force_yield = True
                    if return_parsed_docstr_info is None:
                        print('Warning: return block for {} might be malformed'.format(real_func))
                if key == 'Args':
                    # hack for *args
                    lines = '\n'.join([line.lstrip('*') for line in lines.split('\n')])
                    # print('lines = {!r}'.format(lines))
                    parsed_args = list(docscrape_google.parse_google_argblock(lines))
                    for info in parsed_args:
                        self._hack_for_info(info)
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

        if (self.is_private_name(o.name, o.fullname)
                or self.is_not_in_all(o.name)
                or (self.is_recorded_name(o.name) and not is_overload)):
            self.clear_decorators()
            return
        if not self._indent and self._state not in (EMPTY, FUNC) and not o.is_awaitable_coroutine:
            self.add('\n')
        if not self.is_top_level():
            # This handles class-level attributes.
            # We assume we already parsed out the Attributes section
            # when we visited the class, so now we have to use that info here.
            self_inits = find_self_initializers(o)

            self_inits_lut = dict(self_inits)
            # The docstring is the single source of truth, respect it.
            pseudo_inits = []
            if self._docstring_class_attr_infos is None:
                _docstring_class_attr_infos = {}
            else:
                _docstring_class_attr_infos = self._docstring_class_attr_infos

            for name, info in _docstring_class_attr_infos.items():
                if name in self_inits_lut:
                    pseudo_inits.append((name, self_inits_lut[name]))
                else:
                    pseudo_inits.append((name, None))
            # Maybe we shouldnt do this if there is an Attributes section?
            pseudo_inits.extend(list(ub.dict_diff(self_inits_lut, _docstring_class_attr_infos).items()))

            for init, value in pseudo_inits:
                if init in self.method_names:
                    # Can't have both an attribute and a method/property with the same name.
                    continue

                # Use the init docstring to get a hint for the type
                annotation = None
                # The class attributes should override the init signature
                if init in _docstring_class_attr_infos:
                    typename = _docstring_class_attr_infos[init]['type']
                    try:
                        annotation = fastparse.parse_type_string(typename, 'Any', 0, 0)
                    except Exception:
                        print(f'FAILED ON typename={typename} for {init}')
                        annotation = None
                elif init in name_to_parsed_docstr_info:
                    typename = name_to_parsed_docstr_info[init]['type']
                    try:
                        annotation = fastparse.parse_type_string(typename, 'Any', 0, 0)
                    except Exception:
                        print(f'FAILED ON typename={typename} for {init}')
                        annotation = None
                    # import xdev
                    # xdev.embed()
                init_code = self.get_init(init, value, annotation=annotation)
                if init_code:
                    self.add(init_code)
        # dump decorators, just before "def ..."
        for s in self._decorators:
            self.add(s)
        self.clear_decorators()
        self.add("%s%sdef %s(" % (self._indent, 'async ' if o.is_coroutine else '', o.name))
        self.record_name(o.name)

        DEVELOPER_DEBUGGING = 0
        if DEVELOPER_DEBUGGING:
            # Set this to the name function we are going to debug
            function_to_debug = 'show_chipmatch2'
            print(f'o.name={o.name}')
            if o.name == function_to_debug:
                print('o = {!r}'.format(o))
                print('o.arguments = {!r}'.format(o.arguments))
                import xdev
                xdev.embed()

        # ------------------------------------------
        # Enrich doctypes with inferable information
        # ------------------------------------------
        # Do a quick initial pass to check to compare the parsed docstr types
        # to default values if they exist. If the default value is something
        # like None, but the existing type annotation isn't marked as optional
        # we can insert that for the user.
        name_to_argument = {arg_.variable.name: arg_ for arg_ in o.arguments}
        check_names = set(name_to_argument) & set(name_to_parsed_docstr_info)
        for name in check_names:
            arg_ = name_to_argument[name]
            if arg_.initializer is not None:
                # TODO: find a better way of checking if the default value
                # matches the type of the given doctype and extend the
                # doctype if needbe. For now we are hacking it to
                # handle None specificaly.
                if hasattr(arg_.initializer, 'name') and arg_.initializer.name == 'None':
                    info = name_to_parsed_docstr_info[name]
                    doctype_str = info['type'].replace(' ', '')
                    if all(n not in doctype_str for n in {'None', 'Optional'}):
                        info['type'] = info['type'] + ' | None'
                        self.add_typing_import('Union')
        # ------------------------------------------

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
                        # globals_ = {**mypy_types.__dict__}
                        try:
                            got = fastparse.parse_type_string(doc_type_str, 'Any', 0, 0)
                        except Exception as ex:
                            print('ex = {!r}'.format(ex))
                            print('Failed to parse doc_type_str = {!r}'.format(doc_type_str))
                        else:
                            annotated_type = got
                        #     print('PARSED: annotated_type = {!r}'.format(annotated_type))
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
        elif o.abstract_status == IS_ABSTRACT or o.name in METHODS_WITH_RETURN_VALUE:
            # Always assume abstract methods return Any unless explicitly annotated. Also
            # some dunder methods should not have a None return type.
            retname = None  # implicit Any
        elif has_yield_expression(o) or force_yield:
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
                yield_name = return_parsed_docstr_info[1]
            retname = f'{generator_name}[{yield_name}, {send_name}, {return_name}]'
            # print('o.name = {}'.format(ub.repr2(o.name, nl=1)))
            # print('retname = {!r}'.format(retname))
            # print('retfield = {!r}'.format(retfield))
        elif not has_return_statement(o) and not is_abstract:
            retname = 'None'

        # print('---')
        # print(f'retname={retname!r}')
        # print(f'return_parsed_docstr_info={return_parsed_docstr_info}')
        if retname is None or retname == 'None':
            # print('need retname')
            if return_parsed_docstr_info is not None:
                # print('not none')
                retname = return_parsed_docstr_info[1]
        # print('after')
        # print(f'retname={retname}')

        retfield = ''
        if retname is not None:
            retfield = ' -> ' + retname
        # print(f'retfield={retfield}')

        self.add(', '.join(args))
        self.add("){}: ...\n".format(retfield))
        self._state = FUNC

    def visit_class_def(self, o) -> None:
        # from mypy.stubgen import (
        #     find_method_names, NameExpr, MemberExpr, AliasPrinter, EMPTY_CLASS,
        #     CLASS)
        self._IN_CLASS = o.name

        # Register the class attribute information that we found here
        # We will need to use it in the init method parsing
        self._docstring_class_attr_infos = {}
        parent_mod = ub.import_module_from_name(self.module)

        # Classes we will not make stubs for. TODO: generalize.
        blocklist = {
            '_RationalNDArray',
        }
        if o.name in blocklist:
            return

        real_class = getattr(parent_mod, o.name, None)
        if real_class is not None and real_class.__doc__ is not None:
            from xdoctest.docstr import docscrape_google
            blocks = docscrape_google.split_google_docblocks(real_class.__doc__)
            for key, block in blocks:
                lines = block[0]
                if key == 'Attributes':
                    lines = '\n'.join([line.lstrip('*') for line in lines.split('\n')])
                    parsed_args = list(docscrape_google.parse_google_argblock(lines))
                    for info in parsed_args:
                        self._hack_for_info(info)
                        name = info['name'].replace('*', '')
                        self._docstring_class_attr_infos[name] = info
        ret = super().visit_class_def(o)
        self._docstring_class_attr_infos = None
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
        >>> # xdoctest: +SKIP
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
    from xdev.cli.docstr_stubgen import DocstrStubgenCLI
    DocstrStubgenCLI.main()
