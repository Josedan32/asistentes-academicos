"""Test doubles for the agents module. See spec §12: a fake LLMProvider is what makes
the loop testable without a model running."""

from dataclasses import dataclass, field

from app.application.agents.dto import StudentContext
from app.application.agents.llm_types import LLMMessage, LLMResponse
from app.domain.agents.entities import Conversation, Message, MessageFeedback, ToolCall
from app.domain.agents.materials import CourseMaterial, MaterialChunk


@dataclass
class FakeLLMProvider:
    responses: list[LLMResponse]
    model: str = "fake-v1"
    loaded: bool = True
    calls: list[list[LLMMessage]] = field(default_factory=list)
    tool_names_received: list[set[str]] = field(default_factory=list)

    async def is_loaded(self) -> bool:
        return self.loaded

    async def complete(
        self, messages: list[LLMMessage], tools: list | None = None
    ) -> LLMResponse:
        self.calls.append(messages)
        self.tool_names_received.append({t.name for t in tools} if tools else set())
        if len(self.calls) > len(self.responses):
            raise AssertionError(
                f"FakeLLMProvider called {len(self.calls)} times but only "
                f"{len(self.responses)} responses were scripted"
            )
        return self.responses[len(self.calls) - 1]


@dataclass
class FakeMaterialReader:
    """No-database MaterialReader double: never actually called by the four existing
    tools, only by search_course_material's own tests, which want real search behavior
    and use SqlAlchemyMaterialReader instead — this stub just satisfies the signature."""

    materials: list[CourseMaterial] = field(default_factory=list)
    chunks: list[MaterialChunk] = field(default_factory=list)

    async def list_materials(self, course_id: int) -> list[CourseMaterial]:
        return [m for m in self.materials if m.course_id == course_id]

    async def get_material(self, material_id: int) -> CourseMaterial | None:
        return next((m for m in self.materials if m.id == material_id), None)

    async def search(
        self, course_id: int, query_embedding: list[float], limit: int = 5
    ) -> list[MaterialChunk]:
        return [c for c in self.chunks if c.course_id == course_id][:limit]


@dataclass
class FakeEmbeddingProvider:
    """No-network EmbeddingProvider double: a fixed-length vector per input."""

    dimensions: int = 4

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text))] * self.dimensions for text in texts]


@dataclass
class FakePromptComposer:
    prompt: str = "system prompt"
    version: str = "test-v0"

    def compose_system_prompt(self, context: StudentContext) -> tuple[str, str]:
        return self.prompt, self.version


@dataclass
class InMemoryConversationRepository:
    """A ConversationRepository that assigns ids sequentially, without a database.
    Records everything persisted so tests can assert on it directly."""

    messages: list[Message] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    feedback: list[MessageFeedback] = field(default_factory=list)
    _next_message_id: int = 1
    _next_tool_call_id: int = 1

    async def create(self, conversation: Conversation) -> Conversation:
        from dataclasses import replace

        return replace(conversation, id=1)

    async def add_message(self, message: Message) -> Message:
        from dataclasses import replace

        stored = replace(message, id=self._next_message_id)
        self._next_message_id += 1
        self.messages.append(stored)
        return stored

    async def add_tool_call(self, tool_call: ToolCall) -> ToolCall:
        from dataclasses import replace

        stored = replace(tool_call, id=self._next_tool_call_id)
        self._next_tool_call_id += 1
        self.tool_calls.append(stored)
        return stored

    async def add_feedback(self, feedback: MessageFeedback) -> MessageFeedback:
        from dataclasses import replace

        stored = replace(feedback, id=len(self.feedback) + 1)
        self.feedback.append(stored)
        return stored
