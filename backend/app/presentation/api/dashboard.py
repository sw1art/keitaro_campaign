"""Dashboard API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.infrastructure.keitaro import KeitaroClient
from app.infrastructure.repositories import Repositories
from app.presentation.api.common import resolve_traffic_source_names
from app.presentation.api.mappers import map_campaign, map_operation
from app.presentation.dependencies import get_keitaro, get_repositories
from app.presentation.schemas import DashboardResponse

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    keitaro: KeitaroClient = Depends(get_keitaro),
    repos: Repositories = Depends(get_repositories),
) -> DashboardResponse:
    campaigns = await keitaro.get_campaigns()
    campaigns.sort(key=lambda c: c.get("created_at") or "", reverse=True)

    ts_names = await resolve_traffic_source_names(keitaro)
    recent_campaigns = [
        map_campaign(c, ts_names.get(c.get("traffic_source_id"))) for c in campaigns[:5]
    ]

    operations, total = await repos.operations.list(limit=5, offset=0)
    counts = await repos.operations.counts()

    return DashboardResponse(
        campaigns_count=len(campaigns),
        recent_campaigns=recent_campaigns,
        operations_total=total,
        operations_completed=counts.get("completed", 0),
        operations_failed=counts.get("failed", 0),
        recent_operations=[map_operation(o) for o in operations],
    )
