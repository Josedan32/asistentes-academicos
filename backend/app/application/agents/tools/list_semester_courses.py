"""program_id is deliberately absent from ListSemesterCoursesArgs: the same identity-
injection principle as get_course_detail (spec §7.5, ADR 0008). It is injected server-side
from the authenticated student's profile rather than asked of the model, because the 3B
model does not reliably pull it out of the system prompt on its own — observed in
production as the model asking the student to supply their own program id instead of
answering.

`semester` stays model-supplied so a student can ask about a semester other than their own
current one (e.g. "que puedo matricular en semestre 6"), but it is optional: per the Plan 1
spike (docs ADR 0006, hypothesis 1, confirmed in production), the model does not reliably
infer "this semester" from the system prompt either, and asks the student to repeat
information the server already has instead of answering. Omitting the argument falls back
to the authenticated student's own current_semester rather than leaving the model stuck."""

from pydantic import BaseModel, Field

from app.application.academic.dto import CourseSummary
from app.application.academic.ports import AcademicReader
from app.application.academic.queries import ListSemesterCourses
from app.application.agents.llm_types import ToolDefinition
from app.application.agents.tools.registry import ToolContext, ToolSpec

DESCRIPTION = (
    "List the courses a student takes in a given semester of their own program. Omit "
    "semester to use the student's own current semester."
)


class ListSemesterCoursesArgs(BaseModel):
    semester: int | None = Field(
        default=None, ge=1, le=12,
        description="Semester number, 1 to 12. Omit for the student's own current semester.",
    )


async def _run(
    reader: AcademicReader, args: ListSemesterCoursesArgs, context: ToolContext
) -> list[CourseSummary]:
    semester = args.semester if args.semester is not None else context.current_semester
    return await ListSemesterCourses(reader).execute(
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
