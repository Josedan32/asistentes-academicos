from dataclasses import replace

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.agents.materials import CourseMaterial, MaterialChunk
from app.infrastructure.persistence.models import CourseMaterialModel, MaterialChunkModel


class SqlAlchemyMaterialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_filename(self, course_id: int, filename: str) -> CourseMaterial | None:
        model = (
            await self._session.execute(
                select(CourseMaterialModel).where(
                    CourseMaterialModel.course_id == course_id,
                    CourseMaterialModel.filename == filename,
                )
            )
        ).scalar_one_or_none()
        if model is None:
            return None
        return CourseMaterial(
            id=model.id, course_id=model.course_id, filename=model.filename,
            uploaded_at=model.uploaded_at,
        )

    async def add_material(self, material: CourseMaterial) -> CourseMaterial:
        model = CourseMaterialModel(course_id=material.course_id, filename=material.filename)
        self._session.add(model)
        await self._session.commit()
        return replace(material, id=model.id, uploaded_at=model.uploaded_at)

    async def add_chunks(self, chunks: list[MaterialChunk]) -> None:
        for chunk in chunks:
            self._session.add(
                MaterialChunkModel(
                    material_id=chunk.material_id, course_id=chunk.course_id,
                    sequence=chunk.sequence, page=chunk.page, text=chunk.text,
                    embedding=chunk.embedding,
                )
            )
        await self._session.commit()

    async def delete_material(self, material_id: int) -> None:
        await self._session.execute(
            delete(CourseMaterialModel).where(CourseMaterialModel.id == material_id)
        )
        await self._session.commit()
