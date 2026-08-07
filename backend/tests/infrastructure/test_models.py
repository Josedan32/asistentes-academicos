import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.persistence.models import (
    Base,
    CourseModel,
    CurriculumEntryModel,
    PrerequisiteModel,
    ProgramModel,
)


@pytest.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as active_session:
        yield active_session
    await engine.dispose()


async def test_persists_program_and_course(session: AsyncSession) -> None:
    session.add(ProgramModel(code="ISW", name="Ingenieria en Software", semester_count=10))
    session.add(CourseModel(code="BD2", name="Base de Datos 2", area="Datos", default_credits=3))
    await session.commit()

    programs = (await session.execute(select(ProgramModel))).scalars().all()
    assert [p.code for p in programs] == ["ISW"]


async def test_rejects_duplicate_course_in_same_program(session: AsyncSession) -> None:
    program = ProgramModel(code="ISW", name="Ingenieria en Software", semester_count=10)
    course = CourseModel(code="BD2", name="Base de Datos 2", area="Datos", default_credits=3)
    session.add_all([program, course])
    await session.commit()

    session.add(
        CurriculumEntryModel(
            program_id=program.id, course_id=course.id, semester=4, credits=3
        )
    )
    await session.commit()

    session.add(
        CurriculumEntryModel(
            program_id=program.id, course_id=course.id, semester=5, credits=3
        )
    )
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_prerequisite_links_to_curriculum_entry(session: AsyncSession) -> None:
    program = ProgramModel(code="ISW", name="Ingenieria en Software", semester_count=10)
    first = CourseModel(code="BD1", name="Base de Datos 1", area="Datos", default_credits=3)
    second = CourseModel(code="BD2", name="Base de Datos 2", area="Datos", default_credits=3)
    session.add_all([program, first, second])
    await session.commit()

    entry = CurriculumEntryModel(
        program_id=program.id, course_id=second.id, semester=4, credits=3
    )
    session.add(entry)
    await session.commit()

    session.add(
        PrerequisiteModel(curriculum_entry_id=entry.id, required_course_id=first.id)
    )
    await session.commit()

    stored = (await session.execute(select(PrerequisiteModel))).scalars().all()
    assert stored[0].required_course_id == first.id
