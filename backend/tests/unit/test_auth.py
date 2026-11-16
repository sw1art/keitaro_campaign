"""Unit tests: optional API token auth."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.config import Settings
from app.presentation.dependencies import require_api_token


def _request(headers: dict[str, str], token: str) -> Request:
    app = SimpleNamespace(state=SimpleNamespace(settings=Settings(adrobot_api_token=token)))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "app": app,
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_auth_rejects_missing_token():
    with pytest.raises(HTTPException) as exc_info:
        await require_api_token(_request({}, "secret"))
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_rejects_wrong_token():
    with pytest.raises(HTTPException):
        await require_api_token(_request({"X-Api-Key": "wrong"}, "secret"))


@pytest.mark.asyncio
async def test_auth_accepts_x_api_key():
    await require_api_token(_request({"X-Api-Key": "secret"}, "secret"))


@pytest.mark.asyncio
async def test_auth_accepts_bearer():
    await require_api_token(_request({"Authorization": "Bearer secret"}, "secret"))


@pytest.mark.asyncio
async def test_auth_disabled_when_token_empty():
    await require_api_token(_request({}, ""))
