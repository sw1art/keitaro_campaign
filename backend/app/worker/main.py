"""Worker entrypoint: RabbitMQ consumer + transactional-outbox publisher."""
from __future__ import annotations

import asyncio
import logging

from app.config import get_settings
from app.infrastructure.database.base import build_engine, build_session_factory
from app.infrastructure.keitaro import KeitaroClient
from app.infrastructure.messaging.consumer import WorkerConsumer
from app.infrastructure.messaging.outbox import publish_pending
from app.infrastructure.messaging.publisher import RabbitPublisher
from app.worker.handler import CampaignCreateHandler

logger = logging.getLogger(__name__)

OUTBOX_POLL_INTERVAL = 2.0


async def outbox_loop(session_factory, publisher: RabbitPublisher) -> None:
    while True:
        try:
            await publish_pending(session_factory, publisher)
        except Exception:  # noqa: BLE001 - keep polling
            logger.exception("Outbox poll failed")
        await asyncio.sleep(OUTBOX_POLL_INTERVAL)


async def run() -> None:
    settings = get_settings()
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)

    keitaro = KeitaroClient(settings)
    publisher = RabbitPublisher(settings)
    handler = CampaignCreateHandler(session_factory, keitaro, settings)
    consumer = WorkerConsumer(settings, handler, publisher)

    try:
        await asyncio.gather(
            outbox_loop(session_factory, publisher),
            consumer.run(),
        )
    finally:
        await keitaro.aclose()
        await publisher.close()
        await engine.dispose()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s",
    )
    asyncio.run(run())


if __name__ == "__main__":
    main()
