"""Unit tests: Keitaro payload builders."""
from app.application.services.campaign_builder import (
    build_campaign_payload,
    build_google_stream_payload,
    build_offer_stream_payload,
    build_stream_update_payload,
)


def test_build_campaign_payload():
    payload = build_campaign_payload(
        "My Campaign", 1813, alias="adrobot-abc123", group_id=10332, traffic_source_id=836
    )
    assert payload["name"] == "My Campaign"
    assert payload["alias"] == "adrobot-abc123"
    assert payload["domain_id"] == 1813
    assert payload["group_id"] == 10332
    assert payload["traffic_source_id"] == 836
    assert payload["type"] == "position"
    assert payload["state"] == "active"
    assert payload["cost_type"] == "CPC"


def test_build_google_stream_payload():
    payload = build_google_stream_payload(
        123, ["AU", "MX"], google_url="https://google.com"
    )
    assert payload["campaign_id"] == 123
    assert payload["schema"] == "redirect"
    assert payload["action_type"] == "http"
    assert payload["action_payload"] == "https://google.com"
    assert payload["position"] == 1
    assert payload["offers"] == []
    assert payload["filters"] == [
        {"name": "country", "mode": "accept", "payload": ["AU", "MX"]}
    ]


def test_build_offer_stream_payload():
    offers = [{"offer_id": 25327}, {"offer_id": 25328}]
    payload = build_offer_stream_payload(123, offers, default_share=100)
    assert payload["campaign_id"] == 123
    assert payload["schema"] == "landings"
    assert payload["position"] == 2
    assert payload["filters"] == []
    assert payload["offers"] == [
        {"offer_id": 25327, "share": 100, "state": "active"},
        {"offer_id": 25328, "share": 100, "state": "active"},
    ]


def test_build_stream_update_payload_strips_readonly_fields():
    raw = {
        "id": 1311445,
        "campaign_id": 212138,
        "type": "regular",
        "name": "Offer Flow",
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
        "filters": [{"id": 1, "stream_id": 1311445, "name": "country", "mode": "accept", "payload": ["RO"], "oid": 1}],
        "triggers": [],
        "landings": [],
        "offers": [
            {
                "id": 2060426,
                "stream_id": 1311445,
                "offer_id": 10050,
                "state": "active",
                "share": 0,
                "created_at": "2026-11-16 20:06:58",
                "updated_at": "2026-11-16 20:06:58",
            }
        ],
    }
    payload = build_stream_update_payload(raw)
    assert "id" not in payload
    assert payload["filters"] == [{"name": "country", "mode": "accept", "payload": ["RO"]}]
    assert payload["offers"] == [{"offer_id": 10050, "share": 0, "state": "active"}]
    assert "stream_id" not in payload["offers"][0]
    assert "created_at" not in payload["offers"][0]
