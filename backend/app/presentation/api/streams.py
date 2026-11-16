"""Streams API router (editor)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.application.dto import UpdateOffersCommand
from app.application.services.stream_service import StreamService
from app.infrastructure.keitaro import KeitaroClient
from app.presentation.api.mappers import map_stream
from app.presentation.dependencies import get_keitaro
from app.presentation.schemas import StreamItem, UpdateOffersRequest

router = APIRouter(prefix="/streams", tags=["streams"])


@router.get("/{stream_id}", response_model=StreamItem)
async def get_stream(
    stream_id: int,
    keitaro: KeitaroClient = Depends(get_keitaro),
) -> StreamItem:
    raw = await keitaro.get_stream(stream_id)
    return map_stream(raw)


@router.put("/{stream_id}/offers", response_model=StreamItem)
async def update_stream_offers(
    stream_id: int,
    body: UpdateOffersRequest,
    keitaro: KeitaroClient = Depends(get_keitaro),
) -> StreamItem:
    service = StreamService(keitaro)
    updated = await service.update_offers(
        UpdateOffersCommand(
            stream_id=stream_id,
            offers=[{"offer_id": o.offer_id, "share": o.share} for o in body.offers],
            base_fingerprint=body.base_fingerprint,
        )
    )
    return map_stream(updated)
