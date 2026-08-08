import json
from dataclasses import asdict

from redis.asyncio import Redis

from app.application.agents.llm_types import LLMResponse, ToolCallRequest

CACHE_PREFIX = "response_cache:"


class RedisResponseCache:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def get(self, key: str) -> LLMResponse | None:
        raw = await self._redis.get(CACHE_PREFIX + key)
        if raw is None:
            return None
        payload = json.loads(raw)
        payload["tool_calls"] = [ToolCallRequest(**call) for call in payload["tool_calls"]]
        return LLMResponse(**payload)

    async def set(self, key: str, response: LLMResponse, ttl_seconds: int) -> None:
        await self._redis.set(CACHE_PREFIX + key, json.dumps(asdict(response)), ex=ttl_seconds)
