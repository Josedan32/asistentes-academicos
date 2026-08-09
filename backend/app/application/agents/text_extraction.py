import io

import docx
from pypdf import PdfReader


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
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx(content: bytes) -> str:
    document = docx.Document(io.BytesIO(content))
    return "\n\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text)
