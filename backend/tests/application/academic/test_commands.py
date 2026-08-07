import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.academic.commands import (
    AssignCourseToCurriculum,
    CreateCourse,
    CreateProgram,
    MoveCourseToSemester,
)
from app.domain.academic.exceptions import (
    DuplicateCourseInCurriculumError,
    PrerequisiteNotEarlierError,
)
from app.infrastructure.persistence.academic_repository import SqlAlchemyAcademicRepository


@pytest.fixture
def repository(session: AsyncSession) -> SqlAlchemyAcademicRepository:
    return SqlAlchemyAcademicRepository(session)


async def test_creates_program(repository: SqlAlchemyAcademicRepository) -> None:
    program = await CreateProgram(repository).execute(
        code="ISW", name="Ingenieria en Software", semester_count=10
    )
    assert program.id is not None
    assert program.code == "ISW"


async def test_assigns_course_with_prerequisite(
    repository: SqlAlchemyAcademicRepository,
) -> None:
    program = await CreateProgram(repository).execute(
        code="ISW", name="Ingenieria en Software", semester_count=10
    )
    first = await CreateCourse(repository).execute(
        code="BD1", name="Base de Datos 1", area="Datos", default_credits=3
    )
    second = await CreateCourse(repository).execute(
        code="BD2", name="Base de Datos 2", area="Datos", default_credits=4
    )
    assert program.id is not None and first.id is not None and second.id is not None

    assign = AssignCourseToCurriculum(repository)
    await assign.execute(program_id=program.id, course_id=first.id, semester=3, credits=3)
    entry = await assign.execute(
        program_id=program.id,
        course_id=second.id,
        semester=4,
        credits=4,
        prerequisite_course_ids=(first.id,),
    )

    assert entry.semester == 4
    assert entry.prerequisite_course_ids == (first.id,)


async def test_rejects_assigning_same_course_twice(
    repository: SqlAlchemyAcademicRepository,
) -> None:
    program = await CreateProgram(repository).execute(
        code="ISW", name="Ingenieria en Software", semester_count=10
    )
    course = await CreateCourse(repository).execute(
        code="BD1", name="Base de Datos 1", area="Datos", default_credits=3
    )
    assert program.id is not None and course.id is not None

    assign = AssignCourseToCurriculum(repository)
    await assign.execute(program_id=program.id, course_id=course.id, semester=3, credits=3)
    with pytest.raises(DuplicateCourseInCurriculumError):
        await assign.execute(program_id=program.id, course_id=course.id, semester=5, credits=3)


async def test_move_rejects_breaking_prerequisite_order(
    repository: SqlAlchemyAcademicRepository,
) -> None:
    program = await CreateProgram(repository).execute(
        code="ISW", name="Ingenieria en Software", semester_count=10
    )
    first = await CreateCourse(repository).execute(
        code="BD1", name="Base de Datos 1", area="Datos", default_credits=3
    )
    second = await CreateCourse(repository).execute(
        code="BD2", name="Base de Datos 2", area="Datos", default_credits=4
    )
    assert program.id is not None and first.id is not None and second.id is not None

    assign = AssignCourseToCurriculum(repository)
    await assign.execute(program_id=program.id, course_id=first.id, semester=3, credits=3)
    await assign.execute(
        program_id=program.id,
        course_id=second.id,
        semester=4,
        credits=4,
        prerequisite_course_ids=(first.id,),
    )

    with pytest.raises(PrerequisiteNotEarlierError):
        await MoveCourseToSemester(repository).execute(
            program_id=program.id, course_id=second.id, new_semester=3
        )


async def test_move_persists_new_semester(
    repository: SqlAlchemyAcademicRepository,
) -> None:
    program = await CreateProgram(repository).execute(
        code="ISW", name="Ingenieria en Software", semester_count=10
    )
    course = await CreateCourse(repository).execute(
        code="BD1", name="Base de Datos 1", area="Datos", default_credits=3
    )
    assert program.id is not None and course.id is not None

    await AssignCourseToCurriculum(repository).execute(
        program_id=program.id, course_id=course.id, semester=3, credits=3
    )
    await MoveCourseToSemester(repository).execute(
        program_id=program.id, course_id=course.id, new_semester=7
    )

    curriculum = await repository.load_curriculum(program.id)
    assert curriculum.semester_of(course.id) == 7
