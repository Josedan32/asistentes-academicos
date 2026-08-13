"""course_id is deliberately absent from SearchCourseMaterialArgs, injected instead from
ToolContext.active_course_id — the same identity-injection principle as every other tool's
program_id. `course` is model-supplied only to let a student explicitly name a *different*
(typically prerequisite) course to search, per spec §2."""

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
        # Resolve `course` only against the active course's own prerequisites, never the
        # full catalogue: `course_candidates()` returns every course in the system, and
        # resolving against it would let a course-scoped assistant search an unrelated
        # course's material (e.g. Algebra Lineal reading Ingles material) — the exact
        # cross-course leak this tool exists to prevent, per finding 2 of the final review.
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
    chunks = await deps.material_reader.search(course_id, query_embedding, limit=5)
    return {
        "fragments": [{"text": chunk.text, "page": chunk.page} for chunk in chunks]
    }


SPEC = ToolSpec(
    definition=ToolDefinition(
        name="search_course_material",
        description=DESCRIPTION,
        parameters=SearchCourseMaterialArgs.model_json_schema(),
    ),
    argument_model=SearchCourseMaterialArgs,
    handler=_run,
)
