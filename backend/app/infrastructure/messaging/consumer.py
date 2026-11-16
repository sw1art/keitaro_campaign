"""RabbitMQ consumer for the campaign.create queue."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aio_pika

from app.config import Settings
from app.infrastructure.messaging import topology
from app.infrastructure.messaging.publisher import RabbitPublisher
from app.worker.handler import ACK, DEAD_LETTER, RETRY, CampaignCreateHandler

logger = logging.getLogger(__name__)


class WorkerConsumer:
    def __init__(
        self,
        settings: Settings,
        handler: CampaignCreateHandler,
        publisher: RabbitPublisher,
    ) -> None:
        self._url = settings.rabbitmq_url
        self.handler = handler
        self.publisher = publisher

    async def run(self) -> None:
        while True:
            try:
                connection = await aio_pika.connect_robust(self._url)
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=1)
                _, create_queue = await topology.declare_topology(channel)

                logger.info("Worker consuming queue %s", topology.QUEUE_CREATE)
                async with create_queue.iterator() as iterator:
                    async for message in iterator:
                        await self._on_message(message)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 - keep the worker alive on broker outages
                logger.exception("Consumer connection lost; reconnecting in 2s")
                await asyncio.sleep(2)

    async def _on_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        body: dict[str, Any] = {}
        try:
            body = json.loads(message.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.error("Undecodable message body; dead-lettering")
            await message.reject(requeue=False)
            return

        outcome = DEAD_LETTER
        try:
            outcome = await self.handler.handle(body)
        except Exception:  # noqa: BLE001 - safety net so the loop never dies
            logger.exception("Handler raised unexpectedly")
            outcome = DEAD_LETTER

        try:
            if outcome == ACK:
                await message.ack()
            elif outcome == RETRY:
                await self.publisher.publish(topology.QUEUE_RETRY, body)
                await message.ack()
            else:
                await message.reject(requeue=False)  # routed to DLQ by the queue's DLX
        except Exception:  # noqa: BLE001
            logger.exception("Failed to settle message")
            try:
                await message.reject(requeue=True)
            except Exception:  # noqa: BLE001
                logger.exception("Failed to requeue message")
