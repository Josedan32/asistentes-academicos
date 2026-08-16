from pydantic import BaseModel, Field

from app.application.academic.dto import CourseDetail
from app.application.academic.queries import GetCourseDetail
from app.application.agents.llm_types import ToolDefinition
from app.application.agents.tools.registry import ToolContext, ToolDependencies, ToolSpec

DESCRIPTION = (
    "Get a course's credits, area and description within the student's program. Omit "
    "`course` to get the details of the currently active course."
)


class GetCourseDetailArgs(BaseModel):
    course: str | None = Field(
        default=None,
        description="Course name as the student wrote it. Omit for the active course.",
    )


async def _run(
    deps: ToolDependencies, args: GetCourseDetailArgs, context: ToolContext
) -> CourseDetail | None:
    if not args.course:
        if context.active_course_id is None:
            return None
        return await deps.reader.course_detail(context.active_course_id, context.program_id)
    return await GetCourseDetail(deps.reader).execute(
        course=args.course, program_id=context.program_id
    )


SPEC = ToolSpec(
    definition=ToolDefinition(
        name="get_course_detail",
        description=DESCRIPTION,
        parameters=GetCourseDetailArgs.model_json_schema(),
    ),
    argument_model=GetCourseDetailArgs,
    handler=_run,
)
