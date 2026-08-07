# Module: agents

The tool-calling runtime. Implemented in Plan 2; this file records its contract.

## Ports
- `LLMProvider.complete(messages, tools) -> LLMResponse` where `LLMResponse` normalizes
  `content`, `tool_calls`, `input_tokens`, `output_tokens`, `latency_ms`, `model`.
  The last four are Phase 3's dependent variables.
- `InferenceGate` — acquires a slot and reports queue position.
- `ResponseCache` — keyed on prompt, model and parameters, with TTL.

## Adapters
- `OllamaProvider` uses Ollama's native `/api/chat` in order to set `options.num_ctx`
  (8192; the default of 2048 truncates silently) and `keep_alive`. Ollama returns tool
  arguments as an object, not a JSON string.
- `GroqProvider` targets the hosted comparison model.

## Loop
Compose messages, call the provider with tool definitions, validate arguments with
Pydantic, inject identity server-side, execute, append the result as `role=tool`, repeat.
Hard caps: 3 iterations, per-tool timeout. Invalid arguments return an error to the model
rather than raising. Hitting the cap is recorded, not hidden.

## Tools
`list_semester_courses`, `get_prerequisites`, `get_course_detail`,
`find_course_in_programs` — each backed by a query handler in the academic module. Four
only: small models degrade past five or six. Results never contain student grades or
academic status.

## Persistence
`Conversation`, `Message` (with `prompt_version`), `ToolCall` (name, arguments, result,
duration, row count) and `MessageFeedback`. `ToolCall` is a table, not a JSON column,
because Phase 3 groups by tool name and aggregates durations.
