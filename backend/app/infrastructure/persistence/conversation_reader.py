from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.agents.entities import Conversation, Message, MessageRole
from app.infrastructure.persistence.models import ConversationModel, MessageModel


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
