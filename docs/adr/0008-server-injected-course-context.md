# 8. get_course_detail's program_id is server-injected, not model-generated

Status: accepted (2026-08-07)

## Context
Plan 1's fix wave found that `get_course_detail` degraded silently to `credits=None`
when `program_id` was left optional (residual R2 in the Plan 1 ledger) — the exact
divergence spec §6 exists to prevent. Spec §7.4 spells the tool's signature as
`get_course_detail(course)`: no `program_id` slot at all.

## Decision
`program_id` is not part of `GetCourseDetailArgs` and never appears in the JSON schema
shown to the model. It is injected server-side from the authenticated student's
`StudentProfile`, the same principle spec §7.5 applies to `student_id`, extended here
because the alternative (an optional, model-supplied `program_id`) is exactly what
produced the C1 defect in Plan 1.

## Consequences
- `get_course_detail` always reports credits within the student's own curriculum; it
  cannot be asked about another program's curriculum. `find_course_in_programs` exists
  for that question instead.
- Two tools take `program_id` as a model-generated argument (`list_semester_courses` and
  `get_prerequisites`), matching spec §7.4's table and the measured 47% baseline (ADR 0006).
  `find_course_in_programs` takes no `program_id` at all — it searches across programs.
  Only `get_course_detail` receives injected `program_id`, and only because Plan 1 already
  found the concrete bug this avoids.
