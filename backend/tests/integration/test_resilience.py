"""Resilience tests: partial failures, outbox retention, idempotency."""

from __future__ import annotations

from uuid import uuid4

from app.application.errors import PermanentError
from app.domain.entities import Operation, OutboxEvent
from app.infrastructure.messaging.outbox import publish_pending
from app.infrastructure.repositories import Repositories
from app.worker.handler import ACK, DEAD_LETTER, CampaignCreateHandler


class PartialKeitaro:
    """Creates the campaign and Google flow, then fails on the Offer Flow."""

    def __init__(self) -> None:
        self.campaign_id = 100
        self.streams: list[dict] = []

    async def create_campaign(self, payload):
        self.campaign_id += 1
        return {"id": self.campaign_id}

    async def create_stream(self, payload):
        if payload.get("name") == "Offer Flow":
            raise PermanentError("Offer flow creation rejected")
        self.streams.append(payload)
        return {"id": 2000 + len(self.streams)}

    async def get_campaigns(self, **kwargs):
        return []

    async def get_streams(self, campaign_id):
        return [{"id": 2001, "name": "Google Redirect", "filters": [], "offers": []}]


async def test_handler_marks_needs_attention_on_partial_permanent_failure(
    session_factory, settings
):
    keitaro = PartialKeitaro()
    async with session_factory() as session:
        repos = Repositories(session)
        operation = Operation(
            id=uuid4(),
            type="campaign.create",
            payload={"name": "Test", "geo": ["AU"], "offer_ids": [1, 2], "domain_id": 10},
        )
        await repos.operations.add(operation)
        await session.commit()

    handler = CampaignCreateHandler(session_factory, keitaro, settings)
    outcome = await handler.handle({"operation_id": str(operation.id)})

    assert outcome == DEAD_LETTER

    async with session_factory() as session:
        repos = Repositories(session)
        stored = await repos.operations.get(operation.id)
        assert stored is not None
        assert stored.status == "needs_attention"
        assert stored.result["keitaro_campaign_id"] > 0
        assert stored.result["google_stream_id"] > 0
        assert "offer_stream_id" not in stored.result


async def test_handler_is_idempotent_when_completed(session_factory, settings):
    keitaro = PartialKeitaro()
    async with session_factory() as session:
        repos = Repositories(session)
        operation = Operation(
            id=uuid4(),
            type="campaign.create",
            status="completed",
            payload={"name": "Test", "geo": ["AU"], "offer_ids": [1], "domain_id": 10},
        )
        await repos.operations.add(operation)
        await session.commit()

    handler = CampaignCreateHandler(session_factory, keitaro, settings)
    outcome = await handler.handle({"operation_id": str(operation.id)})
    assert outcome == ACK


class FailingPublisher:
    async def publish(self, event_type, payload):
        raise RuntimeError("broker down")


async def test_outbox_retains_event_on_publish_failure(session_factory):
    event_id = uuid4()
    async with session_factory() as session:
        repos = Repositories(session)
        await repos.outbox.add(
            OutboxEvent(id=event_id, event_type="campaign.create", payload={"x": 1})
        )
        await session.commit()

    published = await publish_pending(session_factory, FailingPublisher())
    assert published == 0

    async with session_factory() as session:
        repos = Repositories(session)
        pending = await repos.outbox.list_pending(limit=10)
        assert any(e.id == event_id for e in pending)
