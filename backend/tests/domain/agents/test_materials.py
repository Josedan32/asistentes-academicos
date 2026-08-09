from app.domain.agents.materials import CourseMaterial, MaterialChunk


def test_course_material_is_a_frozen_dataclass() -> None:
    material = CourseMaterial(course_id=1, filename="guia.pdf")
    assert material.id is None
    assert material.course_id == 1
    assert material.filename == "guia.pdf"


def test_material_chunk_carries_its_embedding() -> None:
    chunk = MaterialChunk(
        material_id=1, course_id=1, sequence=1, page=3, text="Normalización...",
        embedding=[0.1, 0.2, 0.3],
    )
    assert chunk.embedding == [0.1, 0.2, 0.3]
    assert chunk.page == 3
