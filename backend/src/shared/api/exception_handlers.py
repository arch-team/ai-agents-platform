"""Unified exception handlers for FastAPI."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.shared.domain.exceptions import (
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    ResourceQuotaExceededError,
    ValidationError,
)


logger = logging.getLogger(__name__)

# DomainError 子类 -> HTTP 状态码映射
_EXCEPTION_STATUS_MAP: dict[type[DomainError], int] = {
    EntityNotFoundError: 404,
    DuplicateEntityError: 409,
    InvalidStateTransitionError: 409,
    ValidationError: 422,
    ResourceQuotaExceededError: 429,
}


def _resolve_status_code(exc: DomainError) -> int:
    """Resolve HTTP status code using isinstance for subclass support."""
    for exc_type, status_code in _EXCEPTION_STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return status_code
    return 400


def _domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    """DomainError 及其子类的统一处理。"""
    status_code = _resolve_status_code(exc)
    return JSONResponse(
        status_code=status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "details": None,
        },
    )


def _unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    """未处理异常的兜底处理, 不暴露内部信息。"""
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "Internal server error",
            "details": None,
        },
    )


def register_status_mapping(exception_type: type[DomainError], status_code: int) -> None:
    """Register a DomainError subclass to HTTP status code mapping."""
    _EXCEPTION_STATUS_MAP[exception_type] = status_code


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers to FastAPI app."""
    app.add_exception_handler(DomainError, _domain_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _unhandled_exception_handler)
