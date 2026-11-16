"""HTTP middleware: correlation id, security headers, request logging, rate limit."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from starlette.responses import Response

from app.config import Settings
from app.infrastructure.logging import get_logger
from app.presentation.context import set_correlation_id

logger = get_logger("app.access")

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "X-Request-ID": "",  # filled per-request
}


async def request_context_middleware(request: Request, call_next) -> Response:
    cid = set_correlation_id(
        request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
    )
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 1)

    headers = dict(_SECURITY_HEADERS)
    headers["X-Request-ID"] = cid
    for name, value in headers.items():
        response.headers.setdefault(name, value)

    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration_ms,
        correlation_id=cid,
    )
    return response


class _RateLimiter:
    """Simple in-memory sliding-window limiter keyed by client IP."""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._windows: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def hit(self, key: str) -> bool:
        """Return True if the request is allowed, False if it should be rejected."""
        async with self._lock:
            now = time.monotonic()
            window = self._windows[key]
            while window and now - window[0] > 60.0:
                window.popleft()
            if len(window) >= self.per_minute:
                return False
            window.append(now)
            return True


_limiter: _RateLimiter | None = None


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def rate_limit(request: Request) -> None:
    """Reject requests that exceed the configured per-IP rate limit."""
    global _limiter
    settings: Settings = request.app.state.settings
    if not settings.rate_limit_enabled:
        return
    if _limiter is None or _limiter.per_minute != settings.rate_limit_per_minute:
        _limiter = _RateLimiter(settings.rate_limit_per_minute)
    if not await _limiter.hit(_client_ip(request)):
        raise HTTPException(
            status_code=429,
            detail={"code": "RATE_LIMITED", "message": "Too many requests, slow down."},
        )
