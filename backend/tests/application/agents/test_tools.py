from sqlalchemy.ext.asyncio import AsyncSession

from app.application.agents.tools.get_course_detail import GetCourseDetailArgs
from app.application.agents.tools.get_prerequisites import GetPrerequisitesArgs
from app.application.agents.tools.list_semester_courses import ListSemesterCoursesArgs
from app.application.agents.tools.registry import (
    TOOLS,
    ToolContext,
    row_count,
    to_jsonable,
    tool_definitions,
)
from app.infrastructure.persistence.academic_reader import SqlAlchemyAcademicReader
from app.infrastructure.persistence.academic_repository import normalize_name
from app.infrastructure.persistence.models import (
    CourseModel,
    CurriculumEntryModel,
    PrerequisiteModel,
    ProgramModel,
)


def test_exactly_four_tools_are_registered() -> None:
    assert set(TOOLS) == {
        "list_semester_courses", "get_prerequisites", "get_course_detail",
        "find_course_in_programs",
    }


def test_tool_definitions_expose_a_json_schema_for_each_tool() -> None:
    definitions = tool_definitions()
    assert len(definitions) == 4
    assert all(d.parameters["type"] == "object" for d in definitions)


def test_get_course_detail_schema_never_exposes_program_id() -> None:
    """The security boundary from spec §7.5, extended to program_id per residual R2:
    it must never appear in what the model sees, only in what the server injects."""
    schema = TOOLS["get_course_detail"].definition.parameters
    assert "program_id" not in schema["properties"]
    assert set(GetCourseDetailArgs.model_fields) == {"course"}


def test_list_semester_courses_schema_never_exposes_program_id() -> None:
    """qwen2.5:3b does not reliably pull program_id out of the system prompt and instead
    asks the student for it (observed in production) — the same fix as get_course_detail."""
    schema = TOOLS["list_semester_courses"].definition.parameters
    assert "program_id" not in schema["properties"]
    assert set(ListSemesterCoursesArgs.model_fields) == {"semester"}


def test_get_prerequisites_schema_never_exposes_program_id() -> None:
    schema = TOOLS["get_prerequisites"].definition.parameters
    assert "program_id" not in schema["properties"]
    assert set(GetPrerequisitesArgs.model_fields) == {"course"}


def test_row_count_of_a_resolved_course_detail() -> None:
    assert row_count("get_course_detail", object()) == 1


def test_row_count_of_a_missing_course_detail() -> None:
    assert row_count("get_course_detail", None) == 0


def test_to_jsonable_converts_nested_dataclasses() -> None:
    from app.application.academic.dto import PrerequisiteResult, PrerequisiteView

    result = PrerequisiteResult(
        resolved_course_name="Base de Datos 2",
        prerequisites=[
            PrerequisiteView(
                course_id=1, course_code="BD1", course_name="Base de Datos 1", semester=3
            )
        ],
    )
    payload = to_jsonable(result)
    assert payload == {
        "resolved_course_name": "Base de Datos 2",
        "prerequisites": [
            {"course_id": 1, "course_code": "BD1", "course_name": "Base de Datos 1", "semester": 3}
        ],
        "candidates": [],
    }


async def test_get_course_detail_uses_the_injected_program_id_for_credits(
    session: AsyncSession,
) -> None:
    software = ProgramModel(code="ISW", name="Ingenieria en Software", semester_count=10)
    electronics = ProgramModel(code="IEL", name="Ingenieria Electronica", semester_count=10)
    course = CourseModel(
        code="BD2", name="Base de Datos 2", normalized_name=normalize_name("Base de Datos 2"),
        area="Datos", default_credits=4,
    )
    session.add_all([software, electronics, course])
    await session.commit()
    session.add_all([
        CurriculumEntryModel(program_id=software.id, course_id=course.id, semester=4, credits=4),
        CurriculumEntryModel(program_id=electronics.id, course_id=course.id, semester=5, credits=3),
    ])
    await session.commit()

    reader = SqlAlchemyAcademicReader(session)
    spec = TOOLS["get_course_detail"]
    args = spec.argument_model(course="Base de Datos 2")

    in_electronics = await spec.handler(reader, args, ToolContext(program_id=electronics.id))
    in_software = await spec.handler(reader, args, ToolContext(program_id=software.id))

    assert in_electronics.credits == 3
    assert in_software.credits == 4


async def test_list_semester_courses_uses_the_injected_program_id(session: AsyncSession) -> None:
    software = ProgramModel(code="ISW", name="Ingenieria en Software", semester_count=10)
    electronics = ProgramModel(code="IEL", name="Ingenieria Electronica", semester_count=10)
    bd = CourseModel(
        code="BD1", name="Base de Datos 1", normalized_name=normalize_name("Base de Datos 1"),
        area="Datos", default_credits=3,
    )
    circuits = CourseModel(
        code="CIR1", name="Circuitos 1", normalized_name=normalize_name("Circuitos 1"),
        area="Electronica", default_credits=4,
    )
    session.add_all([software, electronics, bd, circuits])
    await session.commit()
    session.add_all([
        CurriculumEntryModel(program_id=software.id, course_id=bd.id, semester=3, credits=3),
        CurriculumEntryModel(
            program_id=electronics.id, course_id=circuits.id, semester=3, credits=4
        ),
    ])
    await session.commit()

    reader = SqlAlchemyAcademicReader(session)
    spec = TOOLS["list_semester_courses"]
    args = spec.argument_model(semester=3)

    in_software = await spec.handler(reader, args, ToolContext(program_id=software.id))
    in_electronics = await spec.handler(reader, args, ToolContext(program_id=electronics.id))

    assert [c.code for c in in_software] == ["BD1"]
    assert [c.code for c in in_electronics] == ["CIR1"]


async def test_get_prerequisites_uses_the_injected_program_id(session: AsyncSession) -> None:
    software = ProgramModel(code="ISW", name="Ingenieria en Software", semester_count=10)
    electronics = ProgramModel(code="IEL", name="Ingenieria Electronica", semester_count=10)
    bd1 = CourseModel(
        code="BD1", name="Base de Datos 1", normalized_name=normalize_name("Base de Datos 1"),
        area="Datos", default_credits=3,
    )
    bd2 = CourseModel(
        code="BD2", name="Base de Datos 2", normalized_name=normalize_name("Base de Datos 2"),
        area="Datos", default_credits=4,
    )
    session.add_all([software, electronics, bd1, bd2])
    await session.commit()
    software_entry = CurriculumEntryModel(
        program_id=software.id, course_id=bd2.id, semester=4, credits=4
    )
    electronics_entry = CurriculumEntryModel(
        program_id=electronics.id, course_id=bd2.id, semester=5, credits=3
    )
    session.add_all([
        CurriculumEntryModel(program_id=software.id, course_id=bd1.id, semester=3, credits=3),
        software_entry, electronics_entry,
    ])
    await session.commit()
    session.add(
        PrerequisiteModel(curriculum_entry_id=software_entry.id, required_course_id=bd1.id)
    )
    await session.commit()

    reader = SqlAlchemyAcademicReader(session)
    spec = TOOLS["get_prerequisites"]
    args = spec.argument_model(course="Base de Datos 2")

    in_software = await spec.handler(reader, args, ToolContext(program_id=software.id))
    in_electronics = await spec.handler(reader, args, ToolContext(program_id=electronics.id))

    assert [p.course_code for p in in_software.prerequisites] == ["BD1"]
    assert in_electronics.prerequisites == []
