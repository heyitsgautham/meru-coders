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


def defined_names(path: Path) -> set[str]:
    """Names bound at module level: functions, classes, assignments and imports."""
    names: set[str] = set()
    if path.is_dir():
        return names
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names.update(t.id for target in targets for t in ast.walk(target) if isinstance(t, ast.Name))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update((alias.asname or alias.name).split(".")[0] for alias in node.names)
        elif isinstance(node, ast.Try):
            for inner in node.body:
                if isinstance(inner, (ast.Import, ast.ImportFrom)):
                    names.update((alias.asname or alias.name).split(".")[0] for alias in inner.names)
    return names


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
