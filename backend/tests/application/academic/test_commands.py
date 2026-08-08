import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.academic.commands import (
    AssignCourseToCurriculum,
    CreateCourse,
    CreateProgram,
    MoveCourseToSemester,
    UpdateCourse,
    UpdateProgram,
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


async def test_assigned_entry_carries_its_persisted_id(
    repository: SqlAlchemyAcademicRepository,
) -> None:
    program = await CreateProgram(repository).execute(
        code="ISW", name="Ingenieria en Software", semester_count=10
    )
    course = await CreateCourse(repository).execute(
        code="BD1", name="Base de Datos 1", area="Datos", default_credits=3
    )
    assert program.id is not None and course.id is not None

    entry = await AssignCourseToCurriculum(repository).execute(
        program_id=program.id, course_id=course.id, semester=3, credits=3
    )
    assert entry.id is not None


async def test_moving_one_course_leaves_siblings_untouched(
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
    third = await CreateCourse(repository).execute(
        code="IS1", name="Ingenieria de Software 1", area="Ingenieria", default_credits=3
    )
    assert program.id is not None
    assert first.id is not None and second.id is not None and third.id is not None

    assign = AssignCourseToCurriculum(repository)
    await assign.execute(program_id=program.id, course_id=first.id, semester=3, credits=3)
    await assign.execute(
        program_id=program.id,
        course_id=second.id,
        semester=4,
        credits=4,
        prerequisite_course_ids=(first.id,),
    )
    await assign.execute(program_id=program.id, course_id=third.id, semester=6, credits=3)

    await MoveCourseToSemester(repository).execute(
        program_id=program.id, course_id=third.id, new_semester=8
    )

    reloaded = await repository.load_curriculum(program.id)
    assert reloaded.semester_of(third.id) == 8
    assert reloaded.semester_of(second.id) == 4
    assert reloaded.entry_for(second.id).prerequisite_course_ids == (first.id,)
    assert reloaded.entry_for(second.id).credits == 4


async def test_updates_a_program(repository: SqlAlchemyAcademicRepository) -> None:
    created = await CreateProgram(repository).execute(
        code="ISW", name="Ingenieria en Software", semester_count=10
    )
    assert created.id is not None

    updated = await UpdateProgram(repository).execute(
        program_id=created.id, code="ISW", name="Ingenieria de Software", semester_count=10,
        is_active=False,
    )
    assert updated.name == "Ingenieria de Software"
    assert updated.is_active is False


async def test_updating_an_unknown_program_raises(
    repository: SqlAlchemyAcademicRepository,
) -> None:
    with pytest.raises(LookupError):
        await UpdateProgram(repository).execute(
            program_id=999, code="X", name="X", semester_count=1, is_active=True
        )


async def test_updates_a_course(repository: SqlAlchemyAcademicRepository) -> None:
    created = await CreateCourse(repository).execute(
        code="BD1", name="Base de Datos 1", area="Datos", default_credits=3
    )
    assert created.id is not None

    updated = await UpdateCourse(repository).execute(
        course_id=created.id, code="BD1", name="Base de Datos I", area="Datos",
        default_credits=4,
    )
    assert updated.name == "Base de Datos I"
    assert updated.default_credits == 4


async def test_updating_an_unknown_course_raises(
    repository: SqlAlchemyAcademicRepository,
) -> None:
    with pytest.raises(LookupError):
        await UpdateCourse(repository).execute(
            course_id=999, code="X", name="X", area="X", default_credits=1
        )
