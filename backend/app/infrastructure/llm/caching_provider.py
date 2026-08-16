from app.application.agents.cache_key import cache_key
from app.application.agents.llm_types import LLMMessage, LLMResponse, ToolDefinition
from app.application.agents.ports import LLMProvider, ResponseCache


class CachingLLMProvider:
    def __init__(self, *, inner: LLMProvider, cache: ResponseCache, ttl_seconds: int) -> None:
        self._inner = inner
        self._cache = cache
        self._ttl_seconds = ttl_seconds

    @property
    def model(self) -> str:
        return self._inner.model

    async def is_loaded(self) -> bool:
        return await self._inner.is_loaded()

    async def complete(
        self, messages: list[LLMMessage], tools: list[ToolDefinition] | None = None
    ) -> LLMResponse:
        key = cache_key(messages, self._inner.model, tools)
        cached = await self._cache.get(key)
        if cached is not None:
            return cached

        response = await self._inner.complete(messages, tools)
        await self._cache.set(key, response, self._ttl_seconds)
        return response
