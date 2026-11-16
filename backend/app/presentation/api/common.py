"""Shared helpers for API routers."""

from __future__ import annotations

import asyncio
import logging

from app.infrastructure.keitaro import KeitaroClient
from app.infrastructure.messaging.outbox import publish_pending
from app.infrastructure.messaging.publisher import RabbitPublisher

logger = logging.getLogger(__name__)


def schedule_best_effort_publish(session_factory, publisher: RabbitPublisher) -> None:
    """Publish pending outbox events in the background (best effort).

    The worker's outbox poller is the reliable fallback if the broker is down.
    """

    async def _run() -> None:
        try:
            await publish_pending(session_factory, publisher, limit=20)
        except Exception:  # noqa: BLE001
            logger.exception("Background outbox publish failed")

    asyncio.create_task(_run())


async def resolve_traffic_source_names(keitaro: KeitaroClient) -> dict[int, str]:
    try:
        sources = await keitaro.get_traffic_sources()
        return {s["id"]: s.get("name") or str(s["id"]) for s in sources}
    except Exception:  # noqa: BLE001 - name resolution is non-critical
        return {}
