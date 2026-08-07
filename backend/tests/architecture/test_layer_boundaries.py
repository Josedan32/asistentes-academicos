"""The domain layer must not depend on any framework.

Dependencies point inward: domain imports nothing external, application imports
domain, infrastructure and api import inward. This test enforces the innermost rule.
"""

import ast
from pathlib import Path

import pytest

DOMAIN_ROOT = Path(__file__).resolve().parents[2] / "app" / "domain"

FORBIDDEN_ROOTS = {
    "fastapi",
    "sqlalchemy",
    "redis",
    "httpx",
    "alembic",
    "pydantic",
    "pydantic_settings",
    "jwt",
    "argon2",
}


def _imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _domain_files() -> list[Path]:
    return sorted(p for p in DOMAIN_ROOT.rglob("*.py") if p.name != "__init__.py")


def test_domain_directory_exists() -> None:
    assert DOMAIN_ROOT.is_dir(), f"missing domain layer at {DOMAIN_ROOT}"


@pytest.mark.parametrize("path", _domain_files(), ids=lambda p: str(p.name))
def test_domain_module_imports_no_framework(path: Path) -> None:
    leaked = _imported_roots(path) & FORBIDDEN_ROOTS
    assert not leaked, (
        f"{path.relative_to(DOMAIN_ROOT)} imports forbidden packages: {sorted(leaked)}"
    )
