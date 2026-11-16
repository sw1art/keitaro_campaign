"""Application-level errors (cross-layer, framework-agnostic)."""

from __future__ import annotations


class KeitaroApiError(Exception):
    """Raised by the Keitaro client on a non-2xx HTTP response."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class KeitaroUnavailableError(KeitaroApiError):
    """Keitaro is unreachable (network error / timeout)."""


class RetryableError(Exception):
    """Temporary failure — the operation should be retried later."""


class PermanentError(Exception):
    """Permanent failure — retrying will not help."""
