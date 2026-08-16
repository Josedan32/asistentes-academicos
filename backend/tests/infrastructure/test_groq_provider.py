import json
from collections.abc import Callable

import httpx
import pytest

from app.application.agents.llm_types import LLMMessage, ToolDefinition
from app.infrastructure.config import get_settings
from app.infrastructure.llm.groq_provider import GroqProvider


def _provider(handler: Callable[[httpx.Request], httpx.Response]) -> GroqProvider:
    return GroqProvider(
        api_key="test-key", model="llama-3.3-70b-versatile", transport=httpx.MockTransport(handler)
    )


async def test_sends_the_bearer_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "hola"}}], "model": "m"}
        )

    response = await _provider(handler).complete([LLMMessage(role="user", content="hola")])
    assert response.content == "hola"


async def test_json_loads_the_tool_call_arguments_string() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "function": {
                                        "name": "get_prerequisites",
                                        "arguments": json.dumps({"program_id": 1, "course": "BD2"}),
                                    },
                                }
                            ],
                        }
                    }
                ],
                "usage": {"prompt_tokens": 50, "completion_tokens": 10},
                "model": "llama-3.3-70b-versatile",
            },
        )

    response = await _provider(handler).complete(
        [LLMMessage(role="user", content="hola")],
        tools=[ToolDefinition(name="get_prerequisites", description="d", parameters={})],
    )

    assert response.tool_calls[0].id == "call_1"
    assert response.tool_calls[0].arguments == {"program_id": 1, "course": "BD2"}
    assert response.input_tokens == 50
    assert response.output_tokens == 10


async def test_is_loaded_is_always_true_for_a_hosted_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("is_loaded must not make a network call for a hosted provider")

    assert await _provider(handler).is_loaded() is True


@pytest.mark.groq
async def test_contract_against_the_real_groq_api() -> None:
    settings = get_settings()
    assert settings.groq_api_key, "GROQ_API_KEY must be set to run -m groq"
    provider = GroqProvider(api_key=settings.groq_api_key, model=settings.groq_model)
    response = await provider.complete([LLMMessage(role="user", content="Hola, quien eres?")])
    assert response.content
