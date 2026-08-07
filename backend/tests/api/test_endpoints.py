import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.v1.deps import get_db_session
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

    Role gating reads the token only, so a directly issued token is enough to
    exercise the admin endpoints.
    """
    from app.api.v1.deps import get_token_issuer

    return get_token_issuer().issue(subject="1", role="coordination")


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


async def test_student_token_cannot_reach_admin_routes(client: AsyncClient) -> None:
    """A valid token is not authorisation. Role gating is a separate check."""
    response = await client.post(
        "/api/v1/admin/programs",
        json={"code": "ISW", "name": "Ingenieria en Software", "semester_count": 10},
        headers={"Authorization": f"Bearer {issue_token('student')}"},
    )
    assert response.status_code == 403
    assert "coordination" in response.json()["detail"].lower()
