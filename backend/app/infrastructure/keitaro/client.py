"""Keitaro admin API client (adapter)."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.application.errors import KeitaroApiError, KeitaroUnavailableError
from app.config import Settings

logger = logging.getLogger(__name__)


class KeitaroClient:
    """Centralized HTTP client for the Keitaro admin API.

    - Only this class talks to Keitaro (Task.md §4.1).
    - Never auto-retries POST/PUT (a timed-out write may have succeeded);
      the worker retries those idempotently instead.
    - GETs retry on transient errors (timeout / 5xx).
    """

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = settings.keitaro_base_url.rstrip("/")
        self._token = settings.keitaro_api_token
        self._timeout = settings.keitaro_timeout
        self._max_retries = max(1, settings.keitaro_max_retries)
        self._transport = transport
        self._client: httpx.AsyncClient | None = None
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_ttl = 300.0  # reference data TTL (5 minutes)

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={"Api-Key": self._token},
                timeout=self._timeout,
                transport=self._transport,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    # --- low-level request ---
    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        retry: bool,
    ) -> Any:
        attempts = self._max_retries if retry else 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                resp = await self.client.request(method, path, params=params, json=json)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                if attempt + 1 < attempts:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise KeitaroUnavailableError(f"Keitaro is unreachable: {exc}") from exc

            if resp.status_code >= 500:
                last_error = KeitaroApiError(
                    f"Keitaro server error {resp.status_code}", status_code=resp.status_code
                )
                if attempt + 1 < attempts:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise last_error

            if resp.status_code >= 400:
                raise KeitaroApiError(
                    f"Keitaro API error {resp.status_code}: {self._body_text(resp)}",
                    status_code=resp.status_code,
                )
            return resp.json() if resp.content else None

        assert last_error is not None
        raise last_error

    @staticmethod
    def _body_text(resp: httpx.Response) -> str:
        try:
            return resp.text[:500]
        except Exception:
            return "<no body>"

    @staticmethod
    def _as_list(data: Any) -> list[dict[str, Any]]:
        if data is None:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Keitaro returns a bare object for single-element collections.
            return [data]
        return []

    async def _cached(self, key: str, fn: Callable[[], Awaitable[Any]]) -> Any:
        now = time.monotonic()
        hit = self._cache.get(key)
        if hit is not None and now - hit[0] < self._cache_ttl:
            return hit[1]
        value = await fn()
        self._cache[key] = (now, value)
        return value

    # --- campaigns ---
    async def get_campaigns(
        self,
        *,
        query: str | None = None,
        state: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if query:
            params["query"] = query
        if state:
            params["state"] = state
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        return self._as_list(await self._request("GET", "/campaigns", params=params, retry=True))

    async def get_campaign(self, campaign_id: int) -> dict[str, Any]:
        data = await self._request("GET", f"/campaigns/{campaign_id}", retry=True)
        return data if isinstance(data, dict) else {}

    async def create_campaign(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = await self._request("POST", "/campaigns", json=payload, retry=False)
        return data if isinstance(data, dict) else {}

    async def update_campaign(self, campaign_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        data = await self._request("PUT", f"/campaigns/{campaign_id}", json=payload, retry=False)
        return data if isinstance(data, dict) else {}

    # --- streams ---
    async def get_streams(self, campaign_id: int) -> list[dict[str, Any]]:
        return self._as_list(
            await self._request("GET", f"/campaigns/{campaign_id}/streams", retry=True)
        )

    async def get_stream(self, stream_id: int) -> dict[str, Any]:
        data = await self._request("GET", f"/streams/{stream_id}", retry=True)
        return data if isinstance(data, dict) else {}

    async def create_stream(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = await self._request("POST", "/streams", json=payload, retry=False)
        return data if isinstance(data, dict) else {}

    async def update_stream(self, stream_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        data = await self._request("PUT", f"/streams/{stream_id}", json=payload, retry=False)
        return data if isinstance(data, dict) else {}

    # --- references ---
    async def get_offers(self, *, fresh: bool = False) -> list[dict[str, Any]]:
        if fresh:
            return self._as_list(await self._get_offers_uncached())
        return self._as_list(await self._cached("offers", self._get_offers_uncached))

    async def _get_offers_uncached(self) -> Any:
        return await self._request("GET", "/offers", retry=True)

    async def get_domains(self, *, fresh: bool = False) -> list[dict[str, Any]]:
        if fresh:
            return self._as_list(await self._get_domains_uncached())
        return self._as_list(await self._cached("domains", self._get_domains_uncached))

    async def _get_domains_uncached(self) -> Any:
        return await self._request("GET", "/domains", retry=True)

    def clear_cache(self) -> None:
        self._cache.clear()

    async def get_traffic_sources(self) -> list[dict[str, Any]]:
        return self._as_list(
            await self._cached("traffic_sources", self._get_traffic_sources_uncached)
        )

    async def _get_traffic_sources_uncached(self) -> Any:
        return await self._request("GET", "/traffic_sources", retry=True)

    async def get_groups(self, type_: str = "campaigns") -> list[dict[str, Any]]:
        return self._as_list(
            await self._request("GET", "/groups", params={"type": type_}, retry=True)
        )

    async def get_stream_filters(self) -> list[dict[str, Any]]:
        return self._as_list(await self._request("GET", "/stream_filters", retry=True))

    async def get_stream_schemas(self) -> list[dict[str, Any]]:
        return self._as_list(await self._request("GET", "/stream_schemas", retry=True))

    async def get_stream_actions(self) -> list[dict[str, Any]]:
        return self._as_list(await self._request("GET", "/streams_actions", retry=True))

    async def get_stream_types(self) -> list[dict[str, Any]]:
        return self._as_list(await self._request("GET", "/stream_types", retry=True))

    # --- custom reports ---
    async def build_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = await self._request("POST", "/report/build", json=payload, retry=False)
        return data if isinstance(data, dict) else {}
