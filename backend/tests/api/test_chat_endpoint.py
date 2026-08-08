import json

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.v1.deps import (
    get_db_session,
    get_inference_gate,
    get_llm_provider,
    get_prompt_composer,
    get_token_issuer,
)
from app.application.agents.llm_types import LLMResponse, ToolCallRequest
from app.infrastructure.persistence.academic_repository import normalize_name
from app.infrastructure.persistence.conversation_repository import SqlAlchemyConversationRepository
from app.infrastructure.persistence.models import (
    CourseModel,
    CurriculumEntryModel,
    ProgramModel,
    StudentProfileModel,
    UserModel,
)
from app.main import app
from tests.application.agents.fakes import FakeLLMProvider, FakePromptComposer


class ImmediateInferenceGate:
    async def enqueue(self) -> str:
        return "ticket"

    async def position(self, ticket: str) -> int | None:
        return 1

    async def release(self, ticket: str) -> None:
        return None


async def _seed_student(session: AsyncSession) -> tuple[int, int]:
    program = ProgramModel(code="ISW", name="Ingenieria en Software", semester_count=10)
    course = CourseModel(
        code="BD2", name="Base de Datos 2",
        normalized_name=normalize_name("Base de Datos 2"),
        area="Datos", default_credits=4,
    )
    session.add_all([program, course])
    await session.commit()
    session.add(
        CurriculumEntryModel(program_id=program.id, course_id=course.id, semester=4, credits=4)
    )
    user = UserModel(email="ana@pascualbravo.edu.co", password_hash="x", role="student")
    session.add(user)
    await session.commit()
    session.add(StudentProfileModel(user_id=user.id, first_name="Ana", last_name="Ruiz",
                                     document="1", program_id=program.id, current_semester=4))
    await session.commit()
    return user.id, program.id


@pytest.fixture
async def client(session_factory: async_sessionmaker[AsyncSession]):
    async def override_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_inference_gate] = lambda: ImmediateInferenceGate()
    app.dependency_overrides[get_prompt_composer] = lambda: FakePromptComposer()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()


def _events(body: str) -> list[tuple[str, dict]]:
    parsed = []
    for block in body.strip().split("\n\n"):
        lines = block.splitlines()
        event = lines[0].removeprefix("event: ")
        data = json.loads(lines[1].removeprefix("data: "))
        parsed.append((event, data))
    return parsed


async def test_chat_without_a_tool_call_streams_tokens_then_done(client, session_factory) -> None:
    async with session_factory() as session:
        user_id, _ = await _seed_student(session)
    token = get_token_issuer().issue(subject=str(user_id), role="student")
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        responses=[LLMResponse(content="Hola, en que te ayudo?")]
    )

    response = await client.post(
        "/api/v1/chat", json={"message": "hola"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    events = _events(response.text)
    names = [name for name, _ in events]
    assert names[-1] == "done"
    assert "token" in names
    assert events[-1][1]["tool_count"] == 0


async def test_chat_with_a_tool_call_streams_thinking_and_tool_call_events(
    client, session_factory
) -> None:
    async with session_factory() as session:
        user_id, program_id = await _seed_student(session)
    token = get_token_issuer().issue(subject=str(user_id), role="student")
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(responses=[
        LLMResponse(content=None, tool_calls=[
            ToolCallRequest(id="1", name="list_semester_courses",
                             arguments={"program_id": program_id, "semester": 4})
        ]),
        LLMResponse(content="Tienes 1 materia."),
    ])

    response = await client.post(
        "/api/v1/chat", json={"message": "que veo?"}, headers={"Authorization": f"Bearer {token}"}
    )

    events = _events(response.text)
    names = [name for name, _ in events]
    assert "thinking" in names
    assert "tool_call" in names
    assert names[-1] == "done"


async def test_chat_requires_authentication(client) -> None:
    response = await client.post("/api/v1/chat", json={"message": "hola"})
    assert response.status_code == 401


async def test_chat_rejects_a_coordination_account(client) -> None:
    token = get_token_issuer().issue(subject="1", role="coordination")
    response = await client.post(
        "/api/v1/chat", json={"message": "hola"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


async def test_feedback_is_accepted_for_the_authors_own_message(client, session_factory) -> None:
    async with session_factory() as session:
        user_id, _ = await _seed_student(session)
        repository = SqlAlchemyConversationRepository(session)
        from app.domain.agents.entities import Conversation, Message, MessageRole

        conversation = await repository.create(
            Conversation(user_id=user_id, course_id=None, title="t")
        )
        message = await repository.add_message(
            Message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content="hola")
        )
    token = get_token_issuer().issue(subject=str(user_id), role="student")

    response = await client.post(
        f"/api/v1/chat/messages/{message.id}/feedback", json={"value": "up"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201


async def test_feedback_is_rejected_for_another_students_message(client, session_factory) -> None:
    async with session_factory() as session:
        owner_id, _ = await _seed_student(session)
        repository = SqlAlchemyConversationRepository(session)
        from app.domain.agents.entities import Conversation, Message, MessageRole

        conversation = await repository.create(
            Conversation(user_id=owner_id, course_id=None, title="t")
        )
        message = await repository.add_message(
            Message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content="hola")
        )
        other = UserModel(email="otro@pascualbravo.edu.co", password_hash="x", role="student")
        session.add(other)
        await session.commit()
        other_id = other.id
    token = get_token_issuer().issue(subject=str(other_id), role="student")

    response = await client.post(
        f"/api/v1/chat/messages/{message.id}/feedback", json={"value": "up"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
