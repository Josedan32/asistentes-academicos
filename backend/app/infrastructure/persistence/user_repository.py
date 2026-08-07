from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.identity.entities import Role, StudentProfile, User
from app.infrastructure.persistence.models import StudentProfileModel, UserModel


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
