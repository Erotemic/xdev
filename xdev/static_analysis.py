import ast
import sys
import re
from os.path import join, dirname, exists


class CodeAnalyzer(ast.NodeVisitor):
    """
    Analyzes a Python file and constructs a directed graph (DiGraph) to represent
    the nesting structure of classes and functions.

    References:
        https://chat.deepseek.com/a/chat/s/12ab67dd-5350-46f1-b560-f28532be743d

    Ignore:
        >>> # xdoctest: +REQUIRES(module:networkx)
        >>> from xdev.cli.pypackage_summary import *  # NOQA
        >>> from xdev.cli import pypackage_summary
        >>> import networkx as nx
        >>> fpath = pypackage_summary.__file__
        >>> self = CodeAnalyzer.parse_file(fpath)
        >>> import networkx as nx
        >>> nx.write_network_text(self.graph)

    Example:
        >>> # xdoctest: +REQUIRES(module:networkx)
        >>> from xdev.cli.pypackage_summary import *  # NOQA
        >>> import ubelt as ub
        >>> text = ub.codeblock(
        ...     '''
        ...     import os
        ...     from math import sqrt
        ...
        ...     class MyClass:
        ...         import sys
        ...
        ...         def __init__(self):
        ...             from datetime import datetime
        ...
        ...         def method1(self):
        ...             import json
        ...
        ...     def my_function(a, b):
        ...         import re
        ...         return a + b
        ...     ''')
        >>> self = CodeAnalyzer(modname='testmod')
        >>> self.parse(text)
        >>> import networkx as nx
        >>> nx.write_network_text(self.graph)
        ╟── os
        ╟── math.sqrt
        ╟── MyClass
        ╎   ├─╼ sys
        ╎   ├─╼ MyClass.__init__
        ╎   │   └─╼ datetime.datetime
        ╎   └─╼ MyClass.method1
        ╎       └─╼ json
        ╙── my_function
            └─╼ re
    """
    def __init__(self, fpath=None, modname=None):
        import networkx as nx
        self.fpath = fpath
        self.modname = modname
        self.graph = nx.DiGraph()  # Directed graph to represent nesting
        self.current_scope = []  # Stack to track the current nesting scope

    def parse(self, text):
        # Parse the source code into an AST
        tree = ast.parse(text)
        self.visit(tree)

    @classmethod
    def parse_file(CodeAnalyzer, fpath):
        with open(fpath, "r") as file:
            source_code = file.read()

        # Create an instance of the analyzer and visit the AST
        analyzer = CodeAnalyzer(fpath)
        analyzer.parse(source_code)
        return analyzer

    def _add_node(self, name, node_type):
        """
        Add a node to the graph with the given name and type.
        """
        self.graph.add_node(name, type=node_type, name=name.split(".")[-1])

    def _add_edge(self, parent, child):
        """
        Add an edge from the parent node to the child node.
        """
        self.graph.add_edge(parent, child)

    def _enter_scope(self, name):
        """
        Enter a new scope (e.g., a class or function).
        """
        self.current_scope.append(name)

    def _exit_scope(self):
        """
        Exit the current scope.
        """
        self.current_scope.pop()

    def _get_full_name(self, name):
        """
        Construct the full name of a node based on the current scope.
        """
        return ".".join(self.current_scope + [name]) if self.current_scope else name

    def visit_FunctionDef(self, node):
        # Construct the full name of the function
        full_name = self._get_full_name(node.name)

        # Add the function node to the graph
        self._add_node(full_name, "function")

        # If there is a parent scope, add an edge from the parent to this function
        if self.current_scope:
            self._add_edge(self.current_scope[-1], full_name)

        # Enter the function scope
        self._enter_scope(full_name)
        self.generic_visit(node)  # Continue visiting child nodes
        self._exit_scope()  # Exit the function scope

    def visit_ClassDef(self, node):
        # Construct the full name of the class
        full_name = self._get_full_name(node.name)

        # Add the class node to the graph
        self._add_node(full_name, "class")

        # If there is a parent scope, add an edge from the parent to this class
        if self.current_scope:
            self._add_edge(self.current_scope[-1], full_name)

        # Enter the class scope
        self._enter_scope(full_name)
        self.generic_visit(node)  # Continue visiting child nodes
        self._exit_scope()  # Exit the class scope

    def visit_Import(self, node):
        # Extract imported modules
        for alias in node.names:
            full_name = alias.name
            self._add_node(full_name, "import")

            # If there is a parent scope, add an edge from the parent to this import
            if self.current_scope:
                self._add_edge(self.current_scope[-1], full_name)
        self.generic_visit(node)  # Continue visiting child nodes

    def visit_ImportFrom(self, node):
        # Extract imported items from a module
        module = node.module
        level = node.level  # Number of leading dots for relative imports

        # Handle relative import names
        if level > 0:
            if self.modname:
                mod_parts = self.modname.split(".")
                base_module = ".".join(mod_parts[:-level])
                module = f"{base_module}.{module}" if module else base_module
            else:
                module = "." * level + (module if module else "")

        for alias in node.names:
            full_name = f"{module}.{alias.name}" if module else alias.name
            self._add_node(full_name, "import")

            # If there is a parent scope, add an edge from the parent to this import
            if self.current_scope:
                self._add_edge(self.current_scope[-1], full_name)
        self.generic_visit(node)  # Continue visiting child nodes


def parse_requirements(fname="requirements.txt", versions=False):
    """
    TODO: keep in sync with xcookie.

    Parse the package dependencies listed in a requirements file but strips
    specific versioning information.

    Args:
        fname (str): path to requirements file
        versions (bool | str):
            If true include version specs.
            If strict, then pin to the minimum version.

    Returns:
        List[str]: list of requirements items

    CommandLine:
        python -c "import setup, ubelt; print(ubelt.urepr(setup.parse_requirements()))"
    """
    require_fpath = fname
    packages = list(gen_packages_items(require_fpath, versions))
    return packages


def parse_line(line, dpath=""):
    """
    Parse information from a line in a requirements text file

    line = 'git+https://a.com/somedep@sometag#egg=SomeDep'
    line = '-e git+https://a.com/somedep@sometag#egg=SomeDep'
    """
    # Remove inline comments
    comment_pos = line.find(" #")
    if comment_pos > -1:
        line = line[:comment_pos]

    if line.startswith("-r "):
        # Allow specifying requirements in other files
        target = join(dpath, line.split(" ")[1])
        for info in parse_require_file(target):
            yield info
    else:
        # See: https://www.python.org/dev/peps/pep-0508/
        info = {"line": line}
        if line.startswith("-e "):
            info["package"] = line.split("#egg=")[1]
        else:
            if "--find-links" in line:
                # setuptools does not seem to handle find links
                line = line.split("--find-links")[0]
            if ";" in line:
                pkgpart, platpart = line.split(";")
                # Handle platform specific dependencies
                # setuptools.readthedocs.io/en/latest/setuptools.html
                # #declaring-platform-specific-dependencies
                plat_deps = platpart.strip()
                info["platform_deps"] = plat_deps
            else:
                pkgpart = line
                platpart = None

            # Remove versioning from the package
            pat = "(" + "|".join([">=", "==", ">"]) + ")"
            parts = re.split(pat, pkgpart, maxsplit=1)
            parts = [p.strip() for p in parts]

            info["package"] = parts[0]
            if len(parts) > 1:
                op, rest = parts[1:]
                version = rest  # NOQA
                info["version"] = (op, version)
        yield info


def parse_require_file(fpath):
    dpath = dirname(fpath)
    with open(fpath, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line and not line.startswith("#"):
                for info in parse_line(line, dpath=dpath):
                    yield info


def gen_packages_items(require_fpath, versions='loose'):
    if exists(require_fpath):
        for info in parse_require_file(require_fpath):
            parts = [info["package"]]
            if versions and "version" in info:
                if versions == "strict":
                    # In strict mode, we pin to the minimum version
                    if info["version"]:
                        # Only replace the first >= instance
                        verstr = "".join(info["version"]).replace(">=", "==", 1)
                        parts.append(verstr)
                else:
                    parts.extend(info["version"])
            if not sys.version.startswith("3.4"):
                # apparently package_deps are broken in 3.4
                plat_deps = info.get("platform_deps")
                if plat_deps is not None:
                    parts.append(";" + plat_deps)
            item = "".join(parts)
            if item:
                yield item
