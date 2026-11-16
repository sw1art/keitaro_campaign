"""Mapping helpers: Keitaro raw dicts -> API schemas."""
from __future__ import annotations

from typing import Any

from app.domain.entities import Operation
from app.presentation.schemas import CampaignItem, OfferItem, OperationItem, StreamItem


def map_operation(op: Operation) -> OperationItem:
    error = None
    if op.error:
        error = {"code": op.error.get("code", "OPERATION_FAILED"), "message": op.error.get("message", "")}
    return OperationItem(
        operation_id=str(op.id),
        type=op.type,
        status=op.status,
        campaign_id=op.keitaro_campaign_id,
        error=error,
        created_at=op.created_at,
        completed_at=op.completed_at,
    )


def map_campaign(raw: dict[str, Any], traffic_source_name: str | None = None) -> CampaignItem:
    return CampaignItem(
        id=raw.get("id"),
        name=raw.get("name") or "",
        state=raw.get("state"),
        alias=raw.get("alias"),
        domain=raw.get("domain"),
        domain_id=raw.get("domain_id"),
        traffic_source_id=raw.get("traffic_source_id"),
        traffic_source=traffic_source_name,
        group_id=raw.get("group_id"),
        group=raw.get("group"),
        cost_type=raw.get("cost_type"),
        cost_value=raw.get("cost_value"),
        cost_currency=raw.get("cost_currency"),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
    )


def map_offer(raw: dict[str, Any]) -> OfferItem:
    country = raw.get("country")
    if isinstance(country, str):
        country = [country] if country else []
    country = country or []
    affiliate = raw.get("affiliate_network")
    return OfferItem(
        id=raw["id"],
        name=raw.get("name") or str(raw["id"]),
        state=raw.get("state"),
        country=list(country),
        group=raw.get("group"),
        affiliate_network=str(affiliate) if affiliate is not None else None,
    )


def map_stream(raw: dict[str, Any]) -> StreamItem:
    return StreamItem(
        id=raw.get("id"),
        type=raw.get("type"),
        name=raw.get("name"),
        campaign_id=raw.get("campaign_id"),
        position=raw.get("position"),
        state=raw.get("state"),
        flow_schema=raw.get("schema"),
        action_type=raw.get("action_type"),
        action_payload=raw.get("action_payload"),
        collect_clicks=raw.get("collect_clicks"),
        filter_or=raw.get("filter_or"),
        weight=raw.get("weight"),
        offer_selection=raw.get("offer_selection"),
        filters=[
            {
                "name": f.get("name"),
                "mode": f.get("mode"),
                "payload": f.get("payload") or [],
            }
            for f in (raw.get("filters") or [])
        ],
        offers=[
            {
                "offer_id": o.get("offer_id"),
                "state": o.get("state"),
                "share": o.get("share") if o.get("share") is not None else 0,
            }
            for o in (raw.get("offers") or [])
        ],
        landings=raw.get("landings") or [],
    )
