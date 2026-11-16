"""FastAPI dependencies and shared singletons."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.config import Settings, get_settings
from app.infrastructure.database.base import build_engine, build_session_factory
from app.infrastructure.keitaro import KeitaroClient
from app.infrastructure.messaging.publisher import RabbitPublisher
from app.infrastructure.repositories import Repositories

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = build_engine(get_settings().database_url)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = build_session_factory(get_engine())
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    async with get_session_factory()() as session:
        yield session


def get_repositories(session: AsyncSession = Depends(get_session)) -> Repositories:
    return Repositories(session)


def get_keitaro(request: Request) -> KeitaroClient:
    return request.app.state.keitaro


def get_publisher(request: Request) -> RabbitPublisher:
    return request.app.state.publisher


async def require_api_token(request: Request) -> None:
    """Optional shared-token auth. Disabled when ADROBOT_API_TOKEN is empty.

    The frontend sends the token as `X-Api-Key` (or `Authorization: Bearer`).
    For a public deployment replace this with a real session/SSO.
    """
    settings: Settings = request.app.state.settings
    if not settings.auth_enabled:
        return

    api_key = request.headers.get("X-Api-Key")
    auth_header = request.headers.get("Authorization", "")
    bearer = ""
    if auth_header.lower().startswith("bearer "):
        bearer = auth_header[7:].strip()
    token = api_key or bearer

    if not token or token != settings.adrobot_api_token:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Invalid or missing API token."},
        )
