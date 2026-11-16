"""Analytics service — builds aggregated reports via Keitaro Custom Reports API."""

from __future__ import annotations

import csv
import io
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.application.errors import KeitaroApiError
from app.application.interfaces import KeitaroClientProtocol

logger = logging.getLogger(__name__)

ALL_METRICS = [
    "clicks",
    "campaign_unique_clicks",
    "conversions",
    "leads",
    "sales",
    "rejected",
    "cr",
    "cost",
    "revenue",
    "profit",
    "roi",
    "epc",
    "cpa",
]

_DELTA_METRICS = [
    "clicks",
    "campaign_unique_clicks",
    "conversions",
    "leads",
    "sales",
    "rejected",
    "cr",
    "cost",
    "revenue",
    "profit",
    "roi",
    "epc",
    "cpa",
]

RANGES = {"today", "yesterday", "last_7_days", "last_30_days", "custom"}


def resolve_range(
    range_key: str,
    from_: str | None = None,
    to_: str | None = None,
    timezone: str = "UTC",
) -> dict[str, str]:
    """Resolve a range key into concrete from/to date strings (inclusive)."""
    tz = ZoneInfo(timezone) if timezone else ZoneInfo("UTC")
    today = datetime.now(tz).date()

    if range_key == "today":
        start = end = today
    elif range_key == "yesterday":
        start = end = today - timedelta(days=1)
    elif range_key == "last_30_days":
        start, end = today - timedelta(days=29), today
    elif range_key == "custom":
        end = date.fromisoformat(to_) if to_ else today
        start = date.fromisoformat(from_) if from_ else end - timedelta(days=6)
    else:  # last_7_days
        start, end = today - timedelta(days=6), today

    if start > end:
        start, end = end, start

    length = (end - start).days
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=length)

    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "prev_from": prev_start.isoformat(),
        "prev_to": prev_end.isoformat(),
        "timezone": timezone,
    }


class AnalyticsService:
    def __init__(self, keitaro: KeitaroClientProtocol) -> None:
        self.keitaro = keitaro

    async def _report(
        self,
        *,
        grouping: list[str],
        metrics: list[str],
        rng: dict[str, str],
        filters: list[dict] | None = None,
        limit: int = 1000,
        sort: list[dict] | None = None,
    ) -> dict:
        payload: dict = {
            "range": {"from": rng["from"], "to": rng["to"], "timezone": rng["timezone"]},
            "metrics": metrics,
            "grouping": grouping,
            "filters": filters or [],
            "sort": sort or [{"name": metrics[0], "order": "desc"}],
            "summary": True,
            "limit": limit,
        }
        return await self.keitaro.build_report(payload)

    async def overview(
        self, range_key: str, from_: str | None, to_: str | None, timezone: str
    ) -> dict:
        rng = resolve_range(range_key, from_, to_, timezone)
        cur = await self._report(grouping=["campaign_id"], metrics=ALL_METRICS, rng=rng, limit=1)
        prev = await self._report(
            grouping=["campaign_id"],
            metrics=ALL_METRICS,
            rng={"from": rng["prev_from"], "to": rng["prev_to"], "timezone": rng["timezone"]},
            limit=1,
        )
        summary = cur.get("summary") or {}
        prev_summary = prev.get("summary") or {}

        deltas: dict[str, float | None] = {}
        for metric in _DELTA_METRICS:
            prev_v = prev_summary.get(metric)
            cur_v = summary.get(metric)
            if isinstance(prev_v, (int, float)) and isinstance(cur_v, (int, float)):
                if prev_v == 0:
                    deltas[metric] = None if cur_v == 0 else 100.0
                else:
                    deltas[metric] = round((cur_v - prev_v) / prev_v * 100.0, 2)
            else:
                deltas[metric] = None

        return {"range": rng, "metrics": summary, "deltas": deltas}

    async def trends(
        self, range_key: str, from_: str | None, to_: str | None, timezone: str
    ) -> dict:
        rng = resolve_range(range_key, from_, to_, timezone)
        report = await self._report(
            grouping=["day"],
            metrics=["clicks", "conversions", "revenue", "cost", "profit", "roi", "cr"],
            rng=rng,
            sort=[{"name": "day", "order": "asc"}],
        )
        rows = sorted(report.get("rows") or [], key=lambda r: r.get("day") or "")
        return {"range": rng, "items": rows}

    async def campaign(
        self, campaign_id: int, range_key: str, from_: str | None, to_: str | None, timezone: str
    ) -> dict:
        rng = resolve_range(range_key, from_, to_, timezone)
        flt = [{"name": "campaign_id", "operator": "EQUALS", "expression": str(campaign_id)}]

        summary = await self._report(
            grouping=["campaign_id"], metrics=ALL_METRICS, rng=rng, filters=flt, limit=1
        )
        streams = await self._report(
            grouping=["stream_id"], metrics=ALL_METRICS, rng=rng, filters=flt
        )
        offers = await self._report(
            grouping=["offer_id"], metrics=ALL_METRICS, rng=rng, filters=flt
        )
        geo = await self._report(grouping=["country"], metrics=ALL_METRICS, rng=rng, filters=flt)

        return {
            "range": rng,
            "campaign_id": campaign_id,
            "metrics": summary.get("summary") or {},
            "streams": streams.get("rows") or [],
            "offers": await self._enrich_offers(offers.get("rows") or []),
            "geo": geo.get("rows") or [],
        }

    async def offers(
        self,
        range_key: str,
        from_: str | None,
        to_: str | None,
        timezone: str,
        campaign_id: int | None = None,
    ) -> dict:
        rng = resolve_range(range_key, from_, to_, timezone)
        filters = (
            [{"name": "campaign_id", "operator": "EQUALS", "expression": str(campaign_id)}]
            if campaign_id
            else []
        )
        report = await self._report(
            grouping=["offer_id"], metrics=ALL_METRICS, rng=rng, filters=filters
        )
        rows = await self._enrich_offers(report.get("rows") or [])

        if campaign_id:
            planned = await self._planned_shares(campaign_id)
            total_clicks = sum(int(r.get("clicks") or 0) for r in rows) or 1
            for row in rows:
                row["planned_share"] = planned.get(row.get("offer_id"))
                row["actual_share"] = round(int(row.get("clicks") or 0) / total_clicks * 100, 2)

        return {"range": rng, "campaign_id": campaign_id, "items": rows}

    async def geo(
        self,
        range_key: str,
        from_: str | None,
        to_: str | None,
        timezone: str,
        campaign_id: int | None = None,
    ) -> dict:
        rng = resolve_range(range_key, from_, to_, timezone)
        filters = (
            [{"name": "campaign_id", "operator": "EQUALS", "expression": str(campaign_id)}]
            if campaign_id
            else []
        )
        report = await self._report(
            grouping=["country"],
            metrics=[
                "clicks",
                "conversions",
                "cr",
                "revenue",
                "cost",
                "profit",
                "roi",
                "epc",
                "cpa",
            ],
            rng=rng,
            filters=filters,
        )
        return {"range": rng, "items": report.get("rows") or []}

    async def export_csv(
        self,
        report_type: str,
        range_key: str,
        from_: str | None,
        to_: str | None,
        timezone: str,
        campaign_id: int | None = None,
    ) -> tuple[bytes, str]:
        rng = resolve_range(range_key, from_, to_, timezone)
        grouping = {
            "campaigns": ["campaign_id"],
            "offers": ["offer_id"],
            "geo": ["country"],
            "streams": ["stream_id"],
        }.get(report_type, ["campaign_id"])
        filters = (
            [{"name": "campaign_id", "operator": "EQUALS", "expression": str(campaign_id)}]
            if campaign_id
            else []
        )
        report = await self._report(
            grouping=grouping, metrics=ALL_METRICS, rng=rng, filters=filters
        )
        rows = report.get("rows") or []

        buf = io.StringIO()
        writer = csv.DictWriter(
            buf, fieldnames=list(rows[0].keys()) if rows else ["metric", "value"]
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        filename = f"adrobot_{report_type}_{rng['from']}_{rng['to']}.csv"
        return buf.getvalue().encode("utf-8"), filename

    async def _enrich_offers(self, rows: list[dict]) -> list[dict]:
        if not rows:
            return rows
        try:
            offers = await self.keitaro.get_offers()
        except KeitaroApiError:
            offers = []
        by_id = {o["id"]: o for o in offers}
        for row in rows:
            offer = by_id.get(row.get("offer_id"))
            if offer:
                row["offer_name"] = offer.get("name")
                row["offer_state"] = offer.get("state")
        return rows

    async def _planned_shares(self, campaign_id: int) -> dict[int, float]:
        try:
            streams = await self.keitaro.get_streams(campaign_id)
        except KeitaroApiError:
            return {}
        flow = next(
            (s for s in streams if s.get("schema") == "landings" or s.get("name") == "Offer Flow"),
            None,
        )
        if not flow:
            return {}
        offers = flow.get("offers") or []
        total = sum(int(o.get("share") or 0) for o in offers) or 1
        return {
            int(o.get("offer_id")): round(int(o.get("share") or 0) / total * 100, 2) for o in offers
        }
