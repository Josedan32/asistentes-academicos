from dataclasses import fields

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.academic.dto import PrerequisiteResult, PrerequisiteView
from app.application.academic.queries import (
    FindCourseInPrograms,
    GetCourseDetail,
    GetCurriculumBoard,
    GetPrerequisites,
    GetProgram,
    ListCourses,
    ListSemesterCourses,
)
from app.infrastructure.persistence.academic_reader import SqlAlchemyAcademicReader
from app.infrastructure.persistence.academic_repository import normalize_name
from app.infrastructure.persistence.models import (
    CourseModel,
    CurriculumEntryModel,
    PrerequisiteModel,
    ProgramModel,
)


@pytest.fixture
async def reader(session: AsyncSession) -> SqlAlchemyAcademicReader:
    software = ProgramModel(code="ISW", name="Ingenieria en Software", semester_count=10)
    electronics = ProgramModel(code="IEL", name="Ingenieria Electronica", semester_count=10)
    bd1 = CourseModel(
        code="BD1",
        name="Base de Datos 1",
        normalized_name=normalize_name("Base de Datos 1"),
        area="Datos",
        default_credits=3,
    )
    bd2 = CourseModel(
        code="BD2",
        name="Base de Datos 2",
        normalized_name=normalize_name("Base de Datos 2"),
        area="Datos",
        default_credits=4,
        description="Modelado avanzado y optimizacion.",
    )
    session.add_all([software, electronics, bd1, bd2])
    await session.commit()

    first = CurriculumEntryModel(
        program_id=software.id, course_id=bd1.id, semester=3, credits=3
    )
    second = CurriculumEntryModel(
        program_id=software.id, course_id=bd2.id, semester=4, credits=4
    )
    shared = CurriculumEntryModel(
        program_id=electronics.id, course_id=bd2.id, semester=5, credits=3
    )
    session.add_all([first, second, shared])
    await session.commit()

    session.add_all([
        PrerequisiteModel(curriculum_entry_id=second.id, required_course_id=bd1.id),
        # BD1 is also a prerequisite of BD2 inside electronics' own curriculum entry
        # (`shared`), but BD1 itself has no entry there — this is what R4's
        # semester=None test exercises.
        PrerequisiteModel(curriculum_entry_id=shared.id, required_course_id=bd1.id),
    ])
    await session.commit()

    return SqlAlchemyAcademicReader(session)


async def test_lists_courses_of_a_semester(reader: SqlAlchemyAcademicReader) -> None:
    rows = await ListSemesterCourses(reader).execute(program_id=1, semester=4)
    assert [row.code for row in rows] == ["BD2"]
    assert rows[0].credits == 4


async def test_credits_come_from_curriculum_not_course_defaults(
    reader: SqlAlchemyAcademicReader,
) -> None:
    """BD2 declares 4 default credits but counts for 3 in the electronics curriculum."""
    rows = await ListSemesterCourses(reader).execute(program_id=2, semester=5)
    assert rows[0].code == "BD2"
    assert rows[0].credits == 3


async def test_gets_prerequisites_of_a_course(reader: SqlAlchemyAcademicReader) -> None:
    result = await GetPrerequisites(reader).execute(program_id=1, course="Base de Datos 2")
    assert result.resolved_course_name == "Base de Datos 2"
    assert [item.course_code for item in result.prerequisites] == ["BD1"]


def test_prerequisite_view_exposes_no_student_data() -> None:
    """Spec 7.4: prerequisites carry no student status or grades. Pin the shape."""
    assert {field.name for field in fields(PrerequisiteView)} == {
        "course_id",
        "course_code",
        "course_name",
        "semester",
    }
    assert {field.name for field in fields(PrerequisiteResult)} == {
        "resolved_course_name",
        "prerequisites",
        "candidates",
    }


async def test_returns_candidates_when_course_name_is_ambiguous(
    reader: SqlAlchemyAcademicReader,
) -> None:
    result = await GetPrerequisites(reader).execute(program_id=1, course="Base de Datos")
    assert result.prerequisites == []
    assert sorted(result.candidates) == ["Base de Datos 1", "Base de Datos 2"]


async def test_gets_course_detail(reader: SqlAlchemyAcademicReader) -> None:
    detail = await GetCourseDetail(reader).execute(course="BD2")
    assert detail is not None
    assert detail.code == "BD2"
    assert detail.name == "Base de Datos 2"
    assert detail.area == "Datos"


async def test_course_detail_reports_curriculum_credits_not_defaults(
    reader: SqlAlchemyAcademicReader,
) -> None:
    """BD2 declares 4 default credits but counts for 3 in the electronics curriculum."""
    detail = await GetCourseDetail(reader).execute(course="BD2", program_id=2)
    assert detail is not None
    assert detail.credits == 3


async def test_course_detail_without_a_program_reports_no_credits(
    reader: SqlAlchemyAcademicReader,
) -> None:
    """Credits are a property of the curriculum entry, never of the course alone."""
    detail = await GetCourseDetail(reader).execute(course="BD2")
    assert detail is not None
    assert detail.credits is None


async def test_finds_a_course_across_programs(reader: SqlAlchemyAcademicReader) -> None:
    placements = await FindCourseInPrograms(reader).execute(course="Base de Datos 2")
    assert {(p.program_code, p.semester) for p in placements} == {("ISW", 4), ("IEL", 5)}


async def test_prerequisite_outside_the_requiring_curriculum_reports_semester_none(
    reader: SqlAlchemyAcademicReader,
) -> None:
    """BD1 is a prerequisite of BD2 in electronics' curriculum, but BD1 itself is not
    assigned there — the outer join must surface that as semester=None, not crash or
    silently coerce to 0."""
    result = await GetPrerequisites(reader).execute(program_id=2, course="Base de Datos 2")
    assert result.resolved_course_name == "Base de Datos 2"
    assert [p.semester for p in result.prerequisites] == [None]


async def test_prerequisite_inside_the_curriculum_reports_its_semester(
    reader: SqlAlchemyAcademicReader,
) -> None:
    result = await GetPrerequisites(reader).execute(program_id=1, course="Base de Datos 2")
    assert [p.semester for p in result.prerequisites] == [3]


async def test_gets_a_single_program_with_its_course_count(
    reader: SqlAlchemyAcademicReader,
) -> None:
    program = await GetProgram(reader).execute(program_id=1)
    assert program is not None
    assert program.code == "ISW"
    assert program.course_count == 2  # BD1 (sem 3) + BD2 (sem 4), from the fixture


async def test_get_program_returns_none_for_unknown_id(
    reader: SqlAlchemyAcademicReader,
) -> None:
    assert await GetProgram(reader).execute(program_id=999) is None


async def test_curriculum_board_lists_every_semester_with_prerequisites_and_sharing(
    reader: SqlAlchemyAcademicReader,
) -> None:
    board = await GetCurriculumBoard(reader).execute(program_id=1)
    assert [entry.course_code for entry in board] == ["BD1", "BD2"]

    bd2 = next(entry for entry in board if entry.course_code == "BD2")
    assert bd2.semester == 4
    assert bd2.credits == 4
    assert [p.course_code for p in bd2.prerequisites] == ["BD1"]
    assert bd2.shared_program_count == 2  # ISW + IEL both curriculum-place BD2

    bd1 = next(entry for entry in board if entry.course_code == "BD1")
    assert bd1.prerequisites == []
    assert bd1.shared_program_count == 1


async def test_lists_every_course_with_its_program_placements(
    reader: SqlAlchemyAcademicReader,
) -> None:
    courses = await ListCourses(reader).execute()
    assert {c.code for c in courses} == {"BD1", "BD2"}

    bd2 = next(c for c in courses if c.code == "BD2")
    assert {p.program_code for p in bd2.placements} == {"ISW", "IEL"}

    bd1 = next(c for c in courses if c.code == "BD1")
    assert [p.program_code for p in bd1.placements] == ["ISW"]
