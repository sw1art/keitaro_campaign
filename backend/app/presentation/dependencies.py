"""FastAPI dependencies and shared singletons."""
from __future__ import annotations

from typing import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.config import get_settings
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
