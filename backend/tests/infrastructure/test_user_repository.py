from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.identity.entities import Role, StudentProfile, User
from app.infrastructure.persistence.models import ProgramModel
from app.infrastructure.persistence.user_repository import SqlAlchemyUserRepository


async def _seed_program(session: AsyncSession) -> int:
    program = ProgramModel(code="ISW", name="Ingenieria en Software", semester_count=10)
    session.add(program)
    await session.commit()
    return program.id


async def test_finds_the_profile_of_a_registered_student(session: AsyncSession) -> None:
    program_id = await _seed_program(session)
    repository = SqlAlchemyUserRepository(session)
    user = await repository.add(
        User(email="ana@pascualbravo.edu.co", password_hash="x", role=Role.STUDENT),
        StudentProfile(
            user_id=0, first_name="Ana", last_name="Ruiz", document="123",
            program_id=program_id, current_semester=4,
        ),
    )

    profile = await repository.find_profile_by_user_id(user.id)

    assert profile is not None
    assert profile.program_id == program_id
    assert profile.current_semester == 4


async def test_returns_none_for_a_coordination_account(session: AsyncSession) -> None:
    repository = SqlAlchemyUserRepository(session)
    user = await repository.add(
        User(email="coord@pascualbravo.edu.co", password_hash="x", role=Role.COORDINATION),
        None,
    )

    assert await repository.find_profile_by_user_id(user.id) is None


async def test_returns_none_for_an_unknown_user(session: AsyncSession) -> None:
    repository = SqlAlchemyUserRepository(session)
    assert await repository.find_profile_by_user_id(999) is None
