"""Operations API router."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query

from app.domain.entities import OutboxEvent
from app.domain.exceptions import ConflictError, NotFoundError
from app.infrastructure.messaging.outbox import build_event_message
from app.infrastructure.messaging.publisher import RabbitPublisher
from app.infrastructure.repositories import Repositories
from app.presentation.api.common import schedule_best_effort_publish
from app.presentation.api.mappers import map_audit_log, map_operation
from app.presentation.dependencies import (
    get_publisher,
    get_repositories,
    get_session_factory,
)
from app.presentation.schemas import (
    AuditLogListResponse,
    OperationItem,
    OperationListResponse,
)

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("", response_model=OperationListResponse)
async def list_operations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    repos: Repositories = Depends(get_repositories),
) -> OperationListResponse:
    items, total = await repos.operations.list(limit=page_size, offset=(page - 1) * page_size)
    return OperationListResponse(
        items=[map_operation(o) for o in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{operation_id}", response_model=OperationItem)
async def get_operation(
    operation_id: UUID,
    repos: Repositories = Depends(get_repositories),
) -> OperationItem:
    operation = await repos.operations.get(operation_id)
    if operation is None:
        raise NotFoundError(f"Operation {operation_id} not found.")
    return map_operation(operation)


@router.post("/{operation_id}/retry", response_model=OperationItem)
async def retry_operation(
    operation_id: UUID,
    repos: Repositories = Depends(get_repositories),
    publisher: RabbitPublisher = Depends(get_publisher),
) -> OperationItem:
    """Re-enqueue a failed operation (resumes from its partial result)."""
    operation = await repos.operations.get(operation_id)
    if operation is None:
        raise NotFoundError(f"Operation {operation_id} not found.")
    if operation.status != "failed":
        raise ConflictError("Only failed operations can be retried.")

    operation.status = "pending"
    operation.error = None
    operation.completed_at = None
    operation.attempts = 0
    await repos.operations.save(operation)

    event = OutboxEvent(
        id=uuid4(),
        event_type=operation.type,
        payload=build_event_message(operation.type, operation.id, operation.payload),
    )
    await repos.outbox.add(event)
    await repos.session.commit()

    schedule_best_effort_publish(get_session_factory(), publisher)
    return map_operation(operation)


@router.get("/{operation_id}/audit", response_model=AuditLogListResponse)
async def get_operation_audit(
    operation_id: UUID,
    repos: Repositories = Depends(get_repositories),
) -> AuditLogListResponse:
    entries = await repos.audit.list_by_operation(operation_id)
    return AuditLogListResponse(
        items=[map_audit_log(e) for e in entries],
        total=len(entries),
        page=1,
        page_size=len(entries) or 1,
    )
