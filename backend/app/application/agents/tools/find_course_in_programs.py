from pydantic import BaseModel, Field

from app.application.academic.dto import ProgramPlacement
from app.application.academic.queries import FindCourseInPrograms
from app.application.agents.llm_types import ToolDefinition
from app.application.agents.tools.registry import ToolContext, ToolDependencies, ToolSpec

DESCRIPTION = "Find which programs and semesters include a given course."


class FindCourseInProgramsArgs(BaseModel):
    course: str = Field(description="Course name as the student wrote it")


async def _run(
    deps: ToolDependencies, args: FindCourseInProgramsArgs, context: ToolContext
) -> list[ProgramPlacement]:
    return await FindCourseInPrograms(deps.reader).execute(course=args.course)


SPEC = ToolSpec(
    definition=ToolDefinition(
        name="find_course_in_programs",
        description=DESCRIPTION,
        parameters=FindCourseInProgramsArgs.model_json_schema(),
    ),
    argument_model=FindCourseInProgramsArgs,
    handler=_run,
)
