from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.agents.entities import (
    Conversation,
    FeedbackValue,
    Message,
    MessageFeedback,
    MessageRole,
    ToolCall,
)
from app.infrastructure.persistence.conversation_reader import SqlAlchemyConversationReader
from app.infrastructure.persistence.conversation_repository import (
    SqlAlchemyConversationRepository,
)
from app.infrastructure.persistence.models import UserModel


async def _seed_user(session: AsyncSession) -> int:
    user = UserModel(email="ana@pascualbravo.edu.co", password_hash="x", role="student")
    session.add(user)
    await session.commit()
    return user.id


async def test_round_trips_a_conversation_with_a_tool_call(session: AsyncSession) -> None:
    user_id = await _seed_user(session)
    repository = SqlAlchemyConversationRepository(session)
    reader = SqlAlchemyConversationReader(session)

    conversation = await repository.create(
        Conversation(user_id=user_id, course_id=None, title="Materias del semestre")
    )
    assert conversation.id is not None

    user_message = await repository.add_message(
        Message(conversation_id=conversation.id, role=MessageRole.USER,
                content="Que materias veo?")
    )
    assistant_message = await repository.add_message(
        Message(conversation_id=conversation.id, role=MessageRole.ASSISTANT,
                content="Tienes 2 materias.", prompt_version="v1")
    )
    tool_call = await repository.add_tool_call(
        ToolCall(message_id=assistant_message.id, name="list_semester_courses",
                 arguments={"program_id": 1, "semester": 4}, result={"rows": []},
                 duration_ms=42, row_count=2, sequence=1)
    )
    assert tool_call.id is not None

    feedback = await repository.add_feedback(
        MessageFeedback(message_id=assistant_message.id, value=FeedbackValue.UP)
    )
    assert feedback.id is not None

    history = await reader.history(conversation.id)
    assert [m.role for m in history] == [MessageRole.USER, MessageRole.ASSISTANT]
    assert [m.content for m in history] == [user_message.content, assistant_message.content]

    loaded = await reader.get(conversation.id)
    assert loaded is not None
    assert loaded.title == "Materias del semestre"


async def test_message_owner_resolves_to_the_conversation_user(session: AsyncSession) -> None:
    user_id = await _seed_user(session)
    repository = SqlAlchemyConversationRepository(session)
    reader = SqlAlchemyConversationReader(session)

    conversation = await repository.create(
        Conversation(user_id=user_id, course_id=None, title="t")
    )
    message = await repository.add_message(
        Message(conversation_id=conversation.id, role=MessageRole.USER, content="hola")
    )

    assert await reader.message_owner(message.id) == user_id


async def test_message_owner_is_none_for_an_unknown_message(session: AsyncSession) -> None:
    reader = SqlAlchemyConversationReader(session)
    assert await reader.message_owner(999) is None


async def test_get_returns_none_for_an_unknown_conversation(session: AsyncSession) -> None:
    reader = SqlAlchemyConversationReader(session)
    assert await reader.get(999) is None
