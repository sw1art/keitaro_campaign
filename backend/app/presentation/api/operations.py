"""Operations API router."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.domain.exceptions import NotFoundError
from app.infrastructure.repositories import Repositories
from app.presentation.api.mappers import map_operation
from app.presentation.dependencies import get_repositories
from app.presentation.schemas import OperationItem, OperationListResponse

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
