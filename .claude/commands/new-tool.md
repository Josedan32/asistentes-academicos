---
description: Scaffold a new agent tool with its query handler and tests
---

Add a new agent tool named $ARGUMENTS.

Before writing anything, confirm the tool count stays at or below six. If it would exceed
six, stop and explain the trade-off — small models confuse tool selection past that point.

Then, in order:
1. Add the read method to `AcademicReader` in `app/application/academic/ports.py` and
   implement it in `app/infrastructure/persistence/academic_reader.py`.
2. Add a DTO in `app/application/academic/dto.py`. Flat, frozen, no domain entities.
3. Add the query handler in `app/application/academic/queries.py`.
4. Add a test in `backend/tests/infrastructure/test_academic_reader.py` covering the happy
   path, the empty result, and — if it takes a course name — the ambiguous case.
5. Register the tool with its Pydantic argument model. Do not hand-write the JSON schema.
6. Add a loop test using the fake `LLMProvider` that scripts a call to this tool.

Identity values are injected server-side and must not appear in the argument model.
Results must not contain student grades or academic status.
