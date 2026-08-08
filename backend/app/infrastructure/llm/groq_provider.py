import json
import time
from typing import Any

import httpx

from app.application.agents.llm_types import (
    LLMMessage,
    LLMResponse,
    ToolCallRequest,
    ToolDefinition,
)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _to_openai_message(message: LLMMessage) -> dict[str, Any]:
    payload: dict[str, Any] = {"role": message.role, "content": message.content}
    if message.role == "tool":
        payload["tool_call_id"] = message.tool_call_id or ""
    return payload


def _to_openai_tools(tools: list[ToolDefinition]) -> list[dict[str, Any]]:
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


class GroqProvider:
    """Talks to Groq's OpenAI-compatible `/openai/v1/chat/completions` endpoint."""

    def __init__(
        self, *, api_key: str, model: str, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._transport = transport

    @property
    def model(self) -> str:
        return self._model

    async def is_loaded(self) -> bool:
        return True  # hosted: no local load state to query

    async def complete(
        self, messages: list[LLMMessage], tools: list[ToolDefinition] | None = None
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [_to_openai_message(m) for m in messages],
            "temperature": 0,
        }
        if tools:
            payload["tools"] = _to_openai_tools(tools)

        start = time.monotonic()
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.post(
                GROQ_URL, json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"}, timeout=60.0,
            )
        response.raise_for_status()
        latency_ms = int((time.monotonic() - start) * 1000)

        body = response.json()
        choice = body["choices"][0]["message"]
        # OpenAI wire format: `arguments` is a JSON-encoded string, the opposite of
        # Ollama's native object. This is the one line that differs between the adapters.
        tool_calls = [
            ToolCallRequest(
                id=call["id"], name=call["function"]["name"],
                arguments=json.loads(call["function"]["arguments"]),
            )
            for call in choice.get("tool_calls") or []
        ]
        usage = body.get("usage", {})
        return LLMResponse(
            content=choice.get("content"),
            tool_calls=tool_calls,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            latency_ms=latency_ms,
            model=body.get("model", self._model),
        )
