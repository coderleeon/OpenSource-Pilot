"""FastAPI middleware components.

Provides:
- ``RequestIDMiddleware``: injects a unique request-ID into every request and
  binds it to the structlog context so all log lines carry it automatically.
- ``register_exception_handlers``: maps custom exceptions to JSON error responses.
"""

from __future__ import annotations

import uuid
from typing import Any, Callable

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.exceptions import (
    CloneError,
    ConfigurationError,
    GitHubAPIError,
    IndexingError,
    IssueNotFoundError,
    LLMError,
    LLMParseError,
    OpenSourcePilotError,
    RepoNotFoundError,
    SearchError,
    StructureParseError,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Request-ID middleware
# ---------------------------------------------------------------------------

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject a unique request ID into every request and response.

    The ID is bound to the structlog context so that every log statement
    emitted during a request automatically includes ``request_id``.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))

        # Bind request context to structlog so all downstream loggers see it.
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


# ---------------------------------------------------------------------------
# Exception → HTTP status mapping
# ---------------------------------------------------------------------------

_EXCEPTION_STATUS_MAP: dict[type[OpenSourcePilotError], int] = {
    RepoNotFoundError: 404,
    IssueNotFoundError: 404,
    CloneError: 502,
    GitHubAPIError: 502,
    StructureParseError: 500,
    LLMError: 502,
    LLMParseError: 500,
    IndexingError: 500,
    SearchError: 500,
    ConfigurationError: 500,
    OpenSourcePilotError: 500,
}


def _build_error_response(exc: OpenSourcePilotError, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register application exception handlers on *app*.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(OpenSourcePilotError)
    async def handle_app_error(request: Request, exc: OpenSourcePilotError) -> JSONResponse:  # type: ignore[type-arg]
        status_code = _EXCEPTION_STATUS_MAP.get(type(exc), 500)
        logger.warning(
            "application_error",
            error_type=type(exc).__name__,
            message=exc.message,
            status_code=status_code,
        )
        return _build_error_response(exc, status_code)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:  # type: ignore[type-arg]
        logger.exception("unexpected_error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred. Please try again later.",
                "details": None,
            },
        )
