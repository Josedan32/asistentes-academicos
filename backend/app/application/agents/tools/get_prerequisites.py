from pydantic import BaseModel, Field

from app.application.academic.dto import PrerequisiteResult
from app.application.academic.queries import GetPrerequisites
from app.application.agents.llm_types import ToolDefinition
from app.application.agents.tools.registry import ToolContext, ToolDependencies, ToolSpec

DESCRIPTION = "Get the prerequisites of a course within the student's own program curriculum."


class GetPrerequisitesArgs(BaseModel):
    course: str = Field(description="Course name as the student wrote it")


async def _run(
    deps: ToolDependencies, args: GetPrerequisitesArgs, context: ToolContext
) -> PrerequisiteResult:
    return await GetPrerequisites(deps.reader).execute(
        program_id=context.program_id, course=args.course
    )


SPEC = ToolSpec(
    definition=ToolDefinition(
        name="get_prerequisites",
        description=DESCRIPTION,
        parameters=GetPrerequisitesArgs.model_json_schema(),
    ),
    argument_model=GetPrerequisitesArgs,
    handler=_run,
)
