"""Shared test fixtures."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.infrastructure.database import Base


@pytest.fixture
def settings() -> Settings:
    return Settings(
        keitaro_base_url="https://keitaro.test/admin_api/v1",
        keitaro_api_token="test-token",
        keitaro_max_retries=1,
        keitaro_timeout=5,
    )


@pytest.fixture
async def session_factory(tmp_path):
    """In-memory-ish SQLite session factory (portable, no Postgres needed)."""
    db_path = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path.as_posix()}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()
