"""Unit tests: in-memory rate limiter."""
import pytest

from app.presentation.middleware import _RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_within_limit():
    limiter = _RateLimiter(per_minute=3)
    assert await limiter.hit("ip-a") is True
    assert await limiter.hit("ip-a") is True
    assert await limiter.hit("ip-a") is True
    assert await limiter.hit("ip-a") is False  # 4th request exceeds the window


@pytest.mark.asyncio
async def test_rate_limiter_is_per_client():
    limiter = _RateLimiter(per_minute=1)
    assert await limiter.hit("ip-a") is True
    assert await limiter.hit("ip-a") is False
    assert await limiter.hit("ip-b") is True
