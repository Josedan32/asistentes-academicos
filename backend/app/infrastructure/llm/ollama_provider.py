import time
from typing import Any

import httpx

from app.application.agents.llm_types import (
    LLMMessage,
    LLMResponse,
    ToolCallRequest,
    ToolDefinition,
)


def _to_ollama_message(message: LLMMessage) -> dict[str, Any]:
    payload: dict[str, Any] = {"role": message.role, "content": message.content}
    if message.name is not None:
        payload["name"] = message.name
    return payload


def _to_ollama_tools(tools: list[ToolDefinition]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in tools
    ]


class OllamaProvider:
    """Talks to Ollama's native `/api/chat` and `/api/ps` endpoints — never the
    OpenAI-compatible `/v1/chat/completions` shim (ADR 0006)."""

    def __init__(
        self, *, base_url: str, model: str, num_ctx: int, keep_alive: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._num_ctx = num_ctx
        self._keep_alive = keep_alive
        self._transport = transport

    @property
    def model(self) -> str:
        return self._model

    async def is_loaded(self) -> bool:
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.get(f"{self._base_url}/api/ps", timeout=5.0)
        response.raise_for_status()
        models = response.json().get("models", [])
        return any(m.get("name") == self._model or m.get("model") == self._model for m in models)

    async def complete(
        self, messages: list[LLMMessage], tools: list[ToolDefinition] | None = None
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [_to_ollama_message(m) for m in messages],
            "stream": False,
            "keep_alive": self._keep_alive,
            "options": {"num_ctx": self._num_ctx, "temperature": 0},
        }
        if tools:
            payload["tools"] = _to_ollama_tools(tools)

        start = time.monotonic()
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.post(f"{self._base_url}/api/chat", json=payload, timeout=180.0)
        response.raise_for_status()
        latency_ms = int((time.monotonic() - start) * 1000)

        body = response.json()
        message = body.get("message", {})
        # Ollama returns `arguments` as a native object, not a JSON-encoded string like
        # OpenAI/Groq. json.loads-ing it here would raise on the first tool call.
        tool_calls = [
            ToolCallRequest(
                id=f"ollama-{index}",
                name=call["function"]["name"],
                arguments=call["function"].get("arguments") or {},
            )
            for index, call in enumerate(message.get("tool_calls") or [])
        ]
        return LLMResponse(
            content=message.get("content") or None,
            tool_calls=tool_calls,
            input_tokens=body.get("prompt_eval_count", 0),
            output_tokens=body.get("eval_count", 0),
            latency_ms=latency_ms,
            model=self._model,
        )
