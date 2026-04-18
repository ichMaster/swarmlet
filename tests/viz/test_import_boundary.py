"""Architectural lint: swarmlet.viz must NOT import interpreter internals.

The visualizer is a consumer of the snapshot file format only. It must not
depend on lexer, parser, AST, analyzer, evaluator, engine, or builtins.
The only allowed cross-package import is `swarmlet.snapshot` (the file format
contract module). This test enforces that boundary at the AST level.
"""

import ast
from pathlib import Path

FORBIDDEN_MODULES = {
    "swarmlet.lexer",
    "swarmlet.parser",
    "swarmlet.ast",
    "swarmlet.analyzer",
    "swarmlet.eval",
    "swarmlet.engine",
    "swarmlet.builtins",
}

VIZ_ROOT = Path(__file__).resolve().parent.parent.parent / "swarmlet" / "viz"


def _viz_python_files():
    return sorted(VIZ_ROOT.rglob("*.py"))


def _imported_modules(source_path: Path):
    tree = ast.parse(source_path.read_text(), filename=str(source_path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
    return modules


def test_viz_root_exists():
    assert VIZ_ROOT.is_dir(), f"viz package directory missing: {VIZ_ROOT}"


def test_viz_files_do_not_import_interpreter_internals():
    violations = []
    for py_file in _viz_python_files():
        for module in _imported_modules(py_file):
            if module in FORBIDDEN_MODULES:
                violations.append((py_file, module))
            for forbidden in FORBIDDEN_MODULES:
                if module.startswith(forbidden + "."):
                    violations.append((py_file, module))
    assert not violations, (
        "swarmlet.viz must not import interpreter internals. "
        f"Violations: {violations}"
    )
