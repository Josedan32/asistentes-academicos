from sqlalchemy.ext.asyncio import AsyncSession

from app.application.agents.tools.get_course_detail import GetCourseDetailArgs
from app.application.agents.tools.registry import (
    TOOLS,
    ToolContext,
    row_count,
    to_jsonable,
    tool_definitions,
)
from app.infrastructure.persistence.academic_reader import SqlAlchemyAcademicReader
from app.infrastructure.persistence.academic_repository import normalize_name
from app.infrastructure.persistence.models import CourseModel, CurriculumEntryModel, ProgramModel


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
