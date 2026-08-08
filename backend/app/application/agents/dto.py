from dataclasses import dataclass


@dataclass(frozen=True)
class StudentContext:
    program_id: int
    current_semester: int
    active_course_name: str | None = None
