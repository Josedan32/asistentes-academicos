from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./academic.db"
    sync_database_url: str = "sqlite:///./academic.db"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "dev-only-insecure-secret-replace-me-32b"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_num_ctx: int = 8192
    ollama_keep_alive: str = "10m"
    ollama_embedding_model: str = "nomic-embed-text"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    # Absolute path: `env_file=".env"` resolves against the current working directory,
    # so settings would load from backend/ but not from the repository root.
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
