import io
import re

import docx
from pypdf import PdfReader

# Some PDFs encode an accented letter as a standalone acute accent glyph followed by the
# bare vowel (e.g. "´ o" instead of "ó"), which pypdf extracts literally. Recompose
# them so the text reads like normal Spanish instead of "definici´ on".
_BROKEN_ACCENT = re.compile(r"´\s?([aeiouAEIOUİı])")
_ACCENTED = {
    "a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú",
    "A": "Á", "E": "É", "I": "Í", "O": "Ó", "U": "Ú",
    "ı": "í", "İ": "Í",
}
# Math-typesetting fonts (e.g. extensible parenthesis/bracket pieces around a matrix) map
# their glyphs into the Private Use Area, which pypdf extracts as codepoints with no real
# character behind them — they render as tofu boxes with no readable fallback.
_PRIVATE_USE_AREA = re.compile("[-]")


class UnsupportedMaterialFormatError(Exception):
    def __init__(self, filename: str) -> None:
        super().__init__(f"unsupported material format: {filename}")


def extract_text(filename: str, content: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return _extract_pdf(content)
    if lower.endswith(".docx"):
        return _extract_docx(content)
    raise UnsupportedMaterialFormatError(filename)


def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    text = _fix_broken_accents(text)
    return _strip_private_use_area(text)


def _fix_broken_accents(text: str) -> str:
    return _BROKEN_ACCENT.sub(lambda match: _ACCENTED[match.group(1)], text)


def _strip_private_use_area(text: str) -> str:
    return _PRIVATE_USE_AREA.sub("", text)


def _extract_docx(content: bytes) -> str:
    document = docx.Document(io.BytesIO(content))
    return "\n\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text)
