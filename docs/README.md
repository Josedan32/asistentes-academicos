# Documentation

Two kinds of document live here, and the difference matters.

**Decision records** (`adr/`) explain *why*. They are written once, when a decision is made,
and are not edited afterwards — a superseded decision gets a new record that references the
old one. Read these before proposing an architectural change; the reasoning that led here is
usually not obvious from the code.

**Module contracts** (`modules/`) explain *what*. They describe each module's interface and
the rules it owns, and they are kept current with the code. A statement here that
contradicts the implementation is a defect, not a stale note.

---

## Decision records

| # | Decision | Why it matters |
|---|---|---|
| [0001](adr/0001-no-agent-framework.md) | Implement the agent loop directly, no LangChain or LlamaIndex | The loop is the object of study; a framework would hide it and make it unmeasurable |
| [0002](adr/0002-light-cqrs.md) | Separate commands from queries, without event sourcing | Reads and writes have opposite shapes here; every agent tool is a read |
| [0003](adr/0003-redis-inference-gate.md) | Redis serialises inference across worker processes | 4 GB of VRAM allows one inference at a time, and an in-process lock cannot see other workers |
| [0004](adr/0004-sqlite-first.md) | SQLite now, PostgreSQL when vectors arrive | Running PostgreSQL in Phase 1 would be infrastructure maintained without being used |
| [0005](adr/0005-english-identifiers.md) | English identifiers, Spanish interface copy | One rule, no per-file judgement calls |
| [0006](adr/0006-local-model-tool-calling-baseline.md) | The 47% tool-calling baseline stands unmodified | A figure obtained by tuning prompts measures prompt engineering, not the model |

`backend/tests/docs/test_adr_structure.py` fails the suite if any record loses its
`Status:` line or its Context, Decision or Consequences sections. That test exists because
an ADR without consequences is how these degrade into notes nobody reads.

### Adding one

Copy the structure of an existing record: numbered filename (`NNNN-kebab-case-slug.md`),
a `Status:` line, then `## Context`, `## Decision`, `## Consequences`. Record the decision
and its costs — not a summary of what the code does.

---

## Module contracts

| Module | Owns |
|---|---|
| [academic](modules/academic.md) | Programs, courses, curricula, prerequisites, course name resolution. Every agent tool reads from here |
| [identity](modules/identity.md) | Users, roles, student profiles, the authentication boundary |
| [agents](modules/agents.md) | The tool-calling runtime: provider port, loop, tools, persistence |

---

## Three rules these documents keep repeating

They are repeated because each one was violated at least once during development and
caught by a review.

**Credits come from the curriculum, never from the course.** The same course is worth
different credits in different programs. `CurriculumEntry.credits` is authoritative;
`Course.default_credits` only pre-fills a form.

**Identity is injected server-side.** It enters the system at exactly one place,
`require_authentication`, and never appears in a request body or in the JSON schema the
model sees. A model-controlled `student_id` is prompt injection reaching another person's
data.

**No grades, no academic status, anywhere.** The design prototype showed prerequisites
carrying `"estado": "aprobada"` and a grade. That was removed from scope: it depends on a
system outside this project's control and puts sensitive personal data into an LLM prompt.

---

## Not tracked in git

`docs/superpowers/` holds working specs and implementation plans, and is git-ignored by the
repository owner's convention. The design spec lives at
`docs/superpowers/specs/2026-08-06-academic-assistants-design.md` on disk. Anything from it
that must survive belongs in an ADR or a module contract.
