"""Unit tests: stream offer editing (optimistic concurrency)."""

from __future__ import annotations

import pytest

from app.application.dto import UpdateOffersCommand
from app.application.errors import KeitaroApiError
from app.application.services.stream_service import StreamService
from app.domain import value_objects
from app.domain.exceptions import ConflictError, NotFoundError, ValidationError


class FakeKeitaro:
    def __init__(self, offers: list[dict], stream: dict) -> None:
        self.offers = offers
        self.stream = stream
        self.updated: dict | None = None

    async def get_offers(self, *, fresh: bool = False):
        return self.offers

    async def get_stream(self, stream_id):
        if stream_id != self.stream["id"]:
            raise KeitaroApiError("not found", status_code=404)
        return self.stream

    async def update_stream(self, stream_id, payload):
        self.updated = payload
        return {**payload, "id": stream_id}


def _stream(offers: list[dict]) -> dict:
    return {
        "id": 1311553,
        "type": "regular",
        "name": "Offer Flow",
        "campaign_id": 212180,
        "position": 2,
        "state": "active",
        "schema": "landings",
        "action_type": "http",
        "action_payload": "",
        "action_options": None,
        "collect_clicks": True,
        "filter_or": False,
        "weight": 0,
        "offer_selection": "before_click",
        "comments": "",
        "filters": [],
        "triggers": [],
        "landings": [],
        "offers": offers,
    }


OFFERS = [{"id": 25327, "state": "active"}, {"id": 24800, "state": "active"}]


async def test_update_offers_ok():
    current = [{"offer_id": 25327, "share": 100}]
    stream = _stream(current)
    keitaro = FakeKeitaro(OFFERS, stream)
    service = StreamService(keitaro)

    cmd = UpdateOffersCommand(
        stream_id=1311553,
        offers=[{"offer_id": 25327, "share": 100}, {"offer_id": 24800, "share": 50}],
        base_fingerprint=value_objects.offers_fingerprint(current),
    )
    await service.update_offers(cmd)
    assert keitaro.updated is not None
    assert [o["offer_id"] for o in keitaro.updated["offers"]] == [25327, 24800]


async def test_update_offers_conflict_on_stale_fingerprint():
    current = [{"offer_id": 25327, "share": 100}]
    keitaro = FakeKeitaro(OFFERS, _stream(current))
    service = StreamService(keitaro)

    cmd = UpdateOffersCommand(
        stream_id=1311553,
        offers=[{"offer_id": 25327, "share": 50}],
        base_fingerprint="stale-fingerprint",
    )
    with pytest.raises(ConflictError):
        await service.update_offers(cmd)


async def test_update_offers_rejects_inactive_offer():
    keitaro = FakeKeitaro([{"id": 25327, "state": "inactive"}], _stream([]))
    service = StreamService(keitaro)
    cmd = UpdateOffersCommand(stream_id=1311553, offers=[{"offer_id": 25327, "share": 100}])
    with pytest.raises(ValidationError):
        await service.update_offers(cmd)


async def test_update_offers_not_found():
    keitaro = FakeKeitaro(OFFERS, _stream([]))
    service = StreamService(keitaro)
    cmd = UpdateOffersCommand(stream_id=999999, offers=[{"offer_id": 25327, "share": 100}])
    with pytest.raises(NotFoundError):
        await service.update_offers(cmd)
