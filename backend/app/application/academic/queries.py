"""Query handlers. Each of the four agent tools in Plan 2 is backed by one of these."""

from dataclasses import dataclass

from app.application.academic.dto import (
    CourseDetail,
    CourseSummary,
    CourseWithUsage,
    CurriculumBoardEntry,
    PrerequisiteResult,
    ProgramPlacement,
    ProgramSummary,
)
from app.application.academic.ports import AcademicReader
from app.application.academic.resolver import Ambiguous, Resolved, resolve_course


@dataclass
class ListPrograms:
    reader: AcademicReader

    async def execute(self) -> list[ProgramSummary]:
        return await self.reader.list_programs()


@dataclass
class GetProgram:
    reader: AcademicReader

    async def execute(self, *, program_id: int) -> ProgramSummary | None:
        return await self.reader.get_program(program_id)


@dataclass
class ListSemesterCourses:
    reader: AcademicReader

    async def execute(self, *, program_id: int, semester: int) -> list[CourseSummary]:
        return await self.reader.list_semester_courses(program_id, semester)


@dataclass
class GetPrerequisites:
    reader: AcademicReader

    async def execute(self, *, program_id: int, course: str) -> PrerequisiteResult:
        resolution = resolve_course(course, await self.reader.course_candidates())
        if isinstance(resolution, Ambiguous):
            return PrerequisiteResult(
                resolved_course_name=None,
                candidates=[candidate.name for candidate in resolution.candidates],
            )
        if not isinstance(resolution, Resolved):
            return PrerequisiteResult(resolved_course_name=None)

        rows = await self.reader.prerequisites_of(program_id, resolution.course_id)
        return PrerequisiteResult(resolved_course_name=resolution.name, prerequisites=rows)


@dataclass
class GetCourseDetail:
    reader: AcademicReader

    async def execute(
        self, *, course: str, program_id: int | None = None
    ) -> CourseDetail | None:
        resolution = resolve_course(course, await self.reader.course_candidates())
        if not isinstance(resolution, Resolved):
            return None
        return await self.reader.course_detail(resolution.course_id, program_id)


@dataclass
class FindCourseInPrograms:
    reader: AcademicReader

    async def execute(self, *, course: str) -> list[ProgramPlacement]:
        resolution = resolve_course(course, await self.reader.course_candidates())
        if not isinstance(resolution, Resolved):
            return []
        return await self.reader.placements_of(resolution.course_id)


@dataclass
class GetCurriculumBoard:
    reader: AcademicReader

    async def execute(self, *, program_id: int) -> list[CurriculumBoardEntry]:
        return await self.reader.curriculum_board(program_id)


@dataclass
class ListCourses:
    reader: AcademicReader

    async def execute(self) -> list[CourseWithUsage]:
        return await self.reader.list_courses()
