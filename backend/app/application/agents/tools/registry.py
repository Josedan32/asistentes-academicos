from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from pydantic import BaseModel

from app.application.academic.ports import AcademicReader
from app.application.agents.llm_types import ToolDefinition


@dataclass(frozen=True)
class ToolContext:
    """Server-injected values a tool handler may need but the model never supplies."""

    program_id: int
    current_semester: int


@dataclass(frozen=True)
class ToolSpec:
    definition: ToolDefinition
    argument_model: type[BaseModel]
    handler: Callable[[AcademicReader, Any, ToolContext], Awaitable[Any]]


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
    return len(result)


# Populated by app.application.agents.tools.__init__, not here: every tool module
# imports ToolContext/ToolSpec from this file at module scope, so building this dict
# here by importing the tool modules back would deadlock whenever some code imports a
# tool module directly (e.g. `from ...tools.get_course_detail import ...`) before ever
# touching this module — Python registers that submodule in sys.modules before its
# body finishes running, and re-entering the import from here would hand back the same
# partially-initialized module, missing SPEC. The package's __init__ is the one point
# Python guarantees has fully run before any dotted submodule import resolves, so it is
# the safe place to import all four tool modules and assemble this dict.
TOOLS: dict[str, ToolSpec] = {}


def tool_definitions() -> list[ToolDefinition]:
    return [spec.definition for spec in TOOLS.values()]
