from fakeredis import FakeAsyncRedis

from app.application.agents.llm_types import LLMMessage, LLMResponse
from app.infrastructure.llm.caching_provider import CachingLLMProvider
from app.infrastructure.redis.response_cache import RedisResponseCache
from tests.application.agents.fakes import FakeLLMProvider


async def test_a_second_identical_call_is_served_from_the_cache() -> None:
    inner = FakeLLMProvider(responses=[LLMResponse(content="a", model="m")])
    cache = RedisResponseCache(FakeAsyncRedis())
    provider = CachingLLMProvider(inner=inner, cache=cache, ttl_seconds=60)
    messages = [LLMMessage(role="user", content="hola")]

    first = await provider.complete(messages)
    second = await provider.complete(messages)

    assert first == second
    assert len(inner.calls) == 1


async def test_a_different_message_is_not_served_from_the_cache() -> None:
    inner = FakeLLMProvider(
        responses=[LLMResponse(content="a", model="m"), LLMResponse(content="b", model="m")]
    )
    cache = RedisResponseCache(FakeAsyncRedis())
    provider = CachingLLMProvider(inner=inner, cache=cache, ttl_seconds=60)

    await provider.complete([LLMMessage(role="user", content="hola")])
    await provider.complete([LLMMessage(role="user", content="adios")])

    assert len(inner.calls) == 2


async def test_model_and_is_loaded_delegate_to_the_inner_provider() -> None:
    inner = FakeLLMProvider(responses=[], model="qwen2.5:3b", loaded=False)
    provider = CachingLLMProvider(
        inner=inner, cache=RedisResponseCache(FakeAsyncRedis()), ttl_seconds=60
    )

    assert provider.model == "qwen2.5:3b"
    assert await provider.is_loaded() is False
