from app.application.agents.chunking import chunk_text


def test_short_text_is_a_single_chunk() -> None:
    assert chunk_text("Una sola oracion corta.") == ["Una sola oracion corta."]


def test_splits_on_paragraph_boundaries_before_the_target_size() -> None:
    paragraphs = ["Primer parrafo. " * 10, "Segundo parrafo. " * 10, "Tercero. " * 10]
    text = "\n\n".join(paragraphs)

    chunks = chunk_text(text, target_size=200)

    assert len(chunks) > 1
    # No chunk exceeds the target by more than one full paragraph's worth of slack —
    # the function must not split mid-sentence to hit an exact byte count.
    assert all(len(chunk) < 400 for chunk in chunks)


def test_empty_text_produces_no_chunks() -> None:
    assert chunk_text("") == []


def test_reassembling_chunks_loses_no_words() -> None:
    text = "Uno dos tres.\n\nCuatro cinco seis.\n\nSiete ocho nueve."
    chunks = chunk_text(text, target_size=20)
    reassembled_words = " ".join(chunks).split()
    original_words = text.split()
    assert sorted(reassembled_words) == sorted(original_words)


def test_a_single_oversized_paragraph_is_split_on_sentence_boundaries() -> None:
    """Regression test for finding 5: a real PDF page (pypdf's extract_text() only emits
    "\\n" within a page, never "\\n\\n") becomes exactly one paragraph by this function's
    "\\n\\n" splitting rule. Without a sentence-level fallback, chunk_text ships the whole
    page as one indivisible, unbounded chunk regardless of target_size — this proves a
    paragraph with several sentences and no internal blank line is still broken up."""
    sentences = [f"Esta es la oracion numero {i} de la pagina." for i in range(1, 21)]
    paragraph = " ".join(sentences)  # no "\n\n" anywhere inside — a single PDF-page paragraph
    target_size = 150

    chunks = chunk_text(paragraph, target_size=target_size)

    assert len(chunks) > 1
    # Each chunk stays close to target_size — a single sentence can push a chunk slightly
    # over, but nothing near the length of the whole 20-sentence paragraph.
    assert all(len(chunk) <= target_size + 100 for chunk in chunks)
    reassembled_words = " ".join(chunks).split()
    assert sorted(reassembled_words) == sorted(paragraph.split())


def test_oversized_paragraph_splitting_still_respects_blank_line_boundaries() -> None:
    """A document with one short paragraph and one oversized paragraph must still split on
    the blank line between them, and only the oversized one gets the sentence-level
    fallback — proving the two passes compose rather than one overriding the other."""
    short_paragraph = "Intro breve."
    long_sentences = [f"Oracion larga numero {i} con mas texto de relleno." for i in range(1, 16)]
    long_paragraph = " ".join(long_sentences)
    text = f"{short_paragraph}\n\n{long_paragraph}"

    chunks = chunk_text(text, target_size=150)

    assert chunks[0] == short_paragraph
    assert len(chunks) > 2
    reassembled_words = " ".join(chunks).split()
    assert sorted(reassembled_words) == sorted(text.split())
