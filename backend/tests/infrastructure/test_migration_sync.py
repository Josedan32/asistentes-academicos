"""The ORM models and the Alembic head must not drift apart.

Every test builds its schema from Base.metadata.create_all, so a model column added
without a revision is invisible to the entire suite — and fatal in production.
"""

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from alembic import command
from app.infrastructure.config import get_settings
from app.infrastructure.persistence.models import Base


def test_models_match_the_migration_head(tmp_path, monkeypatch) -> None:
    db_url = f"sqlite:///{tmp_path / 'drift.db'}"

    # env.py reads the database URL from get_settings(), overriding anything set on
    # the Config object passed to alembic. Point settings at the scratch database
    # instead of the developer's real one, and undo it once the migration has run.
    monkeypatch.setenv("SYNC_DATABASE_URL", db_url)
    get_settings.cache_clear()
    try:
        config = Config("backend/alembic.ini")
        config.set_main_option("script_location", "backend/alembic")
        command.upgrade(config, "head")
    finally:
        get_settings.cache_clear()

    engine = create_engine(db_url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        diff = compare_metadata(context, Base.metadata)

    engine.dispose()
    assert not diff, f"models drifted from the migration head: {diff}"
