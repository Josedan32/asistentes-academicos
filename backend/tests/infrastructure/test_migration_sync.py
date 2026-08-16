from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from alembic import command
from app.infrastructure.config import get_settings
from app.infrastructure.persistence.models import Base

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_models_match_the_migration_head(tmp_path, monkeypatch) -> None:
    db_url = f"sqlite:///{tmp_path / 'drift.db'}"

    monkeypatch.setenv("SYNC_DATABASE_URL", db_url)
    get_settings.cache_clear()
    try:
        config = Config(str(BACKEND_ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
        command.upgrade(config, "head")
    finally:
        get_settings.cache_clear()

    engine = create_engine(db_url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        diff = compare_metadata(context, Base.metadata)

    engine.dispose()
    assert not diff, f"models drifted from the migration head: {diff}"
