import httpx

BATCH_SIZE = 16
REQUEST_TIMEOUT = httpx.Timeout(300.0, connect=10.0)


class OllamaEmbeddingProvider:
    """Talks to Ollama's native `/api/embed` endpoint — same rationale as OllamaProvider not
    using the OpenAI-compatible shim (ADR 0006): one wire format to reason about.

    Requests are batched: a large PDF can produce hundreds of chunks, and asking Ollama to
    embed all of them in a single call risks exceeding any fixed read timeout on slower
    hardware. Smaller batches keep each round trip bounded and let progress survive a
    transient slowdown on one batch instead of failing the whole ingestion."""

    def __init__(
        self, *, base_url: str, model: str, transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._transport = transport

    async def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        async with httpx.AsyncClient(transport=self._transport, timeout=REQUEST_TIMEOUT) as client:
            for start in range(0, len(texts), BATCH_SIZE):
                batch = texts[start : start + BATCH_SIZE]
                response = await client.post(
                    f"{self._base_url}/api/embed",
                    json={"model": self._model, "input": batch},
                )
                response.raise_for_status()
                embeddings.extend(response.json()["embeddings"])
        return embeddings
