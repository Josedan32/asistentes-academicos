import re

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def _split_into_sentences(paragraph: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_BOUNDARY.split(paragraph) if s.strip()]


def _pack(pieces: list[str], target_size: int, joiner: str) -> list[str]:
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
