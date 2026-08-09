import httpx


class OllamaEmbeddingProvider:
    """Talks to Ollama's native `/api/embed` endpoint — same rationale as OllamaProvider not
    using the OpenAI-compatible shim (ADR 0006): one wire format to reason about."""

    def __init__(
        self, *, base_url: str, model: str, transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._transport = transport

    async def embed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.post(
                f"{self._base_url}/api/embed",
                json={"model": self._model, "input": texts},
                timeout=60.0,
            )
        response.raise_for_status()
        return response.json()["embeddings"]
