#!/usr/bin/env python3
import scriptconfig as scfg
import ubelt as ub


class PypackageSummaryCLI(scfg.DataConfig):
    """
    Summarize the complexity of a Python package.

    Related Work:

        https://pypi.org/project/radon/

        https://github.com/thebjorn/pydeps

        https://docs.python.org/3/library/modulefinder.html

    """
    __command__ = 'pypackage_summary'

    dpath = scfg.Value('.', type=str, help='Path to the Python module or package')
    # param1 = scfg.Value(None, help='param1')

    @classmethod
    def main(cls, argv=1, **kwargs):
        """
        Example:
            >>> # xdoctest: +SKIP
            >>> from xdev.cli.pypackage_summary import *  # NOQA
            >>> argv = 0
            >>> kwargs = dict()
            >>> cls = PypackageSummaryCLI
            >>> config = cls(**kwargs)
            >>> cls.main(argv=argv, **config)
        """
        import rich
        from rich.markup import escape
        config = cls.cli(argv=argv, data=kwargs, strict=True)
        rich.print('config = ' + escape(ub.urepr(config, nl=1)))

        from xdev.directory_walker import DirectoryWalker  # NOQA
        kwargs = ub.udict(config) & {
            'dpath',
            # 'exclude_dnames', 'exclude_fnames', 'include_dnames',
            # 'include_fnames', 'max_walk_depth', 'parse_content', 'max_files'
        }
        self = DirectoryWalker(**kwargs)
        self.build()
        # nxtxt_kwargs = {'max_depth': config['max_display_depth']}
        # nxtxt_kwargs = {}
        # self.write_report(**nxtxt_kwargs)

        jobs = self._parallel_process_files(parse_file_stats, 'Parse File Info')
        for fpath, result in jobs:
            node_data = self.graph.nodes[fpath]
            # node_data['stats'].update(result)
            node_data['pystats'] = result

        # self._accum_stats()
        all_imports = []
        all_nested_imports = []
        for node, data in self.graph.nodes(data=True):
            pystats = data.get('pystats', {})
            if pystats:
                all_imports.extend(pystats['import'])
                all_nested_imports.extend(pystats['nested_import'])

        import sys
        known_module_groups = {}
        known_module_groups['stdlib'] = sys.stdlib_module_names
        known_module_groups['scientific'] = {
            'pandas', 'numpy', 'scipy', 'shapely', 'matplotlib',
        }
        known_module_groups['kitware'] = {
            'kwcoco', 'kwarray', 'kwplot', 'kwimage',
            'delayed_image', 'scriptconfig'
        }
        known_module_groups['ubiquitous'] = {
            'rich', 'dateutil', 'networkx', 'more_itertools'
        }

        known_module_groups['ubiquitous2'] = {
            'aiohttp', 'ansible', 'arrow', 'attrs', 'awscli', 'azure-cli',
            'beautifulsoup4', 'black', 'boto3', 'botocore', 'celery', 'click',
            'colorama', 'concurrent.futures', 'coverage', 'cryptography',
            'dateutil', 'delegator.py', 'django', 'docker', 'elasticsearch',
            'fabric', 'factory-boy', 'faker', 'fastapi', 'feedparser', 'flask',
            'freezegun', 'google-cloud-sdk', 'google-cloud-storage', 'grpcio',
            'gunicorn', 'helm', 'html5lib', 'httpie', 'httpx', 'hypothesis',
            'invoke', 'isort', 'jinja2', 'kombu', 'kubernetes', 'libcloud',
            'loguru', 'lxml', 'markdown', 'mock', 'more_itertools', 'mypy',
            'nats', 'networkx', 'oauthlib', 'openpyxl', 'openstacksdk',
            'paramiko', 'pexpect', 'pika', 'pillow', 'pip', 'plumbum', 'protobuf',
            'psutil', 'pulumi', 'pydantic', 'pygments', 'pyinstaller', 'pyjwt',
            'pymongo', 'pyodbc', 'pyopenssl', 'pytest', 'pytest-cov',
            'python-dateutil', 'python-dotenv', 'pytz', 'pyyaml', 'pyzmq',
            'redis', 'requests', 'requests-oauthlib', 'responses', 'rich', 'salt',
            'scp', 'sentry-sdk', 'setuptools', 'sh', 'six', 'sqlalchemy',
            'sshtunnel', 'starlette', 'structlog', 'subprocess32', 'terraform',
            'tornado', 'tqdm', 'typing_extensions', 'tzlocal', 'urllib3',
            'uvicorn', 'uvloop', 'vcrpy', 'virtualenv', 'websockets', 'wheel',
            'xlrd', 'xlwt'
        }

        # From deep seek, might not be quite right.
        known_module_groups['top_100_third_party_libraries'] = [
            # Web Development
            'flask', 'django', 'fastapi', 'starlette', 'uvicorn', 'gunicorn',
            'requests', 'aiohttp', 'httpx', 'websockets', 'bottle', 'sanic',
            'tornado', 'pyramid', 'cherrypy', 'falcon', 'quart', 'socketserver',

            # Data Science and Machine Learning
            'numpy', 'pandas', 'scipy', 'matplotlib', 'seaborn', 'plotly',
            'bokeh', 'scikit-learn', 'tensorflow', 'keras', 'pytorch',
            'pytorch-lightning', 'xgboost', 'lightgbm', 'catboost', 'statsmodels',
            'opencv-python', 'pillow', 'h5py', 'theano', 'nltk', 'spacy',
            'gensim', 'transformers', 'datasets', 'torchvision', 'torchaudio',

            # Data Visualization
            'plotly', 'bokeh', 'altair', 'pygal', 'folium', 'geopandas',
            'dash', 'streamlit', 'panel', 'holoviews',

            # Database and ORM
            'sqlalchemy', 'psycopg2', 'mysql-connector-python', 'pymysql',
            'sqlite3', 'redis', 'pymongo', 'cassandra-driver', 'elasticsearch',
            'influxdb', 'neo4j', 'peewee', 'pony', 'tortoise-orm',

            # Testing and Debugging
            'pytest', 'unittest', 'nose', 'coverage', 'pytest-cov', 'hypothesis',
            'factory-boy', 'freezegun', 'mock', 'responses', 'vcrpy', 'sentry-sdk',
            'loguru', 'structlog', 'line-profiler', 'memory-profiler',

            # Automation and Scripting
            'fabric', 'invoke', 'paramiko', 'ansible', 'salt', 'sh', 'plumbum',
            'pexpect', 'subprocess32', 'click', 'fire', 'typer', 'argparse',
            'docopt', 'cement', 'cliff',

            # DevOps and Cloud
            'docker', 'kubernetes', 'helm', 'terraform', 'pulumi', 'boto3',
            'awscli', 'google-cloud-storage', 'azure-cli', 'openstacksdk',
            'libcloud', 'paramiko', 'scp', 'sshtunnel', 'pyopenssl',

            # Utilities and General Purpose
            'rich', 'tqdm', 'pyyaml', 'toml', 'python-dotenv', 'arrow',
            'python-dateutil', 'pytz', 'tzlocal', 'cryptography', 'pyjwt',
            'oauthlib', 'requests-oauthlib', 'urllib3', 'beautifulsoup4',
            'lxml', 'html5lib', 'feedparser', 'markdown', 'pygments',
            'six', 'attrs', 'pydantic', 'dataclasses', 'typing-extensions',
            'mypy', 'black', 'isort', 'flake8', 'autopep8', 'yapf', 'bandit',
            'safety', 'pip-tools', 'poetry', 'pipenv', 'setuptools', 'wheel',
            'virtualenv', 'conda', 'pyinstaller', 'cx-freeze', 'nuitka',
        ]

        simple_imports = [s.split('.')[0] for s in all_imports]
        simple_import_hist = ub.udict(ub.dict_hist(simple_imports))
        simple_import_hist = simple_import_hist.sorted_values()
        ungrouped = ub.udict(simple_import_hist)
        hist_groups = {}
        for key, modnames in known_module_groups.items():
            hist_groups[key] = ungrouped & modnames
            ungrouped -= modnames
        hist_groups['ungrouped'] = ungrouped
        print(f'hist_groups = {ub.urepr(hist_groups, nl=2)}')

        simple_nested_imports = [s.split('.')[0] for s in all_nested_imports]
        simple_nested_import_hist = ub.udict(ub.dict_hist(simple_nested_imports))
        simple_nested_import_hist = simple_nested_import_hist.sorted_values()
        ungrouped = ub.udict(simple_nested_import_hist)
        nested_hist_groups = {}
        for key, modnames in known_module_groups.items():
            nested_hist_groups[key] = ungrouped & modnames
            ungrouped -= modnames
        nested_hist_groups['ungrouped'] = ungrouped
        print(f'nested_hist_groups = {ub.urepr(nested_hist_groups, nl=2)}')

        ungrouped

        std_simple_import_hist = ub.udict(simple_import_hist) & sys.stdlib_module_names
        tpl_simple_import_hist = ub.udict(simple_import_hist) - sys.stdlib_module_names
        print(f'std_simple_import_hist = {ub.urepr(std_simple_import_hist, nl=1)}')
        print(f'tpl_simple_import_hist = {ub.urepr(tpl_simple_import_hist, nl=1)}')

        print(f'simple_import_hist = {ub.urepr(simple_import_hist, nl=1)}')

        import_hist = ub.udict(ub.dict_hist(all_imports))
        import_hist = import_hist.sorted_values()
        print(f'import_hist = {ub.urepr(import_hist, nl=1)}')


def parse_file_stats(fpath):
    """
    Ignore:
        import sys, ubelt
        sys.path.append(ubelt.expandpath('~/code/xdev'))
        from xdev.cli.pypackage_summary import *  # NOQA
        from xdev.cli import pypackage_summary
        fpath = pypackage_summary.__file__
        stats = parse_file_stats(fpath)
        print(f'stats = {ub.urepr(stats, nl=1)}')
    """
    stats = {}
    if not fpath.endswith('.py'):
        return stats

    from xdev import static_analysis
    analyzer = static_analysis.CodeAnalyzer.parse_file(fpath)

    stats = ub.ddict(list)
    for node, node_data in analyzer.graph.nodes(data=True):
        nested = len(analyzer.graph.pred[node]) > 0
        if nested:
            key = f'nested_{node_data["type"]}'
        else:
            key = f'{node_data["type"]}'
        stats[key].append(node)
    # stats['imports'] = analyzer.imports
    # stats['num_classes'] = len(analyzer.classes)
    # stats['num_functions'] = len(analyzer.functions)
    return stats

__cli__ = PypackageSummaryCLI


if __name__ == '__main__':
    """

    CommandLine:
        python ~/code/xdev/xdev/cli/pypackage_summary.py
        python -m xdev.cli.pypackage_summary
    """
    __cli__.main()
