"""Campaign creation orchestration (use case)."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.application.dto import CreateCampaignCommand
from app.application.errors import KeitaroApiError, PermanentError, RetryableError
from app.application.interfaces import KeitaroClientProtocol
from app.application.services import campaign_builder
from app.config import Settings
from app.domain import value_objects
from app.domain.entities import AuditLogEntry, Campaign, Operation
from app.domain.exceptions import ValidationError
from app.domain.repositories import (
    AuditRepository,
    CampaignRepository,
    OperationRepository,
)

logger = logging.getLogger(__name__)

CommitFn = Callable[[], Awaitable[None]]


def utcnow() -> datetime:
    return datetime.now(UTC)


def classify_keitaro_error(exc: KeitaroApiError) -> Exception:
    """Map a Keitaro API error to a retryable or permanent error."""
    if exc.status_code is None or exc.status_code >= 500 or exc.status_code == 429:
        return RetryableError(str(exc))
    return PermanentError(str(exc))


class CampaignCreationService:
    """Creates a Keitaro campaign with two flows. Idempotent and resumable.

    Progress is committed to ``operation.result`` after each step, so a retried
    message reuses already-created entities instead of duplicating them.
    """

    def __init__(
        self,
        keitaro: KeitaroClientProtocol,
        settings: Settings,
        campaigns: CampaignRepository,
        operations: OperationRepository,
        audit: AuditRepository,
        commit: CommitFn,
    ) -> None:
        self.keitaro = keitaro
        self.settings = settings
        self.campaigns = campaigns
        self.operations = operations
        self.audit = audit
        self.commit = commit

    async def validate_input(
        self, cmd: CreateCampaignCommand, valid_geo_codes: set[str] | None = None
    ) -> list[int]:
        """Validate a create command against the live Keitaro references."""
        value_objects.validate_geo_codes(cmd.geo, valid_codes=valid_geo_codes)

        if not cmd.offer_ids:
            raise ValidationError("At least one offer must be selected.")

        offers = await self.keitaro.get_offers()
        offers_by_id = {o["id"]: o for o in offers}
        for offer_id in cmd.offer_ids:
            offer = offers_by_id.get(offer_id)
            if offer is None:
                raise ValidationError(f"Offer {offer_id} not found in Keitaro.")
            if offer.get("state") != "active":
                raise ValidationError(f"Offer {offer_id} is not active.")

        domains = await self.keitaro.get_domains()
        domain = next((d for d in domains if d["id"] == cmd.domain_id), None)
        if domain is None:
            raise ValidationError(f"Domain {cmd.domain_id} not found in Keitaro.")
        if domain.get("state") != "active":
            raise ValidationError(f"Domain {cmd.domain_id} is not active.")

        return list(dict.fromkeys(cmd.offer_ids))

    async def create(self, operation: Operation) -> Operation:
        """Execute (or resume) campaign creation.

        Raises RetryableError for transient problems and PermanentError for
        non-recoverable problems.
        """
        cmd = CreateCampaignCommand(**operation.payload)
        result: dict = dict(operation.result or {})

        # 1. Campaign
        keitaro_campaign_id = result.get("keitaro_campaign_id")
        if not keitaro_campaign_id:
            alias = f"adrobot-{operation.id.hex[:12]}"
            created = await self._call(
                self.keitaro.create_campaign,
                campaign_builder.build_campaign_payload(
                    cmd.name,
                    cmd.domain_id,
                    alias=alias,
                    group_id=self.settings.keitaro_group_id,
                    traffic_source_id=self.settings.keitaro_traffic_source_id,
                ),
            )
            keitaro_campaign_id = int(created["id"])
            result["keitaro_campaign_id"] = keitaro_campaign_id
            operation.result = result
            await self.operations.save(operation)
            await self._audit(operation, "campaign.create", "campaign", keitaro_campaign_id)
            await self.commit()

        # 2. Google Redirect flow
        google_stream_id = result.get("google_stream_id")
        if not google_stream_id:
            created = await self._call(
                self.keitaro.create_stream,
                campaign_builder.build_google_stream_payload(
                    keitaro_campaign_id,
                    cmd.geo,
                    google_url=self.settings.google_redirect_url,
                ),
            )
            google_stream_id = int(created["id"])
            result["google_stream_id"] = google_stream_id
            operation.result = result
            await self.operations.save(operation)
            await self._audit(operation, "stream.create", "stream", google_stream_id)
            await self.commit()

        # 3. Offer Flow
        offer_stream_id = result.get("offer_stream_id")
        if not offer_stream_id:
            offers = [{"offer_id": oid} for oid in cmd.offer_ids]
            created = await self._call(
                self.keitaro.create_stream,
                campaign_builder.build_offer_stream_payload(
                    keitaro_campaign_id,
                    offers,
                    default_share=self.settings.default_offer_share,
                ),
            )
            offer_stream_id = int(created["id"])
            result["offer_stream_id"] = offer_stream_id
            operation.result = result
            await self.operations.save(operation)
            await self._audit(operation, "stream.create", "stream", offer_stream_id)
            await self.commit()

        # 4. Verify the created configuration
        await self._verify(keitaro_campaign_id, cmd, google_stream_id, offer_stream_id)

        # 5. Persist local campaign registry
        local = await self.campaigns.get_by_keitaro_id(keitaro_campaign_id)
        if local is None:
            local = Campaign(
                id=uuid4(),
                keitaro_id=keitaro_campaign_id,
                name=cmd.name,
                status="active",
            )
            local = await self.campaigns.add(local)
        operation.campaign_id = local.id
        operation.keitaro_campaign_id = keitaro_campaign_id
        await self.operations.save(operation)
        await self.commit()

        return operation

    async def _call(self, fn: Callable[..., Awaitable[Any]], *args: Any) -> Any:
        try:
            return await fn(*args)
        except KeitaroApiError as exc:
            raise classify_keitaro_error(exc) from exc

    async def _verify(
        self,
        campaign_id: int,
        cmd: CreateCampaignCommand,
        google_stream_id: int,
        offer_stream_id: int,
    ) -> None:
        try:
            streams = await self.keitaro.get_streams(campaign_id)
        except KeitaroApiError as exc:
            raise classify_keitaro_error(exc) from exc

        by_id = {s["id"]: s for s in streams}

        google = by_id.get(google_stream_id)
        if google is None:
            raise RetryableError(f"Google Redirect stream {google_stream_id} not visible yet.")
        filters = google.get("filters") or []
        country_filter = next((f for f in filters if f.get("name") == "country"), None)
        if country_filter is None or sorted(country_filter.get("payload") or []) != sorted(cmd.geo):
            raise PermanentError(
                "Google Redirect GEO filter does not match the requested GEO list."
            )

        offer_flow = by_id.get(offer_stream_id)
        if offer_flow is None:
            raise RetryableError(f"Offer Flow stream {offer_stream_id} not visible yet.")
        offer_ids = [o.get("offer_id") for o in (offer_flow.get("offers") or [])]
        if sorted(offer_ids) != sorted(cmd.offer_ids):
            raise PermanentError("Offer Flow offers do not match the requested offers.")
        for o in offer_flow.get("offers") or []:
            if int(o.get("share", 0)) != self.settings.default_offer_share:
                raise PermanentError("Offer Flow shares are not the expected initial value.")

    async def _audit(
        self, operation: Operation, action: str, entity_type: str, entity_id: int
    ) -> None:
        try:
            await self.audit.add(
                AuditLogEntry(
                    id=uuid4(),
                    operation_id=operation.id,
                    action=action,
                    entity_type=entity_type,
                    entity_id=str(entity_id),
                    details={"keitaro_id": entity_id},
                )
            )
        except Exception:  # audit must never break the flow
            logger.exception("Failed to write audit log")
