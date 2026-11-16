"""Application DTOs (commands / results)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CreateCampaignCommand:
    name: str
    geo: list[str]
    offer_ids: list[int]
    domain_id: int


@dataclass
class UpdateOffersCommand:
    stream_id: int
    offers: list[dict[str, Any]] = field(default_factory=list)
    base_fingerprint: str | None = None
