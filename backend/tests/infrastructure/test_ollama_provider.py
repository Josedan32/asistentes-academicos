import json
from collections.abc import Callable

import httpx
import pytest

from app.application.agents.llm_types import LLMMessage, ToolDefinition
from app.infrastructure.llm.ollama_provider import OllamaProvider


def _provider(handler: Callable[[httpx.Request], httpx.Response]) -> OllamaProvider:
    return OllamaProvider(
        base_url="http://localhost:11434", model="qwen2.5:3b", num_ctx=8192, keep_alive="10m",
        transport=httpx.MockTransport(handler),
    )


async def test_sends_num_ctx_and_keep_alive() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.read())
        assert payload["options"]["num_ctx"] == 8192
        assert payload["keep_alive"] == "10m"
        return httpx.Response(200, json={"message": {"content": "hola", "tool_calls": []}})

    response = await _provider(handler).complete([LLMMessage(role="user", content="hola")])
    assert response.content == "hola"


async def test_normalizes_a_tool_call_without_json_loads_ing_the_arguments() -> None:
    """Ollama already returns `arguments` as a dict. json.loads-ing it would raise
    TypeError — this is the exact wire-format asymmetry ADR 0006 pins."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "message": {"content": "", "tool_calls": [
                {"function": {"name": "list_semester_courses",
                               "arguments": {"program_id": 1, "semester": 4}}}
            ]},
            "prompt_eval_count": 120,
            "eval_count": 15,
        })

    response = await _provider(handler).complete(
        [LLMMessage(role="user", content="hola")],
        tools=[ToolDefinition(name="list_semester_courses", description="d", parameters={})],
    )

    assert response.tool_calls[0].name == "list_semester_courses"
    assert response.tool_calls[0].arguments == {"program_id": 1, "semester": 4}
    assert response.input_tokens == 120
    assert response.output_tokens == 15
    assert response.model == "qwen2.5:3b"


async def test_a_final_answer_has_no_tool_calls() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"message": {"content": "Tienes 3 materias.", "tool_calls": []}}
        )

    response = await _provider(handler).complete([LLMMessage(role="user", content="hola")])
    assert response.content == "Tienes 3 materias."
    assert response.tool_calls == []


async def test_is_loaded_checks_api_ps() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/ps":
            return httpx.Response(200, json={"models": [{"name": "qwen2.5:3b"}]})
        raise AssertionError(f"unexpected path {request.url.path}")

    assert await _provider(handler).is_loaded() is True


async def test_is_loaded_is_false_when_a_different_model_is_resident() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"models": [{"name": "llama3.2:3b"}]})

    assert await _provider(handler).is_loaded() is False


@pytest.mark.llm
async def test_contract_against_a_real_ollama_instance() -> None:
    provider = OllamaProvider(
        base_url="http://localhost:11434", model="qwen2.5:3b", num_ctx=8192, keep_alive="10m"
    )
    response = await provider.complete([LLMMessage(role="user", content="Hola, quien eres?")])
    assert response.model == "qwen2.5:3b"
    assert response.latency_ms > 0
