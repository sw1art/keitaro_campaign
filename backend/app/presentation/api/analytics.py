"""Analytics API router (Keitaro Custom Reports)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.application.services.analytics_service import AnalyticsService
from app.infrastructure.keitaro import KeitaroClient
from app.presentation.dependencies import get_keitaro

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _range_params(
    range: str = Query(default="last_7_days"),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    timezone: str = Query(default="Europe/Moscow"),
) -> tuple[str, str | None, str | None, str]:
    return range, from_, to, timezone


@router.get("/overview")
async def overview(
    rp: tuple[str, str | None, str | None, str] = Depends(_range_params),
    keitaro: KeitaroClient = Depends(get_keitaro),
) -> dict:
    range_key, from_, to, timezone = rp
    return await AnalyticsService(keitaro).overview(range_key, from_, to, timezone)


@router.get("/trends")
async def trends(
    rp: tuple[str, str | None, str | None, str] = Depends(_range_params),
    keitaro: KeitaroClient = Depends(get_keitaro),
) -> dict:
    range_key, from_, to, timezone = rp
    return await AnalyticsService(keitaro).trends(range_key, from_, to, timezone)


@router.get("/campaigns/{campaign_id}")
async def campaign_analytics(
    campaign_id: int,
    rp: tuple[str, str | None, str | None, str] = Depends(_range_params),
    keitaro: KeitaroClient = Depends(get_keitaro),
) -> dict:
    range_key, from_, to, timezone = rp
    return await AnalyticsService(keitaro).campaign(campaign_id, range_key, from_, to, timezone)


@router.get("/offers")
async def offer_analytics(
    campaign_id: int | None = Query(default=None),
    rp: tuple[str, str | None, str | None, str] = Depends(_range_params),
    keitaro: KeitaroClient = Depends(get_keitaro),
) -> dict:
    range_key, from_, to, timezone = rp
    return await AnalyticsService(keitaro).offers(range_key, from_, to, timezone, campaign_id)


@router.get("/geo")
async def geo_analytics(
    campaign_id: int | None = Query(default=None),
    rp: tuple[str, str | None, str | None, str] = Depends(_range_params),
    keitaro: KeitaroClient = Depends(get_keitaro),
) -> dict:
    range_key, from_, to, timezone = rp
    return await AnalyticsService(keitaro).geo(range_key, from_, to, timezone, campaign_id)


@router.get("/export")
async def export_csv(
    type: str = Query(default="campaigns"),
    campaign_id: int | None = Query(default=None),
    rp: tuple[str, str | None, str | None, str] = Depends(_range_params),
    keitaro: KeitaroClient = Depends(get_keitaro),
) -> StreamingResponse:
    range_key, from_, to, timezone = rp
    content, filename = await AnalyticsService(keitaro).export_csv(
        type, range_key, from_, to, timezone, campaign_id
    )
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
