from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.agents.ports import LLMProvider
from app.infrastructure.config import get_settings
from app.infrastructure.llm.caching_provider import CachingLLMProvider
from app.infrastructure.llm.ollama_embedding_provider import OllamaEmbeddingProvider
from app.infrastructure.llm.ollama_provider import OllamaProvider
from app.infrastructure.persistence.academic_reader import SqlAlchemyAcademicReader
from app.infrastructure.persistence.academic_repository import SqlAlchemyAcademicRepository
from app.infrastructure.persistence.conversation_reader import SqlAlchemyConversationReader
from app.infrastructure.persistence.conversation_repository import SqlAlchemyConversationRepository
from app.infrastructure.persistence.material_reader import SqlAlchemyMaterialReader
from app.infrastructure.persistence.material_repository import SqlAlchemyMaterialRepository
from app.infrastructure.persistence.session import get_session
from app.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from app.infrastructure.prompts.composer import TemplatePromptComposer
from app.infrastructure.redis.inference_gate import RedisInferenceGate
from app.infrastructure.redis.response_cache import RedisResponseCache
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


def require_student(
    user: Annotated[CurrentUser, Depends(require_authentication)],
) -> CurrentUser:
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Student role required"
        )
    return user


def get_material_repository(session: SessionDep) -> SqlAlchemyMaterialRepository:
    return SqlAlchemyMaterialRepository(session)


def get_material_reader(session: SessionDep) -> SqlAlchemyMaterialReader:
    return SqlAlchemyMaterialReader(session)


@lru_cache
def get_embedding_provider() -> OllamaEmbeddingProvider:
    settings = get_settings()
    return OllamaEmbeddingProvider(
        base_url=settings.ollama_base_url, model=settings.ollama_embedding_model,
    )


def get_conversation_repository(session: SessionDep) -> SqlAlchemyConversationRepository:
    return SqlAlchemyConversationRepository(session)


def get_conversation_reader(session: SessionDep) -> SqlAlchemyConversationReader:
    return SqlAlchemyConversationReader(session)


@lru_cache
def get_redis_client() -> Redis:
    return Redis.from_url(get_settings().redis_url)


def get_inference_gate(redis: Annotated[Redis, Depends(get_redis_client)]) -> RedisInferenceGate:
    return RedisInferenceGate(redis)


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    ollama = OllamaProvider(
        base_url=settings.ollama_base_url, model=settings.ollama_model,
        num_ctx=settings.ollama_num_ctx, keep_alive=settings.ollama_keep_alive,
    )
    cache = RedisResponseCache(Redis.from_url(settings.redis_url))
    return CachingLLMProvider(inner=ollama, cache=cache, ttl_seconds=300)


@lru_cache
def get_prompt_composer() -> TemplatePromptComposer:
    return TemplatePromptComposer()


ConversationRepositoryDep = Annotated[
    SqlAlchemyConversationRepository, Depends(get_conversation_repository)
]
ConversationReaderDep = Annotated[SqlAlchemyConversationReader, Depends(get_conversation_reader)]
InferenceGateDep = Annotated[RedisInferenceGate, Depends(get_inference_gate)]
LLMProviderDep = Annotated[LLMProvider, Depends(get_llm_provider)]
PromptComposerDep = Annotated[TemplatePromptComposer, Depends(get_prompt_composer)]
AcademicReaderDep = Annotated[SqlAlchemyAcademicReader, Depends(get_academic_reader)]
UserRepositoryDep = Annotated[SqlAlchemyUserRepository, Depends(get_user_repository)]
MaterialRepositoryDep = Annotated[
    SqlAlchemyMaterialRepository, Depends(get_material_repository)
]
MaterialReaderDep = Annotated[SqlAlchemyMaterialReader, Depends(get_material_reader)]
EmbeddingProviderDep = Annotated[OllamaEmbeddingProvider, Depends(get_embedding_provider)]
