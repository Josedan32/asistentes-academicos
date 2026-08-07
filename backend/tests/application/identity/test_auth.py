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


async def test_rejects_registration_for_an_unknown_program(context) -> None:
    repository, hasher, _ = context
    with pytest.raises(LookupError):
        await RegisterStudent(repository, hasher).execute(
            email="jose@pascualbravo.edu.co",
            password="a-strong-password",
            first_name="Jose",
            last_name="Hernandez",
            document="1000123456",
            program_id=9999,
            current_semester=4,
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


async def test_unknown_email_and_wrong_password_are_indistinguishable(context) -> None:
    """Account enumeration guard: both failures must look identical to a caller.

    If these two paths ever diverge in type or message, the login endpoint tells an
    attacker which email addresses are registered.
    """
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
    authenticate = Authenticate(repository, hasher, issuer)

    with pytest.raises(InvalidCredentialsError) as wrong_password:
        await authenticate.execute(
            email="jose@pascualbravo.edu.co", password="definitely-not-it"
        )
    with pytest.raises(InvalidCredentialsError) as unknown_email:
        await authenticate.execute(
            email="nadie@pascualbravo.edu.co", password="definitely-not-it"
        )

    assert type(wrong_password.value) is type(unknown_email.value)
    assert str(wrong_password.value) == str(unknown_email.value)


async def test_password_is_hashed_with_argon2_and_salted(context) -> None:
    """A hash that merely differs from the plaintext is not evidence of hashing."""
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

    assert user.password_hash.startswith("$argon2")
    assert hasher.verify("a-strong-password", user.password_hash)
    assert not hasher.verify("a-strong-passwore", user.password_hash)
    assert hasher.hash("a-strong-password") != hasher.hash("a-strong-password")
