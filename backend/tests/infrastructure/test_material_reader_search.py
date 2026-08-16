from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.agents.materials import CourseMaterial, MaterialChunk
from app.infrastructure.persistence.material_reader import SqlAlchemyMaterialReader
from app.infrastructure.persistence.material_repository import SqlAlchemyMaterialRepository
from app.infrastructure.persistence.models import CourseModel


async def test_search_ranks_chunks_by_cosine_similarity_within_the_course(
    session: AsyncSession,
) -> None:
    course = CourseModel(code="BD2", name="Base de Datos 2", area="Datos", default_credits=4)
    other_course = CourseModel(code="BD1", name="Base de Datos 1", area="Datos", default_credits=3)
    session.add_all([course, other_course])
    await session.commit()

    repository = SqlAlchemyMaterialRepository(session)
    material = await repository.add_material(
        CourseMaterial(course_id=course.id, filename="guia.pdf")
    )
    other_material = await repository.add_material(
        CourseMaterial(course_id=other_course.id, filename="otra.pdf")
    )
    assert material.id is not None and other_material.id is not None
    await repository.add_chunks(
        [
            MaterialChunk(
                material_id=material.id,
                course_id=course.id,
                sequence=1,
                page=None,
                text="normalizacion",
                embedding=[1.0, 0.0],
            ),
            MaterialChunk(
                material_id=material.id,
                course_id=course.id,
                sequence=2,
                page=None,
                text="indices",
                embedding=[0.0, 1.0],
            ),
            MaterialChunk(
                material_id=other_material.id,
                course_id=other_course.id,
                sequence=1,
                page=None,
                text="de otra materia",
                embedding=[1.0, 0.0],
            ),
        ]
    )

    reader = SqlAlchemyMaterialReader(session)
    results = await reader.search(course.id, query_embedding=[0.9, 0.1], limit=5)

    assert [chunk.text for chunk in results] == ["normalizacion", "indices"]


async def test_search_respects_the_limit(session: AsyncSession) -> None:
    course = CourseModel(code="BD2", name="Base de Datos 2", area="Datos", default_credits=4)
    session.add(course)
    await session.commit()
    repository = SqlAlchemyMaterialRepository(session)
    material = await repository.add_material(
        CourseMaterial(course_id=course.id, filename="guia.pdf")
    )
    assert material.id is not None
    await repository.add_chunks(
        [
            MaterialChunk(
                material_id=material.id,
                course_id=course.id,
                sequence=i,
                page=None,
                text=f"chunk {i}",
                embedding=[1.0, 0.0],
            )
            for i in range(1, 6)
        ]
    )

    reader = SqlAlchemyMaterialReader(session)
    results = await reader.search(course.id, query_embedding=[1.0, 0.0], limit=3)

    assert len(results) == 3
