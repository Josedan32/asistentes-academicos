import unicodedata
from dataclasses import replace

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.academic.curriculum import Curriculum
from app.domain.academic.entities import Course, CurriculumEntry, Program
from app.infrastructure.persistence.models import (
    CourseModel,
    CurriculumEntryModel,
    PrerequisiteModel,
    ProgramModel,
)


def normalize_name(value: str) -> str:
    """Lowercase and strip accents so 'Ingeniería' and 'ingenieria' match."""
    decomposed = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


class SqlAlchemyAcademicRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_program(self, program: Program) -> Program:
        model = ProgramModel(
            code=program.code,
            name=program.name,
            semester_count=program.semester_count,
            is_active=program.is_active,
        )
        self._session.add(model)
        await self._session.commit()
        return Program(
            id=model.id,
            code=model.code,
            name=model.name,
            semester_count=model.semester_count,
            is_active=model.is_active,
        )

    async def add_course(self, course: Course) -> Course:
        model = CourseModel(
            code=course.code,
            name=course.name,
            normalized_name=normalize_name(course.name),
            area=course.area,
            default_credits=course.default_credits,
            description=course.description,
        )
        self._session.add(model)
        await self._session.commit()
        return Course(
            id=model.id,
            code=model.code,
            name=model.name,
            area=model.area,
            default_credits=model.default_credits,
            description=model.description,
        )

    async def update_program(self, program: Program) -> Program:
        assert program.id is not None, "update_program requires a persisted program"
        model = await self._session.get(ProgramModel, program.id)
        if model is None:
            raise LookupError(f"program {program.id} does not exist")
        model.code = program.code
        model.name = program.name
        model.semester_count = program.semester_count
        model.is_active = program.is_active
        await self._session.commit()
        return program

    async def update_course(self, course: Course) -> Course:
        assert course.id is not None, "update_course requires a persisted course"
        model = await self._session.get(CourseModel, course.id)
        if model is None:
            raise LookupError(f"course {course.id} does not exist")
        model.code = course.code
        model.name = course.name
        model.normalized_name = normalize_name(course.name)
        model.area = course.area
        model.default_credits = course.default_credits
        model.description = course.description
        await self._session.commit()
        return course

    async def course_exists(self, course_id: int) -> bool:
        found = await self._session.get(CourseModel, course_id)
        return found is not None

    async def load_curriculum(self, program_id: int) -> Curriculum:
        program_model = await self._session.get(ProgramModel, program_id)
        if program_model is None:
            raise LookupError(f"program {program_id} does not exist")

        rows = (
            (
                await self._session.execute(
                    select(CurriculumEntryModel).where(
                        CurriculumEntryModel.program_id == program_id
                    )
                )
            )
            .scalars()
            .all()
        )

        entries: list[CurriculumEntry] = []
        for row in rows:
            prerequisite_ids = (
                (
                    await self._session.execute(
                        select(PrerequisiteModel.required_course_id).where(
                            PrerequisiteModel.curriculum_entry_id == row.id
                        )
                    )
                )
                .scalars()
                .all()
            )
            entries.append(
                CurriculumEntry(
                    id=row.id,
                    program_id=row.program_id,
                    course_id=row.course_id,
                    semester=row.semester,
                    credits=row.credits,
                    prerequisite_course_ids=tuple(prerequisite_ids),
                )
            )

        program = Program(
            id=program_model.id,
            code=program_model.code,
            name=program_model.name,
            semester_count=program_model.semester_count,
            is_active=program_model.is_active,
        )
        return Curriculum(program=program, entries=entries)

    async def save_curriculum(self, curriculum: Curriculum) -> None:
        program_id = curriculum.program.id
        if program_id is None:
            raise ValueError("cannot save a curriculum for an unpersisted program")

        for index, entry in enumerate(curriculum.entries):
            if entry.id is None:
                model = CurriculumEntryModel(
                    program_id=program_id,
                    course_id=entry.course_id,
                    semester=entry.semester,
                    credits=entry.credits,
                )
                self._session.add(model)
                await self._session.flush()
                curriculum.entries[index] = replace(entry, id=model.id)
                self._add_prerequisites(model.id, entry.prerequisite_course_ids)
            else:
                existing = await self._session.get(CurriculumEntryModel, entry.id)
                if existing is None:
                    raise LookupError(f"curriculum entry {entry.id} vanished")

                if existing.semester != entry.semester or existing.credits != entry.credits:
                    existing.semester = entry.semester
                    existing.credits = entry.credits

                stored = set(
                    (
                        await self._session.execute(
                            select(PrerequisiteModel.required_course_id).where(
                                PrerequisiteModel.curriculum_entry_id == existing.id
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                if stored != set(entry.prerequisite_course_ids):
                    await self._session.execute(
                        delete(PrerequisiteModel).where(
                            PrerequisiteModel.curriculum_entry_id == existing.id
                        )
                    )
                    self._add_prerequisites(existing.id, entry.prerequisite_course_ids)

        await self._session.commit()

    def _add_prerequisites(self, entry_id: int, course_ids: tuple[int, ...]) -> None:
        for required_course_id in course_ids:
            self._session.add(
                PrerequisiteModel(
                    curriculum_entry_id=entry_id, required_course_id=required_course_id
                )
            )
