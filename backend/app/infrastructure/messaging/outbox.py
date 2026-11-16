"""Transactional outbox: publish pending events to the broker."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.infrastructure.messaging.publisher import RabbitPublisher
from app.infrastructure.repositories import Repositories

logger = logging.getLogger(__name__)


def build_event_message(
    event_type: str, operation_id: UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    """Message envelope delivered to the broker (no API token is included)."""
    return {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "operation_id": str(operation_id),
        "payload": payload,
    }


async def publish_pending(
    session_factory: async_sessionmaker,
    publisher: RabbitPublisher,
    *,
    limit: int = 50,
) -> int:
    """Publish up to `limit` pending outbox events. Returns the published count."""
    published = 0
    async with session_factory() as session:
        repos = Repositories(session)
        events = await repos.outbox.list_pending(limit=limit)
        for event in events:
            try:
                await publisher.publish(event.event_type, event.payload)
                await repos.outbox.mark_published(event.id)
                published += 1
            except Exception:
                logger.exception("Failed to publish outbox event %s", event.id)
                await repos.outbox.bump_attempts(event.id)
                break  # broker is likely down; retry on next poll
        await session.commit()
    return published
