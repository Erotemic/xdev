#!/usr/bin/env python3
"""
CommandLine:
    xdev availpkg numpy
    xdev availpkg opencv-python-headless
    xdev availpkg scipy
    xdev availpkg kwimage
    xdev availpkg kwcoco
    xdev availpkg torch
    xdev availpkg line_profiler
    xdev availpkg uritools
    xdev availpkg textual
"""
import scriptconfig as scfg
import ubelt as ub
from packaging.version import parse as Version


class AvailablePackageConfig(scfg.DataConfig):
    """
    Print a table of available versions of a python package on Pypi

    Refactor of ~/local/tools/supported_python_versions_pip.py to report the
    available versions of a python package that meet some critera
    """
    package_name = scfg.Value(None, position=1, help='the pypi package name')
    request_min = scfg.Value(None, help='request a minimum version')
    refresh = scfg.Value(False, isflag=1, help='if True refresh the cache')


def main(cmdline=1, **kwargs):
    """
    Example:
        >>> # xdoctest: +SKIP
        >>> cmdline = 0
        >>> kwargs = dict(
        >>> )
        >>> main(cmdline=cmdline, **kwargs)
    """
    config = AvailablePackageConfig.legacy(cmdline=cmdline, data=kwargs)
    print('config = ' + ub.urepr(dict(config), nl=1))
    minimum_cross_python_versions(**config)


class ReqPythonVersionSpec:
    """
    For python_version specs in requirements files

    Example:
        >>> pattern = '>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*'
        >>> other = '3.7.2'
        >>> reqspec = ReqPythonVersionSpec(pattern)
        >>> reqspec.highest_explicit()
        >>> reqspec.matches('2.6')
        >>> reqspec.matches('2.7')

    Example:
        >>> self = ReqPythonVersionSpec('~=3.2')
        >>> self.highest_explicit()
    """
    def __init__(self, pattern):
        from packaging.specifiers import SpecifierSet
        self.pattern = pattern
        self.parts = pattern.split(',')
        self.specifier = SpecifierSet(pattern)

        self.constraints = []
        for part in self.parts:
            try:
                oppat, partpat = part.split('=')
                opsuf = '='
            except Exception:
                try:
                    oppat, partpat = part.split('<')
                    opsuf = '<'
                except Exception:
                    oppat, partpat = part.split('>')
                    opsuf = '>'
            opstr = (oppat + opsuf).strip()
            idx = None
            if '.*' in partpat:
                verpat_parts = partpat.split('.')
                idx = verpat_parts.index('*')
                partpat.split('.')
                partver = Version('.'.join(verpat_parts[0:idx]))
            else:
                partver = Version(partpat)
            self.constraints.append({
                'opstr': opstr,
                'idx': idx,
                'partver': partver,
            })

    def highest_explicit(self):

        return max(c['partver'] for c in self.constraints if c['opstr'] in {'>=', '~='})

    def matches(self, other):
        return other in self.specifier

        flag = True
        for constraint in self.constraints:
            idx = constraint['idx']
            pyver_ = Version('.'.join(other.split('.')[0:idx]))
            partver = constraint['partver']
            opstr = constraint['opstr']
            try:
                if opstr == '>':
                    flag &= pyver_ > partver
                elif opstr == '<':
                    flag &= pyver_ < partver
                if opstr == '>=':
                    flag &= pyver_ >= partver
                elif opstr == '<=':
                    flag &= pyver_ <= partver
                elif opstr == '!=':
                    flag &= pyver_ != partver
                elif opstr == '==':
                    flag &= pyver_ == partver
                elif opstr == '!=':
                    flag &= pyver_ == partver
                else:
                    raise KeyError(opstr)
            except Exception:
                print('partver = {!r}'.format(partver))
                print('pyver_ = {!r}'.format(pyver_))
                raise

        return flag


def parse_platform_tag(platform_tag):
    """
    Parse finer grained information out of the package platform tag.

    Example:
        >>> cases = [
        >>>     'manylinux1_x86_64',
        >>>     'macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64',
        >>>     'manylinux1_i686',
        >>>     'win32',
        >>>     'win_amd64',
        >>>     'macosx_10_9_x86_64',
        >>>     'macosx_10_9_intel',
        >>>     'macosx_10_6_intel',
        >>>     'manylinux2010_i686',
        >>>     'manylinux2010_x86_64',
        >>>     'manylinux2014_aarch64',
        >>>     'manylinux_2_12_i686.manylinux2010_i686',
        >>>     'manylinux_2_12_x86_64.manylinux2010_x86_64',
        >>>     'manylinux_2_17_aarch64.manylinux2014_aarch64',
        >>>     'manylinux_2_5_i686.manylinux1_i686',
        >>>     'manylinux_2_5_x86_64.manylinux1_x86_64',
        >>>     'macosx_10_9_universal2',
        >>>     'macosx_11_0_arm64',
        >>>     'manylinux_2_17_x86_64.manylinux2014_x86_64',
        >>>     'macosx_10_14_x86_64',
        >>>     'macosx_10_15_x86_64',
        >>>     'macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64']
        >>> for platform_tag in cases:
        >>>     plat_info = parse_platform_tag(platform_tag)
        >>>     print(f'platform_tag={platform_tag}')
        >>>     print('plat_info = {}'.format(ub.repr2(plat_info, nl=1)))
    """
    if platform_tag == 'any':
        return {
            'os': 'any',
            'arch': 'any',
        }
    parts = platform_tag.split('.')
    os_coarse_parts = []
    os_versions_parts = []
    arch_parts = []
    for part in parts:
        if part == 'win32':
            osver_part = 'win'
            arch_part = 'i686'  # is this right?
        else:
            sub_parts = part.split('_')
            if sub_parts[-1] == '64':
                arch_idx = -2
            else:
                arch_idx = -1
            osver_part = '_'.join(sub_parts[:arch_idx])
            arch_part = '_'.join(sub_parts[arch_idx:])

        if arch_part == 'intel':
            arch_part = 'x86_64'

        if 'linux' in osver_part:
            os_coarse = 'linux'
        elif 'macosx' in osver_part:
            os_coarse = 'macosx'
        elif 'win' in osver_part:
            os_coarse = 'win'
        else:
            raise NotImplementedError(osver_part)
        os_coarse_parts.append(os_coarse)
        os_versions_parts.append(osver_part)
        arch_parts.append(arch_part)

    os_coarse_parts = sorted(set(os_coarse_parts))
    arch_parts = sorted(set(arch_parts))

    # Hack
    if arch_parts == ['universal2', 'x86_64']:
        arch_parts = arch_parts[1:]

    # assert len(arch_parts) == 1, str(platform_tag)
    # assert len(os_coarse_parts) == 1, str(platform_tag)

    arch = arch_parts[0]
    if arch == 'amd64':
        arch = 'x86_64'
    os = os_coarse_parts[0]
    plat_info = {
        'os': os,
        'arch': arch,
        'osver': sorted(set(os_versions_parts)),
    }
    return plat_info


def parse_wheel_name(fname):
    import parse
    # Is there a grammer modification to make that can make one pattern that captures both cases?
    # wheen_name_parser = parse.Parser('{distribution}-{version}(-{build_tag})?-{python_tag}-{abi_tag}-{platform_tag}.whl')
    wheel_name_parser1 = parse.Parser('{distribution}-{version}-{build_tag}-{python_tag}-{abi_tag}-{platform_tag}.whl')
    wheel_name_parser2 = parse.Parser('{distribution}-{version}-{python_tag}-{abi_tag}-{platform_tag}.whl')
    result = wheel_name_parser1.parse(fname) or wheel_name_parser2.parse(fname)
    if result is not None:
        return result.named
    return None


def grab_pypi_items(package_name, refresh=False):
    """
    Get all the information about a package from pypi

    Ignore:
        package_name = 'ubelt'
    """
    import pandas as pd
    import json
    url = "https://pypi.org/pypi/{}/json".format(package_name)
    if 0:
        import requests
        resp = requests.get(url)
        assert resp.status_code == 200
        pypi_package_data = json.loads(resp.text)
    else:
        fpath = ub.Path(
            ub.grabdata(
                url, fname=ub.hash_data(url + 'v2'),
                redo=refresh,
                expires=8 * 60 * 60)
        )
        pypi_package_data = json.loads(fpath.read_text())

    all_releases = pypi_package_data['releases']
    available_releases = {
        version: [item for item in items if not item['yanked']]
        for version, items in all_releases.items()
    }

    flat_table = []
    for version, items in available_releases.items():
        for item in items:
            packagetype = item['packagetype']
            if packagetype == 'sdist':
                pass
            elif packagetype == 'bdist_egg':
                # not handled, sqlalchemy has an example.
                pass
            elif packagetype == 'bdist_wininst':
                # not handled, pandas has an example.
                pass
            elif packagetype == 'bdist_rpm':
                # not handled, IPython has an example.
                pass
            elif packagetype == 'bdist_wheel':
                wheel_info = parse_wheel_name(item['filename'])
                if wheel_info:
                    common = ub.dict_isect(item, wheel_info)
                    common1 = ub.dict_subset(item, common)
                    common2 = ub.dict_subset(wheel_info, common)
                    assert common1 == common2
                    item.update(wheel_info)
            else:
                raise KeyError(f'{packagetype} for {package_name}')
            item['pkg_version'] = version

            platform_tag = item.get('platform_tag', None)
            if platform_tag is not None:
                platinfo = parse_platform_tag(platform_tag)
                item['os'] = platinfo['os']
                item['arch'] = platinfo['arch']

            flat_table.append(item)
    table = pd.DataFrame(flat_table)
    return table


def vectorize(func):
    def wrp(arr):
        out = []
        for x in arr:
            try:
                y = func(x)
            except Exception:
                y = None
            out.append(y)
        return out
        # return [func(x) for x in arr]
    return wrp


def cp_sorter(v):
    import re
    v = str(v.split('_')[0])
    num = re.sub('[a-z]', '', v)
    a = num[0:1]
    b = num[1:]
    try:
        a = int(a)
    except Exception:
        a = -1
    try:
        b = int(b)
    except Exception:
        b = -1
    return (a, b)


def summarize_package_availability(package_name):
    """
    TODO:
        for each released version of the package we want to know

        * For source distros:
            * Does it need to be compiled?
            * What are is the min (or max?) python version
        * For binaries:
            * What python version, arch, and os targets are available.

    Ignore:
        import sys, ubelt
        sys.path.append(ubelt.expandpath('~/local/tools'))
        from supported_python_versions_pip import *  # NOQA
        test_packages = [
            'numpy', 'scipy', 'kwarray', 'pandas', 'ubelt', 'jq', 'kwimage',
        ]
        for package_name in test_packages:
            summarize_package_availability(package_name)
        package_name = 'sqlalchemy'
        package_name = 'scipy'
        package_name = 'numpy'
        package_name = 'kwarray'
        package_name = 'pandas'
        package_name = 'ubelt'
        package_name = 'jq'
        package_name = 'torch'
        summarize_package_availability(package_name)
    """
    import numpy as np
    import pandas as pd
    flat_table = grab_pypi_items(package_name)

    new = []
    for item in flat_table.to_dict('records'):
        # Hack for mac
        if item.get('python_version', None) is not None:
            if item.get('abi_tag', None) is None:
                item['abi_tag'] = item['python_version']
        new.append(item)
    flat_table = pd.DataFrame(new)

    if 1:
        df = pd.DataFrame(flat_table)
        df = df.drop(df.columns.intersection([
            'digests', 'downloads', 'comment_text', 'has_sig',
            # 'filename',
            'size',
            'url', 'upload_time', 'upload_time_iso_8601', 'distribution',
            'md5_digest', 'yanked', 'yanked_reason']), axis=1)

        # def vec_ver(vs):
        #     return [Version(v) for v in vs]

        vec_sorter = vectorize(cp_sorter)

        flags = (df['packagetype'] != 'sdist')
        if not np.any(flags):
            df = df[flags]

        flags = (df['abi_tag'] != 'none')
        if np.any(flags):
            df = df[flags]

        if 0:
            counts = df.value_counts(['pkg_version', 'abi_tag', 'os']).to_frame('count').reset_index()
            # piv = counts.to_frame('count').reset_index().pivot(['pkg_version', 'abi_tag'], 'os', 'count')
            counts = counts.sort_values('abi_tag')
            # counts.sort_values('abi_tag', key=vec_sorter)
            # counts = counts.sort_values('abi_tag')
            piv = counts.pivot(['pkg_version'], ['abi_tag', 'os'], 'count')
        else:
            abi_blocklist = {
                # 'cp36m',
                'cp26m', 'cp26mu', 'cp27m', 'cp27mu', 'cp32m', 'cp33m', 'cp34m', 'cp35m',
                'pypy36_pp73', 'pypy37_pp73', 'pypy38_pp73', 'pypy_73', 'pypy_41'
            }
            flags = df['abi_tag'].apply(lambda x: x in abi_blocklist)
            if np.any(~flags):
                df = df[~flags]

            try:
                counts = df.value_counts(['pkg_version', 'abi_tag', 'os', 'arch']).to_frame('count').reset_index()
            except KeyError:
                counts = []
            if len(counts):
                counts = counts.sort_values('abi_tag')
                piv = counts.pivot(['pkg_version'], ['abi_tag', 'os', 'arch'], 'count')
            else:
                counts = df.value_counts(['pkg_version', 'requires_python'], dropna=False).to_frame('count').reset_index()
                piv = counts.pivot(['pkg_version'], ['requires_python'], 'count')

        vec_ver = vectorize(Version)
        # vec_sorter(['cp310', 'cp27'])
        vec_sorter(df.abi_tag)
        try:
            piv = piv.sort_values('os', axis=1)
        except Exception:
            pass
        try:
            piv = piv.sort_values('abi_tag', axis=1, key=vec_sorter)
        except Exception:
            pass
        try:
            piv = piv.sort_values('pkg_version', key=vec_ver)
        except Exception:
            pass
        import rich
        rich.print('')
        rich.print('package_name = {}'.format(ub.repr2(package_name, nl=1)))
        rich.print(piv.to_string())


def minimum_cross_python_versions(package_name, request_min=None, refresh=False):
    """
    package_name = 'scipy'
    request_min = None

    package_name = 'opencv-python-headless'

    package_name = 'numpy'
    request_min = '1.21.0'
    """
    import pandas as pd
    if request_min is not None:
        request_min = Version(request_min)

    table = grab_pypi_items(package_name, refresh=refresh)
    table = table[~table['yanked']]

    ignore_cols = ['digests', 'downloads', 'comment_text', 'md5_digest',
                   'yanked_reason', 'url', 'upload_time', 'filename',
                   'build_tag', 'distribution']
    ignore_cols = table.columns.intersection(ignore_cols)
    table = table.drop(ignore_cols, axis=1)

    # For each version, ignore the sdist if a bdist exists
    keepers = []
    for pkg_version, group in table.groupby('pkg_version'):
        # Skip release candidates, alphas, and betas
        if any(c in pkg_version for c in ['rc', 'a', 'b']):
            continue
        if len(group['packagetype'].unique()) > 1:
            keepers.append(group[group['packagetype'] != 'sdist'])
        else:
            keepers.append(group)

    table = pd.concat(keepers)

    python_vstrings = [
        '2.6', '2.7', '3.0', '3.1', '3.2', '3.3', '3.4', '3.5',
        '3.6', '3.7', '3.8', '3.9',
        '3.10', '3.11'
    ]

    # https://en.wikipedia.org/wiki/History_of_Python#Version_3

    python_version_rows = [
        {'release_date': '2021-10-04', 'pyver': '3.11'},
        {'release_date': '2021-10-04', 'pyver': '3.10'},
        {'release_date': '2020-10-05', 'pyver': '3.9'},
        {'release_date': '2019-10-14', 'pyver': '3.8'},
        {'release_date': '2018-06-27', 'pyver': '3.7'},
        {'release_date': '2016-12-23', 'pyver': '3.6'},
        {'release_date': '2015-09-13', 'pyver': '3.5'},
        {'release_date': '2014-03-16', 'pyver': '3.4'},

        {'release_date': '2012-09-29', 'pyver': '3.3'},
        {'release_date': '2011-02-20', 'pyver': '3.2'},
        {'release_date': '2009-06-27', 'pyver': '3.1'},
        {'release_date': '2008-12-03', 'pyver': '3.0'},

        {'release_date': '2010-07-03', 'pyver': '2.7'},
        {'release_date': '2008-10-01', 'pyver': '2.6'},
    ]
    python_version_table = pd.DataFrame(python_version_rows)
    python_version_table = python_version_table.set_index('pyver', drop=0)
    python_version_table['release_date'] = python_version_table['release_date'].apply(ub.timeparse)

    cp_codes = {'cp{}{}'.format(*v.split('.')): v for v in python_vstrings}

    doubledigit_pyvers = [v for v in python_vstrings if len(v.split('.')[1]) > 1]
    cp_codes.update({'cp{}_{}'.format(*v.split('.')): v for v in doubledigit_pyvers})

    # Go through packages versions in reverse order.  If at some point, the
    # python requirements disappear, assume the maintainer did not set them and
    # use the last seen from the more recent packages.

    hacked_pkgver_to_pyvers = ub.ddict(set)

    last_min_pyver = None
    new_rows = []
    for pkg_version, subdf in sorted(table.groupby('pkg_version'), key=lambda x: Version(x[0]))[::-1]:
        for row in subdf.to_dict('records'):
            min_pyver = None
            max_pyver = None
            if row['python_version'] is not None:
                min_pyver = cp_codes.get(row['python_version'], row['python_version'])
                max_pyver = cp_codes.get(row['python_version'], row['python_version'])

            upload_time = ub.timeparse(row['upload_time_iso_8601'])
            flags = [upload_time >= t for t in python_version_table['release_date']]
            contemporary_pyvers = python_version_table['pyver'][flags].tolist()

            heuristic_support = None

            if row['requires_python']:
                requires_python = row['requires_python']
                reqspec = ReqPythonVersionSpec(requires_python)
                min_pyver = reqspec.highest_explicit()
                # min_pyver = min_pyver.vstring
                min_pyver = min_pyver.base_version
                last_min_pyver = min_pyver

                # Declared support is generally only good for the python
                # versions that existed at the time.
                declared_support = [v for v in python_vstrings if reqspec.matches(v)]
                heuristic_support = set(contemporary_pyvers) & set(declared_support)
                max_pyver = max(heuristic_support, key=Version)

            if min_pyver == 'py2.py3':
                min_pyver = '2.7'
            if min_pyver == 'py3':
                min_pyver = '3.6'

            if max_pyver == 'py2.py3':
                max_pyver = '2.7'
            if max_pyver == 'py3':
                max_pyver = '3.6'

            if row.get('abi_tag', None) is not None:
                abi_tag = str(row['abi_tag'])
                if abi_tag.startswith('cp'):
                    # Specific ABI, be restrictive
                    max_pyver = row['abi_tag'].replace('m', '').replace('u', '')
                    ...
                if abi_tag == 'abi3':
                    # General ABI Be permissive here.
                    ...

            min_pyver = cp_codes.get(min_pyver, min_pyver)
            max_pyver = cp_codes.get(max_pyver, max_pyver)
            if min_pyver == 'source':
                min_pyver = None
            if max_pyver == 'source':
                max_pyver = None

            # Skip pypy for now
            if min_pyver is not None and min_pyver.startswith('pp'):
                continue
            if max_pyver is not None and max_pyver.startswith('pp'):
                continue

            if min_pyver is None:
                # TODO: can use better heuristics here
                min_pyver = last_min_pyver

            row['min_pyver'] = min_pyver
            row['max_pyver'] = max_pyver

            if heuristic_support is not None:
                if max_pyver is not None:
                    heuristic_support = [v for v in heuristic_support if Version(v) <= Version(max_pyver)]
                    heuristic_support = [v for v in heuristic_support if Version(v) >= Version(min_pyver)]
                hacked_pkgver_to_pyvers[pkg_version].update(heuristic_support)

            if min_pyver is not None:
                hacked_pkgver_to_pyvers[pkg_version].add(min_pyver)

            new_rows.append(row)

    # FIXME: get the real support
    hacked_pyver_to_pkgvers = ub.ddict(set)
    for pkgver, pyvers in hacked_pkgver_to_pyvers.items():
        for pyver in pyvers:
            hacked_pyver_to_pkgvers[pyver].add(pkgver)

    new_table = pd.DataFrame(new_rows)
    new_table = new_table.sort_values('pkg_version', key=vectorize(Version))
    import rich
    rich.print(new_table.to_string())
    rich.print(new_table['min_pyver'].unique())
    rich.print(new_table['max_pyver'].unique())

    summarize_package_availability(package_name)

    chosen_minmax_for = {}
    chosen_minimum_for = {}

    # groups = dict(list(new_table.groupby('min_pyver')))

    for min_pyver, subdf in sorted(new_table.groupby('min_pyver'), key=lambda x: Version(x[0])):
        # print('--- min_pyver = {!r} --- '.format(min_pyver))
        version_to_support = dict(list(subdf.groupby('version')))

        cand_to_score = {}
        try:
            version_to_support = ub.sorted_keys(version_to_support, key=Version)
        except Exception:
            maybe_bad_keys = list(version_to_support.keys())
            print('version_to_support = {!r}'.format(maybe_bad_keys))
            maybe_ok_keys = [k for k in maybe_bad_keys if '.dev0' not in k]
            version_to_support = ub.dict_subset(version_to_support, maybe_ok_keys)

        combo_values = {
            ('linux', 'x86_64'): 101,
            ('macosx', 'x86_64'): 5,
            ('win', 'x86_64'): 11,
        }
        for cand, support in version_to_support.items():
            has_combos = support.value_counts(['os', 'arch']).index.tolist()
            total_have = sum(combo_values.get(k, 0) for k in has_combos)
            score = total_have
            cand_to_score[cand] = score

        cand_to_score = ub.sorted_vals(cand_to_score)
        cand_to_score = ub.sorted_keys(cand_to_score, key=Version)

        # Filter to only the versions we requested, but if
        # none exist, return something
        if request_min is not None:
            valid_cand = [cand for cand in cand_to_score if Version(cand) >= request_min]
        else:
            valid_cand = [cand for cand in cand_to_score]
        if len(valid_cand) == 0:
            valid_cand = list(cand_to_score)
        cand_to_score = {c: cand_to_score[c] for c in valid_cand}

        # This is a proxy metric, but a pretty good one in 2021
        if len(cand_to_score) == 0:
            pass
            # print('no cand for')
            # print(f'min_pyver={min_pyver}')
        else:
            max_score = max(cand_to_score.values())
            min_cand = min(cand_to_score.keys())

            best_cand = min([
                cand for cand, score in cand_to_score.items()
                if score == max_score
            ], key=Version)
            max_cand = max([
                cand for cand, score in cand_to_score.items()
            ], key=Version)
            # print('best_cand = {!r}'.format(best_cand))
            # print('max_cand = {!r}'.format(max_cand))
            chosen_minmax_for[min_pyver] = {
                'min': min_cand,
                'best': best_cand,
                'max': max_cand
            }

    # For each Python version find the minimum and maximum Package version it
    # can handle
    # TODO: implement this
    for pyver in python_vstrings:
        pass

    # TODO better logic:
    # FOR EACH PYTHON VERSION
    # find the minimum version that will work with that Python version.
    rich.print('chosen_minmax_for = {}'.format(ub.repr2(chosen_minmax_for, nl=1)))

    chosen_minimum_for = {k: t['best'] for k, t in chosen_minmax_for.items()}

    # HACK because our other logic is wrong too
    if 1:
        for pyver, pkgvers in hacked_pyver_to_pkgvers.items():
            if pyver not in chosen_minimum_for:
                chosen_minimum_for[pyver] = min(pkgvers, key=Version)

    python_versions = sorted(chosen_minimum_for, key=Version)
    lines = []
    for cur_pyver, next_pyver in ub.iter_window(python_versions, 2):
        pkg_ver = chosen_minimum_for[cur_pyver]
        if not pkg_ver.startswith('stdlib'):
            line = f"{package_name}>={pkg_ver:<8}  ; python_version < {next_pyver!r:<6} and python_version >= {cur_pyver!r:<6}    # Python {cur_pyver}"
            lines.append(line)
        else:
            line = f"# {package_name}>={pkg_ver:<8} is in the stdlib for python_version < '{next_pyver}' and python_version >= '{cur_pyver}'    # Python {cur_pyver}"
            lines.append(line)
    # last
    # https://peps.python.org/pep-0508/
    cur_pyver = python_versions[-1]
    pkg_ver = chosen_minimum_for[cur_pyver]
    if not pkg_ver.startswith('stdlib'):
        # line =     f"{package_name}>={pkg_ver:<8}  ;                             python_version >= {cur_pyver!r:<6}    # Python {cur_pyver}+"
        next_pyver = '4.0'
        line =     f"{package_name}>={pkg_ver:<8}  ; python_version < '{next_pyver}'  and python_version >= {cur_pyver!r:<6}    # Python {cur_pyver}+"
        lines.append(line)
    else:
        line = f"# {package_name}>={pkg_ver:<8} is in the stdlib for python_version < '{next_pyver}' and python_version >= '{cur_pyver}'    # Python {cur_pyver}"
        lines.append(line)
    text = '\n'.join(lines[::-1])
    rich.print(text)


def demo():
    package_names = [
        'ipykernel',
        'IPython',
        # minimum_cross_python_versions(package_name),
        'nbconvert',
        'jupyter_core',
        'pytest',
        'pytest_cov',
        'pytest',
        'jinja2',
        'nbconvert',
        'attrs',
        'jupyter_core',
        'nbclient',
        'jsonschema',
        'numexpr',
        'networkx',
        'coverage',
        'pandas',
        'numpy',
        'scipy',
        'kwcoco',
        'kwimage',
        'ubelt',
        'line_profiler',
        'torch',
        'sqlalchemy',
        'kwarray',
        'uritools',
        'jq',
    ]

    for package_name in package_names:
        minimum_cross_python_versions(package_name)

if __name__ == '__main__':
    """

    CommandLine:
        python ~/code/xdev/xdev/cli/available_package_versions.py
        python -m xdev.cli.available_package_versions
    """
    main()
