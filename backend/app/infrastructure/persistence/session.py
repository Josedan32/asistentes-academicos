from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.infrastructure.config import get_settings


def create_database_engine(url: str) -> AsyncEngine:
    """Build an async engine with SQLite foreign keys actually enforced.

    pysqlite leaves `PRAGMA foreign_keys` off on every new connection, which makes
    the ondelete clauses declared on the models inert. The listener is guarded by
    dialect so it stays correct when PostgreSQL arrives in Phase 2.
    """
    engine = create_async_engine(url, echo=False)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine.sync_engine, "connect")
        def _enable_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


@lru_cache
def create_session_factory() -> async_sessionmaker[AsyncSession]:
    settings = get_settings()
    engine = create_database_engine(settings.database_url)
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    factory = create_session_factory()
    async with factory() as session:
        yield session
