# Module: agents

The tool-calling runtime behind the chat endpoint: a hand-written loop (ADR 0001, no
agent framework) that composes a system prompt, calls an LLM provider with tool
definitions, executes the tools the model asks for, and streams the result over SSE.

## Ports

All in `backend/app/application/agents/ports.py`:

- `ConversationRepository` — write side. `create`, `add_message`, `add_tool_call`,
  `add_feedback`; every call persists and returns the row with its id populated.
- `ConversationReader` — read side. `get`, `history`, `message_owner` (the `user_id` that
  owns a message, used to authorize feedback).
- `LLMProvider` — `model` (property), `is_loaded()` (drives the `loading_model` SSE
  event; hosted providers always return `True`), and
  `complete(messages, tools) -> LLMResponse`. `LLMResponse` normalizes `content`,
  `tool_calls`, `input_tokens`, `output_tokens`, `latency_ms`, `model` across providers.
- `PromptComposer` — `compose_system_prompt(context) -> (prompt_text, prompt_version)`.
  Every `Message` records the version it was generated under.
- `InferenceGate` — `enqueue`, `position`, `release`. One inference at a time, across
  every uvicorn worker process (spec §8.2).
- `ResponseCache` — `get`, `set`. Keyed on a hash of prompt, model and parameters, with
  a TTL.

## Adapters

- `OllamaProvider` (`backend/app/infrastructure/llm/ollama_provider.py`) talks to
  Ollama's native `/api/chat` and `/api/ps` endpoints, never the OpenAI-compatible
  `/v1/chat/completions` shim (ADR 0006). It sets `options.num_ctx` (the default of 2048
  truncates silently) and `keep_alive`. Ollama returns tool call arguments as a native
  object, not a JSON-encoded string.
- `GroqProvider` (`backend/app/infrastructure/llm/groq_provider.py`) targets Groq's
  OpenAI-compatible `/openai/v1/chat/completions` endpoint; unlike Ollama, `arguments`
  arrives as a JSON-encoded string and must be `json.loads`-ed.
- `CachingLLMProvider` (`backend/app/infrastructure/llm/caching_provider.py`) wraps any
  `LLMProvider` with a `ResponseCache` transparently — the loop and the wrapped adapter
  never need to know it is there.
- `RedisInferenceGate` (`backend/app/infrastructure/redis/inference_gate.py`) uses a
  Redis sorted set keyed by an ever-increasing sequence number for FIFO order and an
  O(log n) position lookup (`ZRANK`), atomically, without a separate lock.
- `RedisResponseCache` (`backend/app/infrastructure/redis/response_cache.py`) stores the
  serialized `LLMResponse` under `response_cache:<key>` with the configured TTL.
- `TemplatePromptComposer` (`backend/app/infrastructure/prompts/composer.py`) renders a
  versioned text template (`templates/<version>.txt`) with the student's `program_id`,
  current semester and, when set, the active course.

## Loop

`AgentLoop.run()` (`backend/app/application/agents/agent_loop.py`) persists the user
message, composes the system prompt, then repeats up to `MAX_ITERATIONS` (3) times: call
`provider.complete()` with the four tool definitions, and if the response carries no
tool calls, persist and yield a `DoneEvent` and return. Otherwise it persists the
assistant turn, and for each requested tool call yields a `ThinkingEvent`, validates the
arguments against the tool's Pydantic model, executes the handler with a server-built
`ToolContext` under a `TOOL_TIMEOUT_SECONDS` (10.0) watchdog, persists the `ToolCall` row,
and yields a `ToolCallEvent`. Invalid arguments, an unknown tool name, or a timeout are
each turned into a `role=tool` error message fed back to the model rather than raising.
Exhausting all iterations without a final answer is recorded as `hit_iteration_cap=True`
on the `DoneEvent` and returns a fixed fallback message — the cap is surfaced, not
hidden.

Event types: `ThinkingEvent` (`tool`), `ToolCallEvent` (`name`, `arguments`, `result`,
`duration_ms`, `row_count`), `DoneEvent` (`content`, `tool_count`,
`hit_iteration_cap`).

## Tools

`backend/app/application/agents/tools/`: `list_semester_courses`, `get_prerequisites`,
`get_course_detail`, `find_course_in_programs` — each a thin wrapper around the matching
query handler in the academic module (`ListSemesterCourses`, `GetPrerequisites`,
`GetCourseDetail`, `FindCourseInPrograms`). Four only: small models degrade past five or
six tools (ADR 0006). Results never contain student grades or academic status.

`get_course_detail` is the one deviation: its `GetCourseDetailArgs` has no `program_id`
field, and the JSON schema shown to the model never mentions it (spec §7.4's signature is
`get_course_detail(course)`). `program_id` is instead read from `ToolContext`, built by
the loop from the authenticated student's `StudentContext` and passed to every handler —
the same identity-injection principle spec §7.5 applies to `student_id`, extended here
because Plan 1 already hit the concrete bug an optional, model-supplied `program_id`
produces (ADR 0008). Two other tools take `program_id` as a model-generated argument:
`list_semester_courses` and `get_prerequisites`. `find_course_in_programs` takes no
`program_id` at all — its whole purpose is searching across programs.

## Persistence

`backend/app/domain/agents/entities.py`: `Conversation` (`user_id`, `course_id`,
`title`), `Message` (`conversation_id`, `role`, `content`, `prompt_version`), `ToolCall`
(`message_id`, `name`, `arguments`, `result`, `duration_ms`, `row_count`, `sequence`) and
`MessageFeedback` (`message_id`, `value`, `comment`). Each maps to its own table
(`ConversationModel`, `MessageModel`, `ToolCallModel`, `MessageFeedbackModel` in
`backend/app/infrastructure/persistence/models.py`) behind `ConversationRepository`/
`ConversationReader`. `ToolCall` is a table, not a JSON column, so tool usage can later be
grouped by name and aggregated by duration.

## Chat endpoint

`backend/app/api/v1/chat.py` exposes `POST /api/v1/chat`, streaming Server-Sent Events.
Per turn it enqueues a ticket on the `InferenceGate` and polls its position at a fixed
interval, emitting `queued` events until the ticket reaches the front; polling is bounded
by `MAX_QUEUE_POLL_ITERATIONS`, and exhausting it emits an `error` event with
`code: "queue_timeout"` instead of blocking forever. If the provider reports the model is
not currently loaded, a `loading_model` event is emitted before the loop starts. The loop's
`ThinkingEvent`/`ToolCallEvent` map directly to `thinking`/`tool_call` SSE events; a
`DoneEvent` is chunked word-by-word into a sequence of `token` events followed by one
`done` event (ADR 0007 — `LLMProvider` has no streaming method, so the endpoint chunks the
already-complete response instead of the loop generating it incrementally). Any exception
raised after the stream has started — including `provider.is_loaded()` failing before the
loop even runs — is caught and turned into an `error` event, since a normal HTTP error
response is no longer possible once streaming has begun. The gate ticket is always
released in a `finally` block shielded from cancellation (`anyio.CancelScope(shield=True)`),
so a client disconnect cannot leak a ticket and stall every request queued behind it.

`POST /api/v1/chat/messages/{message_id}/feedback` records a `MessageFeedback` row after
checking `ConversationReader.message_owner()` matches the requesting user.
