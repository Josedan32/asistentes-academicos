from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.agents.materials import CourseMaterial
from app.infrastructure.persistence.models import CourseMaterialModel


class SqlAlchemyMaterialReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_materials(self, course_id: int) -> list[CourseMaterial]:
        rows = (
            await self._session.execute(
                select(CourseMaterialModel)
                .where(CourseMaterialModel.course_id == course_id)
                .order_by(CourseMaterialModel.uploaded_at)
            )
        ).scalars()
        return [
            CourseMaterial(
                id=row.id, course_id=row.course_id, filename=row.filename,
                uploaded_at=row.uploaded_at,
            )
            for row in rows
        ]

    async def get_material(self, material_id: int) -> CourseMaterial | None:
        model = await self._session.get(CourseMaterialModel, material_id)
        if model is None:
            return None
        return CourseMaterial(
            id=model.id, course_id=model.course_id, filename=model.filename,
            uploaded_at=model.uploaded_at,
        )
