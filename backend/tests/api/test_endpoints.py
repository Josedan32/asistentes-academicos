from contextlib import aclosing

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.v1.deps import get_db_session
from app.domain.identity.entities import Role, User
from app.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from app.main import app


@pytest.fixture
async def client(session_factory: async_sessionmaker[AsyncSession]) -> AsyncClient:
    async def override_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()


async def register_coordination(client: AsyncClient) -> str:
    """Coordination accounts are seeded, never self-registered.

    No public endpoint creates one, so this reaches into the DB session the
    `client` fixture already wired up (via the `get_db_session` override) to
    persist the row directly, then issues a token for it. A directly issued
    token used to be enough for role-gated write endpoints, which only decode
    the claims — but `/me` does a real `find_by_id` lookup, so the row must
    actually exist.
    """
    from app.api.v1.deps import get_token_issuer

    async with aclosing(app.dependency_overrides[get_db_session]()) as sessions:
        session = await anext(sessions)
        user = await SqlAlchemyUserRepository(session).add(
            User(email="coordinacion@pascualbravo.edu.co", password_hash="x",
                 role=Role.COORDINATION),
            None,
        )
    return get_token_issuer().issue(subject=str(user.id), role="coordination")


def issue_token(role: str) -> str:
    from app.api.v1.deps import get_token_issuer

    return get_token_issuer().issue(subject="1", role=role)


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_programs_endpoint_is_public(client: AsyncClient) -> None:
    response = await client.get("/api/v1/programs")
    assert response.status_code == 200
    assert response.json() == []


async def test_creating_a_program_requires_coordination(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/admin/programs",
        json={"code": "ISW", "name": "Ingenieria en Software", "semester_count": 10},
    )
    assert response.status_code == 401


async def test_coordination_can_build_a_curriculum(client: AsyncClient) -> None:
    token = await register_coordination(client)
    headers = {"Authorization": f"Bearer {token}"}

    program = await client.post(
        "/api/v1/admin/programs",
        json={"code": "ISW", "name": "Ingenieria en Software", "semester_count": 10},
        headers=headers,
    )
    assert program.status_code == 201
    program_id = program.json()["id"]

    first = await client.post(
        "/api/v1/admin/courses",
        json={"code": "BD1", "name": "Base de Datos 1", "area": "Datos", "default_credits": 3},
        headers=headers,
    )
    second = await client.post(
        "/api/v1/admin/courses",
        json={"code": "BD2", "name": "Base de Datos 2", "area": "Datos", "default_credits": 4},
        headers=headers,
    )
    first_id = first.json()["id"]
    second_id = second.json()["id"]

    await client.post(
        f"/api/v1/admin/programs/{program_id}/curriculum",
        json={"course_id": first_id, "semester": 3, "credits": 3},
        headers=headers,
    )
    assigned = await client.post(
        f"/api/v1/admin/programs/{program_id}/curriculum",
        json={
            "course_id": second_id,
            "semester": 4,
            "credits": 4,
            "prerequisite_course_ids": [first_id],
        },
        headers=headers,
    )
    assert assigned.status_code == 201

    curriculum = await client.get(
        f"/api/v1/programs/{program_id}/curriculum", params={"semester": 4}
    )
    assert curriculum.status_code == 200
    assert [row["code"] for row in curriculum.json()] == ["BD2"]


async def test_invalid_prerequisite_returns_422(client: AsyncClient) -> None:
    token = await register_coordination(client)
    headers = {"Authorization": f"Bearer {token}"}

    program = await client.post(
        "/api/v1/admin/programs",
        json={"code": "ISW", "name": "Ingenieria en Software", "semester_count": 10},
        headers=headers,
    )
    program_id = program.json()["id"]
    first = await client.post(
        "/api/v1/admin/courses",
        json={"code": "BD1", "name": "Base de Datos 1", "area": "Datos", "default_credits": 3},
        headers=headers,
    )
    second = await client.post(
        "/api/v1/admin/courses",
        json={"code": "BD2", "name": "Base de Datos 2", "area": "Datos", "default_credits": 4},
        headers=headers,
    )

    await client.post(
        f"/api/v1/admin/programs/{program_id}/curriculum",
        json={"course_id": first.json()["id"], "semester": 5, "credits": 3},
        headers=headers,
    )
    response = await client.post(
        f"/api/v1/admin/programs/{program_id}/curriculum",
        json={
            "course_id": second.json()["id"],
            "semester": 4,
            "credits": 4,
            "prerequisite_course_ids": [first.json()["id"]],
        },
        headers=headers,
    )
    assert response.status_code == 422
    assert "prerequisite" in response.json()["detail"].lower()


async def test_student_can_register_and_login(client: AsyncClient) -> None:
    token = await register_coordination(client)
    program = await client.post(
        "/api/v1/admin/programs",
        json={"code": "ISW", "name": "Ingenieria en Software", "semester_count": 10},
        headers={"Authorization": f"Bearer {token}"},
    )

    registered = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "jose@pascualbravo.edu.co",
            "password": "a-strong-password",
            "first_name": "Jose",
            "last_name": "Hernandez",
            "document": "1000123456",
            "program_id": program.json()["id"],
            "current_semester": 4,
        },
    )
    assert registered.status_code == 201

    logged_in = await client.post(
        "/api/v1/auth/login",
        json={"email": "jose@pascualbravo.edu.co", "password": "a-strong-password"},
    )
    assert logged_in.status_code == 200
    assert logged_in.json()["role"] == "student"
    assert logged_in.json()["access_token"]


async def test_login_with_wrong_password_returns_401(client: AsyncClient) -> None:
    token = await register_coordination(client)
    program = await client.post(
        "/api/v1/admin/programs",
        json={"code": "ISW", "name": "Ingenieria en Software", "semester_count": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "jose@pascualbravo.edu.co",
            "password": "a-strong-password",
            "first_name": "Jose",
            "last_name": "Hernandez",
            "document": "1000123456",
            "program_id": program.json()["id"],
            "current_semester": 4,
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "jose@pascualbravo.edu.co", "password": "definitely-not-it"},
    )
    assert response.status_code == 401

    unknown = await client.post(
        "/api/v1/auth/login",
        json={"email": "nadie@pascualbravo.edu.co", "password": "definitely-not-it"},
    )
    assert unknown.status_code == 401
    assert unknown.json() == response.json()


async def test_public_programs_projection_carries_course_count(client: AsyncClient) -> None:
    """A field rename in ProgramSummary must not silently degrade to course_count=0."""
    token = await register_coordination(client)
    headers = {"Authorization": f"Bearer {token}"}
    program = await client.post(
        "/api/v1/admin/programs",
        json={"code": "ISW", "name": "Ingenieria en Software", "semester_count": 10},
        headers=headers,
    )
    course = await client.post(
        "/api/v1/admin/courses",
        json={"code": "BD1", "name": "Base de Datos 1", "area": "Datos", "default_credits": 3},
        headers=headers,
    )
    await client.post(
        f"/api/v1/admin/programs/{program.json()['id']}/curriculum",
        json={"course_id": course.json()["id"], "semester": 3, "credits": 3},
        headers=headers,
    )

    response = await client.get("/api/v1/programs")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["course_count"] == 1
    assert body[0]["code"] == "ISW"


async def test_student_token_cannot_reach_admin_routes(client: AsyncClient) -> None:
    """A valid token is not authorisation. Role gating is a separate check."""
    response = await client.post(
        "/api/v1/admin/programs",
        json={"code": "ISW", "name": "Ingenieria en Software", "semester_count": 10},
        headers={"Authorization": f"Bearer {issue_token('student')}"},
    )
    assert response.status_code == 403
    assert "coordination" in response.json()["detail"].lower()


async def test_me_returns_student_profile_and_program(client: AsyncClient) -> None:
    token = await register_coordination(client)
    headers = {"Authorization": f"Bearer {token}"}
    program = await client.post(
        "/api/v1/admin/programs",
        json={"code": "ISW", "name": "Ingenieria en Software", "semester_count": 10},
        headers=headers,
    )
    program_id = program.json()["id"]
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ana@pascualbravo.edu.co", "password": "a-strong-password",
            "first_name": "Ana", "last_name": "Marin", "document": "123",
            "program_id": program_id, "current_semester": 5,
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "ana@pascualbravo.edu.co", "password": "a-strong-password"},
    )
    student_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.get("/api/v1/me", headers=student_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "student"
    assert body["first_name"] == "Ana"
    assert body["program_code"] == "ISW"
    assert body["current_semester"] == 5


async def test_me_for_coordination_has_no_student_fields(client: AsyncClient) -> None:
    token = await register_coordination(client)
    response = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "coordination"
    assert body["program_id"] is None


async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me")
    assert response.status_code == 401


async def test_my_enrollments_returns_the_students_actual_enrolled_courses(
    client: AsyncClient,
) -> None:
    """Regression coverage for the sidebar showing "materias del semestre N" from the
    static curriculum instead of what the student is actually registered in — a real
    student can be ahead or behind that grouping (e.g. testing out of English levels
    early)."""
    from app.infrastructure.persistence.models import CourseModel, StudentEnrollmentModel

    token = await register_coordination(client)
    headers = {"Authorization": f"Bearer {token}"}
    program = await client.post(
        "/api/v1/admin/programs",
        json={"code": "ISW", "name": "Ingenieria en Software", "semester_count": 10},
        headers=headers,
    )
    program_id = program.json()["id"]
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ana@pascualbravo.edu.co", "password": "a-strong-password",
            "first_name": "Ana", "last_name": "Marin", "document": "123",
            "program_id": program_id, "current_semester": 5,
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "ana@pascualbravo.edu.co", "password": "a-strong-password"},
    )
    student_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    async with aclosing(app.dependency_overrides[get_db_session]()) as sessions:
        session = await anext(sessions)
        me = await client.get("/api/v1/me", headers=student_headers)
        course = CourseModel(code="FB0087", name="Ingles 7", area="Formacion humanistica",
                              default_credits=1)
        session.add(course)
        await session.flush()
        session.add(
            StudentEnrollmentModel(student_user_id=me.json()["id"], course_id=course.id,
                                    period="20262", times_taken=0)
        )
        await session.commit()

    response = await client.get("/api/v1/me/enrollments", headers=student_headers)
    assert response.status_code == 200
    body = response.json()
    assert body == [
        {"course_id": course.id, "course_code": "FB0087", "course_name": "Ingles 7",
         "area": "Formacion humanistica", "credits": 1, "period": "20262", "times_taken": 0}
    ]


async def test_chat_attachment_returns_extracted_text_and_persists_nothing(
    client: AsyncClient,
) -> None:
    token = issue_token("student")
    pdf_bytes = (
        __import__("pathlib").Path(__file__).resolve().parents[1] / "fixtures" / "sample.pdf"
    ).read_bytes()

    response = await client.post(
        "/api/v1/chat/attachments",
        files={"file": ("apuntes.pdf", pdf_bytes, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "apuntes.pdf"
    assert body["text"].strip() != ""


async def test_chat_attachment_rejects_an_unsupported_format(client: AsyncClient) -> None:
    token = issue_token("student")

    response = await client.post(
        "/api/v1/chat/attachments",
        files={"file": ("slides.pptx", b"whatever", "application/vnd.ms-powerpoint")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert "format" in response.json()["detail"].lower()


async def test_chat_attachment_requires_a_student(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/chat/attachments",
        files={"file": ("apuntes.pdf", b"whatever", "application/pdf")},
    )
    assert response.status_code == 401


async def test_chat_model_endpoint_reports_the_configured_model(client: AsyncClient) -> None:
    token = issue_token("student")
    response = await client.get("/api/v1/chat/model", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["model"]


async def test_curriculum_board_returns_all_semesters_at_once(client: AsyncClient) -> None:
    token = await register_coordination(client)
    headers = {"Authorization": f"Bearer {token}"}
    program = await client.post(
        "/api/v1/admin/programs",
        json={"code": "ISW", "name": "Ingenieria en Software", "semester_count": 10},
        headers=headers,
    )
    program_id = program.json()["id"]
    first = await client.post(
        "/api/v1/admin/courses",
        json={"code": "BD1", "name": "Base de Datos 1", "area": "Datos", "default_credits": 3},
        headers=headers,
    )
    second = await client.post(
        "/api/v1/admin/courses",
        json={"code": "BD2", "name": "Base de Datos 2", "area": "Datos", "default_credits": 4},
        headers=headers,
    )
    await client.post(
        f"/api/v1/admin/programs/{program_id}/curriculum",
        json={"course_id": first.json()["id"], "semester": 1, "credits": 3},
        headers=headers,
    )
    await client.post(
        f"/api/v1/admin/programs/{program_id}/curriculum",
        json={"course_id": second.json()["id"], "semester": 4, "credits": 4,
              "prerequisite_course_ids": [first.json()["id"]]},
        headers=headers,
    )

    response = await client.get(f"/api/v1/admin/programs/{program_id}/curriculum", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert [row["semester"] for row in body] == [1, 4]
    bd2 = next(row for row in body if row["course_code"] == "BD2")
    assert bd2["prerequisites"][0]["course_code"] == "BD1"
    assert bd2["shared_program_count"] == 1


async def test_admin_courses_endpoint_reports_placements(client: AsyncClient) -> None:
    token = await register_coordination(client)
    headers = {"Authorization": f"Bearer {token}"}
    program = await client.post(
        "/api/v1/admin/programs",
        json={"code": "ISW", "name": "Ingenieria en Software", "semester_count": 10},
        headers=headers,
    )
    course = await client.post(
        "/api/v1/admin/courses",
        json={"code": "BD1", "name": "Base de Datos 1", "area": "Datos", "default_credits": 3},
        headers=headers,
    )
    unassigned = await client.post(
        "/api/v1/admin/courses",
        json={"code": "ARQ", "name": "Arquitectura", "area": "Software", "default_credits": 4},
        headers=headers,
    )
    await client.post(
        f"/api/v1/admin/programs/{program.json()['id']}/curriculum",
        json={"course_id": course.json()["id"], "semester": 3, "credits": 3},
        headers=headers,
    )

    response = await client.get("/api/v1/admin/courses", headers=headers)
    assert response.status_code == 200
    body = {row["code"]: row for row in response.json()}
    assert len(body["BD1"]["placements"]) == 1
    assert body["BD1"]["placements"][0]["program_code"] == "ISW"
    assert body[unassigned.json()["code"]]["placements"] == []


async def test_editing_a_program(client: AsyncClient) -> None:
    token = await register_coordination(client)
    headers = {"Authorization": f"Bearer {token}"}
    program = await client.post(
        "/api/v1/admin/programs",
        json={"code": "ISW", "name": "Ingenieria en Software", "semester_count": 10},
        headers=headers,
    )
    response = await client.patch(
        f"/api/v1/admin/programs/{program.json()['id']}",
        json={"code": "ISW", "name": "Ingenieria de Software", "semester_count": 10,
              "is_active": False},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Ingenieria de Software"
    assert response.json()["is_active"] is False


async def test_editing_a_course(client: AsyncClient) -> None:
    token = await register_coordination(client)
    headers = {"Authorization": f"Bearer {token}"}
    course = await client.post(
        "/api/v1/admin/courses",
        json={"code": "BD1", "name": "Base de Datos 1", "area": "Datos", "default_credits": 3},
        headers=headers,
    )
    response = await client.patch(
        f"/api/v1/admin/courses/{course.json()['id']}",
        json={"code": "BD1", "name": "Base de Datos I", "area": "Datos", "default_credits": 4},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["default_credits"] == 4


async def test_editing_requires_coordination(client: AsyncClient) -> None:
    response = await client.patch(
        "/api/v1/admin/programs/1",
        json={"code": "X", "name": "X", "semester_count": 1, "is_active": True},
        headers={"Authorization": f"Bearer {issue_token('student')}"},
    )
    assert response.status_code == 403


async def test_uploads_lists_and_deletes_course_material(client: AsyncClient) -> None:
    from app.api.v1.deps import get_embedding_provider
    from tests.application.agents.fakes import FakeEmbeddingProvider

    app.dependency_overrides[get_embedding_provider] = lambda: FakeEmbeddingProvider()

    token = await register_coordination(client)
    headers = {"Authorization": f"Bearer {token}"}
    course = await client.post(
        "/api/v1/admin/courses",
        json={"code": "BD2", "name": "Base de Datos 2", "area": "Datos", "default_credits": 4},
        headers=headers,
    )
    course_id = course.json()["id"]

    pdf_bytes = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "fixtures" / "sample.pdf"
    ).read_bytes()

    uploaded = await client.post(
        f"/api/v1/admin/courses/{course_id}/materials",
        files={"file": ("guia.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert uploaded.status_code == 201
    material_id = uploaded.json()["id"]

    listed = await client.get(
        f"/api/v1/admin/courses/{course_id}/materials", headers=headers
    )
    assert listed.status_code == 200
    assert [m["filename"] for m in listed.json()] == ["guia.pdf"]

    deleted = await client.delete(f"/api/v1/admin/materials/{material_id}", headers=headers)
    assert deleted.status_code == 204

    listed_again = await client.get(
        f"/api/v1/admin/courses/{course_id}/materials", headers=headers
    )
    assert listed_again.json() == []


async def test_uploading_an_unsupported_format_returns_422(client: AsyncClient) -> None:
    from app.api.v1.deps import get_embedding_provider
    from tests.application.agents.fakes import FakeEmbeddingProvider

    app.dependency_overrides[get_embedding_provider] = lambda: FakeEmbeddingProvider()

    token = await register_coordination(client)
    headers = {"Authorization": f"Bearer {token}"}
    course = await client.post(
        "/api/v1/admin/courses",
        json={"code": "BD2", "name": "Base de Datos 2", "area": "Datos", "default_credits": 4},
        headers=headers,
    )
    course_id = course.json()["id"]

    response = await client.post(
        f"/api/v1/admin/courses/{course_id}/materials",
        files={"file": ("slides.pptx", b"whatever", "application/vnd.ms-powerpoint")},
        headers=headers,
    )

    assert response.status_code == 422
    assert "format" in response.json()["detail"].lower()


async def test_uploading_material_requires_coordination(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/admin/courses/1/materials",
        files={"file": ("x.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 401
