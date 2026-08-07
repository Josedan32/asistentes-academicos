import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.services import Authenticate, RegisterStudent
from app.domain.identity.entities import Role
from app.domain.identity.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from app.infrastructure.persistence.models import ProgramModel
from app.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from app.infrastructure.security.hasher import Argon2Hasher
from app.infrastructure.security.tokens import JwtTokenIssuer


@pytest.fixture
async def context(
    session: AsyncSession,
) -> tuple[SqlAlchemyUserRepository, Argon2Hasher, JwtTokenIssuer]:
    session.add(ProgramModel(code="ISW", name="Ingenieria en Software", semester_count=10))
    await session.commit()
    return (
        SqlAlchemyUserRepository(session),
        Argon2Hasher(),
        JwtTokenIssuer(
            secret="test-secret-that-is-long-enough-for-hs256",
            algorithm="HS256",
            minutes=60,
        ),
    )


async def test_registers_a_student(context) -> None:
    repository, hasher, _ = context
    user = await RegisterStudent(repository, hasher).execute(
        email="jose@pascualbravo.edu.co",
        password="a-strong-password",
        first_name="Jose",
        last_name="Hernandez",
        document="1000123456",
        program_id=1,
        current_semester=4,
    )
    assert user.id is not None
    assert user.role is Role.STUDENT
    assert user.password_hash != "a-strong-password"


async def test_rejects_duplicate_email(context) -> None:
    repository, hasher, _ = context
    register = RegisterStudent(repository, hasher)
    await register.execute(
        email="jose@pascualbravo.edu.co",
        password="a-strong-password",
        first_name="Jose",
        last_name="Hernandez",
        document="1000123456",
        program_id=1,
        current_semester=4,
    )
    with pytest.raises(EmailAlreadyRegisteredError):
        await register.execute(
            email="jose@pascualbravo.edu.co",
            password="another-password",
            first_name="Otro",
            last_name="Usuario",
            document="1000999999",
            program_id=1,
            current_semester=2,
        )


async def test_authenticates_and_issues_a_token(context) -> None:
    repository, hasher, issuer = context
    await RegisterStudent(repository, hasher).execute(
        email="jose@pascualbravo.edu.co",
        password="a-strong-password",
        first_name="Jose",
        last_name="Hernandez",
        document="1000123456",
        program_id=1,
        current_semester=4,
    )
    token = await Authenticate(repository, hasher, issuer).execute(
        email="jose@pascualbravo.edu.co", password="a-strong-password"
    )
    claims = issuer.decode(token)
    assert claims["role"] == "student"
    assert claims["sub"]


async def test_rejects_wrong_password(context) -> None:
    repository, hasher, issuer = context
    await RegisterStudent(repository, hasher).execute(
        email="jose@pascualbravo.edu.co",
        password="a-strong-password",
        first_name="Jose",
        last_name="Hernandez",
        document="1000123456",
        program_id=1,
        current_semester=4,
    )
    with pytest.raises(InvalidCredentialsError):
        await Authenticate(repository, hasher, issuer).execute(
            email="jose@pascualbravo.edu.co", password="wrong"
        )


async def test_rejects_unknown_email(context) -> None:
    repository, hasher, issuer = context
    with pytest.raises(InvalidCredentialsError):
        await Authenticate(repository, hasher, issuer).execute(
            email="nobody@pascualbravo.edu.co", password="whatever"
        )
