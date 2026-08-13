from dataclasses import dataclass, field

import pytest

from app.application.agents.ingest_material import IngestCourseMaterial
from app.domain.agents.materials import CourseMaterial, MaterialChunk


@dataclass
class FakeMaterialRepository:
    materials: list[CourseMaterial] = field(default_factory=list)
    chunks: list[MaterialChunk] = field(default_factory=list)
    next_id: int = 1

    async def add_material(self, material: CourseMaterial) -> CourseMaterial:
        from dataclasses import replace
        saved = replace(material, id=self.next_id)
        self.next_id += 1
        self.materials.append(saved)
        return saved

    async def add_chunks(self, chunks: list[MaterialChunk]) -> None:
        self.chunks.extend(chunks)

    async def delete_material(self, material_id: int) -> None:
        self.materials = [m for m in self.materials if m.id != material_id]
        self.chunks = [c for c in self.chunks if c.material_id != material_id]


@dataclass
class FakeEmbeddingProvider:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text))] for text in texts]


@dataclass
class RaisingEmbeddingProvider:
    """Simulates an unreachable/unpulled-model Ollama, per finding 3 of the final review."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("embedding provider unreachable")


async def test_ingests_a_pdf_into_chunks_with_embeddings() -> None:
    repository = FakeMaterialRepository()
    embedder = FakeEmbeddingProvider()
    command = IngestCourseMaterial(repository=repository, embedder=embedder)

    pdf_bytes = (
        __import__("pathlib").Path(__file__).resolve().parents[2]
        / "fixtures" / "sample.pdf"
    ).read_bytes()

    material = await command.execute(course_id=7, filename="guia.pdf", content=pdf_bytes)

    assert material.course_id == 7
    assert material.filename == "guia.pdf"
    assert len(repository.chunks) >= 1
    assert all(chunk.course_id == 7 for chunk in repository.chunks)
    assert all(chunk.embedding for chunk in repository.chunks)


async def test_unsupported_format_raises_before_touching_the_repository() -> None:
    from app.application.agents.text_extraction import UnsupportedMaterialFormatError

    repository = FakeMaterialRepository()
    command = IngestCourseMaterial(repository=repository, embedder=FakeEmbeddingProvider())

    with pytest.raises(UnsupportedMaterialFormatError):
        await command.execute(course_id=7, filename="slides.pptx", content=b"")

    assert repository.materials == []


async def test_a_failed_embedding_leaves_no_orphan_material_row() -> None:
    """Regression test for finding 3: `add_material` commits before `embed()` runs. If the
    embedder raises (Ollama down, model not pulled), the just-created material row must be
    deleted rather than surviving as a zero-chunk zombie the admin UI lists as a success."""
    repository = FakeMaterialRepository()
    command = IngestCourseMaterial(repository=repository, embedder=RaisingEmbeddingProvider())

    pdf_bytes = (
        __import__("pathlib").Path(__file__).resolve().parents[2]
        / "fixtures" / "sample.pdf"
    ).read_bytes()

    with pytest.raises(RuntimeError):
        await command.execute(course_id=7, filename="guia.pdf", content=pdf_bytes)

    assert repository.materials == []
    assert repository.chunks == []
