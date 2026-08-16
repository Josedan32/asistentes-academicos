from dataclasses import replace

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.agents.entities import Conversation, Message, MessageFeedback, ToolCall
from app.infrastructure.persistence.models import (
    ConversationModel,
    MessageFeedbackModel,
    MessageModel,
    ToolCallModel,
)


class SqlAlchemyConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, conversation: Conversation) -> Conversation:
        model = ConversationModel(
            user_id=conversation.user_id,
            course_id=conversation.course_id,
            title=conversation.title,
        )
        self._session.add(model)
        await self._session.commit()
        return replace(conversation, id=model.id)

    async def add_message(self, message: Message) -> Message:
        model = MessageModel(
            conversation_id=message.conversation_id,
            role=str(message.role),
            content=message.content,
            prompt_version=message.prompt_version,
            mode=str(message.mode) if message.mode is not None else None,
        )
        self._session.add(model)
        await self._session.commit()
        return replace(message, id=model.id)

    async def add_tool_call(self, tool_call: ToolCall) -> ToolCall:
        model = ToolCallModel(
            message_id=tool_call.message_id,
            name=tool_call.name,
            arguments=tool_call.arguments,
            result=tool_call.result,
            duration_ms=tool_call.duration_ms,
            row_count=tool_call.row_count,
            sequence=tool_call.sequence,
        )
        self._session.add(model)
        await self._session.commit()
        return replace(tool_call, id=model.id)

    async def add_feedback(self, feedback: MessageFeedback) -> MessageFeedback:
        model = MessageFeedbackModel(
            message_id=feedback.message_id,
            value=str(feedback.value),
            comment=feedback.comment,
        )
        self._session.add(model)
        await self._session.commit()
        return replace(feedback, id=model.id)
