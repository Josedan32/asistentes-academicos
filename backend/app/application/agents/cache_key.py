import hashlib
import json

from app.application.agents.llm_types import LLMMessage, ToolDefinition


def cache_key(
    messages: list[LLMMessage], model: str, tools: list[ToolDefinition] | None = None
) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": m.role, "content": m.content, "name": m.name} for m in messages
        ],
        "tools": sorted(t.name for t in (tools or [])),
    }
    canonical = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
