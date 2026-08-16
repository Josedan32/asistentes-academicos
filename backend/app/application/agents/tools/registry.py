from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from pydantic import BaseModel

from app.application.academic.ports import AcademicReader, StudentHistoryReader
from app.application.agents.llm_types import ToolDefinition
from app.application.agents.material_ports import MaterialReader
from app.application.agents.ports import EmbeddingProvider


@dataclass(frozen=True)
class ToolContext:
    program_id: int
    current_semester: int
    active_course_id: int | None = None
    student_user_id: int | None = None


@dataclass(frozen=True)
class ToolDependencies:
    reader: AcademicReader
    material_reader: MaterialReader
    embedder: EmbeddingProvider
    history_reader: StudentHistoryReader | None = None


@dataclass(frozen=True)
class ToolSpec:
    definition: ToolDefinition
    argument_model: type[BaseModel]
    handler: Callable[[ToolDependencies, Any, ToolContext], Awaitable[Any]]


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    return value


def row_count(tool_name: str, result: Any) -> int:
    if result is None:
        return 0
    if tool_name == "get_course_detail":
        return 1
    if tool_name == "get_prerequisites":
        return len(result.prerequisites)
    if tool_name == "search_course_material":
        return len(result["fragments"])
    if tool_name == "get_academic_history":
        return len(result["history"]) + len(result["enrollments"])
    return len(result)


TOOLS: dict[str, ToolSpec] = {}


def tool_definitions() -> list[ToolDefinition]:
    return [spec.definition for spec in TOOLS.values()]
