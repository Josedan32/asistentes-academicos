from typing import Protocol

from app.application.academic.dto import (
    AcademicHistoryEntry,
    CourseDetail,
    CourseSummary,
    CourseWithUsage,
    CurriculumBoardEntry,
    EnrollmentEntry,
    PrerequisiteView,
    ProgramPlacement,
    ProgramSummary,
)
from app.application.academic.resolver import CourseMatch
from app.domain.academic.curriculum import Curriculum
from app.domain.academic.entities import Course, Program


class AcademicRepository(Protocol):
    async def add_program(self, program: Program) -> Program: ...

    async def add_course(self, course: Course) -> Course: ...

    async def update_program(self, program: Program) -> Program: ...

    async def update_course(self, course: Course) -> Course: ...

    async def load_curriculum(self, program_id: int) -> Curriculum: ...

    async def save_curriculum(self, curriculum: Curriculum) -> None: ...

    async def course_exists(self, course_id: int) -> bool: ...


class AcademicReader(Protocol):
    async def list_programs(self) -> list[ProgramSummary]: ...

    async def get_program(self, program_id: int) -> ProgramSummary | None: ...

    async def list_semester_courses(
        self, program_id: int, semester: int
    ) -> list[CourseSummary]: ...

    async def course_candidates(self) -> list[CourseMatch]: ...

    async def prerequisites_of(self, program_id: int, course_id: int) -> list[PrerequisiteView]: ...

    async def course_detail(
        self, course_id: int, program_id: int | None = None
    ) -> CourseDetail | None: ...

    async def placements_of(self, course_id: int) -> list[ProgramPlacement]: ...

    async def curriculum_board(self, program_id: int) -> list[CurriculumBoardEntry]: ...

    async def list_courses(self) -> list[CourseWithUsage]: ...


class StudentHistoryReader(Protocol):
    async def history_of(self, student_user_id: int) -> list[AcademicHistoryEntry]: ...

    async def enrollments_of(self, student_user_id: int) -> list[EnrollmentEntry]: ...
