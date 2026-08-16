class AcademicError(Exception):
    pass


class InvalidSemesterError(AcademicError):
    pass


class InvalidCreditsError(AcademicError):
    pass


class DuplicateCourseInCurriculumError(AcademicError):
    pass


class CourseNotInCurriculumError(AcademicError):
    pass


class PrerequisiteNotInCurriculumError(AcademicError):
    pass


class PrerequisiteNotEarlierError(AcademicError):
    pass
