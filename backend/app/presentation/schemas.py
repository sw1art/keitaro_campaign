"""Request/response Pydantic schemas for the AdRobot API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------- campaigns
class CreateCampaignRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    geo: list[str] = Field(min_length=1)
    offer_ids: list[int] = Field(min_length=1)
    domain_id: int = Field(gt=0)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        return v

    @field_validator("geo")
    @classmethod
    def _normalize_geo(cls, v: list[str]) -> list[str]:
        out: list[str] = []
        for code in v:
            c = code.strip().upper()
            if c not in out:
                out.append(c)
        if not out:
            raise ValueError("geo must not be empty")
        return out

    @field_validator("offer_ids")
    @classmethod
    def _normalize_offer_ids(cls, v: list[int]) -> list[int]:
        out: list[int] = []
        for oid in v:
            if oid not in out:
                out.append(oid)
        if not out:
            raise ValueError("offer_ids must not be empty")
        return out


class CampaignItem(BaseModel):
    id: int
    name: str
    state: str | None = None
    alias: str | None = None
    domain: str | None = None
    domain_id: int | None = None
    traffic_source_id: int | None = None
    traffic_source: str | None = None
    group_id: int | None = None
    group: str | None = None
    cost_type: str | None = None
    cost_value: float | None = None
    cost_currency: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CampaignListResponse(BaseModel):
    items: list[CampaignItem]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------- offers
class OfferItem(BaseModel):
    id: int
    name: str
    state: str | None = None
    country: list[str] = Field(default_factory=list)
    group: str | None = None
    affiliate_network: str | None = None


class OfferListResponse(BaseModel):
    items: list[OfferItem]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------- domains / sources / geo
class DomainItem(BaseModel):
    id: int
    name: str
    state: str | None = None
    is_ssl: bool | None = None
    ssl_status: str | None = None


class DomainListResponse(BaseModel):
    items: list[DomainItem]


class TrafficSourceItem(BaseModel):
    id: int
    name: str
    state: str | None = None


class TrafficSourceListResponse(BaseModel):
    items: list[TrafficSourceItem]


class GeoItem(BaseModel):
    code: str
    name: str


class GeoListResponse(BaseModel):
    items: list[GeoItem]


# ---------------------------------------------------------------- streams
class StreamFilter(BaseModel):
    name: str | None = None
    mode: str | None = None
    payload: list[Any] = Field(default_factory=list)


class StreamOffer(BaseModel):
    offer_id: int
    state: str | None = None
    share: float = 0


class StreamItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    type: str | None = None
    name: str | None = None
    campaign_id: int | None = None
    position: int | None = None
    state: str | None = None
    flow_schema: str | None = Field(default=None, alias="schema")
    action_type: str | None = None
    action_payload: str | None = None
    collect_clicks: bool | None = None
    filter_or: bool | None = None
    weight: float | None = None
    offer_selection: str | None = None
    filters: list[StreamFilter] = Field(default_factory=list)
    offers: list[StreamOffer] = Field(default_factory=list)
    landings: list[Any] = Field(default_factory=list)
    # Fingerprint of the current offers (for optimistic concurrency).
    fingerprint: str | None = None


class StreamListResponse(BaseModel):
    items: list[StreamItem]


class OfferShare(BaseModel):
    offer_id: int = Field(gt=0)
    share: int = Field(gt=0, le=100)


class UpdateOffersRequest(BaseModel):
    offers: list[OfferShare] = Field(min_length=1)
    # Fingerprint of the offers state the client based its edit on (optimistic
    # concurrency). Optional for backward compatibility.
    base_fingerprint: str | None = None


# ---------------------------------------------------------------- operations
class ErrorDetail(BaseModel):
    code: str
    message: str


class OperationItem(BaseModel):
    operation_id: str
    type: str
    status: Literal[
        "pending", "processing", "completed", "failed", "partially_failed", "needs_attention"
    ]
    campaign_id: int | None = None
    current_stage: str | None = None
    progress: int = 0
    error: ErrorDetail | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class OperationListResponse(BaseModel):
    items: list[OperationItem]
    total: int
    page: int
    page_size: int


class CreateCampaignAccepted(BaseModel):
    operation_id: str
    status: str
    message: str
    warnings: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ---------------------------------------------------------------- audit log
class AuditLogItem(BaseModel):
    id: str
    operation_id: str | None = None
    action: str
    entity_type: str
    entity_id: str
    details: dict | None = None
    created_at: datetime | None = None


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItem]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------- dashboard
class DashboardResponse(BaseModel):
    campaigns_count: int
    recent_campaigns: list[CampaignItem]
    operations_total: int
    operations_completed: int
    operations_failed: int
    recent_operations: list[OperationItem]
