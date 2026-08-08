"""program_id is deliberately absent from ListSemesterCoursesArgs: the same identity-
injection principle as get_course_detail (spec §7.5, ADR 0008). It is injected server-side
from the authenticated student's profile rather than asked of the model, because the 3B
model does not reliably pull it out of the system prompt on its own — observed in
production as the model asking the student to supply their own program id instead of
answering. `semester` stays model-supplied: a student legitimately asks about semesters
other than their own current one (e.g. "que puedo matricular en semestre 6")."""

from pydantic import BaseModel, Field

from app.application.academic.dto import CourseSummary
from app.application.academic.ports import AcademicReader
from app.application.academic.queries import ListSemesterCourses
from app.application.agents.llm_types import ToolDefinition
from app.application.agents.tools.registry import ToolContext, ToolSpec

DESCRIPTION = "List the courses a student takes in a given semester of their own program."


class ListSemesterCoursesArgs(BaseModel):
    semester: int = Field(ge=1, le=12, description="Semester number, 1 to 12")


async def _run(
    reader: AcademicReader, args: ListSemesterCoursesArgs, context: ToolContext
) -> list[CourseSummary]:
    return await ListSemesterCourses(reader).execute(
        program_id=context.program_id, semester=args.semester
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
