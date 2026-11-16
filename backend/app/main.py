"""AdRobot FastAPI application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import Settings, get_settings
from app.infrastructure.keitaro import KeitaroClient
from app.infrastructure.messaging.publisher import RabbitPublisher
from app.presentation.api import (
    analytics,
    audit,
    campaigns,
    dashboard,
    operations,
    references,
    streams,
)
from app.presentation.dependencies import (
    get_keitaro,
    get_publisher,
    get_session_factory,
    require_api_token,
)
from app.presentation.exceptions import register_exception_handlers
from app.presentation.middleware import rate_limit, request_context_middleware

logger = logging.getLogger("app")

DESCRIPTION = """
AdRobot — управление рекламными кампаниями Keitaro.

- Создание кампании с двумя потоками (Google Redirect + Offer Flow).
- Редактирование офферов и весов распределения в существующих кампаниях.
- Асинхронное создание через RabbitMQ (статус операции, аудит, retry).
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    settings.check_secrets()
    keitaro = KeitaroClient(settings)
    publisher = RabbitPublisher(settings)
    app.state.keitaro = keitaro
    app.state.publisher = publisher
    logger.info("AdRobot API started (env=%s)", settings.app_env)
    yield
    await keitaro.aclose()
    await publisher.close()


def create_app() -> FastAPI:
    settings: Settings = get_settings()
    logging.getLogger().setLevel(settings.log_level.upper())
    logging.getLogger("app").setLevel(settings.log_level.upper())

    app = FastAPI(
        title="AdRobot API",
        version="0.2.0",
        description=DESCRIPTION,
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(request_context_middleware)

    api = APIRouter(
        prefix="/api/v1",
        dependencies=[Depends(require_api_token), Depends(rate_limit)],
    )
    api.include_router(campaigns.router)
    api.include_router(references.router)
    api.include_router(streams.router)
    api.include_router(operations.router)
    api.include_router(dashboard.router)
    api.include_router(audit.router)
    api.include_router(analytics.router)
    app.include_router(api)

    register_exception_handlers(app)

    @app.get("/healthz", tags=["system"])
    async def _check_keitaro(request: Request) -> str:
        try:
            await get_keitaro(request).get_stream_types()
            return "ok"
        except Exception as exc:  # noqa: BLE001
            logger.warning("health: keitaro check failed: %s", exc)
            return "error"

    async def _readiness_checks(request: Request) -> dict[str, str]:
        checks: dict[str, str] = {}

        try:
            async with get_session_factory()() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as exc:  # noqa: BLE001
            logger.warning("health: database check failed: %s", exc)
            checks["database"] = "error"

        try:
            await get_publisher(request).connect()
            checks["rabbitmq"] = "ok"
        except Exception as exc:  # noqa: BLE001
            logger.warning("health: rabbitmq check failed: %s", exc)
            checks["rabbitmq"] = "error"

        checks["keitaro"] = await _check_keitaro(request)
        return checks

    @app.get("/healthz", tags=["system"])
    async def healthz() -> dict:
        """Liveness probe (no dependency checks)."""
        return {"status": "ok"}

    @app.get("/readyz", tags=["system"])
    async def readyz(request: Request) -> JSONResponse:
        """Readiness probe: DB + RabbitMQ + Keitaro reachability."""
        checks = await _readiness_checks(request)
        healthy = all(v == "ok" for v in checks.values())
        return JSONResponse(
            status_code=200 if healthy else 503,
            content={"status": "ok" if healthy else "degraded", "checks": checks},
        )

    @app.get("/health/live", tags=["system"])
    async def health_live() -> dict:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["system"])
    async def health_ready(request: Request) -> JSONResponse:
        checks = await _readiness_checks(request)
        healthy = all(v == "ok" for v in checks.values())
        return JSONResponse(
            status_code=200 if healthy else 503,
            content={"status": "ok" if healthy else "degraded", "checks": checks},
        )

    @app.get("/health/keitaro", tags=["system"])
    async def health_keitaro(request: Request) -> JSONResponse:
        status = await _check_keitaro(request)
        return JSONResponse(
            status_code=200 if status == "ok" else 503,
            content={"status": status, "checks": {"keitaro": status}},
        )

    return app


app = create_app()
