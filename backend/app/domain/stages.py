"""Campaign creation saga stages and progress mapping."""

from __future__ import annotations

STAGE_PENDING = "pending"
STAGE_CREATING_CAMPAIGN = "creating_campaign"
STAGE_CREATING_GOOGLE_STREAM = "creating_google_stream"
STAGE_CREATING_OFFER_STREAM = "creating_offer_stream"
STAGE_VERIFYING = "verifying"
STAGE_COMPLETED = "completed"

STAGES = (
    STAGE_CREATING_CAMPAIGN,
    STAGE_CREATING_GOOGLE_STREAM,
    STAGE_CREATING_OFFER_STREAM,
    STAGE_VERIFYING,
    STAGE_COMPLETED,
)

STAGE_PROGRESS: dict[str, int] = {
    STAGE_PENDING: 0,
    STAGE_CREATING_CAMPAIGN: 20,
    STAGE_CREATING_GOOGLE_STREAM: 40,
    STAGE_CREATING_OFFER_STREAM: 60,
    STAGE_VERIFYING: 80,
    STAGE_COMPLETED: 100,
}


def progress_for_stage(stage: str | None) -> int:
    return STAGE_PROGRESS.get(stage or STAGE_PENDING, 0)
