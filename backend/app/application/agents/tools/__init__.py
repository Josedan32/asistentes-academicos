from app.application.agents.tools import (
    find_course_in_programs,
    get_course_detail,
    get_prerequisites,
    list_semester_courses,
)
from app.application.agents.tools.registry import TOOLS

TOOLS.update(
    {
        "list_semester_courses": list_semester_courses.SPEC,
        "get_prerequisites": get_prerequisites.SPEC,
        "get_course_detail": get_course_detail.SPEC,
        "find_course_in_programs": find_course_in_programs.SPEC,
    }
)
