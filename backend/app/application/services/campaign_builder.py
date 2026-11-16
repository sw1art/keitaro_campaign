"""Builders for Keitaro campaign/stream payloads.

The exact field names and types follow the OBSERVED live Keitaro schema
(verified against tlgk.host), not assumptions:

- redirect URL lives in ``action_payload`` (string), ``action_options`` stays null;
- ``weight`` is 0 for ordered ("regular") flows;
- flow ``type`` is ``regular`` (ordered by ``position``);
- offer flow uses ``schema: landings`` + empty ``action_payload``.

These shapes are isolated here (adapter layer) and covered by integration tests.
"""

from __future__ import annotations

from typing import Any


def build_campaign_payload(
    name: str,
    domain_id: int,
    *,
    alias: str,
    group_id: int,
    traffic_source_id: int,
) -> dict[str, Any]:
    return {
        "alias": alias,
        "type": "position",
        "name": name,
        "state": "active",
        "cost_type": "CPC",
        "cost_value": 0,
        "cost_auto": True,
        "cost_currency": "USD",
        "group_id": group_id,
        "traffic_source_id": traffic_source_id,
        "domain_id": domain_id,
    }


def build_google_stream_payload(
    campaign_id: int,
    geo: list[str],
    *,
    google_url: str,
    position: int = 1,
) -> dict[str, Any]:
    return {
        "campaign_id": campaign_id,
        "type": "regular",
        "name": "Google Redirect",
        "position": position,
        "state": "active",
        "schema": "redirect",
        "action_type": "http",
        "action_payload": google_url,
        "collect_clicks": True,
        "filter_or": False,
        "weight": 0,
        "offer_selection": "before_click",
        "filters": [{"name": "country", "mode": "accept", "payload": list(geo)}],
        "offers": [],
        "landings": [],
        "triggers": [],
    }


def build_offer_stream_payload(
    campaign_id: int,
    offers: list[dict[str, Any]],
    *,
    position: int = 2,
    default_share: int = 100,
) -> dict[str, Any]:
    return {
        "campaign_id": campaign_id,
        "type": "regular",
        "name": "Offer Flow",
        "position": position,
        "state": "active",
        "schema": "landings",
        "action_type": "http",
        "action_payload": "",
        "collect_clicks": True,
        "filter_or": False,
        "weight": 0,
        "offer_selection": "before_click",
        "filters": [],
        "offers": [
            {
                "offer_id": int(o["offer_id"]),
                "share": o.get("share", default_share),
                "state": "active",
            }
            for o in offers
        ],
        "landings": [],
        "triggers": [],
    }


def build_stream_update_payload(stream: dict[str, Any]) -> dict[str, Any]:
    """Convert a GET /streams/{id} response into a PUT request body.

    Strips read-only fields (``id``, ``created_at``, nested ``id``/``stream_id``/``oid``)
    so a full PUT does not send server-managed values back.
    """
    writable = (
        "campaign_id",
        "type",
        "name",
        "position",
        "state",
        "schema",
        "action_type",
        "action_payload",
        "action_options",
        "collect_clicks",
        "filter_or",
        "weight",
        "offer_selection",
        "comments",
    )
    payload: dict[str, Any] = {k: stream.get(k) for k in writable}

    payload["filters"] = [
        {"name": f.get("name"), "mode": f.get("mode"), "payload": f.get("payload", [])}
        for f in (stream.get("filters") or [])
    ]
    payload["triggers"] = [
        {k: v for k, v in t.items() if k not in ("id", "stream_id", "oid")}
        for t in (stream.get("triggers") or [])
    ]
    payload["offers"] = [
        {"offer_id": o.get("offer_id"), "share": o.get("share"), "state": o.get("state", "active")}
        for o in (stream.get("offers") or [])
    ]
    payload["landings"] = [
        {k: v for k, v in landing.items() if k not in ("id", "stream_id", "oid")}
        for landing in (stream.get("landings") or [])
    ]
    return payload
