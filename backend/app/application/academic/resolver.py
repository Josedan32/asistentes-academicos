"""Resolve a free-text course name to a single course.

The model repeats whatever the student typed, so exact identifiers are not available.
When several courses are plausible the resolver returns the candidates instead of
guessing: a confidently wrong prerequisite is the failure this system exists to prevent.
"""

import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

STRONG_MATCH = 0.86
WEAK_MATCH = 0.62
AMBIGUITY_MARGIN = 0.06


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


@dataclass(frozen=True)
class CourseMatch:
    id: int
    name: str
    code: str


@dataclass(frozen=True)
class Resolved:
    course_id: int
    name: str


@dataclass(frozen=True)
class Ambiguous:
    candidates: list[CourseMatch]


@dataclass(frozen=True)
class NotFound:
    pass


Resolution = Resolved | Ambiguous | NotFound


def resolve_course(query: str, candidates: list[CourseMatch]) -> Resolution:
    normalized_query = normalize(query)
    if not normalized_query or not candidates:
        return NotFound()

    for candidate in candidates:
        if normalize(candidate.code) == normalized_query:
            return Resolved(course_id=candidate.id, name=candidate.name)

    exact = [c for c in candidates if normalize(c.name) == normalized_query]
    if len(exact) == 1:
        return Resolved(course_id=exact[0].id, name=exact[0].name)

    scored = sorted(
        (
            (SequenceMatcher(None, normalized_query, normalize(c.name)).ratio(), c)
            for c in candidates
        ),
        key=lambda pair: pair[0],
        reverse=True,
    )

    best_score, best = scored[0]
    if best_score < WEAK_MATCH:
        return NotFound()

    tied = [candidate for score, candidate in scored if best_score - score <= AMBIGUITY_MARGIN]
    if len(tied) > 1:
        return Ambiguous(candidates=tied)

    if best_score >= STRONG_MATCH:
        return Resolved(course_id=best.id, name=best.name)

    return Ambiguous(candidates=[candidate for _, candidate in scored[:3]])
