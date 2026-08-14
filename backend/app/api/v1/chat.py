import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated, Any

from anyio import CancelScope
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.api.v1.deps import (
    AcademicReaderDep,
    ConversationReaderDep,
    ConversationRepositoryDep,
    CurrentUser,
    EmbeddingProviderDep,
    InferenceGateDep,
    LLMProviderDep,
    MaterialReaderDep,
    PromptComposerDep,
    StudentHistoryReaderDep,
    UserRepositoryDep,
    require_authentication,
    require_student,
)
from app.api.v1.schemas import (
    ChatAttachmentOut,
    ChatIn,
    ConversationDetailOut,
    ConversationSummaryOut,
    FeedbackIn,
    FeedbackOut,
    MessageOut,
    ToolCallOut,
)
from app.application.agents.agent_loop import AgentLoop, DoneEvent, ThinkingEvent, ToolCallEvent
from app.application.agents.dto import StudentContext
from app.application.agents.text_extraction import UnsupportedMaterialFormatError, extract_text
from app.domain.agents.entities import Conversation, FeedbackValue, MessageFeedback
from app.domain.agents.modes import ChatMode

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_ATTACHMENT_CHARS = 6000

ESTIMATED_SECONDS_PER_TURN = 5
QUEUE_POLL_SECONDS = 0.5
MAX_QUEUE_WAIT_SECONDS = 180
MAX_QUEUE_POLL_ITERATIONS = int(MAX_QUEUE_WAIT_SECONDS / QUEUE_POLL_SECONDS)


@router.get("/model")
async def get_model(
    user: Annotated[CurrentUser, Depends(require_authentication)],
    provider: LLMProviderDep,
) -> dict[str, str]:
    return {"model": provider.model}


@router.post("/attachments")
async def upload_chat_attachment(
    user: Annotated[CurrentUser, Depends(require_student)],
    file: Annotated[UploadFile, File()],
) -> ChatAttachmentOut:
    """Extracts a student-uploaded file's text so the frontend can fold it into a single
    chat message — nothing here is persisted server-side beyond that one message. This is
    deliberately not course material: it is scoped to whichever conversation the student
    attaches it in, never indexed for search or shared with other students."""
    content = await file.read()
    if len(content) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE, detail="Attachment exceeds the 10 MB limit"
        )
    try:
        text = extract_text(file.filename or "archivo", content)
    except UnsupportedMaterialFormatError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error

    if len(text) > MAX_ATTACHMENT_CHARS:
        text = text[:MAX_ATTACHMENT_CHARS] + "\n\n[...contenido truncado por longitud...]"
    return ChatAttachmentOut(filename=file.filename or "archivo", text=text)


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
    material_reader: MaterialReaderDep,
    embedder: EmbeddingProviderDep,
    history_reader: StudentHistoryReaderDep,
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
        if payload.course_id is not None:
            course_in_curriculum = await reader.course_detail(
                payload.course_id, profile.program_id
            )
            if course_in_curriculum is None or course_in_curriculum.credits is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, detail="Course not found in curriculum"
                )
        title = payload.message.strip()[:60] or "Nueva conversacion"
        conversation = await conversations.create(
            Conversation(user_id=user.user_id, course_id=payload.course_id, title=title)
        )
        history = []

    active_course_name = None
    if conversation.course_id is not None:
        course = await reader.course_detail(conversation.course_id)
        active_course_name = course.name if course is not None else None

    try:
        mode = ChatMode(payload.mode)
    except ValueError:
        mode = ChatMode.CONSULTA

    if conversation.course_id is None:
        mode = ChatMode.CONSULTA

    enrolled_course_names = tuple(
        entry.course_name for entry in await history_reader.enrollments_of(user.user_id)
    )

    context = StudentContext(
        program_id=profile.program_id, current_semester=profile.current_semester,
        student_user_id=user.user_id,
        active_course_id=conversation.course_id, active_course_name=active_course_name,
        mode=mode, enrolled_course_names=enrolled_course_names,
    )

    async def stream() -> AsyncIterator[bytes]:
        ticket = await gate.enqueue()
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
                              prompt_composer=prompt_composer, material_reader=material_reader,
                              embedder=embedder, history_reader=history_reader)
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
                        "conversation_id": conversation.id, "message_id": event.message_id,
                    })
        except Exception as error:
            yield _sse("error", {"code": "agent_loop_failed", "message": str(error)})
        finally:
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


@router.get("/conversations", response_model=list[ConversationSummaryOut])
async def list_conversations(
    user: Annotated[CurrentUser, Depends(require_student)],
    conversation_reader: ConversationReaderDep,
) -> list[ConversationSummaryOut]:
    rows = await conversation_reader.list_by_user(user.user_id)
    return [
        ConversationSummaryOut(id=r.id, title=r.title, course_id=r.course_id,
                                course_name=r.course_name, created_at=r.created_at)
        for r in rows
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailOut)
async def get_conversation(
    conversation_id: int,
    user: Annotated[CurrentUser, Depends(require_student)],
    conversation_reader: ConversationReaderDep,
    reader: AcademicReaderDep,
) -> ConversationDetailOut:
    conversation = await conversation_reader.get(conversation_id)
    if conversation is None or conversation.user_id != user.user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    course_name = None
    if conversation.course_id is not None:
        course = await reader.course_detail(conversation.course_id)
        course_name = course.name if course is not None else None

    messages = await conversation_reader.full_history(conversation_id)
    return ConversationDetailOut(
        id=conversation_id, title=conversation.title, course_id=conversation.course_id,
        course_name=course_name,
        messages=[
            MessageOut(
                id=m.id, role=m.role, content=m.content,
                tool_calls=[
                    ToolCallOut(id=t.id, name=t.name, arguments=t.arguments, result=t.result,
                                duration_ms=t.duration_ms, row_count=t.row_count,
                                sequence=t.sequence)
                    for t in m.tool_calls
                ],
                feedback=FeedbackOut(value=m.feedback.value, comment=m.feedback.comment)
                if m.feedback is not None else None,
            )
            for m in messages
        ],
    )
