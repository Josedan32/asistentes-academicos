"""student_user_id is injected server-side from ToolContext, the same identity-injection
principle as program_id/active_course_id elsewhere in this package — the model never
supplies it and never sees another student's data."""

from typing import Any

from pydantic import BaseModel

from app.application.agents.llm_types import ToolDefinition
from app.application.agents.tools.registry import ToolContext, ToolDependencies, ToolSpec

DESCRIPTION = (
    "Get the student's own academic history (past courses with grade, pass/fail/"
    "cancelled status, and how many times each was taken) and the courses they are "
    "actually enrolled in this period. Use this to answer questions like which "
    "courses the student has already passed, failed, or repeated, and what they "
    "currently have enrolled — the enrolled list may differ from the curriculum's "
    "own semester grouping."
)


class GetAcademicHistoryArgs(BaseModel):
    pass


async def _run(
    deps: ToolDependencies, args: GetAcademicHistoryArgs, context: ToolContext
) -> dict[str, Any]:
    if context.student_user_id is None or deps.history_reader is None:
        return {"history": [], "enrollments": []}

    history = await deps.history_reader.history_of(context.student_user_id)
    enrollments = await deps.history_reader.enrollments_of(context.student_user_id)
    return {
        "history": [
            {
                "course": entry.course_name, "period": entry.period, "status": entry.status,
                "grade": entry.grade, "concept": entry.concept, "times_taken": entry.times_taken,
            }
            for entry in history
        ],
        "enrollments": [
            {
                "course": entry.course_name, "period": entry.period, "area": entry.area,
                "credits": entry.credits, "times_taken": entry.times_taken,
            }
            for entry in enrollments
        ],
    }


SPEC = ToolSpec(
    definition=ToolDefinition(
        name="get_academic_history",
        description=DESCRIPTION,
        parameters=GetAcademicHistoryArgs.model_json_schema(),
    ),
    argument_model=GetAcademicHistoryArgs,
    handler=_run,
)
