class AcademicError(Exception):
    """Base class for academic domain rule violations."""


class InvalidSemesterError(AcademicError):
    """Semester is outside the range the program defines."""


class InvalidCreditsError(AcademicError):
    """Credits must be a positive integer."""


class DuplicateCourseInCurriculumError(AcademicError):
    """The course is already assigned in this program's curriculum."""


class CourseNotInCurriculumError(AcademicError):
    """The course is not assigned in this program's curriculum."""


class PrerequisiteNotInCurriculumError(AcademicError):
    """A prerequisite must itself be part of the same program's curriculum."""


class PrerequisiteNotEarlierError(AcademicError):
    """A prerequisite must sit in a strictly earlier semester."""
