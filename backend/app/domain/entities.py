"""Domain entities (plain dataclasses, persistence-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

OperationStatuses = ("pending", "processing", "completed", "failed")


@dataclass
class Campaign:
    id: UUID
    name: str
    status: str = "creating"
    keitaro_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Operation:
    id: UUID
    type: str
    status: str = "pending"
    payload: dict = field(default_factory=dict)
    result: dict | None = None
    error: dict | None = None
    attempts: int = 0
    campaign_id: UUID | None = None
    keitaro_campaign_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class OutboxEvent:
    id: UUID
    event_type: str
    payload: dict = field(default_factory=dict)
    status: str = "pending"
    attempts: int = 0
    created_at: datetime | None = None
    published_at: datetime | None = None


@dataclass
class AuditLogEntry:
    id: UUID
    action: str
    entity_type: str
    entity_id: str
    operation_id: UUID | None = None
    details: dict | None = None
    created_at: datetime | None = None
