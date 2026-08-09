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
