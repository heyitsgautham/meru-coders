"""Every environment variable the code reads is documented in an .env.example file."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PYTHON_ENV_READ = re.compile(
    r"""(?:os\.environ\.get|os\.getenv|os\.environ\[|_env_int|_env_bool)\(?\s*["']([A-Z][A-Z0-9_]+)["']"""
)
VITE_ENV_READ = re.compile(r"import\.meta\.env\.(VITE_[A-Z0-9_]+)")
EXAMPLE_ENTRY = re.compile(r"^#?\s*([A-Z][A-Z0-9_]+)=", re.MULTILINE)


def documented(example: Path) -> set[str]:
    return set(EXAMPLE_ENTRY.findall(example.read_text(encoding="utf-8")))


def read_by(paths, pattern) -> set[str]:
    names: set[str] = set()
    for path in paths:
        names.update(pattern.findall(path.read_text(encoding="utf-8", errors="ignore")))
    return names


def test_backend_env_vars_are_in_the_root_env_example():
    sources = [p for p in (REPO_ROOT / "backend").rglob("*.py") if "tests" not in p.parts]
    used = read_by(sources, PYTHON_ENV_READ)
    assert len(used) > 20, "the scan stopped finding the settings module's variables"
    missing = used - documented(REPO_ROOT / ".env.example")
    assert not missing, f"add these to .env.example: {sorted(missing)}"


def test_frontend_env_vars_are_in_the_frontend_env_example():
    sources = [*(REPO_ROOT / "frontend" / "src").rglob("*.ts"), *(REPO_ROOT / "frontend" / "src").rglob("*.tsx")]
    used = read_by(sources, VITE_ENV_READ)
    assert used, "the scan stopped finding import.meta.env reads"
    missing = used - documented(REPO_ROOT / "frontend" / ".env.example")
    assert not missing, f"add these to frontend/.env.example: {sorted(missing)}"


def test_example_files_hold_no_real_secrets():
    for example in (REPO_ROOT / ".env.example", REPO_ROOT / "frontend" / ".env.example"):
        for line in example.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if any(word in name for word in ("KEY", "PASSWORD", "TOKEN", "SECRET")):
                assert value in {"", "change-me"} or value.startswith("your-"), f"{example.name}: {name} has a value"
