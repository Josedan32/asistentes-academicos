import json
from contextlib import aclosing

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.v1 import chat
from app.api.v1.deps import (
    get_db_session,
    get_inference_gate,
    get_llm_provider,
    get_prompt_composer,
    get_token_issuer,
)
from app.application.agents.llm_types import LLMResponse, ToolCallRequest
from app.domain.identity.entities import Role, User
from app.infrastructure.persistence.academic_repository import normalize_name
from app.infrastructure.persistence.conversation_repository import SqlAlchemyConversationRepository
from app.infrastructure.persistence.models import (
    CourseModel,
    CurriculumEntryModel,
    ProgramModel,
    StudentProfileModel,
    UserModel,
)
from app.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from app.infrastructure.prompts.composer import TemplatePromptComposer
from app.main import app
from tests.application.agents.fakes import FakeLLMProvider, FakePromptComposer


class ImmediateInferenceGate:
    async def enqueue(self) -> str:
        return "ticket"

    async def position(self, ticket: str) -> int | None:
        return 1

    async def release(self, ticket: str) -> None:
        return None


class NeverReadyInferenceGate:
    """Always reports a queue position behind the head, so the poll loop never breaks
    on its own — used to exercise the `queue_timeout` bound (finding 1)."""

    async def enqueue(self) -> str:
        return "ticket"

    async def position(self, ticket: str) -> int | None:
        return 2

    async def release(self, ticket: str) -> None:
        return None


class RaisingIsLoadedProvider:
    """An LLMProvider whose `is_loaded()` raises, simulating an unreachable Ollama —
    used to exercise the pre-loop error-event conversion (finding 2)."""

    model = "raising-v1"

    async def is_loaded(self) -> bool:
        raise RuntimeError("Ollama unreachable")

    async def complete(self, messages, tools=None):
        raise AssertionError("complete should not be called when is_loaded raises")


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


async def student_headers(
    client: AsyncClient, email: str = "estudiante@pascualbravo.edu.co"
) -> dict[str, str]:
    """Registers and logs in a student through the real HTTP flow, so tests exercise the
    same path a real client would (see test_endpoints.py::register_coordination for why
    the coordination account itself is seeded directly rather than self-registered)."""
    async with aclosing(app.dependency_overrides[get_db_session]()) as sessions:
        session = await anext(sessions)
        coordinator = await SqlAlchemyUserRepository(session).add(
            User(email=f"coord-{email}", password_hash="x", role=Role.COORDINATION), None,
        )
    coordination_token = get_token_issuer().issue(subject=str(coordinator.id), role="coordination")

    program = await client.post(
        "/api/v1/admin/programs",
        json={
            "code": f"P-{coordinator.id}", "name": "Ingenieria en Software",
            "semester_count": 10,
        },
        headers={"Authorization": f"Bearer {coordination_token}"},
    )
    program_id = program.json()["id"]

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email, "password": "a-strong-password",
            "first_name": "Ana", "last_name": "Ruiz", "document": f"doc-{coordinator.id}",
            "program_id": program_id, "current_semester": 4,
        },
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "a-strong-password"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


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
            ToolCallRequest(id="1", name="list_semester_courses", arguments={"semester": 4})
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


async def test_chat_yields_an_error_event_when_is_loaded_raises_before_streaming(
    client, session_factory
) -> None:
    async with session_factory() as session:
        user_id, _ = await _seed_student(session)
    token = get_token_issuer().issue(subject=str(user_id), role="student")
    app.dependency_overrides[get_llm_provider] = lambda: RaisingIsLoadedProvider()

    response = await client.post(
        "/api/v1/chat", json={"message": "hola"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    events = _events(response.text)
    assert events == [
        ("error", {"code": "agent_loop_failed", "message": "Ollama unreachable"})
    ]


async def test_chat_yields_a_queue_timeout_error_when_the_poll_bound_is_exceeded(
    client, session_factory, monkeypatch
) -> None:
    async with session_factory() as session:
        user_id, _ = await _seed_student(session)
    token = get_token_issuer().issue(subject=str(user_id), role="student")
    monkeypatch.setattr(chat, "QUEUE_POLL_SECONDS", 0.01)
    monkeypatch.setattr(chat, "MAX_QUEUE_POLL_ITERATIONS", 3)
    app.dependency_overrides[get_inference_gate] = lambda: NeverReadyInferenceGate()
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(responses=[])

    response = await client.post(
        "/api/v1/chat", json={"message": "hola"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    events = _events(response.text)
    names = [name for name, _ in events]
    assert names[-1] == "error"
    assert events[-1][1]["code"] == "queue_timeout"


async def test_general_conversation_forces_consulta_mode_even_if_payload_claims_otherwise(
    client, session_factory
) -> None:
    """Regression test for finding 1: a general (no course_id) conversation must always be
    framed as Consulta, even if the client claims a course-scoped mode like "examen" — that
    mode's instructions tell the model to call search_course_material, a tool absent from
    GENERAL_TOOL_NAMES, which would otherwise burn every iteration on a rejected tool call."""
    async with session_factory() as session:
        user_id, _ = await _seed_student(session)
    token = get_token_issuer().issue(subject=str(user_id), role="student")
    app.dependency_overrides[get_prompt_composer] = lambda: TemplatePromptComposer()
    provider = FakeLLMProvider(responses=[LLMResponse(content="ok")])
    app.dependency_overrides[get_llm_provider] = lambda: provider

    response = await client.post(
        "/api/v1/chat", json={"message": "hola", "mode": "examen"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    system_message = provider.calls[0][0]
    assert system_message.role == "system"
    assert "Modo examen" not in system_message.content


async def test_chat_rejects_a_course_id_outside_the_students_curriculum(
    client, session_factory
) -> None:
    """Regression test for finding 6: course_id is the only gate on which course's uploaded
    material search_course_material can read, so it must belong to the student's own program
    curriculum rather than being accepted as any id in the whole catalogue."""
    async with session_factory() as session:
        user_id, _ = await _seed_student(session)
        other_course = CourseModel(
            code="ING1", name="Ingles 1", normalized_name=normalize_name("Ingles 1"),
            area="Idiomas", default_credits=2,
        )
        session.add(other_course)
        await session.commit()
        other_course_id = other_course.id
    token = get_token_issuer().issue(subject=str(user_id), role="student")
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(responses=[])

    response = await client.post(
        "/api/v1/chat", json={"message": "hola", "course_id": other_course_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


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


async def test_done_event_includes_a_message_id_feedback_can_target(client: AsyncClient) -> None:
    headers = await student_headers(client)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        responses=[LLMResponse(content="Hola, en que te ayudo?")]
    )

    response = await client.post("/api/v1/chat", json={"message": "hola"}, headers=headers)
    assert response.status_code == 200
    done_event = next(data for name, data in _events(response.text) if name == "done")
    message_id = done_event["message_id"]

    feedback = await client.post(
        f"/api/v1/chat/messages/{message_id}/feedback", json={"value": "up"}, headers=headers
    )
    assert feedback.status_code == 201


async def test_lists_conversations_most_recent_first(client: AsyncClient) -> None:
    headers = await student_headers(client)

    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        responses=[LLMResponse(content="Hola, en que te ayudo?")]
    )
    first = await client.post(
        "/api/v1/chat", json={"message": "primera pregunta"}, headers=headers
    )
    assert first.status_code == 200

    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        responses=[LLMResponse(content="Claro, dime mas")]
    )
    second = await client.post(
        "/api/v1/chat", json={"message": "segunda pregunta"}, headers=headers
    )
    assert second.status_code == 200

    response = await client.get("/api/v1/chat/conversations", headers=headers)
    assert response.status_code == 200
    titles = [row["title"] for row in response.json()]
    assert titles[0] == "segunda pregunta"
    assert titles[1] == "primera pregunta"


async def test_gets_a_conversation_with_messages(client: AsyncClient) -> None:
    headers = await student_headers(client)
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        responses=[LLMResponse(content="Hola, en que te ayudo?")]
    )
    created = await client.post("/api/v1/chat", json={"message": "hola"}, headers=headers)
    assert created.status_code == 200
    done_event = next(data for name, data in _events(created.text) if name == "done")
    conversation_id = done_event["conversation_id"]

    response = await client.get(f"/api/v1/chat/conversations/{conversation_id}", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][0]["content"] == "hola"


async def test_cannot_read_another_students_conversation(client: AsyncClient) -> None:
    headers_a = await student_headers(client, email="a@pascualbravo.edu.co")
    headers_b = await student_headers(client, email="b@pascualbravo.edu.co")
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        responses=[LLMResponse(content="Hola, en que te ayudo?")]
    )
    created = await client.post("/api/v1/chat", json={"message": "hola"}, headers=headers_a)
    assert created.status_code == 200
    done_event = next(data for name, data in _events(created.text) if name == "done")
    conversation_id = done_event["conversation_id"]

    response = await client.get(
        f"/api/v1/chat/conversations/{conversation_id}", headers=headers_b
    )
    assert response.status_code == 404
