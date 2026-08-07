from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.config import get_settings
from app.infrastructure.persistence.academic_reader import SqlAlchemyAcademicReader
from app.infrastructure.persistence.academic_repository import SqlAlchemyAcademicRepository
from app.infrastructure.persistence.session import get_session
from app.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from app.infrastructure.security.hasher import Argon2Hasher
from app.infrastructure.security.tokens import JwtTokenIssuer


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@lru_cache
def get_password_hasher() -> Argon2Hasher:
    return Argon2Hasher()


@lru_cache
def get_token_issuer() -> JwtTokenIssuer:
    settings = get_settings()
    return JwtTokenIssuer(
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        minutes=settings.access_token_minutes,
    )


def get_academic_repository(session: SessionDep) -> SqlAlchemyAcademicRepository:
    return SqlAlchemyAcademicRepository(session)


def get_academic_reader(session: SessionDep) -> SqlAlchemyAcademicReader:
    return SqlAlchemyAcademicReader(session)


def get_user_repository(session: SessionDep) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


class CurrentUser:
    def __init__(self, user_id: int, role: str) -> None:
        self.user_id = user_id
        self.role = role


def require_authentication(
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token"
        )
    token = authorization.split(" ", 1)[1]
    try:
        claims = get_token_issuer().decode(token)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from error
    return CurrentUser(user_id=int(claims["sub"]), role=str(claims["role"]))


def require_coordination(
    user: Annotated[CurrentUser, Depends(require_authentication)],
) -> CurrentUser:
    if user.role != "coordination":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Coordination role required"
        )
    return user
