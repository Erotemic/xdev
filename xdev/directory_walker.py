import os
import rich
import ubelt as ub
import networkx as nx
from xdev.patterns import MultiPattern
from progiter.manager import ProgressManager


STAT_COLUMN_ORDER = [
    'files',
    'main_code',
    'main_comments',
    'size',
    'test_code',
    'test_comments',
    'total',
]


def _order_columns(df, extra_last=('name',)):
    """Keep dirstats tables compact and stable."""
    existing = list(df.columns)
    preferred = [c for c in STAT_COLUMN_ORDER if c in existing]
    extra_last = [c for c in extra_last if c in existing]
    middle = [c for c in existing if c not in preferred and c not in extra_last]
    return df[preferred + middle + extra_last]


def _stats_total(stats):
    """Total logical text lines from a node stats dict."""
    return sum(v for k, v in stats.items() if k.endswith('.total') or k == 'total')


class DirectoryWalker:
    """
    Configurable directory walker that can explore a directory
    and report information about its contents in a concise manner.

    Options will impact how long this process takes based on how much data /
    metadata we need to parse out of the filesystem.

    Ignore:
        >>> from xdev.directory_walker import *  # NOQA
        >>> self = DirectoryWalker('.', exclude_dnames=['.*'])
        >>> self._walk()
        >>> self._update_labels()
        >>> self.write_network_text()
    """

    def __init__(self,
                 dpath,
                 exclude_dnames=None,
                 exclude_fnames=None,
                 include_dnames=None,
                 include_fnames=None,
                 max_walk_depth=None,
                 max_files=None,
                 parse_content=False,
                 python=False,
                 rust=False,
                 show_progress=True,
                 ignore_empty_dirs=False,
                 sort=False,
                 fs=None,
                 **kwargs):
        """
        Args:
            dpath (str | PathLike): the path to walk

            exclude_dnames (Coercable[MultiPattern]):
                blocks directory names matching this pattern

            exclude_fnames (Coercable[MultiPattern]):
                blocks file names matching this pattern

            include_dnames (Coercable[MultiPattern]):
                if specified, excludes directories that do NOT match this pattern.

            include_fnames (Coercable[MultiPattern]):
                if specified, excludes files that do NOT match this pattern.

            max_files (None | int):
                ignore all files in directories with more than this number.

            max_walk_depth (None | int):
                how far to recurse

            parse_content (bool):
                if True, count total lines for text-like files.

            python (bool):
                if True, enable Python code/doc line analysis.

            rust (bool):
                if True, enable Rust code/comment line analysis, with test splitting.

            sort (bool):
                if True, sort files and directories before adding them to the
                graph.

            fs (fsspec.spec.AbstractFileSystem):
                experimental: an fsspec filesystem

            **kwargs : passed to label options
        """
        if 'block_fnames' in kwargs:
            ub.schedule_deprecation(
                'xdev', 'DirectoryWalker block_fnames', 'arg',
                migration='Use exclude_fnames instead',
                deprecate='now',
            )
            if exclude_fnames is not None:
                raise ValueError('mutex with block_fnames')
            exclude_fnames = kwargs.pop('block_fnames')
        if 'block_dnames' in kwargs:
            ub.schedule_deprecation(
                'xdev', 'DirectoryWalker block_dnames', 'arg',
                migration='Use exclude_dnames instead',
                deprecate='now',
            )
            if exclude_dnames is not None:
                raise ValueError('mutex with block_dnames')
            exclude_dnames = kwargs.pop('block_dnames')

        self.dpath = ub.Path(dpath).absolute()
        self.exclude_fnames = _null_coerce(MultiPattern, exclude_fnames)
        self.exclude_dnames = _null_coerce(MultiPattern, exclude_dnames)
        self.include_fnames = _null_coerce(MultiPattern, include_fnames)
        self.include_dnames = _null_coerce(MultiPattern, include_dnames)
        self.max_walk_depth = max_walk_depth
        self.parse_content = parse_content
        self.python = python
        self.rust = rust
        self.max_files = max_files
        self.show_progress = show_progress
        self.ignore_empty_dirs = ignore_empty_dirs
        self.sort = sort

        kwargs = ub.udict(kwargs)

        self.label_options = {
            'abs_root_label': True,
            'pathstyle': 'name',
            'show_nfiles': 'auto',
            'show_types': False,
            'colors': True,
        }
        self.label_options.update(kwargs & self.label_options)
        kwargs -= self.label_options

        if kwargs:
            raise ValueError(f'Unhandled kwargs {kwargs}')

        self.fs = fs
        self.graph = None
        self._topo_order = None
        self._type_to_path = {}

    @property
    def root(self):
        """
        Alias for ``self.dpath``
        """
        return self.dpath

    def write_network_text(self, **kwargs):
        nx.write_network_text(self.graph, rich.print, end='', **kwargs)


    def _stats_table_for_node(self, node, humanize=False):
        """
        Return an extension-by-kind stats table for one graph node.

        The table is intentionally compact and uses the same column naming
        convention as the CLI display: ``main_*`` / ``test_*`` / ``total``.
        """
        import pandas as pd  # type: ignore

        node_data = self.graph.nodes[node]  # type: ignore
        stats = node_data.get('stats', {})
        stat_rows = []
        for key, value in stats.items():
            ext, kind = key.split('.', 1)
            if not ext:
                ext = '*null*'
            stat_rows.append({'ext': ext, 'kind': kind, 'value': value})

        if stat_rows:
            table = pd.DataFrame(stat_rows)
            piv = table.pivot_table(
                index='ext', columns='kind', values='value', aggfunc='sum', fill_value=0)
            if 'size' in piv.columns:
                piv = piv.sort_values('size')
        else:
            piv = pd.DataFrame(
                [],
                index=pd.Index([], name='ext'),
                columns=pd.Index(['files', 'size'], name='kind'),
            )

        if len(piv):
            totals = piv.sum(axis=0)
        else:
            totals = pd.Series({'files': 0, 'size': 0})
        piv.loc['∑ total'] = totals

        for col in piv.columns:
            if col != 'size':
                try:
                    piv[col] = piv[col].fillna(0).astype(int)
                except (TypeError, ValueError):
                    pass

        if humanize and 'size' in piv.columns:
            piv = piv.copy()
            piv['size'] = piv['size'].fillna(0).astype(int).apply(byte_str)

        piv = _order_columns(piv, extra_last=())
        return piv

    def _summary_row_for_node(self, node, *, humanize=True):
        """Return the compact aggregate row for a graph node."""
        piv = self._stats_table_for_node(node, humanize=False)
        if len(piv):
            row = piv.loc['∑ total'].to_dict()
        else:
            row = {'files': 0, 'size': 0}
        clean = {}
        for key, value in row.items():
            if key == 'size':
                try:
                    size = int(value)
                except (TypeError, ValueError):
                    size = 0
                clean[key] = byte_str(size) if humanize else size
            else:
                try:
                    clean[key] = int(value)
                except (TypeError, ValueError):
                    clean[key] = value
        return clean

    def stats_table(self, max_depth=1, include_files=True, max_rows=None, humanize=True):
        """
        Return a path-by-stats table suitable for plain-text reports.

        Args:
            max_depth (int | None): maximum graph depth to include. ``None``
                includes every node under the root.
            include_files (bool): if False, only directory rows are emitted.
            max_rows (int | None): optional row limit for very large reports.
            humanize (bool): if True, format byte sizes for display.
        """
        import pandas as pd  # type: ignore

        if self.graph is None:
            raise RuntimeError('stats_table() requires build() first')
        root = self.root
        rows = []

        def rec(node, depth):
            if max_rows is not None and len(rows) >= max_rows:
                return
            node_data = self.graph.nodes[node]  # type: ignore
            if depth > 0 and (include_files or node_data['type'] == 'dir'):
                row = self._summary_row_for_node(node, humanize=humanize)
                try:
                    rel = node.relative_to(root)
                    name = rel.as_posix()
                except Exception:
                    name = os.fspath(node)
                row['name'] = name
                rows.append(row)
            if max_depth is not None and depth >= max_depth:
                return
            if node_data['type'] == 'dir':
                for child in self.graph.succ[node]:  # type: ignore
                    rec(child, depth + 1)

        rec(root, 0)
        df = pd.DataFrame(rows)
        if len(df):
            df = _order_columns(df, extra_last=('name',))
        else:
            df = pd.DataFrame(columns=STAT_COLUMN_ORDER + ['name'])
        return df

    def extension_stats_table(self, humanize=True):
        """Return extension-level stats for the root node."""
        if self.graph is None:
            raise RuntimeError('extension_stats_table() requires build() first')
        return self._stats_table_for_node(self.root, humanize=humanize)

    def dirstats_text(self, max_depth=1, max_rows=None, include_files=True):
        """Return a stable plain-text dirstats report."""
        lines = []
        lines.append(f'Stats root: {self.root}')
        lines.append(f'Max display depth: {max_depth if max_depth is not None else "full"}')
        lines.append('')
        lines.append('Path summary:')
        path_df = self.stats_table(
            max_depth=max_depth,
            include_files=include_files,
            max_rows=max_rows,
            humanize=True,
        )
        if len(path_df):
            lines.append(path_df.to_string(index=False))
            if max_rows is not None and len(path_df) >= max_rows:
                lines.append(f'... truncated after {max_rows} rows ...')
        else:
            lines.append('(no child paths)')
        lines.append('')
        lines.append('Extension summary:')
        ext_df = self.extension_stats_table(humanize=True)
        if len(ext_df):
            lines.append(ext_df.to_string())
        else:
            lines.append('(no extension stats)')
        return '\n'.join(lines)

    def write_report(self, max_nodes=10, **nxtxt_kwargs):
        """
        Args:
            **nxtxt_kwargs:
                path : string or file or callable or None
                   Filename or file handle for data output.
                   if a function, then it will be called for each generated line.
                   if None, this will default to "sys.stdout.write"

                with_labels : bool | str
                    If True will use the "label" attribute of a node to display if it
                    exists otherwise it will use the node value itself. If given as a
                    string, then that attribute name will be used instead of "label".
                    Defaults to True.

                sources : List
                    Specifies which nodes to start traversal from. Note: nodes that are not
                    reachable from one of these sources may not be shown. If unspecified,
                    the minimal set of nodes needed to reach all others will be used.

                max_depth : int | None
                    The maximum depth to traverse before stopping. Defaults to None.

                ascii_only : Boolean
                    If True only ASCII characters are used to construct the visualization

                end : string
                    The line ending character

                vertical_chains : Boolean
                    If True, chains of nodes will be drawn vertically when possible.

        Example:
            >>> # xdoctest: +REQUIRES(module:pandas)
            >>> import xdev
            >>> walker = xdev.DirectoryWalker.demo()
            >>> walker.write_report(max_nodes=0)
        """
        import pandas as pd  # type: ignore

        if len(self.graph.nodes) <= max_nodes * 10000:  # type: ignore
            try:
                self.write_network_text(**nxtxt_kwargs)
            except KeyboardInterrupt:
                ...
        else:
            print('...graph to big, not printing')

        if len(self._topo_order):  # type: ignore
            root_node = self._topo_order[0]  # type: ignore
        else:
            root_node = None

        def _node_table(node):
            node_data = self.graph.nodes[node]  # type: ignore
            stats = node_data.get('stats', {})
            stat_rows = []
            for k, v in stats.items():
                ext, kind = k.split('.')
                if not ext:
                    # ext = '∅'
                    # ext = '𝙣𝙪𝙡𝙡'
                    ext = '*null*'
                stat_rows.append({'ext': ext, 'kind': kind, 'value': v})
            table = pd.DataFrame(stat_rows)

            if len(table) > 0:
                piv = table.pivot(index='ext', columns='kind', values='value')
                piv = piv.sort_values('size')
            else:
                piv = pd.DataFrame([], index=pd.Index([], name='ext'), columns=pd.Index(['size', 'files'], name='kind'))

            totals = piv.sum(axis=0)
            disp_totals = totals.copy()
            disp_totals = disp_totals.astype(object)
            disp_totals['size'] = byte_str(totals['size'])
            disp_piv = piv.copy()
            disp_piv['size'] = piv['size'].apply(byte_str)
            disp_piv = disp_piv.fillna('--')
            disp_piv.loc['∑ total'] = disp_totals
            disp_piv['files'] = disp_piv['files'].astype(int)
            disp_piv = _order_columns(disp_piv, extra_last=())
            return disp_piv

        if root_node:
            child_rows = []
            for node in self.graph.succ[root_node]:  # type: ignore
                disp_piv = _node_table(node)
                row = disp_piv.iloc[-1].to_dict()
                row['name'] = self.graph.nodes[node]['name']  # type: ignore
                child_rows.append(row)
            if child_rows:
                print('')
                df = pd.DataFrame(child_rows)
                if 'total' in df.columns:
                    df = df.sort_values('total')
                df = _order_columns(df, extra_last=('name',))
                rich.print(df)
                # if self.graph.nodes[node]['type'] == 'dir':
                # print(f'node={node}')

            disp_piv = _node_table(root_node)
            print('')
            rich.print(disp_piv[:-1])
            rich.print(disp_piv[-1:])
        print('root_node = {}'.format(ub.urepr(root_node, nl=1)))

        if 0:
            # Feature to show most recently modified files in a tree?
            table = []
            for node, node_data in self.graph.nodes(data=True):
                node_data['path_stat'] = node.stat()
                node_data['path'] = node
                table.append(node_data)

            table = sorted(table, key=lambda r: r['path_stat'].st_mtime)
            for row in table:
                import xdev
                time = xdev.datetime.coerce(row['path_stat'].st_mtime)
                if 'dev' in str(row['path']):
                    print(time, row['path'])

            [r['path'] for r in table]

        # disp_stats = self._humanize_stats(stats, 'dir', reduce_prefix=True)
        # rich.print('stats = {}'.format(ub.urepr(disp_stats, nl=1)))

    def build(self):
        """
        Build the internal graph structure with requested metadata
        """
        self._walk()
        self._update_stats()
        self._update_labels()
        self._sort()
        return self

    def stats(self, typed=False, root=None):
        """
        Return stats about the directories starting at the root.
        Requires walker has been built. If root unspecified uses walker root
        """
        node = self.graph.nodes[self.root]  # type: ignore
        stats = node['stats']
        # node_type = node['type']
        if typed:
            _stats = stats
        else:
            _stats = self._reduce_stats(stats)
        return _stats
        # self._humanize_stats(stats, node_type)
        # disp_stats = self._humanize_stats(_stats, node_type)

    def _inplace_filter_dnames(self, dnames):
        if self.include_dnames is not None:
            dnames[:] = [d for d in dnames if self.include_dnames.match(d)]
        if self.exclude_dnames is not None:
            dnames[:] = [d for d in dnames if not self.exclude_dnames.match(d)]

    def _inplace_filter_fnames(self, fnames):
        if self.include_fnames is not None:
            fnames[:] = [f for f in fnames if self.include_fnames.match(f)]
        if self.exclude_fnames is not None:
            fnames[:] = [f for f in fnames if not self.exclude_fnames.match(f)]

    def _walk(self):
        dpath = self.dpath
        g = nx.DiGraph()

        g.add_node(self.dpath, label=self.dpath.name, type='dir', is_root=True)

        max_files = self.max_files

        pman = ProgressManager(enabled=self.show_progress)
        with pman:
            prog = pman.progiter(desc='Walking directory')

            if self.max_walk_depth is not None:
                start_depth = str(self.dpath).count(os.path.sep)

            if self.fs is None:
                walkgen = self.dpath.walk()
            else:
                walkgen = self.fs.walk(os.fspath(dpath))

            for root, dnames, fnames in walkgen:

                if self.fs is not None:
                    root = ub.Path(root)

                prog.step()

                root_attrs = {}

                root_attrs['unfiltered_num_dirs'] = len(dnames)
                root_attrs['unfiltered_num_files'] = len(fnames)

                if self.max_walk_depth is not None:
                    curr_depth = str(root).count(os.path.sep)
                    rel_depth = (curr_depth - start_depth)
                    if rel_depth >= self.max_walk_depth:
                        del dnames[:]

                # Remove directories / files that match the blocklist or dont
                # match the include list
                self._inplace_filter_dnames(dnames)
                self._inplace_filter_fnames(fnames)

                root_attrs['num_dirs'] = len(dnames)
                root_attrs['num_files'] = num_files = len(fnames)

                too_many_files = max_files is not None and num_files >= max_files
                if too_many_files:
                    root_attrs['too_many_files'] = too_many_files

                g.add_node(
                    root,
                    type='dir',
                    name=root.name,
                    label=root.name,
                    **root_attrs,
                )
                # if root != dpath:
                #     g.add_edge(root.parent, root)

                if self.sort:
                    # TODO: good API to customize sorting
                    fnames = sorted(fnames)
                    dnames = sorted(dnames)

                if not too_many_files:
                    for f in fnames:
                        fpath = root / f
                        g.add_node(fpath, name=fpath.name, label=fpath.name, type='file')
                        g.add_edge(root, fpath)

                for d in dnames:
                    dpath = root / d
                    g.add_node(dpath, name=dpath.name, label=dpath.name, type='dir')
                    g.add_edge(root, dpath)

        self._topo_order = list(nx.topological_sort(g))
        self.graph = g

        if self.ignore_empty_dirs:
            for node in self._topo_order[::-1]:
                node_data = g.nodes[node]
                if node_data['type'] == 'file':
                    node_data['stats'] = {'file': 1}
            self._accum_stats()

            to_remove = []
            for node in self._topo_order[::-1]:
                node_data = g.nodes[node]
                if node_data['stats'].get('file', 0) == 0:
                    to_remove.append(node)

            g.remove_nodes_from(to_remove)
            self._topo_order = list(nx.topological_sort(g))
            self.graph = g

        self._type_to_path = {}
        for p, d in self.graph.nodes(data=True):
            t = d['type']
            if t not in self._type_to_path:
                self._type_to_path[t] = []
            self._type_to_path[t].append(p)

    @property
    def file_paths(self):
        return self._type_to_path.get('file', [])

    @property
    def dir_paths(self):
        return self._type_to_path.get('dir', [])

    def _accum_stats(self):
        g = self.graph
        # Accumulate size stats
        ### Iterate from leaf-to-root, and accumulate info in directories
        for node in self._topo_order[::-1]:  # type: ignore
            children = g.succ[node]  # type: ignore
            node_data = g.nodes[node]  # type: ignore
            if node_data['type'] == 'dir':
                node_data['stats'] = accum_stats = {}
                for child in children:
                    child_data = g.nodes[child]  # type: ignore
                    child_stats = child_data.get('stats', {})
                    for key, stat_value in child_stats.items():
                        # a collections.Counter might be more efficient
                        # but we probably want to serialize to dictionary
                        # after.
                        if key not in accum_stats:
                            accum_stats[key] = 0
                        accum_stats[key] += stat_value

    def _update_stats(self):
        g = self.graph
        fs = self.fs

        # Get size stats for each file.
        pman = ProgressManager(enabled=self.show_progress)
        with pman:
            prog = pman.progiter(desc='Parse File Info', total=len(g))  # type: ignore
            for fpath, node_data in g.nodes(data=True):  # type: ignore
                if node_data['type'] == 'file':
                    stats = parse_file_stats(
                        fpath,
                        parse_content=self.parse_content,
                        parse_python=self.python,
                        parse_rust=self.rust,
                        fs=fs,
                    )
                    node_data['stats'] = stats
                prog.step()
        self._accum_stats()

    def _update_stats2(self):

        # Variant that uses parallel process boilerplate
        def worker(fpath):
            stats = parse_file_stats(
                fpath,
                parse_content=self.parse_content,
                parse_python=self.python,
                parse_rust=self.rust,
            )
            return stats

        self._parallel_process_files(worker, 'Parse File Info')
        self._accum_stats()

    def _parallel_process_files(self, func, desc=None, max_workers=8, mode='thread'):
        """
        Applies a function to every node.
        """
        graph = self.graph

        if desc is None:
            desc = str(func)

        # Get size stats for each file.
        jobs = ub.JobPool(mode=mode, max_workers=max_workers)
        pman = ProgressManager(backend='progiter')
        submit_desc = 'Submit: ' + desc
        collect_desc = 'Collect: ' + desc

        with pman, jobs:
            # Get the files from the graph first.
            fpaths = [
                path
                for path, data in graph.nodes(data=True)  # type: ignore
                if data['isfile']
            ]
            prog = ub.ProgIter(fpaths, desc=submit_desc, total=len(fpaths),
                               homogeneous=False)
            for fpath in prog:
                job = jobs.submit(func, fpath)
                job.fpath = fpath  # type: ignore

            for job in ub.ProgIter(jobs.as_completed(), desc=collect_desc,
                                   total=len(jobs)):
                fpath = job.fpath  # type: ignore
                result = job.result()
                yield fpath, result

    @classmethod
    def _reduce_stats(cls, stats):
        """
        Combines stats over the a prefix
        """
        suffixes = [k.split('.', 1)[1] for k in stats.keys()]
        _stats = ub.udict(ub.group_items(stats.values(), suffixes)).map_values(sum)
        # _stats.update({k: v for k, v in stats.items() if k.endswith('.files')})
        return _stats

    @classmethod
    def _humanize_stats(cls, stats, node_type, reduce_prefix=False):
        disp_stats = {}
        if reduce_prefix:
            _stats = cls._reduce_stats(stats)
        else:
            _stats = stats
        if node_type == 'dir':
            for k, v in _stats.items():
                if k.endswith('.size') or k == 'size':
                    disp_stats[k] = byte_str(v)
                else:
                    disp_stats[k] = v
        elif node_type == 'file':
            disp_stats = {k.split('.', 1)[1]: v for k, v in _stats.items()}
            disp_stats.pop('files', None)
            if 'size' in disp_stats:
                disp_stats['size'] = byte_str(disp_stats['size'])
        else:
            raise KeyError(node_type)
        return disp_stats

    def _find_duplicate_files(self):
        hasher = 'blake3'
        for path, node_data in self.graph.nodes(data=True):  # type: ignore
            if node_data['isfile']:
                node_data[hasher] = ub.hash_file(path, hasher=hasher)

        hash_to_paths = ub.ddict(list)
        for path, node_data in self.graph.nodes(data=True):  # type: ignore
            if node_data['isfile']:
                hash = node_data[hasher]
                hash_to_paths[hash].append(path)

        hash_to_paths = ub.udict(hash_to_paths)
        dups = []
        for k, v in hash_to_paths.items():
            if len(v) > 1:
                dups.append(k)
        dup_hash_to_paths = hash_to_paths & dups  # type: ignore
        print('dup_hash_to_paths = {}'.format(ub.urepr(dup_hash_to_paths, nl=2)))

    def _update_path_metadata(self):
        g = self.graph
        for path in self._topo_order:  # type: ignore
            node_data = g.nodes[path]  # type: ignore

            islink = os.path.islink(path)
            isfile = os.path.isfile(path)
            isdir = os.path.isdir(path)

            if islink:
                target = os.readlink(path)
                isbroken = not isdir and not isfile
                node_data['broken'] = isbroken
                node_data['target'] = target

            if isfile:
                node_data['X_ok'] = os.access(path, os.X_OK)

            types = []
            if islink:
                types.append('L')
                if isbroken:
                    types.append('B')
            if isfile:
                types.append('F')
            if isdir:
                types.append('D')
            typelabel = ''.join(types)

            node_data['islink'] = islink
            node_data['isfile'] = isfile
            node_data['isdir'] = isdir
            node_data['typelabel'] = typelabel

    def _update_labels(self):
        """
        Update how each node will be displayed
        """
        from os.path import relpath
        from rich.markup import escape

        label_options = self.label_options
        pathstyle = label_options['pathstyle']
        show_nfiles = label_options['show_nfiles']
        show_types = label_options['show_types']
        abs_root_label = label_options['abs_root_label']
        colors = label_options['colors']

        def pathrep_name(p, node_data):
            return node_data['name']

        def pathrep_rel(p, node_data):
            return relpath(p, self.dpath)

        def pathrep_abs(p, node_data):
            return os.fspath(p)

        if pathstyle == 'name':
            pathrep_func = pathrep_name
        elif pathstyle == 'rel':
            pathrep_func = pathrep_rel
        elif pathstyle == 'abs':
            pathrep_func = pathrep_abs
        else:
            raise KeyError(pathstyle)

        self._update_path_metadata()

        for path, node_data in self.graph.nodes(data=True):  # type: ignore
            stats = node_data.get('stats', None)
            node_type = node_data.get('type', None)

            if abs_root_label and node_data.get('is_root', False):
                pathrep = pathrep_abs(path, node_data)
            else:
                pathrep = pathrep_func(path, node_data)

            if stats:
                disp_stats = self._humanize_stats(stats, node_type)
                stats_text = ub.urepr(disp_stats, nl=0, compact=1)
                suffix = ': ' + stats_text
            else:
                suffix = ''

            prefix_parts = []

            if show_types:
                prefix_parts.append(f'({node_data["typelabel"]})')

            if node_type == 'dir':
                richlink = True
                color = 'blue'

                if show_nfiles == 'auto':
                    show_nfiles_ = node_data.get('too_many_files', False)
                else:
                    show_nfiles_ = show_nfiles
                if show_nfiles_ and 'num_files' in node_data:
                    prefix_parts.append(
                        '[ {} ]'.format(node_data['num_files'])
                    )
            elif node_type == 'file':
                richlink = False
                if node_data.get('X_ok', False):
                    color = 'green'
                else:
                    color = 'reset'
            else:
                raise KeyError(node_type)

            targetrep = None
            if node_data['islink']:
                target = node_data['target']
                targetrep = target
                if node_data['broken']:
                    color = 'red'
                else:
                    color = 'cyan'
                if node_data['isdir']:
                    target_color = 'blue'
                    target_richlink = True
                else:
                    target_color = 'reset'
                    target_richlink = False

                if colors:
                    targetrep = escape(targetrep)
                    if target_richlink:
                        import urllib.parse
                        encoded_target = 'file://' + urllib.parse.quote(os.fspath(target))
                        targetrep = f'[link={encoded_target}]{targetrep}[/link]'
                    targetrep = f'[{target_color}]{targetrep}[/{target_color}]'

            if colors:
                if richlink:
                    import urllib.parse
                    pathrep = escape(pathrep)
                    encoded_path = 'file://' + urllib.parse.quote(os.fspath(path))
                    pathrep = f'[link={encoded_path}]{pathrep}[/link]'
                pathrep = f'[{color}]{pathrep}[/{color}]'

            if targetrep is not None:
                pathrep = f'{pathrep} -> {targetrep}'

            if prefix_parts:
                prefix = ' '.join(prefix_parts) + ' '
            else:
                prefix = ''
            node_data['label'] = prefix + pathrep + suffix

    def _sort(self):
        g = self.graph
        # Order nodes based on size
        ordered_nodes = dict(g.nodes(data=True))  # type: ignore
        ordered_edges = []
        for node in self._topo_order[::-1]:  # type: ignore
            # Sort children by total lines
            children = g.succ[node]  # type: ignore
            children = ub.udict({c: g.nodes[c] for c in children})  # type: ignore
            children = children.sorted_keys(lambda c: (g.nodes[c]['type'], _stats_total(g.nodes[c].get('stats', {}))), reverse=True)  # type: ignore
            for c, d in children.items():
                ordered_nodes.pop(c, None)
                ordered_nodes[c] = d
                ordered_edges.append((node, c))

            # ordered_nodes.update(children)

        assert not (set(g.edges) - set(ordered_edges))  # type: ignore
        new = nx.DiGraph()
        new.add_nodes_from(ordered_nodes.items())
        new.add_edges_from(ordered_edges)
        self.graph = new

    @classmethod
    def demo(cls):
        """
        Create a persistent demo directory tree and return a built walker.

        The directory is created under ``ub.Path.appdir('directory_walker/demo')`` and
        is re-initialized on each call to keep doctests deterministic.

        Returns:
            DirectoryWalker

        Example:
            >>> import xdev
            >>> walker = xdev.DirectoryWalker.demo()
            >>> walker.dpath.exists()
            True
        """
        import os
        import ubelt as ub

        demo_root = ub.Path.appdir('xdev/directory_walker/demo').ensuredir()

        # Make deterministic by clearing and recreating
        if demo_root.exists():
            demo_root.delete()
        demo_root.ensuredir()

        # Build a small stable tree
        (demo_root / 'adir').ensuredir()
        (demo_root / 'bdir').ensuredir()
        (demo_root / 'adir' / 'foo.txt').write_text('hello')
        (demo_root / 'adir' / 'bar.md').write_text('world')
        (demo_root / 'bdir' / 'foo.md').write_text('x')

        # Optional symlink (best effort)
        link_path = demo_root / 'alink.txt'
        try:
            os.symlink(demo_root / 'adir' / 'foo.txt', link_path)
        except Exception:
            # Windows / permissions / filesystem may not allow symlinks
            pass

        walker = cls(demo_root)
        walker.build()
        return walker

    def find(self, pattern, data=False, root=None, filetype=None):
        """
        Search for nodes whose **name** matches a MultiPattern, optionally filtering by type.

        Args:
            pattern: Coerced via ``MultiPattern.coerce(pattern)`` and tested with
                ``pattern.match(node.name)``.
            data (bool): if True, also yield the node data dict
            root (pathlib.Path | None): if specified, search descendants of this node
            filetype (Iterable[str] | None):
                Iterable of type chars from {'f', 'd', 'l'}:
                  - 'f' = regular file
                  - 'd' = directory
                  - 'l' = symlink
                Examples: 'f', 'fd', {'l'}, ['f','l'].

        Yields:
            pathlib.Path | Tuple[pathlib.Path, dict]

        Example:
            >>> import xdev
            >>> walker = DirectoryWalker.demo()
            >>> sorted(p.name for p in walker.find('foo.txt'))
            ['foo.txt']
            >>> sorted(p.name for p in walker.find('foo*', filetype='f'))
            ['foo.md', 'foo.txt']
            >>> sorted(p.name for p in walker.find('adir', filetype='d'))
            ['adir']
            >>> # Best-effort: only assert something meaningful if the symlink exists
            >>> links = list(walker.find('alink.txt', filetype='l'))
            >>> (len(links) == 1)
            True
        """
        import networkx as nx

        if self.graph is None:
            raise RuntimeError('DirectoryWalker.find() requires build() first')

        graph = self.graph

        # Normalize root
        if root is not None:
            if root not in graph:
                raise KeyError(f'root {root!r} not found in graph')
            nodes = nx.descendants(graph, root)
        else:
            nodes = graph.nodes

        # Coerce pattern
        pattern = MultiPattern.coerce(pattern)

        # Normalize filetype: iterable of chars in {f,d,l}
        ftypes = None
        if filetype is not None:
            ftypes = set(filetype)
            unknown = ftypes - {'f', 'd', 'l'}
            if unknown:
                raise ValueError(f'unknown filetype chars={sorted(unknown)!r}, expected subset of {{"f","d","l"}}')

        for node in nodes:
            # Match only on node.name
            if not pattern.match(node.name):
                continue

            node_data = graph.nodes[node]

            if ftypes is not None:
                keep = False
                if ('l' in ftypes and node_data['islink']):
                    keep = True
                if ('f' in ftypes and node_data['isfile']):
                    keep = True
                if ('d' in ftypes and node_data['isdir']):
                    keep = True

                if not keep:
                    continue

            if data:
                yield node, node_data
            else:
                yield node

    def find_one(self, pattern, data=False, root=None, filetype=None):
        """
        Find exactly one node matching a pattern (and optional type filter).

        Args:
            pattern: Coerced via ``kwutil.MultiPattern.coerce(pattern)`` (see ``find``).
            data (bool): if True, also return the node data dict.
            root (pathlib.Path | None): if specified, search descendants of this node.
            filetype (Iterable[str] | None): iterable of {'f','d','l'} (see ``find``).

        Returns:
            pathlib.Path | Tuple[pathlib.Path, dict]

        Raises:
            KeyError: if zero or multiple matches are found.

        Example:
            >>> walker = DirectoryWalker.demo()
            >>> walker.find_one('foo.txt').name
            'foo.txt'
        """
        matches = list(self.find(pattern, data=data, root=root, filetype=filetype))

        if not matches:
            raise KeyError(f'find_one({pattern!r}) found no matches')

        if len(matches) > 1:
            raise KeyError(
                f'find_one({pattern!r}) found {len(matches)} matches, expected exactly one'
            )

        return matches[0]


def parse_file_stats(
    fpath,
    parse_content=True,
    parse_python=False,
    parse_rust=False,
    fs=None,
):
    """
    Get information about a file.

    ``parse_content`` counts ``total`` lines for UTF-8 text-like files.
    Language flags add richer analysis for selected source formats.
    """
    ext = fpath.suffix
    prefix = ext.lstrip('.') + '.'
    stats = {}
    try:
        if fs is None:
            stat_obj = fpath.stat()
            size = stat_obj.st_size
        else:
            stat_obj = fs.stat(os.fspath(fpath))
            size = stat_obj['size']
    except FileNotFoundError:
        is_broken = True
        stats['broken_link'] = True
        stats['size'] = 0
    else:
        is_broken = False
        stats['size'] = size

    stats['files'] = 1

    if not is_broken and parse_content:
        # ``Path.walk`` reports symlinked directories in ``fnames`` when it is
        # not following symlinks. Treat those entries as file-like for size
        # accounting, but do not try to read their contents.
        try:
            if fs is None:
                is_readable_file = fpath.is_file()
            else:
                stat_type = stat_obj.get('type', None)
                is_readable_file = stat_type is None or stat_type == 'file'
        except OSError:
            is_readable_file = False

        if is_readable_file:
            try:
                if fs is None:
                    text = fpath.read_text(encoding='utf8')
                else:
                    with fs.open(os.fspath(fpath), 'rt', encoding='utf8') as file:
                        text = file.read()
            except (UnicodeDecodeError, IsADirectoryError, PermissionError):
                # Binary, non-UTF8, unreadable, or directory-like entries count
                # as files/bytes but not text.
                ...
            else:
                stats['total'] = _text_total_lines(text)

                if parse_python and ext == '.py':
                    try:
                        stats.update(parse_python_content_stats(text))
                    except Exception:
                        ...

                elif parse_rust and ext == '.rs':
                    try:
                        stats.update(parse_rust_content_stats(text, fpath=fpath))
                    except Exception:
                        ...

    stats = {prefix + k: v for k, v in stats.items()}
    return stats


def _text_total_lines(text):
    """Return the number of logical lines in text."""
    if not text:
        return 0
    return len(text.splitlines())


def parse_python_content_stats(source: str):
    """
    Count Python code and comment/docstring lines.

    Python does not get a test split in dirstats. Test files are counted as
    main Python text so the report stays compact and language-neutral.
    """
    import ast
    import io
    import tokenize

    comment_lines = set()
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                start, end = tok.start[0] - 1, tok.end[0] - 1
                comment_lines.update(range(start, end + 1))
    except Exception:
        pass

    try:
        tree = ast.parse(source)
    except Exception:
        pass
    else:
        nodes = [tree]
        nodes.extend(
            n for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        )
        for node in nodes:
            body = getattr(node, 'body', None)
            if not body:
                continue
            first = body[0]
            if (
                isinstance(first, ast.Expr) and
                isinstance(getattr(first, 'value', None), ast.Constant) and
                isinstance(first.value.value, str)
            ):
                start = getattr(first, 'lineno', None)
                end = getattr(first, 'end_lineno', start)
                if start is not None:
                    comment_lines.update(range(start - 1, end))

    try:
        raw_code = strip_comments_and_newlines(source)
        code_lines = _text_total_lines(raw_code)
    except Exception:
        code_lines = 0

    return {
        'main_code': code_lines,
        'main_comments': len(comment_lines),
    }

def strip_comments_and_newlines(source):
    """
    Removes hashtag comments from underlying source

    Args:
        source (str | List[str]):

    TODO:
        would be better if this was some sort of configurable minify API

    Example:
        >>> from xdev.directory_walker import strip_comments_and_newlines
        >>> import ubelt as ub
        >>> fmtkw = dict(sss=chr(39) * 3, ddd=chr(34) * 3)
        >>> source = ub.codeblock(
        >>>    '''
               # comment 1
               a = '# not a comment'  # comment 2

               multiline_string = {ddd}

               one

               {ddd}
               b = [
                   1,  # foo


                   # bar
                   3,
               ]
               c = 3
               ''').format(**fmtkw)
        >>> non_comments = strip_comments_and_newlines(source)
        >>> print(non_comments)
        >>> assert non_comments.count(chr(10)) == 10
        >>> assert non_comments.count('#') == 1
    """
    import tokenize
    if isinstance(source, str):
        import io
        f = io.StringIO(source)
        readline = f.readline
    else:
        readline = iter(source).__next__

    def strip_hashtag_comments(tokens):
        """
        Drop comment tokens from a `tokenize` stream.
        """
        return (t for t in tokens if t[0] != tokenize.COMMENT)

    def strip_consecutive_newlines(tokens):
        """
        Consecutive newlines are dropped and trailing whitespace

        Adapated from: https://github.com/mitogen-hq/mitogen/blob/master/mitogen/minify.py#L65
        """
        prev_typ = None
        prev_end_col = 0
        skipped_rows = 0
        for token_info in tokens:
            typ, tok, (start_row, start_col), (end_row, end_col), line = token_info
            if typ in (tokenize.NL, tokenize.NEWLINE):
                if prev_typ in (tokenize.NL, tokenize.NEWLINE, None):
                    skipped_rows += 1
                    continue
                else:
                    start_col = prev_end_col
                end_col = start_col + 1
            prev_typ = typ
            prev_end_col = end_col
            yield typ, tok, (start_row - skipped_rows, start_col), (end_row - skipped_rows, end_col), line

    tokens = tokenize.generate_tokens(readline)
    tokens = strip_hashtag_comments(tokens)
    tokens = strip_docstrings(tokens)
    tokens = strip_consecutive_newlines(tokens)
    new_source = tokenize.untokenize(tokens)
    return new_source


def strip_docstrings(tokens):
    """
    Replace docstring tokens with NL tokens in a `tokenize` stream.

    Any STRING token not part of an expression is deemed a docstring.
    Indented docstrings are not yet recognised.
    """
    import tokenize
    stack = []
    state = 'wait_string'
    for t in tokens:
        typ = t[0]
        if state == 'wait_string':
            if typ in (tokenize.NL, tokenize.COMMENT):
                yield t
            elif typ in (tokenize.DEDENT, tokenize.INDENT, tokenize.STRING):
                stack.append(t)
            elif typ == tokenize.NEWLINE:
                stack.append(t)
                start_line, end_line = stack[0][2][0], stack[-1][3][0] + 1
                for i in range(start_line, end_line):
                    yield tokenize.NL, '\n', (i, 0), (i, 1), '\n'
                for t in stack:
                    if t[0] in (tokenize.DEDENT, tokenize.INDENT):
                        yield t[0], t[1], (i + 1, t[2][1]), (i + 1, t[3][1]), t[4]
                del stack[:]
            else:
                stack.append(t)
                for t in stack:
                    yield t
                del stack[:]
                state = 'wait_newline'
        elif state == 'wait_newline':
            if typ == tokenize.NEWLINE:
                state = 'wait_string'
            yield t


def byte_str(num, unit='auto', precision=2):
    """
    Automatically chooses relevant unit (KB, MB, or GB) for displaying some
    number of bytes.

    Args:
        num (int): number of bytes
        unit (str): which unit to use, can be auto, B, KB, MB, GB, or TB

    References:
        .. [WikiOrdersOfMag] https://en.wikipedia.org/wiki/Orders_of_magnitude_(data)

    Returns:
        str: string representing the number of bytes with appropriate units

    Example:
        >>> import ubelt as ub
        >>> num_list = [1, 100, 1024,  1048576, 1073741824, 1099511627776]
        >>> result = ub.urepr(list(map(byte_str, num_list)), nl=0)
        >>> print(result)
        ['0.00 KB', '0.10 KB', '1.00 KB', '1.00 MB', '1.00 GB', '1.00 TB']
        >>> byte_str(10, unit='B')
        '10.00 B'
    """
    abs_num = abs(num)
    if unit == 'auto':
        if abs_num < 2.0 ** 10:
            unit = 'KB'
        elif abs_num < 2.0 ** 20:
            unit = 'KB'
        elif abs_num < 2.0 ** 30:
            unit = 'MB'
        elif abs_num < 2.0 ** 40:
            unit = 'GB'
        else:
            unit = 'TB'
    if unit.lower().startswith('b'):
        num_unit = num
    elif unit.lower().startswith('k'):
        num_unit =  num / (2.0 ** 10)
    elif unit.lower().startswith('m'):
        num_unit =  num / (2.0 ** 20)
    elif unit.lower().startswith('g'):
        num_unit = num / (2.0 ** 30)
    elif unit.lower().startswith('t'):
        num_unit = num / (2.0 ** 40)
    else:
        raise ValueError('unknown num={!r} unit={!r}'.format(num, unit))
    fmtstr = ('{:.' + str(precision) + 'f} {}')
    res = fmtstr.format(num_unit, unit)
    return res




def dirstats_report_text(
    dpath,
    *,
    exclude_dnames=None,
    exclude_fnames=None,
    include_dnames=None,
    include_fnames=None,
    max_walk_depth=None,
    max_display_depth=1,
    max_rows=None,
    parse_content=True,
    python=False,
    rust=False,
    include_files=True,
    show_progress=False,
):
    """
    Build and return a stable plain-text dirstats report.

    This is the programmatic counterpart to the interactive ``dirstats`` CLI.
    It is intended for scripts that need deterministic report text without
    progress bars or rich console formatting.
    """
    walker = DirectoryWalker(
        dpath,
        exclude_dnames=exclude_dnames,
        exclude_fnames=exclude_fnames,
        include_dnames=include_dnames,
        include_fnames=include_fnames,
        max_walk_depth=max_walk_depth,
        parse_content=parse_content,
        python=python,
        rust=rust,
        show_progress=show_progress,
    ).build()
    return walker.dirstats_text(
        max_depth=max_display_depth,
        max_rows=max_rows,
        include_files=include_files,
    )

def _null_coerce(cls, arg, **kwargs):
    if arg is None:
        return arg
    else:
        return cls.coerce(arg, **kwargs)


class DirectoryDiff:
    """
    Given two directory walkers (that walk over what should be similar
    directories), compare the state of them both.

    Ignore:
        from xdev.directory_walker import *  # NOQA
        walker1 = DirectoryWalker('.')
        walker2 = DirectoryWalker('.')
        walker1.build()
        walker2.build()
        self = DirectoryDiff(walker1, walker2).build()
        self.write_report()
    """
    def __init__(self, walker1, walker2):
        self.walker1 = walker1
        self.walker2 = walker2

    def build(self):
        rel_paths1 = {p.relative_to(self.walker1.dpath) for p in self.walker1.graph.nodes}
        rel_paths2 = {p.relative_to(self.walker2.dpath) for p in self.walker2.graph.nodes}
        self.root1 = self.walker1.dpath
        self.root2 = self.walker2.dpath
        self.common_paths = rel_paths1 & rel_paths2
        self.unique_paths1 = rel_paths1 - rel_paths2
        self.unique_paths2 = rel_paths2 - rel_paths1

        common_table = []
        for rel_path in self.common_paths:
            path1 = self.root1 / rel_path
            path2 = self.root2 / rel_path
            row = {
                'rel_path': rel_path,
                'type': None,
                'hash': None,
                'num_errors': 0,
            }
            data1 = self.walker1.graph.nodes[path1]
            data2 = self.walker2.graph.nodes[path2]

            to_compare = {
                'item1': {'type': data1['type']},
                'item2': {'type': data2['type']},
            }
            type1 = data1['type']
            type2 = data2['type']
            if type1 == type2:
                if data1['isfile']:
                    # TODO: control what is compared.
                    to_compare['item1']['hash'] = ub.hash_file(path1)
                    to_compare['item2']['hash'] = ub.hash_file(path2)

                    stat1 = path1.stat()
                    stat2 = path2.stat()
                    to_compare['item1']['st_mode'] = stat1.st_mode
                    to_compare['item2']['st_mode'] = stat2.st_mode
                    to_compare['item1']['st_mtime'] = stat1.st_mtime
                    to_compare['item2']['st_mtime'] = stat2.st_mtime
                    to_compare['item1']['st_ctime'] = stat1.st_ctime
                    to_compare['item2']['st_ctime'] = stat2.st_ctime
                    to_compare['item1']['st_gid'] = stat1.st_gid
                    to_compare['item2']['st_gid'] = stat2.st_gid
                    to_compare['item1']['st_uid'] = stat1.st_uid
                    to_compare['item2']['st_uid'] = stat2.st_uid

                to_compare['item1']['stats'] = data2['stats']
                to_compare['item2']['stats'] = data2['stats']

            compare1 = to_compare['item1']
            compare2 = to_compare['item2']
            for k in compare1.keys():
                v1 = compare1[k]
                v2 = compare2[k]
                if v1 != v2:
                    row[k] = f'MISMATCH: {v1} {v2}'
                    row['num_errors'] += 1
                else:
                    row[k] = v1
            common_table.append(row)

        self.common_table = common_table
        return self

    def summary(self):
        from collections import Counter
        error_hist = Counter({0: 0, 1: 0})
        error_hist.update(r['num_errors'] for r in self.common_table)
        summary = {
            'n_common_paths': len(self.common_paths),
            'n_unique_paths1': len(self.unique_paths1),
            'n_unique_paths2': len(self.unique_paths2),
            'error_hist': error_hist,
        }
        return summary

    def write_report(self):
        summary = self.summary()
        print(f'summary = {ub.urepr(summary, nl=1)}')


# TODO: move rust utils to helpers


def parse_rust_content_stats(source: str, fpath=None):
    """
    Count effective Rust lines of code.

    This counts non-empty lines after removing Rust comments, while preserving
    comment-like text inside normal strings, raw strings, byte strings, and C
    strings. Rust nested block comments are handled.

    Returns:
        Dict[str, int]: contains ``main_code`` / ``main_comments`` and
        ``test_code`` / ``test_comments`` when test code is detected by path
        or ``#[cfg(test)]`` / ``#[test]`` spans. Doc comments are counted as
        comments.

    Example:
        >>> import ubelt as ub
        >>> source = ub.codeblock(
        >>>     r'''
        >>>     // module comment
        >>>
        >>>     fn main() {
        >>>         println!("http://example.com"); // trailing comment
        >>>         let text = "/* not comment */";
        >>>         let raw = r#"// not comment"#;
        >>>         /*
        >>>           block comment
        >>>           /* nested */
        >>>         */
        >>>         /// doc comment
        >>>         pub fn documented() {}
        >>>     }
        >>>     ''')
        >>> stats = parse_rust_content_stats(source)
        >>> assert stats['main_code'] == 6
        >>> assert stats['main_comments'] == 3
    """
    import collections

    n = len(source)
    i = 0
    line = 0
    line_has_code = collections.defaultdict(bool)
    comment_lines = set()

    def mark_comment_char(ch, is_doc):
        nonlocal line
        if ch == '\n':
            line += 1
        elif not ch.isspace():
            comment_lines.add(line)

    def mark_code_span(start, stop):
        nonlocal line
        j = start
        while j < stop:
            ch = source[j]
            if ch == '\n':
                line += 1
            elif not ch.isspace():
                line_has_code[line] = True
            j += 1

    while i < n:
        ch = source[i]

        # Rust line comments: //, ///, //!
        if source.startswith('//', i):
            is_doc = source.startswith('///', i) or source.startswith('//!', i)
            while i < n and source[i] != '\n':
                mark_comment_char(source[i], is_doc)
                i += 1
            continue

        # Rust nested block comments: /* ... */, /** ... */, /*! ... */
        if source.startswith('/*', i):
            is_doc = (
                source.startswith('/**', i) and
                not source.startswith('/***', i)
            ) or source.startswith('/*!', i)
            depth = 0
            while i < n:
                if source.startswith('/*', i):
                    depth += 1
                    mark_comment_char(source[i], is_doc)
                    mark_comment_char(source[i + 1], is_doc)
                    i += 2
                    continue
                if source.startswith('*/', i):
                    mark_comment_char(source[i], is_doc)
                    mark_comment_char(source[i + 1], is_doc)
                    i += 2
                    depth -= 1
                    if depth <= 0:
                        break
                    continue
                mark_comment_char(source[i], is_doc)
                i += 1
            continue

        # Rust raw strings: r"...", r#"..."#, br"...", br#"..."#.
        close_delim = _rust_raw_string_close_delim(source, i)
        if close_delim is not None:
            open_quote = source.find('"', i)
            stop = source.find(close_delim, open_quote + 1)
            if stop < 0:
                stop = n
            else:
                stop += len(close_delim)
            mark_code_span(i, stop)
            i = stop
            continue

        # Normal string-ish literals. This avoids treating // or /* inside a
        # string as a comment.
        if (
            ch == '"' or
            (ch in {'b', 'c'} and i + 1 < n and source[i + 1] == '"')
        ):
            stop = i + 1
            if ch in {'b', 'c'} and i + 1 < n and source[i + 1] == '"':
                stop = i + 2
            escape = False
            while stop < n:
                c = source[stop]
                stop += 1
                if escape:
                    escape = False
                elif c == '\\':
                    escape = True
                elif c == '"':
                    break
            mark_code_span(i, stop)
            i = stop
            continue

        if ch == '\n':
            line += 1
            i += 1
            continue

        if not ch.isspace():
            line_has_code[line] = True

        i += 1

    code_lines = {k for k, v in line_has_code.items() if v}
    test_lines = _rust_test_line_numbers(source, fpath=fpath)

    test_code_lines = len(code_lines & test_lines)
    test_comment_lines = len(comment_lines & test_lines)

    return {
        'main_code': len(code_lines) - test_code_lines,
        'main_comments': len(comment_lines) - test_comment_lines,
        'test_code': test_code_lines,
        'test_comments': test_comment_lines,
    }


def _rust_test_line_numbers(source: str, fpath=None):
    """
    Return 0-based Rust source lines that belong to test code.

    This intentionally stays lightweight: integration-test files are detected
    by path, and unit-test spans are detected from ``#[cfg(test)]`` /
    ``#[test]`` attributes with brace matching.
    """
    import bisect
    import os
    import re

    total_lines = _text_total_lines(source)
    if total_lines == 0:
        return set()

    if fpath is not None:
        parts = set(os.fspath(fpath).replace('\\', '/').split('/'))
        name = getattr(fpath, 'name', os.path.basename(os.fspath(fpath)))
        if 'tests' in parts or name in {'tests.rs', 'test.rs'}:
            return set(range(total_lines))

    line_starts = [0]
    for idx, ch in enumerate(source):
        if ch == '\n':
            line_starts.append(idx + 1)

    def line_for_pos(pos):
        return bisect.bisect_right(line_starts, pos) - 1

    test_lines = set()
    attr_pattern = re.compile(r'#\s*\[\s*(?:cfg\s*\(\s*test\s*\)|test)')
    for match in attr_pattern.finditer(source):
        start = match.start()
        open_brace = source.find('{', match.end())
        if open_brace < 0:
            continue
        close_brace = _find_matching_rust_brace(source, open_brace)
        if close_brace is None:
            close_brace = open_brace
        first_line = line_for_pos(start)
        last_line = line_for_pos(close_brace)
        test_lines.update(range(first_line, last_line + 1))
    return test_lines


def _find_matching_rust_brace(source: str, open_pos: int):
    """Find the matching brace, skipping common Rust string/comment forms."""
    n = len(source)
    i = open_pos
    depth = 0
    while i < n:
        if source.startswith('//', i):
            end = source.find('\n', i)
            i = n if end < 0 else end + 1
            continue
        if source.startswith('/*', i):
            comment_depth = 0
            while i < n:
                if source.startswith('/*', i):
                    comment_depth += 1
                    i += 2
                    continue
                if source.startswith('*/', i):
                    i += 2
                    comment_depth -= 1
                    if comment_depth <= 0:
                        break
                    continue
                i += 1
            continue
        close_delim = _rust_raw_string_close_delim(source, i)
        if close_delim is not None:
            open_quote = source.find('"', i)
            stop = source.find(close_delim, open_quote + 1)
            i = n if stop < 0 else stop + len(close_delim)
            continue
        ch = source[i]
        if (
            ch == '"' or
            (ch in {'b', 'c'} and i + 1 < n and source[i + 1] == '"')
        ):
            i += 2 if ch in {'b', 'c'} and i + 1 < n and source[i + 1] == '"' else 1
            escape = False
            while i < n:
                c = source[i]
                i += 1
                if escape:
                    escape = False
                elif c == '\\':
                    escape = True
                elif c == '"':
                    break
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _rust_raw_string_close_delim(source: str, pos: int):
    """
    Return the closing delimiter for a Rust raw string at ``pos``, or None.
    """
    n = len(source)
    if source.startswith(('br', 'cr'), pos):
        j = pos + 2
        prefix_len = 2
    elif pos < n and source[pos] == 'r':
        j = pos + 1
        prefix_len = 1
    else:
        return None

    while j < n and source[j] == '#':
        j += 1

    if j < n and source[j] == '"':
        hashes = source[pos + prefix_len:j]
        return '"' + hashes
    return None
