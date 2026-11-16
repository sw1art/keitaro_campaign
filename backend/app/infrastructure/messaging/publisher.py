"""RabbitMQ publisher (implements MessagePublisherProtocol)."""
from __future__ import annotations

import json
import logging
from typing import Any

import aio_pika
from aio_pika import DeliveryMode

from app.application.interfaces import MessagePublisherProtocol
from app.config import Settings
from app.infrastructure.messaging import topology

logger = logging.getLogger(__name__)


class RabbitPublisher(MessagePublisherProtocol):
    def __init__(self, settings: Settings) -> None:
        self._url = settings.rabbitmq_url
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractRobustChannel | None = None
        self._exchange: aio_pika.abc.AbstractRobustExchange | None = None

    async def connect(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            return
        self._connection = await aio_pika.connect_robust(self._url)
        self._channel = await self._connection.channel()
        self._exchange, _ = await topology.declare_topology(self._channel)

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        await self.connect()
        assert self._exchange is not None
        body = json.dumps(payload, default=str).encode()
        message = aio_pika.Message(body=body, delivery_mode=DeliveryMode.PERSISTENT)
        await self._exchange.publish(message, routing_key=event_type)

    async def close(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
        self._connection = None
        self._channel = None
        self._exchange = None
