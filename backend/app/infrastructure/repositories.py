"""SQLAlchemy repository implementations of the domain repository ports."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import AuditLogEntry, Campaign, Operation, OutboxEvent
from app.infrastructure.database import models


def _utcnow() -> datetime:
    return datetime.now(UTC)


class SqlCampaignRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, campaign: Campaign) -> Campaign:
        model = models.Campaign(
            id=campaign.id,
            keitaro_id=campaign.keitaro_id,
            name=campaign.name,
            status=campaign.status,
            created_at=campaign.created_at or _utcnow(),
            updated_at=campaign.updated_at or _utcnow(),
        )
        self.session.add(model)
        await self.session.flush()
        campaign.created_at = model.created_at
        campaign.updated_at = model.updated_at
        return campaign

    async def get(self, campaign_id: UUID) -> Campaign | None:
        model = await self.session.get(models.Campaign, campaign_id)
        return self._to_entity(model) if model else None

    async def get_by_keitaro_id(self, keitaro_id: int) -> Campaign | None:
        res = await self.session.execute(
            select(models.Campaign).where(models.Campaign.keitaro_id == keitaro_id)
        )
        return self._to_entity(res.scalar_one_or_none())

    async def save(self, campaign: Campaign) -> None:
        model = await self.session.get(models.Campaign, campaign.id)
        if model is None:
            return
        model.name = campaign.name
        model.status = campaign.status
        model.keitaro_id = campaign.keitaro_id
        model.updated_at = _utcnow()
        await self.session.flush()

    @staticmethod
    def _to_entity(model: models.Campaign | None) -> Campaign | None:
        if model is None:
            return None
        return Campaign(
            id=model.id,
            keitaro_id=model.keitaro_id,
            name=model.name,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SqlOperationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, operation: Operation) -> Operation:
        model = models.Operation(
            id=operation.id,
            type=operation.type,
            status=operation.status,
            campaign_id=operation.campaign_id,
            keitaro_campaign_id=operation.keitaro_campaign_id,
            payload=operation.payload,
            result=operation.result,
            error=operation.error,
            attempts=operation.attempts,
            current_stage=operation.current_stage,
            progress=operation.progress,
            started_at=operation.started_at,
            finished_at=operation.finished_at,
            created_at=operation.created_at or _utcnow(),
            updated_at=operation.updated_at or _utcnow(),
            completed_at=operation.completed_at,
        )
        self.session.add(model)
        await self.session.flush()
        operation.created_at = model.created_at
        operation.updated_at = model.updated_at
        return operation

    async def get(self, operation_id: UUID) -> Operation | None:
        model = await self.session.get(models.Operation, operation_id)
        return self._to_entity(model)

    async def save(self, operation: Operation) -> None:
        model = await self.session.get(models.Operation, operation.id)
        if model is None:
            return
        model.status = operation.status
        model.campaign_id = operation.campaign_id
        model.keitaro_campaign_id = operation.keitaro_campaign_id
        model.payload = operation.payload
        model.result = operation.result
        model.error = operation.error
        model.attempts = operation.attempts
        model.current_stage = operation.current_stage
        model.progress = operation.progress
        model.started_at = operation.started_at
        model.finished_at = operation.finished_at
        model.completed_at = operation.completed_at
        model.updated_at = _utcnow()
        await self.session.flush()

    async def get_by_keitaro_campaign_id(self, keitaro_id: int) -> Operation | None:
        res = await self.session.execute(
            select(models.Operation).where(models.Operation.keitaro_campaign_id == keitaro_id)
        )
        return self._to_entity(res.scalar_one_or_none())

    async def list(self, *, limit: int, offset: int) -> tuple[list[Operation], int]:
        total = await self.session.scalar(select(func.count()).select_from(models.Operation))
        res = await self.session.execute(
            select(models.Operation)
            .order_by(models.Operation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_entity(m) for m in res.scalars().all()], int(total or 0)

    async def counts(self) -> dict[str, int]:
        res = await self.session.execute(
            select(models.Operation.status, func.count()).group_by(models.Operation.status)
        )
        return {status: int(count) for status, count in res.all()}

    @staticmethod
    def _to_entity(model: models.Operation | None) -> Operation | None:
        if model is None:
            return None
        return Operation(
            id=model.id,
            type=model.type,
            status=model.status,
            campaign_id=model.campaign_id,
            keitaro_campaign_id=model.keitaro_campaign_id,
            payload=model.payload or {},
            result=model.result,
            error=model.error,
            attempts=model.attempts,
            current_stage=model.current_stage,
            progress=model.progress or 0,
            started_at=model.started_at,
            finished_at=model.finished_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            completed_at=model.completed_at,
        )


class SqlOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, event: OutboxEvent) -> OutboxEvent:
        model = models.OutboxEvent(
            id=event.id,
            event_type=event.event_type,
            payload=event.payload,
            status=event.status,
            attempts=event.attempts,
            created_at=event.created_at or _utcnow(),
        )
        self.session.add(model)
        await self.session.flush()
        event.created_at = model.created_at
        return event

    async def list_pending(self, *, limit: int) -> list[OutboxEvent]:
        res = await self.session.execute(
            select(models.OutboxEvent)
            .where(models.OutboxEvent.status == "pending")
            .order_by(models.OutboxEvent.created_at.asc())
            .limit(limit)
        )
        return [self._to_entity(m) for m in res.scalars().all()]

    async def mark_published(self, event_id: UUID) -> None:
        model = await self.session.get(models.OutboxEvent, event_id)
        if model is None:
            return
        model.status = "published"
        model.published_at = _utcnow()
        await self.session.flush()

    async def bump_attempts(self, event_id: UUID) -> None:
        model = await self.session.get(models.OutboxEvent, event_id)
        if model is None:
            return
        model.attempts = (model.attempts or 0) + 1
        await self.session.flush()

    @staticmethod
    def _to_entity(model: models.OutboxEvent) -> OutboxEvent:
        return OutboxEvent(
            id=model.id,
            event_type=model.event_type,
            payload=model.payload or {},
            status=model.status,
            attempts=model.attempts or 0,
            created_at=model.created_at,
            published_at=model.published_at,
        )


class SqlAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, entry: AuditLogEntry) -> AuditLogEntry:
        model = models.AuditLog(
            id=entry.id,
            operation_id=entry.operation_id,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            details=entry.details,
            created_at=entry.created_at or _utcnow(),
        )
        self.session.add(model)
        await self.session.flush()
        entry.created_at = model.created_at
        return entry

    async def list_by_operation(self, operation_id: UUID) -> list[AuditLogEntry]:
        res = await self.session.execute(
            select(models.AuditLog)
            .where(models.AuditLog.operation_id == operation_id)
            .order_by(models.AuditLog.created_at.asc())
        )
        return [self._to_entity(m) for m in res.scalars().all()]

    async def list(self, *, limit: int, offset: int) -> tuple[list[AuditLogEntry], int]:
        total = await self.session.scalar(select(func.count()).select_from(models.AuditLog))
        res = await self.session.execute(
            select(models.AuditLog)
            .order_by(models.AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_entity(m) for m in res.scalars().all()], int(total or 0)

    @staticmethod
    def _to_entity(model: models.AuditLog) -> AuditLogEntry:
        return AuditLogEntry(
            id=model.id,
            operation_id=model.operation_id,
            action=model.action,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            details=model.details,
            created_at=model.created_at,
        )


class Repositories:
    """Bundle of repositories bound to a single session (per request / task)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.campaigns = SqlCampaignRepository(session)
        self.operations = SqlOperationRepository(session)
        self.outbox = SqlOutboxRepository(session)
        self.audit = SqlAuditRepository(session)
