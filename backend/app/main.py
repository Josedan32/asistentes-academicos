import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import admin, auth, chat, me, public
from app.infrastructure.config import get_settings

DEV_JWT_SECRET = "dev-only-insecure-secret-replace-me-32b"

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if get_settings().jwt_secret == DEV_JWT_SECRET:
        logger.warning(
            "JWT_SECRET is still the development default. Anyone who reads this "
            "repository can forge a coordination token. Set JWT_SECRET before exposing "
            "this server to anyone."
        )
    yield


app = FastAPI(title="Academic Assistants API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(chat.router)
app.include_router(me.router)


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
