from app.application.academic.resolver import (
    Ambiguous,
    CourseMatch,
    NotFound,
    Resolved,
    resolve_course,
)

CANDIDATES = [
    CourseMatch(id=1, name="Base de Datos 1", code="BD1"),
    CourseMatch(id=2, name="Base de Datos 2", code="BD2"),
    CourseMatch(id=3, name="Ingenieria de Software 1", code="IS1"),
    CourseMatch(id=4, name="Herramientas de Programacion 2", code="HP2"),
]


def test_resolves_exact_name() -> None:
    result = resolve_course("Base de Datos 2", CANDIDATES)
    assert isinstance(result, Resolved)
    assert result.course_id == 2


def test_resolves_ignoring_case_and_accents() -> None:
    result = resolve_course("BASE DE DATOS 2", CANDIDATES)
    assert isinstance(result, Resolved)
    assert result.course_id == 2


def test_resolves_by_course_code() -> None:
    result = resolve_course("hp2", CANDIDATES)
    assert isinstance(result, Resolved)
    assert result.course_id == 4


def test_resolves_close_misspelling() -> None:
    result = resolve_course("Ingenieria de Sofware 1", CANDIDATES)
    assert isinstance(result, Resolved)
    assert result.course_id == 3


def test_returns_candidates_when_query_is_ambiguous() -> None:
    result = resolve_course("Base de Datos", CANDIDATES)
    assert isinstance(result, Ambiguous)
    assert {candidate.id for candidate in result.candidates} == {1, 2}


def test_returns_not_found_for_unrelated_query() -> None:
    result = resolve_course("Termodinamica Aplicada", CANDIDATES)
    assert isinstance(result, NotFound)


def test_mid_confidence_match_offers_only_plausible_candidates() -> None:
    """The scored fallback must drop candidates it scored below WEAK_MATCH.

    "Ingenieria de Sistemas 1" is not contained in any course name and scores 0.792
    against "Ingenieria de Software 1", landing between WEAK_MATCH and STRONG_MATCH.
    The other three courses score below WEAK_MATCH. Without the filter this branch
    would return the top three regardless, offering the student two irrelevant courses.
    """
    result = resolve_course("Ingenieria de Sistemas 1", CANDIDATES)
    assert isinstance(result, Ambiguous)
    assert [candidate.id for candidate in result.candidates] == [3]


def test_resolves_a_natural_abbreviation() -> None:
    result = resolve_course("Herramientas", CANDIDATES)
    assert isinstance(result, Resolved)
    assert result.course_id == 4


def test_containment_needs_a_meaningful_length() -> None:
    """A one or two character query must not match everything it appears inside."""
    assert isinstance(resolve_course("1", CANDIDATES), NotFound)
    assert isinstance(resolve_course("de", CANDIDATES), NotFound)
