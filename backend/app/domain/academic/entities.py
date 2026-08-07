from dataclasses import dataclass


@dataclass(frozen=True)
class Program:
    code: str
    name: str
    semester_count: int
    is_active: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("program code must not be blank")
        if not self.name.strip():
            raise ValueError("program name must not be blank")
        if not 1 <= self.semester_count <= 12:
            raise ValueError("semester_count must be between 1 and 12")


@dataclass(frozen=True)
class Course:
    code: str
    name: str
    area: str
    default_credits: int
    description: str = ""
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("course code must not be blank")
        if not self.name.strip():
            raise ValueError("course name must not be blank")
        if self.default_credits < 1:
            raise ValueError("default_credits must be positive")


@dataclass(frozen=True)
class CurriculumEntry:
    program_id: int
    course_id: int
    semester: int
    credits: int
    prerequisite_course_ids: tuple[int, ...] = ()
    id: int | None = None
