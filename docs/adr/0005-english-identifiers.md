# 5. English identifiers, Spanish interface copy

Status: accepted (2026-08-06)

## Context
The repository owner's standing rule is English code, comments, documentation and
commits. The domain is Colombian academia, and tool identifiers appear in the chat
transparency panel, which students read.

## Decision
All identifiers in English, including domain entities and tool names
(`Program`, `Course`, `CurriculumEntry`, `get_prerequisites`). All user-facing interface
copy in Spanish. The transparency panel shows a Spanish prose label next to the English
monospace identifier.

## Consequences
- One rule, no per-file judgement calls.
- Institutional terms need a translation table: carrera → Program, materia → Course,
  malla curricular → CurriculumEntry, prerrequisito → Prerequisite.
- Students see English identifiers only in the expanded tool detail.
