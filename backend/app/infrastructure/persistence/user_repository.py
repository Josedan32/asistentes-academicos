from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.identity.entities import Role, StudentProfile, User
from app.infrastructure.persistence.models import ProgramModel, StudentProfileModel, UserModel


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_email(self, email: str) -> User | None:
        model = (
            await self._session.execute(
                select(UserModel).where(UserModel.email == email.strip().lower())
            )
        ).scalar_one_or_none()
        if model is None:
            return None
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            role=Role(model.role),
        )

    async def add(self, user: User, profile: StudentProfile | None) -> User:
        model = UserModel(
            email=user.email.strip().lower(),
            password_hash=user.password_hash,
            role=str(user.role),
        )
        self._session.add(model)
        await self._session.flush()

        if profile is not None:
            self._session.add(
                StudentProfileModel(
                    user_id=model.id,
                    first_name=profile.first_name,
                    last_name=profile.last_name,
                    document=profile.document,
                    program_id=profile.program_id,
                    current_semester=profile.current_semester,
                )
            )

        await self._session.commit()
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            role=Role(model.role),
        )

    async def program_exists(self, program_id: int) -> bool:
        return await self._session.get(ProgramModel, program_id) is not None

    async def find_profile_by_user_id(self, user_id: int) -> StudentProfile | None:
        model = await self._session.get(StudentProfileModel, user_id)
        if model is None:
            return None
        return StudentProfile(
            user_id=model.user_id,
            first_name=model.first_name,
            last_name=model.last_name,
            document=model.document,
            program_id=model.program_id,
            current_semester=model.current_semester,
        )
