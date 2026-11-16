"""Stream/offer editing use case."""

from __future__ import annotations

from app.application.dto import UpdateOffersCommand
from app.application.errors import KeitaroApiError
from app.application.interfaces import KeitaroClientProtocol
from app.application.services import campaign_builder
from app.domain import value_objects
from app.domain.exceptions import ConflictError, NotFoundError, ValidationError


class StreamService:
    """Edits offers/shares of an existing stream via a full PUT (no settings lost)."""

    def __init__(self, keitaro: KeitaroClientProtocol) -> None:
        self.keitaro = keitaro

    async def update_offers(self, cmd: UpdateOffersCommand) -> dict:
        offers = value_objects.validate_offer_shares(cmd.offers, require_at_least_one=True)

        # Validate offers exist and are active (bypass cache to re-check live state).
        all_offers = await self.keitaro.get_offers(fresh=True)
        offers_by_id = {o["id"]: o for o in all_offers}
        for entry in offers:
            offer = offers_by_id.get(entry["offer_id"])
            if offer is None:
                raise ValidationError(f"Offer {entry['offer_id']} not found in Keitaro.")
            if offer.get("state") != "active":
                raise ValidationError(f"Offer {entry['offer_id']} is not active.")

        # Re-fetch the freshest stream right before the update so a full PUT
        # cannot clobber concurrent changes to other fields.
        try:
            stream = await self.keitaro.get_stream(cmd.stream_id)
        except KeitaroApiError as exc:
            if exc.status_code == 404:
                raise NotFoundError(f"Stream {cmd.stream_id} not found.") from exc
            raise

        # Optimistic concurrency: detect changes made after the client loaded the stream.
        if cmd.base_fingerprint is not None:
            current = value_objects.offers_fingerprint(
                [
                    {"offer_id": o.get("offer_id"), "share": o.get("share")}
                    for o in (stream.get("offers") or [])
                ]
            )
            if current != cmd.base_fingerprint:
                raise ConflictError(
                    "The stream was modified by someone else. Reload the campaign and retry."
                )

        payload = campaign_builder.build_stream_update_payload(stream)
        payload["offers"] = [
            {"offer_id": entry["offer_id"], "share": entry["share"], "state": "active"}
            for entry in offers
        ]

        await self.keitaro.update_stream(cmd.stream_id, payload)

        # Verify the actual state after update.
        try:
            return await self.keitaro.get_stream(cmd.stream_id)
        except KeitaroApiError as exc:
            if exc.status_code == 404:
                raise NotFoundError(f"Stream {cmd.stream_id} not found after update.") from exc
            raise
