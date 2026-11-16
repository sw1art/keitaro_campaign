"""Request-scoped context (correlation id)."""

from __future__ import annotations

import contextvars
from uuid import uuid4

_correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    return _correlation_id.get() or ""


def set_correlation_id(value: str | None) -> str:
    cid = (value or "").strip() or str(uuid4())
    _correlation_id.set(cid)
    return cid
