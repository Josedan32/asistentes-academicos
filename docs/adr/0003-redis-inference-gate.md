# 3. Use Redis to serialize inference across worker processes

Status: accepted (2026-08-06)

## Context
The development machine has 4 GB of VRAM and a single Ollama instance. Concurrent
inference requests degrade every request. uvicorn runs multiple worker processes, so an
in-process `asyncio.Lock` would appear to limit concurrency without actually doing so.
The chat interface also shows queue position, so the gate must expose it.

## Decision
Redis holds the inference gate as a list or sorted set supporting position lookup, plus a
TTL-keyed response cache. Persistence is disabled — both structures are safe to lose.
Phase 2 adds the ingestion queue on the same instance.

## Consequences
- Correct concurrency limiting regardless of worker count.
- Redis becomes a hard runtime dependency of the chat endpoint.
- Sessions and tokens deliberately stay in JWT, not Redis.
