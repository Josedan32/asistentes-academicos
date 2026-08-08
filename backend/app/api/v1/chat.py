import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated, Any

from anyio import CancelScope
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.v1.deps import (
    AcademicReaderDep,
    ConversationReaderDep,
    ConversationRepositoryDep,
    CurrentUser,
    InferenceGateDep,
    LLMProviderDep,
    PromptComposerDep,
    UserRepositoryDep,
    require_student,
)
from app.api.v1.schemas import ChatIn, FeedbackIn
from app.application.agents.agent_loop import AgentLoop, DoneEvent, ThinkingEvent, ToolCallEvent
from app.application.agents.dto import StudentContext
from app.domain.agents.entities import Conversation, FeedbackValue, MessageFeedback

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

ESTIMATED_SECONDS_PER_TURN = 5
QUEUE_POLL_SECONDS = 0.5
MAX_QUEUE_WAIT_SECONDS = 180
MAX_QUEUE_POLL_ITERATIONS = int(MAX_QUEUE_WAIT_SECONDS / QUEUE_POLL_SECONDS)


def _sse(event: str, data: dict[str, Any]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode()


def _chunk_into_tokens(content: str) -> list[str]:
    if not content:
        return []
    words = content.split(" ")
    return [word + (" " if index < len(words) - 1 else "") for index, word in enumerate(words)]


@router.post("")
async def chat(
    payload: ChatIn,
    user: Annotated[CurrentUser, Depends(require_student)],
    conversations: ConversationRepositoryDep,
    conversation_reader: ConversationReaderDep,
    reader: AcademicReaderDep,
    users: UserRepositoryDep,
    provider: LLMProviderDep,
    prompt_composer: PromptComposerDep,
    gate: InferenceGateDep,
) -> StreamingResponse:
    profile = await users.find_profile_by_user_id(user.user_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    if payload.conversation_id is not None:
        conversation = await conversation_reader.get(payload.conversation_id)
        if conversation is None or conversation.user_id != user.user_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        history = await conversation_reader.history(payload.conversation_id)
    else:
        title = payload.message.strip()[:60] or "Nueva conversacion"
        conversation = await conversations.create(
            Conversation(user_id=user.user_id, course_id=payload.course_id, title=title)
        )
        history = []

    context = StudentContext(
        program_id=profile.program_id, current_semester=profile.current_semester
    )

    async def stream() -> AsyncIterator[bytes]:
        ticket = await gate.enqueue()
        # Everything from here on must funnel exceptions into an `error` SSE event rather
        # than propagating: the stream has already started, so a normal HTTP error response
        # is no longer possible (spec §9.2). This also covers pre-loop failures such as
        # `provider.is_loaded()` raising (e.g. Ollama unreachable), not just `AgentLoop.run`.
        try:
            for _ in range(MAX_QUEUE_POLL_ITERATIONS):
                position = await gate.position(ticket)
                if position is None or position <= 1:
                    break
                yield _sse("queued", {"position": position,
                                       "estimated_wait": position * ESTIMATED_SECONDS_PER_TURN})
                await asyncio.sleep(QUEUE_POLL_SECONDS)
            else:
                yield _sse("error", {
                    "code": "queue_timeout",
                    "message": "Timed out waiting for the inference queue",
                })
                return

            if not await provider.is_loaded():
                yield _sse("loading_model", {})

            loop = AgentLoop(provider=provider, reader=reader, conversations=conversations,
                              prompt_composer=prompt_composer)
            async for event in loop.run(conversation=conversation, history=history,
                                         user_message=payload.message, context=context):
                if isinstance(event, ThinkingEvent):
                    yield _sse("thinking", {"tool": event.tool})
                elif isinstance(event, ToolCallEvent):
                    yield _sse("tool_call", {
                        "name": event.name, "arguments": event.arguments,
                        "result": event.result, "duration_ms": event.duration_ms,
                        "row_count": event.row_count,
                    })
                elif isinstance(event, DoneEvent):
                    for token in _chunk_into_tokens(event.content):
                        yield _sse("token", {"text": token})
                    yield _sse("done", {
                        "tool_count": event.tool_count, "total_ms": 0, "source_count": 0,
                        "conversation_id": conversation.id,
                    })
        except Exception as error:
            yield _sse("error", {"code": "agent_loop_failed", "message": str(error)})
        finally:
            # Shielded: on client disconnect the ASGI server may cancel this task group
            # outright, and an unshielded `await` here would raise at its first checkpoint
            # before the Redis ZREM runs — leaking the ticket and blocking every other
            # queued request behind it, since RedisInferenceGate sets no TTL on entries.
            with CancelScope(shield=True):
                await gate.release(ticket)

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.post("/messages/{message_id}/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    message_id: int,
    payload: FeedbackIn,
    user: Annotated[CurrentUser, Depends(require_student)],
    conversations: ConversationRepositoryDep,
    conversation_reader: ConversationReaderDep,
) -> dict[str, int]:
    owner_id = await conversation_reader.message_owner(message_id)
    if owner_id is None or owner_id != user.user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Message not found")

    feedback = await conversations.add_feedback(
        MessageFeedback(
            message_id=message_id, value=FeedbackValue(payload.value), comment=payload.comment
        )
    )
    assert feedback.id is not None
    return {"id": feedback.id}
