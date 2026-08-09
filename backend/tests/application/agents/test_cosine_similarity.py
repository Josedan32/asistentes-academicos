import math

from app.application.agents.cosine_similarity import cosine_similarity


def test_identical_vectors_have_similarity_one() -> None:
    assert math.isclose(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)


def test_orthogonal_vectors_have_similarity_zero() -> None:
    assert math.isclose(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0, abs_tol=1e-9)


def test_opposite_vectors_have_similarity_negative_one() -> None:
    assert math.isclose(cosine_similarity([1.0, 0.0], [-1.0, 0.0]), -1.0)


def test_a_zero_vector_has_zero_similarity_not_a_division_error() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0
