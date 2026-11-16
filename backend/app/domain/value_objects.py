"""Pure domain value objects and business rules (no framework dependencies)."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from app.domain.exceptions import BusinessRuleError, ValidationError

_GEO_RE = re.compile(r"^[A-Z]{2}$")


def calculate_distribution(offers: Sequence[Mapping[str, Any]]) -> dict[int, float]:
    """Compute traffic share percentages from offer `share` weights.

    percentage = share / sum(shares) * 100, rounded to 2 decimals (display only).
    Returns an empty mapping when there are no offers or the total is <= 0.
    """
    if not offers:
        return {}
    total = sum(float(o["share"]) for o in offers)
    if total <= 0:
        return {}
    return {int(o["offer_id"]): round(float(o["share"]) / total * 100.0, 2) for o in offers}


def normalize_geo_code(value: Any) -> str:
    """Normalize and validate a single ISO 3166-1 alpha-2 code."""
    if not isinstance(value, str):
        raise ValidationError(f"Invalid GEO code: {value!r} is not a string")
    code = value.strip().upper()
    if not _GEO_RE.match(code):
        raise ValidationError(
            f"Invalid GEO code: {value!r}. Expected ISO 3166-1 alpha-2 (e.g. AU)."
        )
    return code


def validate_geo_codes(codes: Sequence[Any], *, valid_codes: set[str] | None = None) -> list[str]:
    """Validate a list of GEO codes: non-empty, unique, well-formed, known.

    `valid_codes` optionally restricts values to a known set (ISO dictionary).
    """
    if not codes:
        raise ValidationError("At least one GEO must be selected.")
    normalized: list[str] = []
    for raw in codes:
        code = normalize_geo_code(raw)
        if valid_codes is not None and code not in valid_codes:
            raise ValidationError(f"Unknown GEO code: {code}.")
        if code in normalized:
            raise ValidationError(f"Duplicate GEO code: {code}.")
        normalized.append(code)
    return normalized


def validate_offer_shares(
    offers: Sequence[Mapping[str, Any]], *, require_at_least_one: bool = True
) -> list[dict[str, Any]]:
    """Validate offer entries.

    Verified against the live Keitaro: ``share`` must be an integer in (0, 100].
    """
    if require_at_least_one and not offers:
        raise BusinessRuleError("The offer list must not be empty.")
    seen: set[int] = set()
    result: list[dict[str, Any]] = []
    for raw in offers:
        offer_id = raw.get("offer_id")
        share = raw.get("share")
        if not isinstance(offer_id, int) or offer_id <= 0:
            raise ValidationError(f"Invalid offer_id: {offer_id!r}.")
        if offer_id in seen:
            raise ValidationError(f"Duplicate offer_id: {offer_id}.")
        if isinstance(share, bool) or not isinstance(share, int):
            raise ValidationError(f"Share for offer {offer_id} must be an integer.")
        if share <= 0:
            raise ValidationError(f"Share for offer {offer_id} must be greater than zero.")
        if share > 100:
            raise ValidationError(f"Share for offer {offer_id} must not exceed 100.")
        seen.add(offer_id)
        result.append({"offer_id": offer_id, "share": share})
    return result


def offers_fingerprint(offers: Sequence[Mapping[str, Any]]) -> str:
    """Stable hash of the (offer_id, share) pairs, order-insensitive.

    Used for optimistic concurrency: the client sends the fingerprint of the
    state it based its edit on; a mismatch means the stream changed meanwhile.
    """
    canon = sorted((int(o["offer_id"]), o["share"]) for o in offers)
    payload = json.dumps(canon, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()
