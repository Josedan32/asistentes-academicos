from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.agents.dto import (
    ConversationSummary,
    FeedbackView,
    MessageDetail,
    ToolCallView,
)
from app.domain.agents.entities import Conversation, Message, MessageRole
from app.infrastructure.persistence.models import (
    ConversationModel,
    CourseModel,
    MessageFeedbackModel,
    MessageModel,
    ToolCallModel,
)


class SqlAlchemyConversationReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, conversation_id: int) -> Conversation | None:
        model = await self._session.get(ConversationModel, conversation_id)
        if model is None:
            return None
        return Conversation(
            id=model.id, user_id=model.user_id, course_id=model.course_id, title=model.title
        )

    async def history(self, conversation_id: int) -> list[Message]:
        rows = (
            await self._session.execute(
                select(MessageModel)
                .where(MessageModel.conversation_id == conversation_id)
                .order_by(MessageModel.id)
            )
        ).scalars()
        return [
            Message(
                id=row.id,
                conversation_id=row.conversation_id,
                role=MessageRole(row.role),
                content=row.content,
                prompt_version=row.prompt_version,
            )
            for row in rows
        ]

    async def message_owner(self, message_id: int) -> int | None:
        return (
            await self._session.execute(
                select(ConversationModel.user_id)
                .join(MessageModel, MessageModel.conversation_id == ConversationModel.id)
                .where(MessageModel.id == message_id)
            )
        ).scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[ConversationSummary]:
        statement = (
            select(ConversationModel, CourseModel.name)
            .outerjoin(CourseModel, CourseModel.id == ConversationModel.course_id)
            .where(ConversationModel.user_id == user_id)
            # created_at alone can tie at typical clock resolution when rows are
            # inserted back-to-back within a test or a fast request burst; the id
            # tiebreaker keeps "most recent first" deterministic.
            .order_by(ConversationModel.created_at.desc(), ConversationModel.id.desc())
        )
        rows = (await self._session.execute(statement)).all()
        return [
            ConversationSummary(id=c.id, title=c.title, course_id=c.course_id,
                                 course_name=course_name, created_at=c.created_at)
            for c, course_name in rows
        ]

    async def full_history(self, conversation_id: int) -> list[MessageDetail]:
        messages = (
            (
                await self._session.execute(
                    select(MessageModel)
                    .where(MessageModel.conversation_id == conversation_id)
                    .order_by(MessageModel.id)
                )
            )
            .scalars()
            .all()
        )

        result: list[MessageDetail] = []
        for message in messages:
            tool_call_rows = (
                (
                    await self._session.execute(
                        select(ToolCallModel)
                        .where(ToolCallModel.message_id == message.id)
                        .order_by(ToolCallModel.sequence)
                    )
                )
                .scalars()
                .all()
            )
            feedback_row = (
                await self._session.execute(
                    select(MessageFeedbackModel).where(
                        MessageFeedbackModel.message_id == message.id
                    )
                )
            ).scalar_one_or_none()
            result.append(
                MessageDetail(
                    id=message.id, role=message.role, content=message.content,
                    tool_calls=[
                        ToolCallView(id=t.id, name=t.name, arguments=t.arguments,
                                     result=t.result, duration_ms=t.duration_ms,
                                     row_count=t.row_count, sequence=t.sequence)
                        for t in tool_call_rows
                    ],
                    feedback=FeedbackView(value=feedback_row.value, comment=feedback_row.comment)
                    if feedback_row is not None else None,
                )
            )
        return result
