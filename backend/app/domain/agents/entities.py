from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class FeedbackValue(StrEnum):
    UP = "up"
    DOWN = "down"


@dataclass(frozen=True)
class Conversation:
    user_id: int
    course_id: int | None
    title: str
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("conversation title must not be blank")


@dataclass(frozen=True)
class Message:
    conversation_id: int
    role: MessageRole
    content: str
    prompt_version: str | None = None
    id: int | None = None


@dataclass(frozen=True)
class ToolCall:
    message_id: int
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | list[Any] | None
    duration_ms: int
    row_count: int
    sequence: int
    id: int | None = None

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("tool call sequence must start at 1")
        if self.duration_ms < 0:
            raise ValueError("tool call duration_ms must not be negative")


@dataclass(frozen=True)
class MessageFeedback:
    message_id: int
    value: FeedbackValue
    comment: str | None = None
    id: int | None = None
