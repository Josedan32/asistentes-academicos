from dataclasses import dataclass, field, replace

from app.domain.academic.entities import CurriculumEntry, Program
from app.domain.academic.exceptions import (
    CourseNotInCurriculumError,
    DuplicateCourseInCurriculumError,
    InvalidCreditsError,
    InvalidSemesterError,
    PrerequisiteNotEarlierError,
    PrerequisiteNotInCurriculumError,
)


@dataclass
class Curriculum:
    """A program's course map. Owns every rule that spans more than one entry."""

    program: Program
    entries: list[CurriculumEntry] = field(default_factory=list)

    def semester_of(self, course_id: int) -> int | None:
        for entry in self.entries:
            if entry.course_id == course_id:
                return entry.semester
        return None

    def entry_for(self, course_id: int) -> CurriculumEntry:
        """Return the entry for a course, raising if the course is not in this curriculum."""
        return self.entries[self._index_of(course_id)]

    def assign(
        self,
        *,
        course_id: int,
        semester: int,
        credits: int,
        prerequisite_course_ids: tuple[int, ...] = (),
    ) -> CurriculumEntry:
        self._require_valid_semester(semester)
        if credits < 1:
            raise InvalidCreditsError(f"credits must be positive, got {credits}")
        if self.semester_of(course_id) is not None:
            raise DuplicateCourseInCurriculumError(
                f"course {course_id} is already in program {self.program.id}"
            )
        for prerequisite_id in prerequisite_course_ids:
            self._require_earlier(prerequisite_id, semester)

        entry = CurriculumEntry(
            program_id=self._program_id(),
            course_id=course_id,
            semester=semester,
            credits=credits,
            prerequisite_course_ids=tuple(prerequisite_course_ids),
        )
        self.entries.append(entry)
        return entry

    def move(self, course_id: int, new_semester: int) -> CurriculumEntry:
        self._require_valid_semester(new_semester)
        index = self._index_of(course_id)
        entry = self.entries[index]

        for prerequisite_id in entry.prerequisite_course_ids:
            self._require_earlier(prerequisite_id, new_semester)

        for other in self.entries:
            if other.course_id == course_id:
                continue
            if course_id in other.prerequisite_course_ids and other.semester <= new_semester:
                raise PrerequisiteNotEarlierError(
                    f"course {course_id} is a prerequisite of {other.course_id} "
                    f"in semester {other.semester}"
                )

        moved = replace(entry, semester=new_semester)
        self.entries[index] = moved
        return moved

    def _program_id(self) -> int:
        if self.program.id is None:
            raise ValueError("curriculum requires a persisted program")
        return self.program.id

    def _index_of(self, course_id: int) -> int:
        for index, entry in enumerate(self.entries):
            if entry.course_id == course_id:
                return index
        raise CourseNotInCurriculumError(f"course {course_id} is not in this curriculum")

    def _require_valid_semester(self, semester: int) -> None:
        if not 1 <= semester <= self.program.semester_count:
            raise InvalidSemesterError(
                f"semester must be between 1 and {self.program.semester_count}, got {semester}"
            )

    def _require_earlier(self, prerequisite_course_id: int, semester: int) -> None:
        prerequisite_semester = self.semester_of(prerequisite_course_id)
        if prerequisite_semester is None:
            raise PrerequisiteNotInCurriculumError(
                f"prerequisite {prerequisite_course_id} is not in this curriculum"
            )
        if prerequisite_semester >= semester:
            raise PrerequisiteNotEarlierError(
                f"prerequisite {prerequisite_course_id} sits in semester "
                f"{prerequisite_semester}, not earlier than {semester}"
            )
