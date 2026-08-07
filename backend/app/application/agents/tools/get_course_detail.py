"""program_id is deliberately absent from GetCourseDetailArgs: the spec's tool signature
is get_course_detail(course) (spec §7.4), and Plan 1's fix wave found that leaving
program_id optional lets credits silently degrade to None (residual R2). It is injected
server-side from the authenticated student's profile instead, the same principle §7.5
applies to identity."""

from pydantic import BaseModel, Field

from app.application.academic.dto import CourseDetail
from app.application.academic.ports import AcademicReader
from app.application.academic.queries import GetCourseDetail
from app.application.agents.llm_types import ToolDefinition
from app.application.agents.tools.registry import ToolContext, ToolSpec

DESCRIPTION = "Get a course's credits, area and description within the student's program."


class GetCourseDetailArgs(BaseModel):
    course: str = Field(description="Course name as the student wrote it")


async def _run(
    reader: AcademicReader, args: GetCourseDetailArgs, context: ToolContext
) -> CourseDetail | None:
    return await GetCourseDetail(reader).execute(course=args.course, program_id=context.program_id)


SPEC = ToolSpec(
    definition=ToolDefinition(
        name="get_course_detail",
        description=DESCRIPTION,
        parameters=GetCourseDetailArgs.model_json_schema(),
    ),
    argument_model=GetCourseDetailArgs,
    handler=_run,
)
