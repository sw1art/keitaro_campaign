"""Worker: campaign.create message handler (idempotent saga runner)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.application.errors import PermanentError, RetryableError
from app.application.services.campaign_service import CampaignCreationService, utcnow
from app.config import Settings
from app.domain.entities import Operation
from app.infrastructure.keitaro import KeitaroClient
from app.infrastructure.logging import get_logger
from app.infrastructure.messaging import topology
from app.infrastructure.repositories import Repositories, SqlOperationRepository

logger = get_logger("worker.handler")

# Handler outcomes, mapped by the consumer to broker actions.
ACK = "ack"
RETRY = "retry"
DEAD_LETTER = "dead_letter"

_PARTIAL_KEYS = ("keitaro_campaign_id", "google_stream_id", "offer_stream_id")


def _has_partial_result(result: dict | None) -> bool:
    return bool(result) and any(result.get(k) for k in _PARTIAL_KEYS)


class CampaignCreateHandler:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        keitaro: KeitaroClient,
        settings: Settings,
    ) -> None:
        self.session_factory = session_factory
        self.keitaro = keitaro
        self.settings = settings

    async def handle(self, message: dict[str, Any]) -> str:
        raw_id = message.get("operation_id")
        try:
            operation_id = UUID(str(raw_id))
        except (TypeError, ValueError, AttributeError):
            logger.error("Malformed message, no valid operation_id: %r", raw_id)
            return DEAD_LETTER

        async with self.session_factory() as session:
            repos = Repositories(session)
            operation = await repos.operations.get(operation_id)
            if operation is None:
                logger.warning("Operation %s not found; dropping message", operation_id)
                return ACK
            if operation.status == "completed":
                return ACK  # idempotent: already done

            operation.status = "processing"
            operation.attempts += 1
            if operation.started_at is None:
                operation.started_at = utcnow()
            await repos.operations.save(operation)
            await session.commit()

            service = CampaignCreationService(
                self.keitaro,
                self.settings,
                repos.campaigns,
                repos.operations,
                repos.audit,
                commit=session.commit,
            )
            try:
                await service.create(operation)
            except RetryableError as exc:
                operation = await repos.operations.get(operation_id)
                if operation is not None and operation.attempts >= topology.MAX_ATTEMPTS:
                    status = (
                        "partially_failed" if _has_partial_result(operation.result) else "failed"
                    )
                    await self._fail(
                        repos.operations,
                        operation,
                        exc,
                        code="KEITARO_OPERATION_FAILED",
                        status=status,
                    )
                    await session.commit()
                    return DEAD_LETTER
                if operation is not None:
                    operation.status = "pending"
                    await repos.operations.save(operation)
                    await session.commit()
                logger.warning(
                    "Retry scheduled for %s (attempt %s): %s",
                    operation_id,
                    operation.attempts if operation else "?",
                    exc,
                )
                return RETRY
            except PermanentError as exc:
                operation = await repos.operations.get(operation_id)
                if operation is not None:
                    status = (
                        "needs_attention" if _has_partial_result(operation.result) else "failed"
                    )
                    await self._fail(
                        repos.operations,
                        operation,
                        exc,
                        code="KEITARO_OPERATION_FAILED",
                        status=status,
                    )
                    await session.commit()
                return DEAD_LETTER
            except Exception as exc:  # noqa: BLE001 - last resort
                logger.exception("Unexpected error processing %s", operation_id)
                operation = await repos.operations.get(operation_id)
                if operation is not None:
                    status = (
                        "needs_attention" if _has_partial_result(operation.result) else "failed"
                    )
                    await self._fail(
                        repos.operations, operation, exc, code="INTERNAL_ERROR", status=status
                    )
                    await session.commit()
                return DEAD_LETTER

            operation = await repos.operations.get(operation_id)
            if operation is not None:
                operation.status = "completed"
                operation.completed_at = utcnow()
                operation.finished_at = utcnow()
                await repos.operations.save(operation)
                await session.commit()
            return ACK

    @staticmethod
    async def _fail(
        operations: SqlOperationRepository,
        operation: Operation,
        exc: Exception,
        *,
        code: str,
        status: str,
    ) -> None:
        operation.status = status
        message = str(exc) or "Operation failed"
        operation.error = {"code": code, "message": message}
        now = utcnow()
        operation.completed_at = now
        operation.finished_at = now
        await operations.save(operation)
