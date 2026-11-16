"""RabbitMQ topology: exchanges, queues, bindings."""
from __future__ import annotations

import aio_pika
from aio_pika import ExchangeType

EXCHANGE = "adrobot.events"
DLX = "adrobot.dlx"

QUEUE_CREATE = "campaign.create"
QUEUE_RETRY = "campaign.create.retry"
QUEUE_DLQ = "campaign.create.dlq"

RETRY_TTL_MS = 5000
MAX_ATTEMPTS = 5


async def declare_topology(
    channel: aio_pika.abc.AbstractChannel,
) -> tuple[aio_pika.abc.AbstractExchange, aio_pika.abc.AbstractQueue]:
    """Declare exchanges/queues/bindings and return (events exchange, create queue)."""
    events = await channel.declare_exchange(EXCHANGE, ExchangeType.DIRECT, durable=True)
    await channel.declare_exchange(DLX, ExchangeType.DIRECT, durable=True)

    create_queue = await channel.declare_queue(
        QUEUE_CREATE,
        durable=True,
        arguments={
            "x-dead-letter-exchange": DLX,
            "x-dead-letter-routing-key": QUEUE_DLQ,
        },
    )
    await create_queue.bind(events, routing_key=QUEUE_CREATE)

    retry_queue = await channel.declare_queue(
        QUEUE_RETRY,
        durable=True,
        arguments={
            "x-message-ttl": RETRY_TTL_MS,
            "x-dead-letter-exchange": EXCHANGE,
            "x-dead-letter-routing-key": QUEUE_CREATE,
        },
    )
    await retry_queue.bind(events, routing_key=QUEUE_RETRY)

    dlq = await channel.declare_queue(QUEUE_DLQ, durable=True)
    dlx_exchange = await channel.declare_exchange(DLX, ExchangeType.DIRECT, durable=True)
    await dlq.bind(dlx_exchange, routing_key=QUEUE_DLQ)

    return events, create_queue
