# Module: academic

Owns programs, courses, curricula and prerequisites. Every agent tool reads from here.

## Domain
- `Program(code, name, semester_count, is_active)` — validates a 1..12 semester count.
- `Course(code, name, area, default_credits, description)` — independent of any program.
- `CurriculumEntry(program_id, course_id, semester, credits, prerequisite_course_ids)`.
- `Curriculum` aggregate — owns every rule spanning more than one entry:
  `assign()` and `move()` raise `InvalidSemesterError`, `InvalidCreditsError`,
  `DuplicateCourseInCurriculumError`, `CourseNotInCurriculumError`, `PrerequisiteNotInCurriculumError`,
  `PrerequisiteNotEarlierError`. `semester_of()` and `entry_for()` read it back;
  `entry_for()` raises `CourseNotInCurriculumError` for an unknown course.

## Key rules
- A course belongs to many programs. `CurriculumEntry` is the association.
- Prerequisites hang off a `CurriculumEntry`, so they can differ per program.
- The prerequisite's *owning* side (`curriculum_entry_id`) is enforced by the schema; its
  *required* side (`required_course_id`) is not. Nothing in the database prevents a
  prerequisite naming a course outside that program's curriculum — the `Curriculum`
  aggregate does, via `PrerequisiteNotInCurriculumError`. Every write goes through the
  aggregate, so the invariant holds in practice, but it is a domain guarantee rather than
  a structural one.
- `CurriculumEntry.credits` is authoritative; `Course.default_credits` only pre-fills forms.
- `move()` re-validates both directions: a course may not land on or before its own
  prerequisites, nor on or after anything that depends on it.

## Application
Commands: `CreateProgram`, `CreateCourse`, `AssignCourseToCurriculum`, `MoveCourseToSemester`.
Queries: `ListPrograms`, `ListSemesterCourses`, `GetPrerequisites`, `GetCourseDetail`,
`FindCourseInPrograms` — the last four back the agent tools.

## Course name resolution
`resolve_course()` takes free text and returns `Resolved`, `Ambiguous` or `NotFound`.

Order: course code, exact normalized name, literal containment, then similarity.

- **Containment** fires when the student's text appears verbatim inside a course name, and
  is guarded by `MIN_CONTAINMENT_LENGTH = 4` so a stray digit or `"de"` cannot match
  everything. It exists because `SequenceMatcher` penalises length differences, so natural
  abbreviations such as `"Herramientas"` scored 0.571 and dead-ended at `NotFound`.
- **Similarity** resolves above `STRONG_MATCH` (0.86), returns candidates between
  `WEAK_MATCH` (0.62) and `STRONG_MATCH`, and returns nothing below. The mid-confidence
  branch filters candidates by `WEAK_MATCH` before truncating — without that filter it
  offered students courses it had itself scored as irrelevant.

Ties return candidates rather than guessing — a confidently wrong prerequisite is the
failure mode this system exists to prevent.
