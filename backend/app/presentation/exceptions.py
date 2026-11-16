"""Exception handlers mapping domain/application errors to HTTP responses."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.application.errors import KeitaroApiError, KeitaroUnavailableError
from app.domain.exceptions import (
    BusinessRuleError,
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


def _error(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def _validation(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content=_error(exc.code, exc.message))

    @app.exception_handler(BusinessRuleError)
    async def _business(request: Request, exc: BusinessRuleError):
        return JSONResponse(status_code=422, content=_error(exc.code, exc.message))

    @app.exception_handler(NotFoundError)
    async def _not_found(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content=_error(exc.code, exc.message))

    @app.exception_handler(ConflictError)
    async def _conflict(request: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content=_error(exc.code, exc.message))

    @app.exception_handler(DomainError)
    async def _domain(request: Request, exc: DomainError):
        return JSONResponse(status_code=400, content=_error(exc.code, exc.message))

    @app.exception_handler(KeitaroUnavailableError)
    async def _keitaro_unavailable(request: Request, exc: KeitaroUnavailableError):
        return JSONResponse(status_code=503, content=_error("KEITARO_UNAVAILABLE", "Keitaro is unavailable"))

    @app.exception_handler(KeitaroApiError)
    async def _keitaro_api(request: Request, exc: KeitaroApiError):
        return JSONResponse(
            status_code=502,
            content=_error("KEITARO_API_ERROR", "Keitaro API returned an error"),
        )

    @app.exception_handler(RequestValidationError)
    async def _request_validation(request: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(x) for x in first.get("loc", []) if x != "body")
        msg = first.get("msg", "Invalid request")
        return JSONResponse(
            status_code=422,
            content=_error("VALIDATION_ERROR", f"{loc}: {msg}" if loc else msg),
        )
