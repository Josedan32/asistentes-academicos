class AcademicError(Exception):
    """Base class for academic domain rule violations."""


class InvalidSemester(AcademicError):
    """Semester is outside the range the program defines."""


class InvalidCredits(AcademicError):
    """Credits must be a positive integer."""


class DuplicateCourseInCurriculum(AcademicError):
    """The course is already assigned in this program's curriculum."""


class CourseNotInCurriculum(AcademicError):
    """The course is not assigned in this program's curriculum."""


class PrerequisiteNotInCurriculum(AcademicError):
    """A prerequisite must itself be part of the same program's curriculum."""


class PrerequisiteNotEarlier(AcademicError):
    """A prerequisite must sit in a strictly earlier semester."""
