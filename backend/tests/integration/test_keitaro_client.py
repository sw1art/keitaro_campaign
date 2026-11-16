"""Integration tests for KeitaroClient using a mocked HTTP transport."""
from __future__ import annotations

import httpx
import pytest

from app.application.errors import KeitaroApiError, KeitaroUnavailableError
from app.infrastructure.keitaro.client import KeitaroClient


def make_client(handler, settings):
    return KeitaroClient(settings, transport=httpx.MockTransport(handler))


async def test_get_campaigns_ok(settings):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Api-Key"] == "test-token"
        return httpx.Response(200, json=[{"id": 1, "name": "A"}])

    client = make_client(handler, settings)
    result = await client.get_campaigns()
    assert result == [{"id": 1, "name": "A"}]
    await client.aclose()


async def test_single_object_collection_is_normalized(settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": 1813, "name": "kylovoa.com"})

    client = make_client(handler, settings)
    domains = await client.get_domains()
    assert domains == [{"id": 1813, "name": "kylovoa.com"}]
    await client.aclose()


async def test_4xx_raises_keitaro_api_error(settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="bad request")

    client = make_client(handler, settings)
    with pytest.raises(KeitaroApiError) as exc_info:
        await client.get_offers()
    assert exc_info.value.status_code == 400
    await client.aclose()


async def test_5xx_raises_after_retries(settings):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500)

    # max_retries=1 -> no retry
    client = make_client(handler, settings)
    with pytest.raises(KeitaroApiError):
        await client.get_stream_filters()
    assert calls["n"] == 1
    await client.aclose()


async def test_network_error_raises_unavailable(settings):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    client = make_client(handler, settings)
    with pytest.raises(KeitaroUnavailableError):
        await client.get_campaigns()
    await client.aclose()


async def test_post_is_not_retried_on_5xx(settings):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500)

    client = make_client(handler, settings)
    with pytest.raises(KeitaroApiError):
        await client.create_campaign({"name": "x"})
    assert calls["n"] == 1  # POST/PUT are never auto-retried
    await client.aclose()
