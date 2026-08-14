from pathlib import Path

import pytest

from app.application.agents.text_extraction import (
    UnsupportedMaterialFormatError,
    _fix_broken_accents,
    _strip_private_use_area,
    extract_text,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def test_extracts_text_from_a_pdf() -> None:
    content = (FIXTURES / "sample.pdf").read_bytes()
    text = extract_text("guia.pdf", content)
    assert "normalizacion" in text.lower()


def test_extracts_text_from_a_docx() -> None:
    content = (FIXTURES / "sample.docx").read_bytes()
    text = extract_text("apuntes.docx", content)
    assert "indice" in text.lower()


def test_unsupported_extension_raises() -> None:
    with pytest.raises(UnsupportedMaterialFormatError):
        extract_text("diapositivas.pptx", b"")


def test_recomposes_accents_split_by_pdf_extraction() -> None:
    assert _fix_broken_accents("la noci´ on de espacio vectorial") == (
        "la noción de espacio vectorial"
    )
    assert _fix_broken_accents("cap´ıtulo 2") == "capítulo 2"


def test_strips_private_use_area_glyphs_from_matrix_typesetting() -> None:
    broken = "A = " + chr(0xf8ec) + "1 2" + chr(0xf8ed) + " matrix"
    assert _strip_private_use_area(broken) == "A = 1 2 matrix"
