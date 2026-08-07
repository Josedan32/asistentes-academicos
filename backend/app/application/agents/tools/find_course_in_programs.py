from pydantic import BaseModel, Field

from app.application.academic.dto import ProgramPlacement
from app.application.academic.ports import AcademicReader
from app.application.academic.queries import FindCourseInPrograms
from app.application.agents.llm_types import ToolDefinition
from app.application.agents.tools.registry import ToolContext, ToolSpec

DESCRIPTION = "Find which programs and semesters include a given course."


class FindCourseInProgramsArgs(BaseModel):
    course: str = Field(description="Course name as the student wrote it")


async def _run(
    reader: AcademicReader, args: FindCourseInProgramsArgs, context: ToolContext
) -> list[ProgramPlacement]:
    return await FindCourseInPrograms(reader).execute(course=args.course)


SPEC = ToolSpec(
    definition=ToolDefinition(
        name="find_course_in_programs",
        description=DESCRIPTION,
        parameters=FindCourseInProgramsArgs.model_json_schema(),
    ),
    argument_model=FindCourseInProgramsArgs,
    handler=_run,
)
