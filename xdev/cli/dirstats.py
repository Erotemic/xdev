#!/usr/bin/env python3
import scriptconfig as scfg
import ubelt as ub
import os

if not os.environ.get('_ARGCOMPLETE', ''):
    import networkx as nx
    import rich
    from kwutil.util_pattern import MultiPattern
    from progiter.manager import ProgressManager


class DirectoryStatsCLI(scfg.DataConfig):
    """
    Analysis for code in a repository

    Examples
    --------
    python ~/code/xdev/xdev/cli/repo_stats.py .
    """
    __command__ = 'dirstats'

    dpath = scfg.Value('.', type=str, help='path to the git repo. If prefixed with ``module:``, then treated as a python module', position=1)
    # block_dnames = scfg.Value('py:auto', help='A coercable multi-pattern. If "py:auto" chooses sensible defaults for a Python dev.', nargs='+')
    # block_fnames = scfg.Value('py:auto', help='A coercable multi-pattern. If "py:auto" chooses sensible defaults for a Python dev.', nargs='+')
    block_dnames = scfg.Value(None, help='A coercable multi-pattern. If "py:auto" chooses sensible defaults for a Python dev.', nargs='+')
    block_fnames = scfg.Value(None, help='A coercable multi-pattern. If "py:auto" chooses sensible defaults for a Python dev.', nargs='+')

    include_dnames = scfg.Value(None, help='A coercable multi-pattern. Only directory names matching this pattern will be considered', nargs='+')
    include_fnames = scfg.Value(None, help='A coercable multi-pattern. Only file names matching this pattern will be considered', nargs='+')

    parse_content = scfg.Value(True, isflag=True, help='if True parse stats about the content of each file')
    # parse_meta_stats = scfg.Value(True, isflag=True, help='if True parse stats about the content of each file')

    max_walk_depth = scfg.Value(None, short_alias=['L'], help='maximum depth to walk')
    max_display_depth = scfg.Value(None, short_alias=['D'], help='maximum depth to display')

    verbose = scfg.Value(0, isflag=True, short_alias=['-v'])
    version = scfg.Value(False, isflag=True, short_alias=['-V'])
    python = scfg.Value(False, isflag=True, help='enable python repository defaults', alias=['pydev'])

    def __post_init__(config):
        if config.dpath.startswith('module:'):
            config.dpath = ub.modname_to_modpath(config.dpath.split('module:', 1)[1])

        if config.python:
            if config.block_dnames is None:
                config.block_dnames = 'py:auto'
            if config.block_fnames is None:
                config.block_fnames = 'py:auto'

        if config.block_dnames == 'py:auto':
            config.block_dnames = [
                # '_*',
                '__pycache__',
                '_static',
                '_modules',
                'htmlcov',
                '.*',
            ]

        if config.block_fnames == 'py:auto':
            config.block_fnames = [
                '*.pyc',
                '*.pyi',
            ]

    @classmethod
    def _register_main(cls, func):
        cls.main = func
        return func

__cli__ = DirectoryStatsCLI


@__cli__._register_main
def main(cmdline=1, **kwargs):
    """
    Example:
        >>> # xdoctest: +SKIP
        >>> cmdline = 0
        >>> kwargs = dict(dpath='module:watch')
        >>> main(cmdline=cmdline, **kwargs)
    """
    config = DirectoryStatsCLI.cli(cmdline=cmdline, data=kwargs, strict=True)

    if config.verbose:
        kwargs = {'dpath': ub.modname_to_modpath('kwarray')}
    rich.print('config = ' + ub.urepr(config, nl=1))

    kwargs = ub.udict(config) & {
        'dpath', 'block_dnames', 'block_fnames', 'include_dnames',
        'include_fnames', 'max_walk_depth', 'parse_content'
    }
    self = DirectoryAnalysis(**kwargs)
    self.build()
    nxtxt_kwargs = {'max_depth': config['max_display_depth']}
    self.write_report(**nxtxt_kwargs)


class DirectoryAnalysis:
    def __init__(self, dpath, block_dnames=None, block_fnames=None,
                 include_dnames=None, include_fnames=None, max_walk_depth=None,
                 parse_content=True):
        self.dpath = ub.Path(dpath).resolve()
        if block_dnames is not None:
            block_dnames = MultiPattern.coerce(block_dnames)
        if block_fnames is not None:
            block_fnames = MultiPattern.coerce(block_fnames)
        if include_fnames is not None:
            include_fnames = MultiPattern.coerce(include_fnames)
        if include_dnames is not None:
            include_dnames = MultiPattern.coerce(include_dnames)
        self.block_fnames = block_fnames
        self.block_dnames = block_dnames
        self.include_fnames = include_fnames
        self.include_dnames = include_dnames
        self.max_walk_depth = max_walk_depth
        self.graph = None
        self.parse_content = parse_content
        self._topo_order = None

    def write_report(self, **nxtxt_kwargs):
        import pandas as pd
        # lines = []
        # write = lines.append
        # nx.write_network_text(self.graph, write, end='', **nxtxt_kwargs)
        try:
            nx.write_network_text(self.graph, rich.print, end='', **nxtxt_kwargs)
        except KeyboardInterrupt:
            ...
        # text = '\n'.join(lines)
        # rich.print(text)

        root_node = self._topo_order[0]

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
            disp_totals['size'] = byte_str(totals['size'])
            disp_piv = piv.copy()
            disp_piv['size'] = piv['size'].apply(byte_str)
            disp_piv = disp_piv.fillna('--')
            disp_piv.loc['∑ total'] = disp_totals
            disp_piv['files'] = disp_piv['files'].astype(int)
            return disp_piv

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
            # if self.graph.nodes[node]['ntype'] == 'dir':
            # print(f'node={node}')

        disp_piv = _node_table(root_node)
        print('')
        rich.print(disp_piv[:-1])
        rich.print(disp_piv[-1:])
        print('root_node = {}'.format(ub.urepr(root_node, nl=1)))

        # disp_stats = self._humanize_stats(stats, 'dir', reduce_prefix=True)
        # rich.print('stats = {}'.format(ub.urepr(disp_stats, nl=1)))

    def build(self):
        self._walk()
        self._update_stats()
        self._update_labels()
        self._sort()

    def _inplace_filter_dnames(self, dnames):
        if self.include_dnames is not None:
            dnames[:] = [d for d in dnames if self.include_dnames.match(d)]
        if self.block_dnames is not None:
            dnames[:] = [d for d in dnames if not self.block_dnames.match(d)]

    def _inplace_filter_fnames(self, fnames):
        if self.include_fnames is not None:
            fnames[:] = [f for f in fnames if self.include_fnames.match(f)]
        if self.block_fnames is not None:
            fnames[:] = [f for f in fnames if not self.block_fnames.match(f)]

    def _walk(self):
        dpath = self.dpath
        g = nx.DiGraph()
        g.add_node(self.dpath, label=self.dpath.name, type='dir')

        pman = ProgressManager()
        with pman:
            prog = pman.progiter(desc='Walking directory')

            if self.max_walk_depth is not None:
                start_depth = str(self.dpath).count(os.path.sep)

            for root, dnames, fnames in self.dpath.walk():
                prog.step()

                if self.max_walk_depth is not None:
                    curr_depth = str(root).count(os.path.sep)
                    rel_depth = (curr_depth - start_depth)
                    if rel_depth >= self.max_walk_depth:
                        del dnames[:]

                g.add_node(root, name=root.name, label=root.name, type='dir')
                if root != dpath:
                    g.add_edge(root.parent, root)

                # Remove directories / files that match the blocklist or dont
                # match the include list
                self._inplace_filter_dnames(dnames)
                self._inplace_filter_fnames(fnames)

                for f in fnames:
                    fpath = root / f
                    g.add_node(fpath, name=fpath.name, label=fpath.name, type='file')
                    g.add_edge(root, fpath)

        self._topo_order = list(nx.topological_sort(g))
        self.graph = g

    def _update_stats(self):
        g = self.graph

        # Get size stats for each file.
        pman = ProgressManager()
        with pman:
            prog = pman.progiter(desc='Parse File Info', total=len(g))
            for fpath, node_data in g.nodes(data=True):
                if node_data['type'] == 'file':
                    stats = parse_file_stats(fpath,
                                             parse_content=self.parse_content)
                    node_data['stats'] = stats
                prog.step()

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
                        if key not in accum_stats:
                            accum_stats[key] = 0
                        accum_stats[key] += stat_value

    def _humanize_stats(self, stats, ntype, reduce_prefix=False):
        disp_stats = {}
        if reduce_prefix:
            suffixes = [k.split('.', 1)[1] for k in stats.keys()]
            _stats = ub.udict(ub.group_items(stats.values(), suffixes)).map_values(sum)
            # _stats.update({k: v for k, v in stats.items() if k.endswith('.files')})
        else:
            _stats = stats
        if ntype == 'dir':
            for k, v in _stats.items():
                if k.endswith('.size') or k == 'size':
                    disp_stats[k] = byte_str(v)
                else:
                    disp_stats[k] = v
        elif ntype == 'file':
            disp_stats = {k.split('.', 1)[1]: v for k, v in _stats.items()}
            disp_stats.pop('files', None)
            disp_stats['size'] = byte_str(disp_stats['size'])
        else:
            raise KeyError(ntype)
        return disp_stats

    def _update_labels(self):
        g = self.graph
        for p in list(g.nodes):
            node_data = g.nodes[p]
            stats = node_data.get('stats', None)
            ntype = node_data.get('type', None)
            if stats:
                disp_stats = self._humanize_stats(stats, ntype)
                stats_text = ub.urepr(disp_stats, nl=0, compact=1)
                if ntype == 'dir':
                    color = 'blue'
                    node_data['label'] = f'[{color}][link={p}]' + node_data['name'] + f'[/link][/{color}]' + ': ' + stats_text
                elif ntype == 'file':
                    color = 'green'
                    node_data['label'] = f'[{color}]' + node_data['name'] + f'[/{color}]' + ': ' + stats_text
            else:
                if ntype == 'dir':
                    color = 'blue'
                    node_data['label'] = f'[{color}]' + node_data['name'] + f'[/{color}]'
                elif ntype == 'file':
                    color = 'green'
                    node_data['label'] = f'[{color}]' + node_data['name'] + f'[/{color}]'

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


def parse_file_stats(fpath, parse_content=True):
    """
    Get information about a file, including things like number of code lines /
    documentation lines, if that sort of information is available.
    """
    ext = fpath.suffix
    prefix = ext.lstrip('.') + '.'
    stats = {}
    is_broken = 0
    try:
        stats['size'] = fpath.stat().st_size
    except FileNotFoundError:
        is_broken = 1
        stats['broken_link'] = 1
        stats['size'] = 0

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

    CommandLine:
        xdoctest -m xdoctest.static_analysis _strip_hashtag_comments_and_newlines

    TODO:
        would be better if this was some sort of configurable minify API

    Example:
        >>> from xdoctest.static_analysis import _strip_hashtag_comments_and_newlines
        >>> from xdoctest import utils
        >>> fmtkw = dict(sss=chr(39) * 3, ddd=chr(34) * 3)
        >>> source = utils.codeblock(
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
        >>> non_comments = _strip_hashtag_comments_and_newlines(source)
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
        ['0.00KB', '0.10KB', '1.00KB', '1.00MB', '1.00GB', '1.00TB']
        >>> byte_str(10, unit='B')
        10.00B
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


if __name__ == '__main__':
    """

    CommandLine:
        python ~/code/xdev/xdev/cli/repo_stats.py
        python -m repo_analysis
    """
    main()
