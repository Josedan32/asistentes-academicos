from typing import Protocol

from app.application.agents.dto import StudentContext
from app.application.agents.llm_types import LLMMessage, LLMResponse, ToolDefinition
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


class LLMProvider(Protocol):
    @property
    def model(self) -> str: ...

    async def is_loaded(self) -> bool:
        """Whether the model is currently resident (drives the `loading_model` SSE event).

        Hosted providers have no local load state and always return True.
        """
        ...

    async def complete(
        self, messages: list[LLMMessage], tools: list[ToolDefinition] | None = None
    ) -> LLMResponse: ...


class PromptComposer(Protocol):
    def compose_system_prompt(self, context: StudentContext) -> tuple[str, str]:
        """Returns (prompt_text, prompt_version). Every Message records the version."""
        ...


class InferenceGate(Protocol):
    """One inference at a time, across every uvicorn worker process (spec §8.2)."""

    async def enqueue(self) -> str:
        """Returns a ticket id."""
        ...

    async def position(self, ticket: str) -> int | None:
        """1-indexed queue position, or None if the ticket is unknown/already released."""
        ...

    async def release(self, ticket: str) -> None: ...


class ResponseCache(Protocol):
    """Keyed on a hash of prompt, model and parameters, with TTL (spec §8.2)."""

    async def get(self, key: str) -> LLMResponse | None: ...

    async def set(self, key: str, response: LLMResponse, ttl_seconds: int) -> None: ...
