import pytest
from fakeredis import FakeAsyncRedis

from app.application.agents.llm_types import LLMResponse, ToolCallRequest
from app.infrastructure.redis.response_cache import RedisResponseCache


@pytest.fixture
async def cache():
    redis = FakeAsyncRedis()
    yield RedisResponseCache(redis)
    await redis.aclose()


async def test_cache_miss_returns_none(cache: RedisResponseCache) -> None:
    assert await cache.get("missing") is None


async def test_round_trips_a_response(cache: RedisResponseCache) -> None:
    response = LLMResponse(content="hola", input_tokens=1, output_tokens=2, latency_ms=3, model="m")
    await cache.set("key1", response, ttl_seconds=60)
    assert await cache.get("key1") == response


async def test_round_trips_a_response_with_tool_calls(cache: RedisResponseCache) -> None:
    response = LLMResponse(
        content=None,
        tool_calls=[ToolCallRequest(id="1", name="get_prerequisites", arguments={"course": "BD2"})],
        model="m",
    )
    await cache.set("key2", response, ttl_seconds=60)
    assert await cache.get("key2") == response
