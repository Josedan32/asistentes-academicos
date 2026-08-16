from pydantic import BaseModel, Field

from app.application.academic.dto import CourseSummary
from app.application.academic.queries import ListSemesterCourses
from app.application.agents.llm_types import ToolDefinition
from app.application.agents.tools.registry import ToolContext, ToolDependencies, ToolSpec

DESCRIPTION = (
    "List the courses a student takes in a given semester of their own program. Omit "
    "semester to use the student's own current semester."
)


class ListSemesterCoursesArgs(BaseModel):
    semester: int | None = Field(
        default=None,
        ge=1,
        le=12,
        description="Semester number, 1 to 12. Omit for the student's own current semester.",
    )


async def _run(
    deps: ToolDependencies, args: ListSemesterCoursesArgs, context: ToolContext
) -> list[CourseSummary]:
    semester = args.semester if args.semester is not None else context.current_semester
    return await ListSemesterCourses(deps.reader).execute(
        program_id=context.program_id, semester=semester
    )


SPEC = ToolSpec(
    definition=ToolDefinition(
        name="list_semester_courses",
        description=DESCRIPTION,
        parameters=ListSemesterCoursesArgs.model_json_schema(),
    ),
    argument_model=ListSemesterCoursesArgs,
    handler=_run,
)
