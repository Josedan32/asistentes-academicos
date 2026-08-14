from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.agents.materials import CourseMaterial, MaterialChunk
from app.infrastructure.persistence.material_reader import SqlAlchemyMaterialReader
from app.infrastructure.persistence.material_repository import SqlAlchemyMaterialRepository
from app.infrastructure.persistence.models import CourseModel


async def test_adds_a_material_and_its_chunks_then_lists_them(session: AsyncSession) -> None:
    course = CourseModel(code="BD2", name="Base de Datos 2", area="Datos", default_credits=4)
    session.add(course)
    await session.commit()

    repository = SqlAlchemyMaterialRepository(session)
    material = await repository.add_material(
        CourseMaterial(course_id=course.id, filename="guia.pdf")
    )
    assert material.id is not None

    await repository.add_chunks([
        MaterialChunk(
            material_id=material.id, course_id=course.id, sequence=1, page=1,
            text="Primer fragmento", embedding=[0.1, 0.2],
        ),
        MaterialChunk(
            material_id=material.id, course_id=course.id, sequence=2, page=1,
            text="Segundo fragmento", embedding=[0.3, 0.4],
        ),
    ])

    reader = SqlAlchemyMaterialReader(session)
    materials = await reader.list_materials(course.id)
    assert [m.filename for m in materials] == ["guia.pdf"]


async def test_deleting_a_material_cascades_its_chunks(session: AsyncSession) -> None:
    course = CourseModel(code="BD2", name="Base de Datos 2", area="Datos", default_credits=4)
    session.add(course)
    await session.commit()

    repository = SqlAlchemyMaterialRepository(session)
    material = await repository.add_material(
        CourseMaterial(course_id=course.id, filename="guia.pdf")
    )
    assert material.id is not None
    await repository.add_chunks([
        MaterialChunk(
            material_id=material.id, course_id=course.id, sequence=1, page=None,
            text="x", embedding=[0.1],
        ),
    ])

    await repository.delete_material(material.id)

    reader = SqlAlchemyMaterialReader(session)
    assert await reader.list_materials(course.id) == []


async def test_find_by_filename_returns_none_when_no_material_matches(
    session: AsyncSession,
) -> None:
    course = CourseModel(code="BD2", name="Base de Datos 2", area="Datos", default_credits=4)
    session.add(course)
    await session.commit()

    repository = SqlAlchemyMaterialRepository(session)
    assert await repository.find_by_filename(course.id, "guia.pdf") is None


async def test_find_by_filename_returns_the_matching_material(session: AsyncSession) -> None:
    course = CourseModel(code="BD2", name="Base de Datos 2", area="Datos", default_credits=4)
    session.add(course)
    await session.commit()

    repository = SqlAlchemyMaterialRepository(session)
    await repository.add_material(CourseMaterial(course_id=course.id, filename="guia.pdf"))

    found = await repository.find_by_filename(course.id, "guia.pdf")
    assert found is not None
    assert found.filename == "guia.pdf"
