"""Campaigns API router."""
from __future__ import annotations

import asyncio
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto import CreateCampaignCommand
from app.application.services.campaign_service import CampaignCreationService
from app.config import get_settings
from app.domain.entities import Operation, OutboxEvent
from app.infrastructure.geo import get_valid_geo_codes
from app.infrastructure.keitaro import KeitaroClient
from app.infrastructure.messaging.outbox import build_event_message, publish_pending
from app.infrastructure.messaging.publisher import RabbitPublisher
from app.infrastructure.repositories import Repositories
from app.presentation.api.mappers import map_campaign, map_operation, map_stream
from app.presentation.dependencies import (
    get_keitaro,
    get_publisher,
    get_repositories,
    get_session_factory,
)
from app.presentation.schemas import (
    CampaignItem,
    CampaignListResponse,
    CreateCampaignAccepted,
    CreateCampaignRequest,
    OperationItem,
    StreamListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/campaigns", tags=["campaigns"])

EVENT_TYPE_CREATE = "campaign.create"


async def _resolve_traffic_source_names(keitaro: KeitaroClient) -> dict[int, str]:
    try:
        sources = await keitaro.get_traffic_sources()
        return {s["id"]: s.get("name") or str(s["id"]) for s in sources}
    except Exception:  # noqa: BLE001 - name resolution is non-critical
        return {}


async def _publish_best_effort(session_factory, publisher: RabbitPublisher) -> None:
    try:
        await publish_pending(session_factory, publisher, limit=20)
    except Exception:  # noqa: BLE001
        logger.exception("Background outbox publish failed")


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    search: str | None = Query(default=None),
    state: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    keitaro: KeitaroClient = Depends(get_keitaro),
) -> CampaignListResponse:
    raw = await keitaro.get_campaigns(query=search or None, state=state or None)
    # Client-side state filter in case the Keitaro endpoint ignores `state`.
    if state:
        raw = [c for c in raw if c.get("state") == state]
    total = len(raw)
    start = (page - 1) * page_size
    page_items = raw[start : start + page_size]

    ts_names = await _resolve_traffic_source_names(keitaro)
    items = [
        map_campaign(c, ts_names.get(c.get("traffic_source_id"))) for c in page_items
    ]
    return CampaignListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=CreateCampaignAccepted, status_code=202)
async def create_campaign(
    body: CreateCampaignRequest,
    request: Request,
    repos: Repositories = Depends(get_repositories),
    keitaro: KeitaroClient = Depends(get_keitaro),
    publisher: RabbitPublisher = Depends(get_publisher),
) -> CreateCampaignAccepted:
    settings = get_settings()
    service = CampaignCreationService(
        keitaro,
        settings,
        repos.campaigns,
        repos.operations,
        repos.audit,
        commit=repos.session.commit,
    )
    cmd = CreateCampaignCommand(
        name=body.name,
        geo=body.geo,
        offer_ids=body.offer_ids,
        domain_id=body.domain_id,
    )
    # Synchronous validation against live references.
    await service.validate_input(cmd, valid_geo_codes=get_valid_geo_codes())

    # Transactional outbox: operation + event in a single transaction.
    operation = Operation(
        id=uuid4(),
        type=EVENT_TYPE_CREATE,
        payload={
            "name": cmd.name,
            "geo": cmd.geo,
            "offer_ids": cmd.offer_ids,
            "domain_id": cmd.domain_id,
        },
    )
    operation = await repos.operations.add(operation)
    event = OutboxEvent(
        id=uuid4(),
        event_type=EVENT_TYPE_CREATE,
        payload=build_event_message(EVENT_TYPE_CREATE, operation.id, operation.payload),
    )
    await repos.outbox.add(event)
    await repos.session.commit()

    # Best-effort immediate publish; the worker's outbox poller is the fallback.
    asyncio.create_task(_publish_best_effort(get_session_factory(), publisher))

    return CreateCampaignAccepted(
        operation_id=str(operation.id),
        status="pending",
        message="Campaign creation started",
    )


@router.get("/{campaign_id}", response_model=CampaignItem)
async def get_campaign(
    campaign_id: int,
    keitaro: KeitaroClient = Depends(get_keitaro),
) -> CampaignItem:
    raw = await keitaro.get_campaign(campaign_id)
    ts_names = await _resolve_traffic_source_names(keitaro)
    return map_campaign(raw, ts_names.get(raw.get("traffic_source_id")))


@router.get("/{campaign_id}/streams", response_model=StreamListResponse)
async def get_campaign_streams(
    campaign_id: int,
    keitaro: KeitaroClient = Depends(get_keitaro),
) -> StreamListResponse:
    raw = await keitaro.get_streams(campaign_id)
    return StreamListResponse(items=[map_stream(s) for s in raw])


@router.get("/{campaign_id}/status", response_model=OperationItem)
async def get_campaign_status(
    campaign_id: str,
    repos: Repositories = Depends(get_repositories),
) -> OperationItem:
    operation = None
    try:
        operation = await repos.operations.get(UUID(campaign_id))
    except (ValueError, AttributeError):
        pass
    if operation is None:
        try:
            operation = await repos.operations.get_by_keitaro_campaign_id(int(campaign_id))
        except ValueError:
            pass
    if operation is None:
        from app.domain.exceptions import NotFoundError

        raise NotFoundError(f"Operation for campaign {campaign_id} not found.")
    return map_operation(operation)
