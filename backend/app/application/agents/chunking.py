import re

# Splits on the whitespace immediately after a sentence-ending punctuation mark, keeping
# the punctuation with the sentence it closes. This is a heuristic, not a full sentence
# tokenizer — good enough to avoid mid-sentence cuts without pulling in an NLP dependency.
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def _split_into_sentences(paragraph: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_BOUNDARY.split(paragraph) if s.strip()]


def _pack(pieces: list[str], target_size: int, joiner: str) -> list[str]:
    """Packs consecutive pieces into groups joined by `joiner`, closing a group once adding
    the next piece would exceed target_size — the packing strategy shared by paragraph-level
    and (for paragraphs that alone exceed target_size) sentence-level chunking."""
    packed: list[str] = []
    current = pieces[0]
    for piece in pieces[1:]:
        if len(current) + len(joiner) + len(piece) <= target_size:
            current = f"{current}{joiner}{piece}"
        else:
            packed.append(current)
            current = piece
    packed.append(current)
    return packed


def chunk_text(text: str, target_size: int = 650) -> list[str]:
    """Splits on paragraph boundaries (blank lines), packing consecutive paragraphs into a
    chunk until adding the next one would exceed target_size — never splitting a paragraph
    mid-sentence to hit an exact size.

    A single paragraph that alone exceeds target_size (e.g. a PDF page: pypdf's
    extract_text() only emits "\\n" within a page, so a whole page is one paragraph by this
    function's definition) is packed one level deeper, at sentence boundaries, rather than
    shipped as one unbounded chunk — same "never split mid-sentence" guarantee, applied to
    the next-smaller unit."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = paragraphs[0]
    for paragraph in paragraphs[1:]:
        if len(current) + 2 + len(paragraph) <= target_size:
            current = f"{current}\n\n{paragraph}"
        else:
            chunks.append(current)
            current = paragraph
    chunks.append(current)

    result: list[str] = []
    for chunk in chunks:
        if len(chunk) <= target_size:
            result.append(chunk)
            continue
        sentences = _split_into_sentences(chunk)
        result.extend(_pack(sentences, target_size, " ") if len(sentences) > 1 else [chunk])
    return result
