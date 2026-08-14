import json
from collections.abc import Callable

import httpx

from app.infrastructure.llm.ollama_embedding_provider import OllamaEmbeddingProvider


def _provider(handler: Callable[[httpx.Request], httpx.Response]) -> OllamaEmbeddingProvider:
    return OllamaEmbeddingProvider(
        base_url="http://localhost:11434", model="nomic-embed-text",
        transport=httpx.MockTransport(handler),
    )


async def test_embeds_a_batch_of_texts() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.read())
        assert payload["model"] == "nomic-embed-text"
        assert payload["input"] == ["primer texto", "segundo texto"]
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2], [0.3, 0.4]]})

    result = await _provider(handler).embed(["primer texto", "segundo texto"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]


async def test_embeds_a_single_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": [[0.5, 0.6]]})

    result = await _provider(handler).embed(["solo un texto"])

    assert result == [[0.5, 0.6]]


async def test_splits_large_inputs_into_batches() -> None:
    seen_batch_sizes: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.read())
        seen_batch_sizes.append(len(payload["input"]))
        return httpx.Response(
            200, json={"embeddings": [[0.0] for _ in payload["input"]]}
        )

    texts = [f"texto {i}" for i in range(20)]
    result = await _provider(handler).embed(texts)

    assert seen_batch_sizes == [16, 4]
    assert len(result) == 20
