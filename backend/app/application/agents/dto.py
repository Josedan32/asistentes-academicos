from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.agents.modes import ChatMode


@dataclass(frozen=True)
class StudentContext:
    program_id: int
    current_semester: int
    student_user_id: int | None = None
    active_course_id: int | None = None
    active_course_name: str | None = None
    mode: ChatMode = ChatMode.CONSULTA
    # Course names the student is actually enrolled in this period — independent of the
    # curriculum's "semester N" grouping, since real students drift from it. Kept short
    # (names only) so it stays cheap to always include in the system prompt.
    enrolled_course_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class ToolCallView:
    id: int
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | list[Any] | None
    duration_ms: int
    row_count: int
    sequence: int


@dataclass(frozen=True)
class FeedbackView:
    value: str
    comment: str | None


@dataclass(frozen=True)
class MessageDetail:
    id: int
    role: str
    content: str
    tool_calls: list[ToolCallView] = field(default_factory=list)
    feedback: FeedbackView | None = None


@dataclass(frozen=True)
class ConversationSummary:
    id: int
    title: str
    course_id: int | None
    course_name: str | None
    created_at: datetime
