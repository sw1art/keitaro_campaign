"""Unit tests: analytics service (range resolution + report building)."""
from __future__ import annotations

from app.application.services.analytics_service import AnalyticsService, resolve_range


def test_resolve_range_custom():
    rng = resolve_range("custom", "2026-11-10", "2026-11-16", "UTC")
    assert rng["from"] == "2026-11-10"
    assert rng["to"] == "2026-11-16"
    assert rng["prev_from"] == "2026-11-03"
    assert rng["prev_to"] == "2026-11-09"


def test_resolve_range_last_7_days_shape():
    rng = resolve_range("last_7_days", None, None, "UTC")
    assert rng["from"] <= rng["to"]
    # previous period is adjacent and same length
    assert rng["prev_to"] < rng["from"]


class FakeKeitaroReports:
    def __init__(self) -> None:
        self.call_count = 0

    async def build_report(self, payload: dict) -> dict:
        self.call_count += 1
        clicks = 20 if self.call_count == 1 else 10
        summary = {
            "clicks": clicks,
            "campaign_unique_clicks": clicks,
            "conversions": 2,
            "leads": 0,
            "sales": 0,
            "rejected": 0,
            "cr": 0,
            "cost": 0,
            "revenue": 0,
            "profit": 0,
            "roi": 0,
            "epc": 0,
            "cpa": 0,
        }
        return {"rows": [], "summary": summary, "total": 0}


async def test_overview_computes_deltas():
    service = AnalyticsService(FakeKeitaroReports())
    result = await service.overview("custom", "2026-11-10", "2026-11-16", "UTC")
    assert result["metrics"]["clicks"] == 20
    assert result["deltas"]["clicks"] == 100.0
    assert result["range"]["from"] == "2026-11-10"


async def test_export_csv():
    class Fake:
        async def build_report(self, payload):
            return {"rows": [{"offer_id": 1, "clicks": 5}, {"offer_id": 2, "clicks": 3}], "summary": {}, "total": 2}

    service = AnalyticsService(Fake())
    content, filename = await service.export_csv("offers", "custom", "2026-11-10", "2026-11-16", "UTC")
    assert filename.endswith(".csv")
    text = content.decode("utf-8")
    assert "offer_id,clicks" in text
    assert "1,5" in text
