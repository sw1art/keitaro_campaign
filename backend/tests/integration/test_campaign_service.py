"""Integration tests: campaign creation orchestration (idempotency, resume)."""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.dto import CreateCampaignCommand
from app.application.services.campaign_service import CampaignCreationService
from app.domain.entities import Operation
from app.domain.exceptions import ValidationError
from app.infrastructure.repositories import Repositories


class FakeKeitaro:
    def __init__(self) -> None:
        self.offers = [
            {"id": 1, "state": "active", "name": "O1"},
            {"id": 2, "state": "active", "name": "O2"},
            {"id": 3, "state": "inactive", "name": "O3"},
        ]
        self.domains = [{"id": 10, "state": "active", "name": "d.com"}]
        self.created_campaigns: list[dict] = []
        self.created_streams: list[dict] = []
        self.streams: dict[int, dict] = {}
        self._next_campaign = 100
        self._next_stream = 1000

    async def get_offers(self):
        return self.offers

    async def get_domains(self):
        return self.domains

    async def create_campaign(self, payload):
        self._next_campaign += 1
        self.created_campaigns.append(payload)
        return {"id": self._next_campaign}

    async def create_stream(self, payload):
        self._next_stream += 1
        self.created_streams.append(payload)
        self.streams[self._next_stream] = payload
        return {"id": self._next_stream}

    async def get_streams(self, campaign_id):
        return [
            {"id": sid, **payload}
            for sid, payload in self.streams.items()
            if payload.get("campaign_id") == campaign_id
        ]

    # unused protocol methods
    async def get_campaigns(self, **kw):
        raise NotImplementedError

    async def get_campaign(self, campaign_id):
        raise NotImplementedError

    async def get_stream(self, stream_id):
        raise NotImplementedError

    async def update_stream(self, stream_id, payload):
        raise NotImplementedError

    async def get_traffic_sources(self):
        raise NotImplementedError

    async def get_groups(self, type_="campaigns"):
        raise NotImplementedError

    async def get_stream_filters(self):
        raise NotImplementedError


def _make_operation():
    return Operation(
        id=uuid4(),
        type="campaign.create",
        payload={"name": "Test", "geo": ["AU"], "offer_ids": [1, 2], "domain_id": 10},
    )


async def test_create_campaign_creates_two_flows_and_registry(session_factory, settings):
    keitaro = FakeKeitaro()
    async with session_factory() as session:
        repos = Repositories(session)
        operation = await repos.operations.add(_make_operation())
        await session.commit()

        service = CampaignCreationService(
            keitaro, settings, repos.campaigns, repos.operations, repos.audit, session.commit
        )
        operation = await service.create(operation)

        assert operation.result["keitaro_campaign_id"] > 0
        assert operation.result["google_stream_id"] > 0
        assert operation.result["offer_stream_id"] > 0
        assert operation.keitaro_campaign_id > 0
        assert operation.campaign_id is not None

        assert len(keitaro.created_campaigns) == 1
        assert len(keitaro.created_streams) == 2

        local = await repos.campaigns.get_by_keitaro_id(operation.keitaro_campaign_id)
        assert local is not None
        assert local.name == "Test"


async def test_create_is_idempotent_on_retry(session_factory, settings):
    keitaro = FakeKeitaro()
    async with session_factory() as session:
        repos = Repositories(session)
        operation = await repos.operations.add(_make_operation())
        await session.commit()

        service = CampaignCreationService(
            keitaro, settings, repos.campaigns, repos.operations, repos.audit, session.commit
        )
        await service.create(operation)

        campaigns_before = len(keitaro.created_campaigns)
        streams_before = len(keitaro.created_streams)

        # Reload (as a worker retry would) and run again.
        reloaded = await repos.operations.get(operation.id)
        assert reloaded is not None
        await service.create(reloaded)

        assert len(keitaro.created_campaigns) == campaigns_before
        assert len(keitaro.created_streams) == streams_before


async def test_validate_input_rejects_inactive_offer(session_factory, settings):
    keitaro = FakeKeitaro()
    async with session_factory() as session:
        repos = Repositories(session)
        service = CampaignCreationService(
            keitaro, settings, repos.campaigns, repos.operations, repos.audit, session.commit
        )
        cmd = CreateCampaignCommand(
            name="X", geo=["AU"], offer_ids=[3], domain_id=10
        )  # offer 3 is inactive
        with pytest.raises(ValidationError):
            await service.validate_input(cmd, valid_geo_codes={"AU", "MX"})


async def test_validate_input_ok(session_factory, settings):
    keitaro = FakeKeitaro()
    async with session_factory() as session:
        repos = Repositories(session)
        service = CampaignCreationService(
            keitaro, settings, repos.campaigns, repos.operations, repos.audit, session.commit
        )
        cmd = CreateCampaignCommand(name="X", geo=["AU"], offer_ids=[1, 2], domain_id=10)
        assert await service.validate_input(cmd, valid_geo_codes={"AU", "MX"}) == [1, 2]
