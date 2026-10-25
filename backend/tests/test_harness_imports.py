"""The evaluation harnesses and scripts import first-party code that exists.

They run by hand and not in CI, so a moved module or renamed function would
otherwise only show up when someone next runs them. This test resolves every
``backend.*`` and ``reference.*`` import in backend/evaluation/ and
backend/scripts/ statically, without executing the scripts, and checks that
each imported name is defined in the target module.
"""

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIRS = (REPO_ROOT / "backend" / "evaluation", REPO_ROOT / "backend" / "scripts")
FIRST_PARTY = ("backend", "reference")


def harness_files():
    return sorted(path for directory in HARNESS_DIRS for path in directory.rglob("*.py"))


def module_file(module: str) -> Path | None:
    base = REPO_ROOT.joinpath(*module.split("."))
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.exists():
            return candidate
    # A directory without __init__.py is a namespace package, as reference/ is.
    return base if base.is_dir() else None


def bound_names(statements) -> set[str]:
    """Names bound by module-level statements, looking inside if and try blocks."""
    names: set[str] = set()
    for node in statements:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names.update(t.id for target in targets for t in ast.walk(target) if isinstance(t, ast.Name))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update((alias.asname or alias.name).split(".")[0] for alias in node.names)
        elif isinstance(node, ast.If):
            names |= bound_names(node.body) | bound_names(node.orelse)
        elif isinstance(node, ast.Try):
            handlers = [stmt for handler in node.handlers for stmt in handler.body]
            names |= bound_names(node.body + handlers + node.orelse + node.finalbody)
    return names


def defined_names(path: Path) -> set[str]:
    """Names a module defines at top level; empty for a namespace package directory."""
    if path.is_dir():
        return set()
    return bound_names(ast.parse(path.read_text(encoding="utf-8")).body)


def first_party_imports(path: Path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module.split(".")[0] in FIRST_PARTY:
            yield node.lineno, node.module, [alias.name for alias in node.names]
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in FIRST_PARTY:
                    yield node.lineno, alias.name, []


@pytest.mark.parametrize("path", harness_files(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_first_party_imports_resolve(path):
    problems = []
    for line, module, names in first_party_imports(path):
        target = module_file(module)
        if target is None:
            problems.append(f"line {line}: no module {module}")
            continue
        available = defined_names(target)
        for name in names:
            if name != "*" and name not in available and module_file(f"{module}.{name}") is None:
                problems.append(f"line {line}: {module} has no {name}")
    assert not problems, "\n".join(problems)


def test_harnesses_no_longer_edit_sys_path_to_reach_the_backend():
    """Only imports of external clones under repos/ may still need a sys.path entry."""
    offenders = []
    for path in harness_files():
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and ast.unparse(node.func) in ("sys.path.insert", "sys.path.append"):
                source = ast.get_source_segment(path.read_text(encoding="utf-8"), node) or ""
                external = "repos" in source or "REPO_PATH" in source or "repo_path" in source
                entry_point = path.name == "build_rigveda_dataset.py"
                if not (external or entry_point):
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}")
    assert not offenders, offenders


def relative_imports(path: Path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.level > 0:
            yield node


@pytest.mark.parametrize(
    "path",
    sorted((REPO_ROOT / "backend").rglob("*.py")),
    ids=lambda p: str(p.relative_to(REPO_ROOT)),
)
def test_relative_imports_resolve(path):
    """A relative import inside a function only fails when that function runs, so check them all here."""
    problems = []
    package = path.parent.relative_to(REPO_ROOT).parts
    for node in relative_imports(path):
        base = package[: len(package) - (node.level - 1)]
        module = ".".join(base + tuple(node.module.split("."))) if node.module else ".".join(base)
        target = module_file(module)
        if target is None:
            problems.append(f"line {node.lineno}: no module {module}")
            continue
        available = defined_names(target)
        for alias in node.names:
            if alias.name not in available and module_file(f"{module}.{alias.name}") is None:
                problems.append(f"line {node.lineno}: {module} has no {alias.name}")
    assert not problems, "\n".join(problems)
