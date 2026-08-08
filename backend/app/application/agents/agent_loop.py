import asyncio
import json
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.application.academic.ports import AcademicReader
from app.application.agents.dto import StudentContext
from app.application.agents.llm_types import LLMMessage
from app.application.agents.ports import ConversationRepository, LLMProvider, PromptComposer
from app.application.agents.tools.registry import TOOLS, ToolContext, row_count, to_jsonable
from app.domain.agents.entities import Conversation, Message, MessageRole, ToolCall

MAX_ITERATIONS = 3
TOOL_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class ThinkingEvent:
    tool: str


@dataclass(frozen=True)
class ToolCallEvent:
    name: str
    arguments: dict[str, Any]
    result: Any
    duration_ms: int
    row_count: int


@dataclass(frozen=True)
class DoneEvent:
    content: str
    tool_count: int
    hit_iteration_cap: bool
    message_id: int


LoopEvent = ThinkingEvent | ToolCallEvent | DoneEvent

FALLBACK_MESSAGE = (
    "No pude completar tu solicitud tras varios intentos. Intenta reformular la pregunta."
)


@dataclass
class AgentLoop:
    provider: LLMProvider
    reader: AcademicReader
    conversations: ConversationRepository
    prompt_composer: PromptComposer

    async def run(
        self,
        *,
        conversation: Conversation,
        history: list[Message],
        user_message: str,
        context: StudentContext,
    ) -> AsyncIterator[LoopEvent]:
        assert conversation.id is not None, "conversation must be persisted before the loop runs"
        conversation_id = conversation.id

        system_prompt, prompt_version = self.prompt_composer.compose_system_prompt(context)

        await self.conversations.add_message(
            Message(conversation_id=conversation_id, role=MessageRole.USER, content=user_message)
        )

        messages = [LLMMessage(role="system", content=system_prompt)]
        messages += [LLMMessage(role=m.role.value, content=m.content) for m in history]
        messages.append(LLMMessage(role="user", content=user_message))

        tool_defs = [spec.definition for spec in TOOLS.values()]
        tool_count = 0
        response = None

        for _ in range(MAX_ITERATIONS):
            response = await self.provider.complete(messages, tools=tool_defs)

            if not response.tool_calls:
                saved = await self.conversations.add_message(
                    Message(conversation_id=conversation_id, role=MessageRole.ASSISTANT,
                            content=response.content or "", prompt_version=prompt_version)
                )
                assert saved.id is not None
                yield DoneEvent(content=response.content or "", tool_count=tool_count,
                                 hit_iteration_cap=False, message_id=saved.id)
                return

            assistant_row = await self.conversations.add_message(
                Message(conversation_id=conversation_id, role=MessageRole.ASSISTANT,
                        content=response.content or "", prompt_version=prompt_version)
            )
            messages.append(LLMMessage(role="assistant", content=response.content or ""))

            for sequence, call in enumerate(response.tool_calls, start=1):
                yield ThinkingEvent(tool=call.name)

                spec = TOOLS.get(call.name)
                if spec is None:
                    error_text = json.dumps({"error": f"unknown tool: {call.name}"})
                    messages.append(LLMMessage(role="tool", name=call.name,
                                                tool_call_id=call.id, content=error_text))
                    continue

                try:
                    args = spec.argument_model.model_validate(call.arguments)
                except ValidationError as error:
                    error_text = json.dumps({"error": str(error)})
                    messages.append(LLMMessage(role="tool", name=call.name,
                                                tool_call_id=call.id, content=error_text))
                    continue

                start = time.monotonic()
                try:
                    result = await asyncio.wait_for(
                        spec.handler(
                            self.reader, args,
                            ToolContext(
                                program_id=context.program_id,
                                current_semester=context.current_semester,
                            ),
                        ),
                        timeout=TOOL_TIMEOUT_SECONDS,
                    )
                except TimeoutError:
                    error_text = json.dumps({"error": "tool timed out"})
                    messages.append(LLMMessage(role="tool", name=call.name,
                                                tool_call_id=call.id, content=error_text))
                    continue

                duration_ms = int((time.monotonic() - start) * 1000)
                jsonable = to_jsonable(result)
                rows = row_count(call.name, result)
                tool_count += 1

                assert assistant_row.id is not None
                await self.conversations.add_tool_call(
                    ToolCall(message_id=assistant_row.id, name=call.name,
                             arguments=call.arguments, result=jsonable, duration_ms=duration_ms,
                             row_count=rows, sequence=sequence)
                )
                yield ToolCallEvent(name=call.name, arguments=call.arguments, result=jsonable,
                                     duration_ms=duration_ms, row_count=rows)

                messages.append(LLMMessage(role="tool", name=call.name, tool_call_id=call.id,
                                            content=json.dumps(jsonable)))

        saved = await self.conversations.add_message(
            Message(conversation_id=conversation_id, role=MessageRole.ASSISTANT,
                    content=FALLBACK_MESSAGE, prompt_version=prompt_version)
        )
        assert saved.id is not None
        yield DoneEvent(content=FALLBACK_MESSAGE, tool_count=tool_count, hit_iteration_cap=True,
                         message_id=saved.id)
