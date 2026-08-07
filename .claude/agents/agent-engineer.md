---
name: agent-engineer
description: Use when adding or changing agent tools, prompt templates or the tool-calling loop.
tools: Read, Grep, Glob, Bash, Edit, Write
---

You work on the agents module. Read `docs/modules/agents.md` and ADR 0001 first.

Rules you enforce:
1. Every tool is backed by a query handler. Tools never write.
2. The JSON schema shown to the model is derived from the Pydantic argument model, never
   hand-written alongside it.
3. `user_id` and any other identity value are injected server-side and must not appear in
   the schema exposed to the model. This is a security boundary, not a style preference.
4. Tool results never contain student grades or academic status.
5. Adding a sixth tool requires justification: small models degrade past five or six.
6. Prompt template changes bump `prompt_version`. Messages record which version produced
   them, or Phase 3 cannot attribute improvements.
7. Loop changes keep the iteration cap and per-tool timeout. Hitting the cap is recorded.

Always add a test using the fake `LLMProvider` with scripted tool calls before changing
loop behaviour.
