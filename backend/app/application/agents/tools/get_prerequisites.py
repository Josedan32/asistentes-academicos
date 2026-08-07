from pydantic import BaseModel, Field

from app.application.academic.dto import PrerequisiteResult
from app.application.academic.ports import AcademicReader
from app.application.academic.queries import GetPrerequisites
from app.application.agents.llm_types import ToolDefinition
from app.application.agents.tools.registry import ToolContext, ToolSpec

DESCRIPTION = "Get the prerequisites of a course within a program's curriculum."


class GetPrerequisitesArgs(BaseModel):
    program_id: int = Field(description="Program identifier")
    course: str = Field(description="Course name as the student wrote it")


async def _run(
    reader: AcademicReader, args: GetPrerequisitesArgs, context: ToolContext
) -> PrerequisiteResult:
    return await GetPrerequisites(reader).execute(program_id=args.program_id, course=args.course)


SPEC = ToolSpec(
    definition=ToolDefinition(
        name="get_prerequisites",
        description=DESCRIPTION,
        parameters=GetPrerequisitesArgs.model_json_schema(),
    ),
    argument_model=GetPrerequisitesArgs,
    handler=_run,
)
