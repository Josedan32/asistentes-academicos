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
        # Full definition, not just the name: a tool's JSON schema changing (e.g. an
        # argument removed to fix a model behaviour bug) must invalidate old cached
        # completions generated under the previous schema, not keep serving them.
        "tools": [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in sorted((tools or []), key=lambda t: t.name)
        ],
    }
    canonical = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
