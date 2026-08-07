# 1. Implement the agent loop directly, without LangChain or LlamaIndex

Status: accepted (2026-08-06)

## Context
The research group's line of work is agents. The tool-calling loop is the object of
study, not an implementation detail. LangChain's `AgentExecutor` encapsulates exactly
that loop.

## Decision
Implement the loop directly against provider APIs, behind an `LLMProvider` protocol.
Use narrow single-purpose libraries where useful (`pypdf`, a text splitter in Phase 2),
never a framework that owns the architecture.

## Consequences
- Every step is instrumentable, which is what Phase 3 measures.
- A fake `LLMProvider` makes the loop testable with no model running.
- We write and maintain roughly 80 lines per provider adapter ourselves.
- No free document loaders; Phase 2 wires its own ingestion.
