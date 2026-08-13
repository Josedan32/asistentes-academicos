from sqlalchemy.ext.asyncio import AsyncSession

from app.application.agents.tools.get_course_detail import GetCourseDetailArgs
from app.application.agents.tools.get_prerequisites import GetPrerequisitesArgs
from app.application.agents.tools.list_semester_courses import ListSemesterCoursesArgs
from app.application.agents.tools.registry import (
    TOOLS,
    ToolContext,
    ToolDependencies,
    row_count,
    to_jsonable,
    tool_definitions,
)
from app.application.agents.tools.search_course_material import SearchCourseMaterialArgs
from app.domain.agents.materials import CourseMaterial, MaterialChunk
from app.infrastructure.persistence.academic_reader import SqlAlchemyAcademicReader
from app.infrastructure.persistence.academic_repository import normalize_name
from app.infrastructure.persistence.material_reader import SqlAlchemyMaterialReader
from app.infrastructure.persistence.material_repository import SqlAlchemyMaterialRepository
from app.infrastructure.persistence.models import (
    CourseModel,
    CurriculumEntryModel,
    PrerequisiteModel,
    ProgramModel,
)
from tests.application.agents.fakes import FakeEmbeddingProvider, FakeMaterialReader


def _deps(reader: SqlAlchemyAcademicReader) -> ToolDependencies:
    return ToolDependencies(
        reader=reader, material_reader=FakeMaterialReader(), embedder=FakeEmbeddingProvider()
    )


def test_exactly_five_tools_are_registered() -> None:
    assert set(TOOLS) == {
        "list_semester_courses", "get_prerequisites", "get_course_detail",
        "find_course_in_programs", "search_course_material",
    }


def test_tool_definitions_expose_a_json_schema_for_each_tool() -> None:
    definitions = tool_definitions()
    assert len(definitions) == 5
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

    in_electronics = await spec.handler(
        _deps(reader), args, ToolContext(program_id=electronics.id, current_semester=4)
    )
    in_software = await spec.handler(
        _deps(reader), args, ToolContext(program_id=software.id, current_semester=4)
    )

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

    in_software = await spec.handler(
        _deps(reader), args, ToolContext(program_id=software.id, current_semester=4)
    )
    in_electronics = await spec.handler(
        _deps(reader), args, ToolContext(program_id=electronics.id, current_semester=4)
    )

    assert [c.code for c in in_software] == ["BD1"]
    assert [c.code for c in in_electronics] == ["CIR1"]


async def test_list_semester_courses_defaults_to_the_students_own_semester(
    session: AsyncSession,
) -> None:
    """qwen2.5:3b sometimes asks the student which semester they mean even when they are
    plainly asking about their own ("que puedo ver este semestre") — omitting the argument
    must not be a dead end, it must fall back to the injected current_semester."""
    software = ProgramModel(code="ISW", name="Ingenieria en Software", semester_count=10)
    bd = CourseModel(
        code="BD1", name="Base de Datos 1", normalized_name=normalize_name("Base de Datos 1"),
        area="Datos", default_credits=3,
    )
    session.add_all([software, bd])
    await session.commit()
    session.add(
        CurriculumEntryModel(program_id=software.id, course_id=bd.id, semester=5, credits=3)
    )
    await session.commit()

    reader = SqlAlchemyAcademicReader(session)
    spec = TOOLS["list_semester_courses"]
    args = spec.argument_model()

    rows = await spec.handler(
        _deps(reader), args, ToolContext(program_id=software.id, current_semester=5)
    )

    assert [c.code for c in rows] == ["BD1"]


async def test_list_semester_courses_honours_an_explicit_semester_over_the_default(
    session: AsyncSession,
) -> None:
    software = ProgramModel(code="ISW", name="Ingenieria en Software", semester_count=10)
    bd = CourseModel(
        code="BD1", name="Base de Datos 1", normalized_name=normalize_name("Base de Datos 1"),
        area="Datos", default_credits=3,
    )
    session.add_all([software, bd])
    await session.commit()
    session.add(
        CurriculumEntryModel(program_id=software.id, course_id=bd.id, semester=6, credits=3)
    )
    await session.commit()

    reader = SqlAlchemyAcademicReader(session)
    spec = TOOLS["list_semester_courses"]
    args = spec.argument_model(semester=6)

    rows = await spec.handler(
        _deps(reader), args, ToolContext(program_id=software.id, current_semester=5)
    )

    assert [c.code for c in rows] == ["BD1"]


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

    in_software = await spec.handler(
        _deps(reader), args, ToolContext(program_id=software.id, current_semester=4)
    )
    in_electronics = await spec.handler(
        _deps(reader), args, ToolContext(program_id=electronics.id, current_semester=4)
    )

    assert [p.course_code for p in in_software.prerequisites] == ["BD1"]
    assert in_electronics.prerequisites == []


def test_search_course_material_schema_never_exposes_course_id() -> None:
    schema = TOOLS["search_course_material"].definition.parameters
    assert "course_id" not in schema["properties"]
    assert set(SearchCourseMaterialArgs.model_fields) == {"query", "course"}


async def test_search_course_material_uses_the_active_course_by_default(
    session: AsyncSession,
) -> None:
    course = CourseModel(
        code="BD2", name="Base de Datos 2", normalized_name=normalize_name("Base de Datos 2"),
        area="Datos", default_credits=4,
    )
    session.add(course)
    await session.commit()

    material_repository = SqlAlchemyMaterialRepository(session)
    material = await material_repository.add_material(
        CourseMaterial(course_id=course.id, filename="guia.pdf")
    )
    assert material.id is not None
    await material_repository.add_chunks([
        MaterialChunk(material_id=material.id, course_id=course.id, sequence=1, page=None,
                       text="que es normalizacion", embedding=[1.0, 0.0]),
    ])

    reader = SqlAlchemyAcademicReader(session)
    material_reader = SqlAlchemyMaterialReader(session)
    spec = TOOLS["search_course_material"]
    args = spec.argument_model(query="que es normalizacion")
    deps = ToolDependencies(
        reader=reader, material_reader=material_reader, embedder=FakeEmbeddingProvider(dimensions=2)
    )

    result = await spec.handler(
        deps, args,
        ToolContext(program_id=1, current_semester=1, active_course_id=course.id),
    )

    assert result["fragments"][0]["text"] == "que es normalizacion"


async def test_search_course_material_searches_a_named_course_instead_of_the_active_one(
    session: AsyncSession,
) -> None:
    """A student can name a different course (typically a prerequisite) to search, per
    spec §2 — proving `Resolved` actually rewires `course_id` away from `active_course_id`."""
    active_course = CourseModel(
        code="BD2", name="Base de Datos 2", normalized_name=normalize_name("Base de Datos 2"),
        area="Datos", default_credits=4,
    )
    named_course = CourseModel(
        code="BD1", name="Base de Datos 1", normalized_name=normalize_name("Base de Datos 1"),
        area="Datos", default_credits=3,
    )
    session.add_all([active_course, named_course])
    await session.commit()

    material_repository = SqlAlchemyMaterialRepository(session)
    active_material = await material_repository.add_material(
        CourseMaterial(course_id=active_course.id, filename="bd2.pdf")
    )
    named_material = await material_repository.add_material(
        CourseMaterial(course_id=named_course.id, filename="bd1.pdf")
    )
    assert active_material.id is not None and named_material.id is not None
    await material_repository.add_chunks([
        MaterialChunk(material_id=active_material.id, course_id=active_course.id, sequence=1,
                       page=None, text="contenido de base de datos 2", embedding=[1.0, 0.0]),
        MaterialChunk(material_id=named_material.id, course_id=named_course.id, sequence=1,
                       page=None, text="contenido de base de datos 1", embedding=[1.0, 0.0]),
    ])

    reader = SqlAlchemyAcademicReader(session)
    material_reader = SqlAlchemyMaterialReader(session)
    spec = TOOLS["search_course_material"]
    args = spec.argument_model(query="contenido", course="Base de Datos 1")
    deps = ToolDependencies(
        reader=reader, material_reader=material_reader, embedder=FakeEmbeddingProvider(dimensions=2)
    )

    result = await spec.handler(
        deps, args,
        ToolContext(program_id=1, current_semester=1, active_course_id=active_course.id),
    )

    assert result["fragments"] == [{"text": "contenido de base de datos 1", "page": None}]


async def test_search_course_material_falls_back_to_active_course_when_the_name_is_unresolved(
    session: AsyncSession,
) -> None:
    """An unresolvable `course` (NotFound/Ambiguous) must not leave the tool stuck — it
    silently keeps searching the active course rather than surfacing a resolver error."""
    active_course = CourseModel(
        code="BD2", name="Base de Datos 2", normalized_name=normalize_name("Base de Datos 2"),
        area="Datos", default_credits=4,
    )
    session.add(active_course)
    await session.commit()

    material_repository = SqlAlchemyMaterialRepository(session)
    material = await material_repository.add_material(
        CourseMaterial(course_id=active_course.id, filename="bd2.pdf")
    )
    assert material.id is not None
    await material_repository.add_chunks([
        MaterialChunk(material_id=material.id, course_id=active_course.id, sequence=1, page=None,
                       text="contenido de base de datos 2", embedding=[1.0, 0.0]),
    ])

    reader = SqlAlchemyAcademicReader(session)
    material_reader = SqlAlchemyMaterialReader(session)
    spec = TOOLS["search_course_material"]
    args = spec.argument_model(query="contenido", course="Materia que no existe zzz")
    deps = ToolDependencies(
        reader=reader, material_reader=material_reader, embedder=FakeEmbeddingProvider(dimensions=2)
    )

    result = await spec.handler(
        deps, args,
        ToolContext(program_id=1, current_semester=1, active_course_id=active_course.id),
    )

    assert result["fragments"] == [{"text": "contenido de base de datos 2", "page": None}]
