def chunk_text(text: str, target_size: int = 650) -> list[str]:
    """Splits on paragraph boundaries (blank lines), packing consecutive paragraphs into a
    chunk until adding the next one would exceed target_size — never splitting a paragraph
    mid-sentence to hit an exact size."""
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
    return chunks
