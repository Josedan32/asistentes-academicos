# 2. Separate commands from queries, without event sourcing

Status: accepted (2026-08-06)

## Context
Writes (coordination editing curricula) are rare and must enforce invariants. Reads
(agent tools) are constant, latency-sensitive, and want denormalized shapes. Most CQRS
material bundles the pattern with event sourcing, which is a separate pattern.

## Decision
Two ports per module: `AcademicRepository` for writes through domain aggregates,
`AcademicReader` for reads returning flat DTOs. One database. No event bus, no event
sourcing, no eventual consistency.

## Consequences
- Agent tools skip aggregate hydration entirely.
- Invariants have exactly one home: the `Curriculum` aggregate.
- Two ports to keep in sync instead of one.
- Phase 2's vector index fits the same shape as a materialized read projection.
