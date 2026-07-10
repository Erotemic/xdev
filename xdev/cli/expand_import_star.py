#!/usr/bin/env python3
"""
Replace `from <module> import *` with explicit imports for only the names actually used.

Note:
    This file was largely written by ChatGPT, but has been tested and appears
    to work well.

Usage:
    python fix_star_imports.py path/to/file.py

Notes & limitations:
- Only rewrites absolute star imports (i.e., `level == 0`). Relative (`from .x import *`)
  are skipped with a warning because the package context is ambiguous from a single file.
- Multi-line 'import *' statements are uncommon and not supported; each star import is
  expected to be on a single line.
- We conservatively detect "used names" as bare identifiers (not attributes like np.array).
  That exactly matches what star-imports bring into the namespace.
- If multiple star-import modules export the same name, we assign it to the first star
  import encountered and warn about the conflict.
"""

import ast
import builtins
import importlib
import os
from typing import Dict, List, Set, Tuple, cast

import kwconf


class ExpandImportStarCLI(kwconf.Config):
    """
    Expands / Reifies implicit imports (star imports).

    Replace 'from <module> import *' with explicit imports for used names.
    """

    path = kwconf.Value(
        None,
        position=1,
        required=True,
        help='Path to the Python file to rewrite',
    )
    inplace = kwconf.Flag(
        False,
        short_alias=['i'],
        help='if True overwrite the original file with the expanded args',
    )
    check = kwconf.Flag(
        False,
        help='if True check that the expanded import statement executes',
    )
    verbose = kwconf.Value(0, help='verbosity level')

    @classmethod
    def main(cls, argv=None, **kwargs):
        """
        Example:

        """
        args = cls.cli(
            argv=argv,
            data=kwargs,
            strict=True,
            special_options=False,
            verbose='auto',
        )

        if not os.path.isfile(args.path):
            raise FileNotFoundError(f'{args.path}')

        ret = process_file(args)  # type: ignore
        return ret


__cli__ = ExpandImportStarCLI


# ----------------------------
# AST utilities
# ----------------------------


class NameUsageCollector(ast.NodeVisitor):
    """
    Collect:
      - used_names: all bare names that are read (Load)
      - defined_names: all names that are defined anywhere (Store)
      - import_defs: names introduced by imports
      - def_names: names introduced by def/class
      - with_except_aliases: aliases introduced by `with ... as x` / `except ... as x`
    """

    def __init__(self) -> None:
        self.used_names: Set[str] = set()
        self.defined_names: Set[str] = set()
        self.import_defs: Set[str] = set()
        self.def_names: Set[str] = set()
        self.with_except_aliases: Set[str] = set()

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        elif isinstance(node.ctx, ast.Store):
            self.defined_names.add(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.def_names.add(node.name)
        self._collect_args(node.args)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.def_names.add(node.name)
        self._collect_args(node.args)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.def_names.add(node.name)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.import_defs.add(alias.asname or alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            if alias.name != '*':
                self.import_defs.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_With(self, node: ast.With):
        for item in node.items:
            if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                self.with_except_aliases.add(item.optional_vars.id)
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        for item in node.items:
            if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                self.with_except_aliases.add(item.optional_vars.id)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.name and isinstance(node.name, str):
            self.with_except_aliases.add(node.name)
        self.generic_visit(node)

    def _collect_args(self, args: ast.arguments):
        for a in (
            list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs)
        ):
            if isinstance(a, ast.arg):
                self.defined_names.add(a.arg)
        if args.vararg:
            self.defined_names.add(args.vararg.arg)
        if args.kwarg:
            self.defined_names.add(args.kwarg.arg)


def find_star_imports(tree: ast.AST) -> List[ast.ImportFrom]:
    stars: List[ast.ImportFrom] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if any(alias.name == '*' for alias in node.names):
                stars.append(node)
    return stars


def builtin_names() -> Set[str]:
    return set(dir(builtins))


# ----------------------------
# Export discovery
# ----------------------------


def discover_module_exports(module_name: str) -> Set[str]:
    """
    Return the set of names exported by a module:
    - If __all__ exists, use that.
    - Otherwise, use public attributes (not starting with underscore).
    On failure, return empty set.
    """
    try:
        mod = importlib.import_module(module_name)
    except Exception:
        return set()
    if hasattr(mod, '__all__'):
        try:
            all_list = set(getattr(mod, '__all__'))
            # Filter to identifiers
            return {
                n for n in all_list if isinstance(n, str) and n.isidentifier()
            }
        except Exception:
            pass
    try:
        return {n for n in dir(mod) if n and not n.startswith('_')}
    except Exception:
        return set()


# ----------------------------
# Rewriter
# ----------------------------


def rewrite_source_lines(
    src_lines: List[str], mapping: Dict[int, str], removals: Set[int]
) -> List[str]:
    """
    Replace specific 0-based line indices with the given text and/or drop them.
    mapping: line_index -> replacement line (with trailing newline)
    removals: set of line_index to remove entirely
    """
    out: List[str] = []
    for i, line in enumerate(src_lines):
        if i in removals:
            continue
        if i in mapping:
            out.append(mapping[i])
        else:
            out.append(line)
    return out


def build_explicit_import_line(
    module: str, names: List[str], original_indent: str
) -> str:
    # Keep lines readable if there are many names: use parentheses when long.
    joined = ', '.join(names)
    candidate = f'{original_indent}from {module} import {joined}\n'
    if len(candidate) <= 100:
        return candidate
    # Multi-line with parentheses
    inner = ',\n'.join(f'{original_indent}    {n}' for n in names)
    return f'{original_indent}from {module} import (\n{inner},\n{original_indent})\n'


# ----------------------------
# Main logic
# ----------------------------


def process_file(args: ExpandImportStarCLI) -> int:
    path = cast(str, args.path)
    text = open(path, 'r', encoding='utf-8').read()
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as e:
        print(f'[error] Failed to parse {path}: {e}')
        return 2

    stars = find_star_imports(tree)
    if not stars:
        print(
            '[info] No `from <module> import *` statements found. No changes made.'
        )
        return 0

    # Gather name usage/defs
    collector = NameUsageCollector()
    collector.visit(tree)

    defined = (
        collector.defined_names
        | collector.import_defs
        | collector.def_names
        | collector.with_except_aliases
    )
    used = collector.used_names
    builtins_set = builtin_names()

    # Candidate undefined names that might be provided by star imports
    undefined = {n for n in used if n not in defined and n not in builtins_set}

    # For each star import, compute exported names
    star_info: List[Tuple[ast.ImportFrom, Set[str]]] = []
    for node in stars:
        if (node.level or 0) > 0:
            print(
                f'[warn] Skipping relative star import at line {node.lineno}: '
                f"'from {'.' * node.level}{node.module or ''} import *'"
            )
            star_info.append((node, set()))
            continue
        if not node.module:
            star_info.append((node, set()))
            continue

        # FIXME: we shouldn't do this unless we have more than one import * and
        # we want to check.
        exports = discover_module_exports(node.module)
        if not exports:
            print(
                f"[warn] Could not determine exports for module '{node.module}' "
                f'(line {node.lineno}). Leaving as-is.'
            )
        star_info.append((node, exports))

    # Assign undefined names to a providing star-import module (first match wins)
    name_to_provider: Dict[str, ast.ImportFrom] = {}
    conflicts: Dict[str, List[str]] = {}
    unresolvable = []
    for name in sorted(undefined):
        providers = [node for (node, exports) in star_info if name in exports]
        if not providers:
            unresolvable.append(name)
            continue
        chosen = providers[0]
        name_to_provider[name] = chosen
        # Note any conflicts (multiple providers)
        if len(providers) > 1:
            conflicts.setdefault(name, []).extend(
                [p.module for p in providers if p.module]
            )

    if unresolvable:
        raise Exception('Unresolvable names: ' + ', '.join(unresolvable))

    for n, mods in conflicts.items():
        # De-duplicate and keep readable
        uniq = sorted(set(mods))
        print(
            f"[warn] Name '{n}' is exported by multiple star-import modules: {', '.join(uniq)}. Using the first encountered."
        )

    # For each star import node, collect its assigned names
    provider_to_names: Dict[ast.ImportFrom, Set[str]] = {}
    for name, node in name_to_provider.items():
        provider_to_names.setdefault(node, set()).add(name)

    # Prepare line edits
    src_lines = text.splitlines(keepends=True)
    replacements: Dict[int, str] = {}
    removals: Set[int] = set()

    for node in stars:
        line_idx = node.lineno - 1
        original_line = src_lines[line_idx]
        indent = original_line[
            : len(original_line) - len(original_line.lstrip())
        ]

        used_from_this = sorted(provider_to_names.get(node, set()))
        if (node.level or 0) > 0:
            # Relative import: leave untouched
            continue

        if not node.module:
            continue

        if not used_from_this:
            # No names used from this star import -> remove it completely
            print(
                f'[info] Removing unused star import at line {node.lineno}: from {node.module} import *'
            )
            removals.add(line_idx)
            continue

        if args.check:
            from collections import defaultdict

            # Import each name individually from the base module to verify resolvability.
            _g: Dict[str, object] = {}
            resolved: Dict[str, object] = {}
            unresolved: List[str] = []
            # FIXME: we are doing this check twice
            for _name in used_from_this:
                _l: Dict[str, object] = {}
                try:
                    # Use "as __tmp" to avoid polluting the per-name locals with arbitrary identifiers.
                    exec(f'from {node.module} import {_name} as __tmp', _g, _l)
                    resolved[_name] = _l['__tmp']
                except Exception:
                    unresolved.append(_name)

            if unresolved:
                # Fail fast with a clear, actionable error message.
                raise RuntimeError(
                    'Could not import the following names from '
                    f"'from {node.module} import *' at line {node.lineno}: "
                    f'{", ".join(sorted(unresolved))}'
                )

            # Group by where names resolve (object.__module__ or its class' module).
            name_groups: Dict[str, List[str]] = defaultdict(list)
            for _name, _obj in resolved.items():
                _mod = getattr(_obj, '__module__', None)
                if not _mod:
                    _mod = getattr(
                        getattr(_obj, '__class__', object),
                        '__module__',
                        '__ungrouped__',
                    )
                name_groups[str(_mod)].append(_name)

            # Deterministic order: base module group first (if present), then lexicographically.
            order = sorted(
                name_groups.keys(), key=lambda m: (m != node.module, m)
            )
            lines: List[str] = []
            for grp in order:
                lines.append(
                    build_explicit_import_line(
                        module=node.module,  # keep importing from the base module
                        names=sorted(
                            name_groups[grp]
                        ),  # but group by resolved origin
                        original_indent=indent,
                    )
                )
            replacements[line_idx] = ''.join(lines)

        else:
            new_line = build_explicit_import_line(
                node.module, used_from_this, indent
            )
            replacements[line_idx] = new_line

        # new_line = build_explicit_import_line(
        #     module=node.module, names=used_from_this, original_indent=indent)

        # replacements[line_idx] = new_line
        # print(f"[info] Handle line {node.lineno}: 'from {node.module} import *' -> explicit import of {len(used_from_this)} name(s)")

    # If nothing to change, exit
    if not replacements and not removals:
        print('[info] No safe rewrites determined. No changes made.')
        return 0

    new_src = rewrite_source_lines(src_lines, replacements, removals)

    if args.inplace:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(''.join(new_src))
        print(f'[success] Updated {path}')
    else:
        import xdev

        diff = xdev.difftext(
            text,
            ''.join(new_src),
            style='unified',
            fromfile=args.path,
            tofile=args.path,
            colored=True,
        )
        print(diff)
        # print(f'removals={removals}')
        # print(f'replacements={replacements}')
    return 0


def _group_names_by_defining_module(
    base_module: str, names: List[str]
) -> Dict[str, List[str]]:
    """
    Dynamically import each name from `base_module` and try to infer the module
    it actually belongs to, primarily via `obj.__module__` (fallback to
    `obj.__class__.__module__`). Group names by that module.

    If inference fails or yields something that doesn't look importable,
    fall back to the provided `base_module`.
    """
    import traceback

    groups: Dict[str, List[str]] = {}
    # We'll import into isolated globals/locals for safety
    g: Dict[str, object] = {}
    l: Dict[str, object] = {}

    for n in names:
        inferred_mod = base_module
        try:
            # Import the specific name into our empty namespace
            # Using exec so we don't leak names into our own module globals.
            exec(f'from {base_module} import {n}', g, l)
            obj = l.get(n, None)
            if obj is not None:
                mod = getattr(obj, '__module__', None)
                if not mod:
                    mod = getattr(
                        getattr(obj, '__class__', object), '__module__', None
                    )
                # Prefer a submodule beneath the base module if it matches; otherwise,
                # still allow a fully-qualified module path (e.g. 'numpy.random').
                if isinstance(mod, str) and mod:
                    inferred_mod = mod
        except Exception:
            # On failure, keep the base module; also leave a breadcrumb on stderr
            # without breaking the flow.
            print(
                f"[warn] Failed to introspect '{n}' from '{base_module}'. Using base module.",
                flush=True,
            )
            traceback.print_exc()
        groups.setdefault(inferred_mod, []).append(n)
    return groups


if __name__ == '__main__':
    __cli__.main()
