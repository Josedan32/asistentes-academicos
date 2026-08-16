import httpx

BATCH_SIZE = 16
REQUEST_TIMEOUT = httpx.Timeout(300.0, connect=10.0)


class OllamaEmbeddingProvider:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        transport: httpx.AsyncBaseTransport | None = None,
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
