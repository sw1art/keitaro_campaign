"""Ports for external systems (implemented in infrastructure)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class KeitaroClientProtocol(ABC):
    """Adapter port to the Keitaro admin API."""

    @abstractmethod
    async def get_campaigns(
        self,
        *,
        query: str | None = None,
        state: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_campaign(self, campaign_id: int) -> dict[str, Any]: ...

    @abstractmethod
    async def create_campaign(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def get_streams(self, campaign_id: int) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_stream(self, stream_id: int) -> dict[str, Any]: ...

    @abstractmethod
    async def create_stream(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def update_stream(self, stream_id: int, payload: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def get_offers(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_domains(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_traffic_sources(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_groups(self, type_: str = "campaigns") -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_stream_filters(self) -> list[dict[str, Any]]: ...


class MessagePublisherProtocol(ABC):
    """Port for publishing events to the message broker."""

    @abstractmethod
    async def publish(self, event_type: str, payload: dict[str, Any]) -> None: ...
