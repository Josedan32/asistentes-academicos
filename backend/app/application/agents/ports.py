from typing import Protocol

from app.domain.agents.entities import Conversation, Message, MessageFeedback, ToolCall


class ConversationRepository(Protocol):
    """Write-side port. Every call persists and returns the row with its id populated."""

    async def create(self, conversation: Conversation) -> Conversation: ...

    async def add_message(self, message: Message) -> Message: ...

    async def add_tool_call(self, tool_call: ToolCall) -> ToolCall: ...

    async def add_feedback(self, feedback: MessageFeedback) -> MessageFeedback: ...


class ConversationReader(Protocol):
    """Read-side port."""

    async def get(self, conversation_id: int) -> Conversation | None: ...

    async def history(self, conversation_id: int) -> list[Message]: ...

    async def message_owner(self, message_id: int) -> int | None:
        """The user_id of the conversation a message belongs to, or None if unknown."""
        ...
