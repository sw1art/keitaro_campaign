"""Structured logging (structlog) — JSON output with correlation id + secret masking."""
from __future__ import annotations

import logging
import sys

import structlog

from app.presentation.context import get_correlation_id

_SENSITIVE_FRAGMENTS = ("token", "password", "api_key", "api-key", "authorization", "secret")


def _mask(value: str) -> str:
    if not isinstance(value, str):
        return value
    return value if len(value) <= 6 else f"{value[:3]}***{value[-2:]}"


def _merge_correlation_id(logger, method_name, event_dict):
    cid = get_correlation_id()
    if cid:
        event_dict.setdefault("correlation_id", cid)
    return event_dict


def _mask_secrets(logger, method_name, event_dict):
    for key in list(event_dict):
        if any(frag in str(key).lower() for frag in _SENSITIVE_FRAGMENTS):
            event_dict[key] = "***"
    return event_dict


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    """Route stdlib logging AND structlog through a single JSON (or console) renderer."""
    renderer = (
        structlog.processors.JSONRenderer(ensure_ascii=False)
        if json_output
        else structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())
    )
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            timestamper,
            _merge_correlation_id,
        ],
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            _mask_secrets,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            timestamper,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            _merge_correlation_id,
            _mask_secrets,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
