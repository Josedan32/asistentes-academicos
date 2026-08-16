from app.application.agents.chunking import chunk_text


def test_short_text_is_a_single_chunk() -> None:
    assert chunk_text("Una sola oracion corta.") == ["Una sola oracion corta."]


def test_splits_on_paragraph_boundaries_before_the_target_size() -> None:
    paragraphs = ["Primer parrafo. " * 10, "Segundo parrafo. " * 10, "Tercero. " * 10]
    text = "\n\n".join(paragraphs)

    chunks = chunk_text(text, target_size=200)

    assert len(chunks) > 1
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
    sentences = [f"Esta es la oracion numero {i} de la pagina." for i in range(1, 21)]
    paragraph = " ".join(sentences)
    target_size = 150

    chunks = chunk_text(paragraph, target_size=target_size)

    assert len(chunks) > 1
    assert all(len(chunk) <= target_size + 100 for chunk in chunks)
    reassembled_words = " ".join(chunks).split()
    assert sorted(reassembled_words) == sorted(paragraph.split())


def test_oversized_paragraph_splitting_still_respects_blank_line_boundaries() -> None:
    short_paragraph = "Intro breve."
    long_sentences = [f"Oracion larga numero {i} con mas texto de relleno." for i in range(1, 16)]
    long_paragraph = " ".join(long_sentences)
    text = f"{short_paragraph}\n\n{long_paragraph}"

    chunks = chunk_text(text, target_size=150)

    assert chunks[0] == short_paragraph
    assert len(chunks) > 2
    reassembled_words = " ".join(chunks).split()
    assert sorted(reassembled_words) == sorted(text.split())
