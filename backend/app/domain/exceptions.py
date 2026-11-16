"""Domain exceptions — framework-agnostic."""

from __future__ import annotations


class DomainError(Exception):
    """Base error carrying a stable machine-readable code and a user message."""

    code = "DOMAIN_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class ValidationError(DomainError):
    code = "VALIDATION_ERROR"


class NotFoundError(DomainError):
    code = "NOT_FOUND"


class ConflictError(DomainError):
    code = "CONFLICT"


class BusinessRuleError(DomainError):
    code = "BUSINESS_RULE_ERROR"
