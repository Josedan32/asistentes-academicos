from typing import Any

from pydantic import BaseModel, Field

from app.application.academic.resolver import CourseMatch, Resolved, resolve_course
from app.application.agents.llm_types import ToolDefinition
from app.application.agents.tools.registry import ToolContext, ToolDependencies, ToolSpec

DESCRIPTION = (
    "Search the active course's uploaded study material for a concept or exercise. To search "
    "a different course's material instead (e.g. a prerequisite), pass its name in `course`."
)


class SearchCourseMaterialArgs(BaseModel):
    query: str = Field(description="What the student wants explained or practiced")
    course: str | None = Field(
        default=None,
        description="Course to search if different from the active one, e.g. a prerequisite",
    )


async def _run(
    deps: ToolDependencies, args: SearchCourseMaterialArgs, context: ToolContext
) -> dict[str, Any]:
    course_id = context.active_course_id
    if args.course is not None and context.active_course_id is not None:
        prerequisites = await deps.reader.prerequisites_of(
            context.program_id, context.active_course_id
        )
        candidates = [
            CourseMatch(id=p.course_id, name=p.course_name, code=p.course_code)
            for p in prerequisites
        ]
        resolution = resolve_course(args.course, candidates)
        if isinstance(resolution, Resolved):
            course_id = resolution.course_id

    if course_id is None:
        return {"fragments": []}

    query_embedding = (await deps.embedder.embed([args.query]))[0]
    chunks = await deps.material_reader.search(course_id, query_embedding, limit=8)
    seen_text: set[str] = set()
    fragments = []
    for chunk in chunks:
        if chunk.text in seen_text:
            continue
        seen_text.add(chunk.text)
        fragments.append({"text": chunk.text, "page": chunk.page})
    return {"fragments": fragments}


SPEC = ToolSpec(
    definition=ToolDefinition(
        name="search_course_material",
        description=DESCRIPTION,
        parameters=SearchCourseMaterialArgs.model_json_schema(),
    ),
    argument_model=SearchCourseMaterialArgs,
    handler=_run,
)
