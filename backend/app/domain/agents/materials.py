from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CourseMaterial:
    course_id: int
    filename: str
    id: int | None = None
    uploaded_at: datetime | None = None


@dataclass(frozen=True)
class MaterialChunk:
    material_id: int
    course_id: int
    sequence: int
    text: str
    embedding: list[float]
    page: int | None = None
    id: int | None = None
