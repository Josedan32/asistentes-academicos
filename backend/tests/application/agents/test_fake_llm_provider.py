import pytest

from app.application.agents.llm_types import LLMMessage, LLMResponse
from tests.application.agents.fakes import FakeLLMProvider


async def test_returns_scripted_responses_in_order() -> None:
    provider = FakeLLMProvider(
        responses=[LLMResponse(content="uno"), LLMResponse(content="dos")]
    )
    first = await provider.complete([LLMMessage(role="user", content="a")])
    second = await provider.complete([LLMMessage(role="user", content="b")])

    assert first.content == "uno"
    assert second.content == "dos"
    assert len(provider.calls) == 2


async def test_raises_when_called_more_times_than_scripted() -> None:
    provider = FakeLLMProvider(responses=[LLMResponse(content="uno")])
    await provider.complete([LLMMessage(role="user", content="a")])

    with pytest.raises(AssertionError, match="called"):
        await provider.complete([LLMMessage(role="user", content="b")])


async def test_is_loaded_defaults_to_true() -> None:
    provider = FakeLLMProvider(responses=[])
    assert await provider.is_loaded() is True
