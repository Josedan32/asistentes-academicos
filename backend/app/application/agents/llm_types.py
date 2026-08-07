from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LLMMessage:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tool_call_id: str | None = None
    name: str | None = None  # tool name, set when role == "tool"


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema, derived from a Pydantic model


@dataclass(frozen=True)
class ToolCallRequest:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class LLMResponse:
    """Normalizes every provider's reply. The last four fields are Phase 3's dependent
    variables (spec §7.2) — they must never be provider-specific."""

    content: str | None
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    model: str = ""
