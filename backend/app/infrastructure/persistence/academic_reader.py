from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.academic.dto import (
    CourseDetail,
    CourseSummary,
    PrerequisiteView,
    ProgramPlacement,
    ProgramSummary,
)
from app.application.academic.resolver import CourseMatch
from app.infrastructure.persistence.models import (
    CourseModel,
    CurriculumEntryModel,
    PrerequisiteModel,
    ProgramModel,
)


class SqlAlchemyAcademicReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_programs(self) -> list[ProgramSummary]:
        statement = (
            select(ProgramModel, func.count(CurriculumEntryModel.id))
            .outerjoin(CurriculumEntryModel, CurriculumEntryModel.program_id == ProgramModel.id)
            .group_by(ProgramModel.id)
            .order_by(ProgramModel.name)
        )
        rows = (await self._session.execute(statement)).all()
        return [
            ProgramSummary(
                id=program.id,
                code=program.code,
                name=program.name,
                semester_count=program.semester_count,
                is_active=program.is_active,
                course_count=count,
            )
            for program, count in rows
        ]

    async def list_semester_courses(
        self, program_id: int, semester: int
    ) -> list[CourseSummary]:
        statement = (
            select(CourseModel, CurriculumEntryModel)
            .join(CurriculumEntryModel, CurriculumEntryModel.course_id == CourseModel.id)
            .where(
                CurriculumEntryModel.program_id == program_id,
                CurriculumEntryModel.semester == semester,
            )
            .order_by(CourseModel.name)
        )
        rows = (await self._session.execute(statement)).all()
        return [
            CourseSummary(
                id=course.id,
                code=course.code,
                name=course.name,
                area=course.area,
                credits=entry.credits,
                semester=entry.semester,
            )
            for course, entry in rows
        ]

    async def course_candidates(self) -> list[CourseMatch]:
        rows = (await self._session.execute(select(CourseModel))).scalars().all()
        return [CourseMatch(id=row.id, name=row.name, code=row.code) for row in rows]

    async def prerequisites_of(
        self, program_id: int, course_id: int
    ) -> list[PrerequisiteView]:
        entry_id = (
            await self._session.execute(
                select(CurriculumEntryModel.id).where(
                    CurriculumEntryModel.program_id == program_id,
                    CurriculumEntryModel.course_id == course_id,
                )
            )
        ).scalar_one_or_none()
        if entry_id is None:
            return []

        statement = (
            select(CourseModel, CurriculumEntryModel.semester)
            .join(PrerequisiteModel, PrerequisiteModel.required_course_id == CourseModel.id)
            .outerjoin(
                CurriculumEntryModel,
                (CurriculumEntryModel.course_id == CourseModel.id)
                & (CurriculumEntryModel.program_id == program_id),
            )
            .where(PrerequisiteModel.curriculum_entry_id == entry_id)
            .order_by(CourseModel.name)
        )
        rows = (await self._session.execute(statement)).all()
        return [
            PrerequisiteView(
                course_id=course.id,
                course_code=course.code,
                course_name=course.name,
                semester=semester or 0,
            )
            for course, semester in rows
        ]

    async def course_detail(
        self, course_id: int, program_id: int | None = None
    ) -> CourseDetail | None:
        course = await self._session.get(CourseModel, course_id)
        if course is None:
            return None

        credits: int | None = None
        if program_id is not None:
            credits = (
                await self._session.execute(
                    select(CurriculumEntryModel.credits).where(
                        CurriculumEntryModel.course_id == course_id,
                        CurriculumEntryModel.program_id == program_id,
                    )
                )
            ).scalar_one_or_none()

        return CourseDetail(
            id=course.id,
            code=course.code,
            name=course.name,
            area=course.area,
            description=course.description,
            credits=credits,
        )

    async def placements_of(self, course_id: int) -> list[ProgramPlacement]:
        statement = (
            select(ProgramModel, CurriculumEntryModel)
            .join(CurriculumEntryModel, CurriculumEntryModel.program_id == ProgramModel.id)
            .where(CurriculumEntryModel.course_id == course_id)
            .order_by(ProgramModel.name)
        )
        rows = (await self._session.execute(statement)).all()
        return [
            ProgramPlacement(
                program_id=program.id,
                program_code=program.code,
                program_name=program.name,
                semester=entry.semester,
                credits=entry.credits,
            )
            for program, entry in rows
        ]
