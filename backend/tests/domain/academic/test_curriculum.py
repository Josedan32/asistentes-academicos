import pytest

from app.domain.academic.curriculum import Curriculum
from app.domain.academic.entities import CurriculumEntry, Program
from app.domain.academic.exceptions import (
    CourseNotInCurriculumError,
    DuplicateCourseInCurriculumError,
    InvalidCreditsError,
    InvalidSemesterError,
    PrerequisiteNotEarlierError,
    PrerequisiteNotInCurriculumError,
)


def make_program() -> Program:
    return Program(id=1, code="ISW", name="Ingenieria en Software", semester_count=10)


def make_curriculum() -> Curriculum:
    program = make_program()
    return Curriculum(
        program=program,
        entries=[
            CurriculumEntry(id=1, program_id=1, course_id=100, semester=3, credits=3),
            CurriculumEntry(id=2, program_id=1, course_id=101, semester=3, credits=4),
        ],
    )


def test_program_rejects_out_of_range_semester_count() -> None:
    with pytest.raises(ValueError):
        Program(code="ISW", name="Ingenieria en Software", semester_count=0)


def test_program_rejects_blank_code() -> None:
    with pytest.raises(ValueError):
        Program(code="   ", name="Ingenieria en Software", semester_count=10)


def test_assign_adds_entry_to_curriculum() -> None:
    curriculum = make_curriculum()
    entry = curriculum.assign(course_id=200, semester=4, credits=3)
    assert entry.course_id == 200
    assert entry.semester == 4
    assert curriculum.semester_of(200) == 4


def test_assign_accepts_prerequisite_from_earlier_semester() -> None:
    curriculum = make_curriculum()
    entry = curriculum.assign(
        course_id=200, semester=4, credits=3, prerequisite_course_ids=(100,)
    )
    assert entry.prerequisite_course_ids == (100,)


def test_assign_rejects_semester_beyond_program_length() -> None:
    curriculum = make_curriculum()
    with pytest.raises(InvalidSemesterError):
        curriculum.assign(course_id=200, semester=11, credits=3)


def test_assign_rejects_zero_credits() -> None:
    curriculum = make_curriculum()
    with pytest.raises(InvalidCreditsError):
        curriculum.assign(course_id=200, semester=4, credits=0)


def test_assign_rejects_course_already_in_curriculum() -> None:
    curriculum = make_curriculum()
    with pytest.raises(DuplicateCourseInCurriculumError):
        curriculum.assign(course_id=100, semester=5, credits=3)


def test_assign_rejects_prerequisite_absent_from_curriculum() -> None:
    curriculum = make_curriculum()
    with pytest.raises(PrerequisiteNotInCurriculumError):
        curriculum.assign(course_id=200, semester=4, credits=3, prerequisite_course_ids=(999,))


def test_assign_rejects_prerequisite_in_same_semester() -> None:
    curriculum = make_curriculum()
    with pytest.raises(PrerequisiteNotEarlierError):
        curriculum.assign(course_id=200, semester=3, credits=3, prerequisite_course_ids=(100,))


def test_move_updates_semester() -> None:
    curriculum = make_curriculum()
    curriculum.assign(course_id=200, semester=4, credits=3, prerequisite_course_ids=(100,))
    moved = curriculum.move(course_id=200, new_semester=6)
    assert moved.semester == 6
    assert curriculum.semester_of(200) == 6


def test_move_rejects_landing_on_own_prerequisite_semester() -> None:
    curriculum = make_curriculum()
    curriculum.assign(course_id=200, semester=4, credits=3, prerequisite_course_ids=(100,))
    with pytest.raises(PrerequisiteNotEarlierError):
        curriculum.move(course_id=200, new_semester=3)


def test_move_rejects_overtaking_a_dependent_course() -> None:
    curriculum = make_curriculum()
    curriculum.assign(course_id=200, semester=4, credits=3)
    curriculum.assign(course_id=300, semester=5, credits=3, prerequisite_course_ids=(200,))
    with pytest.raises(PrerequisiteNotEarlierError):
        curriculum.move(course_id=200, new_semester=5)


def test_move_rejects_unknown_course() -> None:
    curriculum = make_curriculum()
    with pytest.raises(CourseNotInCurriculumError):
        curriculum.move(course_id=999, new_semester=2)
