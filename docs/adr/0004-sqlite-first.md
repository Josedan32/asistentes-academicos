# 4. Start on SQLite, move to PostgreSQL when vectors arrive

Status: accepted (2026-08-06)

## Context
Phase 1 stores programs, courses, curricula, users and conversations — no vector search.
PostgreSQL would be infrastructure maintained without being used.

## Decision
SQLite through async SQLAlchemy for Phase 1. Alembic from the first commit so the change
is a migration rather than a rewrite. PostgreSQL with pgvector arrives in Phase 2, when a
vector index is genuinely needed.

## Consequences
- No container required to run the backend.
- SQLite does not enforce foreign keys by default and has no trigram operator, so course
  name resolution runs in Python; Phase 2 can move it to `pg_trgm`.
- Alembic must run with `render_as_batch=True` for SQLite column changes.
