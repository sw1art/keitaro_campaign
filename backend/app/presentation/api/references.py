"""Reference data routers: offers, domains, traffic sources, GEO dictionary."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.infrastructure.geo import get_countries
from app.infrastructure.keitaro import KeitaroClient
from app.presentation.api.mappers import map_offer
from app.presentation.dependencies import get_keitaro
from app.presentation.schemas import (
    DomainItem,
    DomainListResponse,
    GeoListResponse,
    OfferListResponse,
    TrafficSourceItem,
    TrafficSourceListResponse,
)

router = APIRouter(tags=["references"])


@router.get("/offers", response_model=OfferListResponse)
async def list_offers(
    search: str | None = Query(default=None),
    state: str = Query(default="active"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    keitaro: KeitaroClient = Depends(get_keitaro),
) -> OfferListResponse:
    offers = await keitaro.get_offers()

    if state == "all":
        filtered = offers
    elif state == "inactive":
        filtered = [o for o in offers if o.get("state") != "active"]
    else:
        filtered = [o for o in offers if o.get("state") == "active"]

    if search:
        needle = search.strip().lower()
        filtered = [
            o
            for o in filtered
            if needle in (o.get("name") or "").lower() or needle in str(o.get("id"))
        ]

    total = len(filtered)
    start = (page - 1) * page_size
    items = [map_offer(o) for o in filtered[start : start + page_size]]
    return OfferListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/domains", response_model=DomainListResponse)
async def list_domains(
    keitaro: KeitaroClient = Depends(get_keitaro),
) -> DomainListResponse:
    raw = await keitaro.get_domains()
    items = [
        DomainItem(
            id=d["id"],
            name=d.get("name"),
            state=d.get("state"),
            is_ssl=d.get("is_ssl"),
            ssl_status=d.get("ssl_status"),
        )
        for d in raw
        if d.get("state") == "active"
    ]
    return DomainListResponse(items=items)


@router.get("/traffic-sources", response_model=TrafficSourceListResponse)
async def list_traffic_sources(
    keitaro: KeitaroClient = Depends(get_keitaro),
) -> TrafficSourceListResponse:
    raw = await keitaro.get_traffic_sources()
    items = [
        TrafficSourceItem(id=t["id"], name=t.get("name"), state=t.get("state")) for t in raw
    ]
    return TrafficSourceListResponse(items=items)


@router.get("/dictionaries/geo", response_model=GeoListResponse)
async def list_geo() -> GeoListResponse:
    return GeoListResponse(items=get_countries())
