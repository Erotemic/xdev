import os
import rich
import ubelt as ub
import networkx as nx
from xdev.patterns import MultiPattern
from progiter.manager import ProgressManager


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
                 show_progress=True,
                 ignore_empty_dirs=False,
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
                if True, include content analysis

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
        self.max_files = max_files
        self.show_progress = show_progress
        self.ignore_empty_dirs = ignore_empty_dirs

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

    def write_network_text(self, **kwargs):
        nx.write_network_text(self.graph, rich.print, end='', **kwargs)

    def write_report(self, **nxtxt_kwargs):
        import pandas as pd
        try:
            self.write_network_text(**nxtxt_kwargs)
        except KeyboardInterrupt:
            ...

        if len(self._topo_order):
            root_node = self._topo_order[0]
        else:
            root_node = None

        def _node_table(node):
            node_data = self.graph.nodes[node]
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
            return disp_piv

        if root_node:
            child_rows = []
            for node in self.graph.succ[root_node]:
                disp_piv = _node_table(node)
                row = disp_piv.iloc[-1].to_dict()
                row['name'] = self.graph.nodes[node]['name']
                child_rows.append(row)
            if child_rows:
                print('')
                df = pd.DataFrame(child_rows)
                if 'total_lines' in df.columns:
                    df = df.sort_values('total_lines')
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
        for node in self._topo_order[::-1]:
            children = g.succ[node]
            node_data = g.nodes[node]
            if node_data['type'] == 'dir':
                node_data['stats'] = accum_stats = {}
                for child in children:
                    child_data = g.nodes[child]
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
        pman = ProgressManager()
        with pman:
            prog = pman.progiter(desc='Parse File Info', total=len(g))
            for fpath, node_data in g.nodes(data=True):
                if node_data['type'] == 'file':
                    stats = parse_file_stats(fpath,
                                             parse_content=self.parse_content, fs=fs)
                    node_data['stats'] = stats
                prog.step()
        self._accum_stats()

    def _update_stats2(self):

        # Variant that uses parallel process boilerplate
        def worker(fpath):
            stats = parse_file_stats(fpath, parse_content=self.parse_content)
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
                for path, data in graph.nodes(data=True)
                if data['isfile']
            ]
            prog = ub.ProgIter(fpaths, desc=submit_desc, total=len(fpaths),
                               homogeneous=False)
            for fpath in prog:
                job = jobs.submit(func, fpath)
                job.fpath = fpath

            for job in ub.ProgIter(jobs.as_completed(), desc=collect_desc,
                                   total=len(jobs)):
                fpath = job.fpath
                result = job.result()
                yield fpath, result

    def _humanize_stats(self, stats, node_type, reduce_prefix=False):
        disp_stats = {}
        if reduce_prefix:
            suffixes = [k.split('.', 1)[1] for k in stats.keys()]
            _stats = ub.udict(ub.group_items(stats.values(), suffixes)).map_values(sum)
            # _stats.update({k: v for k, v in stats.items() if k.endswith('.files')})
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
        for path, node_data in self.graph.nodes(data=True):
            if node_data['isfile']:
                node_data[hasher] = ub.hash_file(path, hasher=hasher)

        hash_to_paths = ub.ddict(list)
        for path, node_data in self.graph.nodes(data=True):
            if node_data['isfile']:
                hash = node_data[hasher]
                hash_to_paths[hash].append(path)

        hash_to_paths = ub.udict(hash_to_paths)
        dups = []
        for k, v in hash_to_paths.items():
            if len(v) > 1:
                dups.append(k)
        dup_hash_to_paths = hash_to_paths & dups
        print('dup_hash_to_paths = {}'.format(ub.urepr(dup_hash_to_paths, nl=2)))

    def _update_path_metadata(self):
        g = self.graph
        for path in self._topo_order:
            node_data = g.nodes[path]

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

        for path, node_data in self.graph.nodes(data=True):
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
        ordered_nodes = dict(g.nodes(data=True))
        ordered_edges = []
        for node in self._topo_order[::-1]:
            # Sort children by total lines
            children = g.succ[node]
            children = ub.udict({c: g.nodes[c] for c in children})
            children = children.sorted_keys(lambda c: (g.nodes[c]['type'], g.nodes[c].get('stats', {}).get('total_lines', 0)), reverse=True)
            for c, d in children.items():
                ordered_nodes.pop(c, None)
                ordered_nodes[c] = d
                ordered_edges.append((node, c))

            # ordered_nodes.update(children)

        assert not (set(g.edges) - set(ordered_edges))
        new = nx.DiGraph()
        new.add_nodes_from(ordered_nodes.items())
        new.add_edges_from(ordered_edges)
        self.graph = new


def parse_file_stats(fpath, parse_content=True, fs=None):
    """
    Get information about a file, including things like number of code lines /
    documentation lines, if that sort of information is available.
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
        try:
            text = fpath.read_text()
        except UnicodeDecodeError:
            # Binary file
            ...
        else:
            total_lines = text.count('\n')
            stats['total_lines'] = total_lines

            if ext == '.py':
                try:
                    raw_code = strip_comments_and_newlines(text)
                    code_lines = raw_code.count('\n')
                except Exception:
                    ...
                else:
                    stats['code_lines'] = code_lines

                try:
                    # TODO: this belongs more in the pypackage summarizer
                    # from xdoctest.core import package_calldefs
                    from xdoctest.static_analysis import TopLevelVisitor
                    self = TopLevelVisitor.parse(text)
                    calldefs = self.calldefs
                    total_doclines = 0
                    for k, v in calldefs.items():
                        if v.docstr is not None:
                            total_doclines += v.docstr.count('\n')
                except Exception:
                    ...
                else:
                    stats['doc_lines'] = total_doclines

    stats = {prefix + k: v for k, v in stats.items()}
    return stats


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


def _null_coerce(cls, arg, **kwargs):
    if arg is None:
        return arg
    else:
        return cls.coerce(arg, **kwargs)
