"""AdRobot FastAPI application."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.infrastructure.keitaro import KeitaroClient
from app.infrastructure.messaging.publisher import RabbitPublisher
from app.presentation.api import campaigns, operations, references, streams
from app.presentation.exceptions import register_exception_handlers

DESCRIPTION = """
AdRobot — управление рекламными кампаниями Keitaro.

- Создание кампании с двумя потоками (Google Redirect + Offer Flow).
- Редактирование офферов и весов распределения в существующих кампаниях.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    keitaro = KeitaroClient(settings)
    publisher = RabbitPublisher(settings)
    app.state.keitaro = keitaro
    app.state.publisher = publisher
    yield
    await keitaro.aclose()
    await publisher.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AdRobot API",
        version="0.1.0",
        description=DESCRIPTION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = APIRouter(prefix="/api/v1")
    api.include_router(campaigns.router)
    api.include_router(references.router)
    api.include_router(streams.router)
    api.include_router(operations.router)
    app.include_router(api)

    register_exception_handlers(app)

    @app.get("/healthz", tags=["system"])
    async def healthz() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
