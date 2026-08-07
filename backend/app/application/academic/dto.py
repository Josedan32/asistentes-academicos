from dataclasses import dataclass, field


@dataclass(frozen=True)
class CourseSummary:
    id: int
    code: str
    name: str
    area: str
    credits: int
    semester: int


@dataclass(frozen=True)
class ProgramSummary:
    id: int
    code: str
    name: str
    semester_count: int
    is_active: bool
    course_count: int


@dataclass(frozen=True)
class PrerequisiteView:
    course_id: int
    course_code: str
    course_name: str
    semester: int


@dataclass(frozen=True)
class PrerequisiteResult:
    """Prerequisites carry no student status or grades. See spec section 7.4."""

    resolved_course_name: str | None
    prerequisites: list[PrerequisiteView] = field(default_factory=list)
    candidates: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CourseDetail:
    id: int
    code: str
    name: str
    area: str
    description: str
    credits: int | None


@dataclass(frozen=True)
class ProgramPlacement:
    program_id: int
    program_code: str
    program_name: str
    semester: int
    credits: int
