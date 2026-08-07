from pydantic import BaseModel, Field

from app.application.academic.dto import CourseSummary
from app.application.academic.ports import AcademicReader
from app.application.academic.queries import ListSemesterCourses
from app.application.agents.llm_types import ToolDefinition
from app.application.agents.tools.registry import ToolContext, ToolSpec

DESCRIPTION = "List the courses a student takes in a given semester of a program."


class ListSemesterCoursesArgs(BaseModel):
    program_id: int = Field(description="Program identifier")
    semester: int = Field(ge=1, le=12, description="Semester number, 1 to 12")


async def _run(
    reader: AcademicReader, args: ListSemesterCoursesArgs, context: ToolContext
) -> list[CourseSummary]:
    return await ListSemesterCourses(reader).execute(
        program_id=args.program_id, semester=args.semester
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
