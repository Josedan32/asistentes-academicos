"""program_id is deliberately absent from GetCourseDetailArgs: the spec's tool signature
is get_course_detail(course) (spec §7.4), and Plan 1's fix wave found that leaving
program_id optional lets credits silently degrade to None (residual R2). It is injected
server-side from the authenticated student's profile instead, the same principle §7.5
applies to identity.

`course` itself is optional for the same reason: qwen2.5:3b sometimes asks the student
to name the course even when one is already active (observed in production on "de que
trata esta materia") instead of reading it out of its own context. Omitting the argument
falls back to context.active_course_id, resolved with no name-matching at all."""

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
