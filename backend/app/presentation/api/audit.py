"""Audit log API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.infrastructure.repositories import Repositories
from app.presentation.api.mappers import map_audit_log
from app.presentation.dependencies import get_repositories
from app.presentation.schemas import AuditLogListResponse

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    repos: Repositories = Depends(get_repositories),
) -> AuditLogListResponse:
    items, total = await repos.audit.list(limit=page_size, offset=(page - 1) * page_size)
    return AuditLogListResponse(
        items=[map_audit_log(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
    )
