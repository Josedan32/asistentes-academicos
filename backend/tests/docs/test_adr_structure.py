"""Every ADR must carry the sections that make it a decision record, not a note."""

import re
from pathlib import Path

import pytest

ADR_DIR = Path(__file__).resolve().parents[3] / "docs" / "adr"
REQUIRED_SECTIONS = ("## Context", "## Decision", "## Consequences")
FILENAME_PATTERN = re.compile(r"^\d{4}-[a-z0-9-]+\.md$")


def adr_files() -> list[Path]:
    return sorted(ADR_DIR.glob("*.md"))


def test_adr_directory_is_not_empty() -> None:
    assert adr_files(), f"no ADRs found in {ADR_DIR}"


@pytest.mark.parametrize("path", adr_files(), ids=lambda p: p.name)
def test_adr_filename_is_numbered(path: Path) -> None:
    assert FILENAME_PATTERN.match(path.name), f"{path.name} must look like 0001-some-slug.md"


@pytest.mark.parametrize("path", adr_files(), ids=lambda p: p.name)
def test_adr_has_required_sections(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [section for section in REQUIRED_SECTIONS if section not in text]
    assert not missing, f"{path.name} is missing {missing}"


@pytest.mark.parametrize("path", adr_files(), ids=lambda p: p.name)
def test_adr_declares_a_status(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert re.search(r"^Status:\s*\S+", text, re.MULTILINE), f"{path.name} has no Status line"


def test_adr_numbers_are_unique() -> None:
    numbers = [path.name[:4] for path in adr_files()]
    assert len(numbers) == len(set(numbers)), f"duplicate ADR numbers: {numbers}"
