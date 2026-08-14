from dataclasses import dataclass

from app.application.agents.chunking import chunk_text
from app.application.agents.material_ports import MaterialRepository
from app.application.agents.ports import EmbeddingProvider
from app.application.agents.text_extraction import extract_text
from app.domain.agents.materials import CourseMaterial, MaterialChunk


@dataclass
class IngestCourseMaterial:
    repository: MaterialRepository
    embedder: EmbeddingProvider

    async def execute(self, *, course_id: int, filename: str, content: bytes) -> CourseMaterial:
        text = extract_text(filename, content)  # raises before any write, per the test above
        chunks = chunk_text(text)

        existing = await self.repository.find_by_filename(course_id, filename)
        if existing is not None:
            assert existing.id is not None
            await self.repository.delete_material(existing.id)

        material = await self.repository.add_material(
            CourseMaterial(course_id=course_id, filename=filename)
        )
        assert material.id is not None

        if chunks:
            try:
                embeddings = await self.embedder.embed(chunks)
                await self.repository.add_chunks([
                    MaterialChunk(
                        material_id=material.id, course_id=course_id, sequence=index + 1,
                        page=None, text=chunk, embedding=embedding,
                    )
                    for index, (chunk, embedding) in enumerate(
                        zip(chunks, embeddings, strict=True)
                    )
                ])
            except Exception:
                await self.repository.delete_material(material.id)
                raise

        return material
