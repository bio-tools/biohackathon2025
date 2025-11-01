"""
Generate architecture diagrams for the `bridge` package and its subpackages using D2.
Diagrams are saved in `docs/source/api_reference/_architecture_generated/`.
This script is a part of CI documentation generation.

Run via:
    poetry run gen-diagrams
"""

import ast
import os
import pathlib
import shutil
import subprocess
import textwrap
from pathlib import Path

from grimp import build_graph

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
PKG_DIR = SRC_DIR / "bridge"
DOCS_DIR = BASE_DIR / "docs" / "source" / "api_reference" / "_architecture_generated"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

PACKAGE = "bridge"

# These packages can be diagrammed themselves (unless excluded below),
# but we will NOT draw edges *to* them in the global view. For per-package
# diagrams we only consider in-package relationships anyway.
EXCLUDE_PACKAGES = {
    "bridge.utils",
    "bridge.config",
    "bridge.logging",
}


def is_package(node: str) -> bool:
    """Check if `bridge/foo/bar` has an __init__.py."""
    return (SRC_DIR / Path(*node.split(".")) / "__init__.py").exists()


def is_module(node: str) -> bool:
    """Check if `bridge/foo/bar.py` exists (and it's not a package)."""
    return (SRC_DIR / Path(*node.split("."))).with_suffix(".py").exists()


def is_internal_module(name: str) -> bool:
    """Check if a module belongs to the target package."""
    return name.startswith(PACKAGE)


def is_special(name: str) -> bool:
    """Check if a module is special (dunder or __init__)."""
    parts = name.split(".")
    return any(part.startswith("__") or part == "__init__" for part in parts)


def extract_docstrings(base_dir: pathlib.Path, package: str) -> dict[str, str]:
    """Extract top-level docstrings for both packages and modules."""
    docs: dict[str, str] = {}
    for path in base_dir.rglob("*.py"):
        rel_path = path.relative_to(base_dir.parent)
        module_name = ".".join(rel_path.with_suffix("").parts)
        if not module_name.startswith(package):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                node = ast.parse(f.read())
            doc = ast.get_docstring(node)
            if not doc:
                continue
            doc = " ".join(doc.strip().splitlines())
            if path.name == "__init__.py":
                package_name = ".".join(module_name.split(".")[:-1])
                docs[package_name] = doc
            else:
                docs[module_name] = doc
        except (SyntaxError, OSError):
            continue
    return docs


def list_all_packages(root_dir: pathlib.Path, root_pkg: str) -> set[str]:
    """
    Recursively list all packages (directories with __init__.py), including the root package.
    """
    pkgs: set[str] = set()
    # Ensure root package is included
    pkgs.add(root_pkg)
    for path in root_dir.rglob("__init__.py"):
        rel = path.parent.relative_to(SRC_DIR)
        pkg = ".".join(rel.parts)
        if pkg and pkg.startswith(root_pkg):
            pkgs.add(pkg)
    return pkgs


def immediate_child_of(module: str, base_pkg: str) -> str:
    """
    Given a fully-qualified module under base_pkg, return the immediate child node:
    base_pkg.<child> (one level below base_pkg).
    """
    base_parts = base_pkg.split(".")
    parts = module.split(".")
    if len(parts) <= len(base_parts):
        # treat equal-level as not a child
        return base_pkg
    return ".".join(parts[: len(base_parts) + 1])


def collect_children_nodes(graph, package: str) -> set[str]:
    """
    Collect all immediate children (modules or subpackages) under `package`
    based on modules present in the import graph.
    """
    children: set[str] = set()
    prefix = package + "."
    for m in graph.modules:
        if not is_internal_module(m) or is_special(m):
            continue
        if m.startswith(prefix):
            child = immediate_child_of(m, package)
            if child != package:
                children.add(child)
    return children


def build_edges_for_package(graph, package: str) -> tuple[dict[str, set[str]], set[str]]:
    """
    Build dependency edges among immediate children of `package`.
    Edge A->B exists if any module under A directly imports a module under B.
    """
    edges: dict[str, set[str]] = {}
    nodes = collect_children_nodes(graph, package)
    prefix = package + "."

    for module in graph.modules:
        if not is_internal_module(module) or is_special(module):
            continue
        if not module.startswith(prefix):
            continue

        src_child = immediate_child_of(module, package)
        if src_child == package:
            # skip the package's __init__ (or exact level) as a "child" source
            continue
        if src_child not in nodes:
            nodes.add(src_child)

        for imported in graph.find_modules_directly_imported_by(module):
            if not is_internal_module(imported) or is_special(imported):
                continue
            if not imported.startswith(prefix):
                # only care about imports that stay within this package subtree
                continue

            tgt_child = immediate_child_of(imported, package)
            if tgt_child == package:
                continue
            if tgt_child not in nodes:
                nodes.add(tgt_child)

            if src_child != tgt_child:
                edges.setdefault(src_child, set()).add(tgt_child)

    return edges, nodes


def generate_d2_for_package(
    package: str,
    nodes: set[str],
    edges: dict[str, set[str]],
    docstrings: dict[str, str],
) -> str:
    """Generate D2 source for a single package diagram."""
    lines = [
        f"# Auto-generated architecture diagram for {package}",
        "vars: {",
        "  d2-config: {",
        "    theme-id: 200",
        "    layout-engine: elk",
        "  }",
        "}",
        "",
    ]

    all_nodes = sorted(nodes)

    for node in all_nodes:
        title = node.replace(package + ".", "") if node != package else node
        desc = docstrings.get(node, "").strip()
        node_id = node.replace(".", "_")

        lines.append(f"{node_id}: |md")
        lines.append(f"  # {title}\n")
        if desc:
            wrapped = "<br/>\n  ".join(line for line in textwrap.fill(desc, width=40).splitlines())
            lines.append(f"  {wrapped}  ")
        lines.append("|")
        lines.append(f"{node_id}.shape: rectangle")
        lines.append(f"{node_id}.style.border-radius: 10")

        kind = "package" if is_package(node) else ("module" if is_module(node) else "unknown")
        if kind == "module":
            lines.append(f"{node_id}.style.stroke: '#FC99E7'")

        lines.append("")

    for src, tgts in edges.items():
        for tgt in tgts:
            lines.append(f"{src.replace('.', '_')} -> {tgt.replace('.', '_')}")

    return "\n".join(lines) + "\n"


def write_diagram(package: str, d2_source: str):
    """Write the .d2 (and optionally render .svg) using dot-separated filenames."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    d2_path = DOCS_DIR / f"{package}.dependencies.d2"
    d2_path.write_text(d2_source, encoding="utf-8")
    print(f"Wrote {d2_path}")

    d2_exe = shutil.which("d2")
    svg_path = DOCS_DIR / f"{package}.dependencies.svg"

    if not d2_exe:
        print("D2 CLI not found.")
        print(" • macOS: brew install d2")
        print(" • Windows: scoop install d2")
        print(" • Linux: see https://d2lang.com/tour/install/")
        return

    try:
        subprocess.run(
            [d2_exe, str(d2_path), str(svg_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"Rendered {svg_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to render {package} diagram.")
        print(e.stderr.strip() or e.stdout.strip() or "Unknown error.")


def main():
    """Generate architecture diagrams for all subpackages."""
    # Ensure grimp resolves modules from ./src
    os.environ["PYTHONPATH"] = str(SRC_DIR)

    # Build the full project graph once
    graph = build_graph(PACKAGE)

    # Extract docstrings once
    docstrings = extract_docstrings(PKG_DIR, PACKAGE)

    # Find all subpackages recursively (including root)
    packages = sorted(list_all_packages(PKG_DIR, PACKAGE))

    for pkg in packages:
        if pkg in EXCLUDE_PACKAGES:
            continue

        edges, nodes = build_edges_for_package(graph, pkg)
        # If a subpackage has no children, skip (nothing to diagram)
        if not nodes:
            continue

        d2_source = generate_d2_for_package(pkg, nodes, edges, docstrings)
        write_diagram(pkg, d2_source)

        print("")


if __name__ == "__main__":
    main()
