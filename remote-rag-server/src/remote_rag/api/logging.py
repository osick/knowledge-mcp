"""Structured logging configuration using structlog."""

import logging
import sys
from typing import Any

import structlog

from remote_rag.config import settings


def setup_logging() -> None:
    """Configure structured logging with structlog."""
    # Determine if we should use JSON or console format
    use_json = settings.log_format.lower() == "json"

    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if use_json:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Console output for development
        processors.extend(
            [
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )

    # Configure structlog
    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]


def log_request(
    logger: structlog.stdlib.BoundLogger,
    method: str,
    path: str,
    **kwargs: Any,
) -> None:
    """
    Log an HTTP request.

    Args:
        logger: Structlog logger instance
        method: HTTP method
        path: Request path
        **kwargs: Additional context to log
    """
    logger.info(
        "http_request",
        method=method,
        path=path,
        **kwargs,
    )


def log_response(
    logger: structlog.stdlib.BoundLogger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    **kwargs: Any,
) -> None:
    """
    Log an HTTP response.

    Args:
        logger: Structlog logger instance
        method: HTTP method
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        **kwargs: Additional context to log
    """
    logger.info(
        "http_response",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=round(duration_ms, 2),
        **kwargs,
    )


def log_error(
    logger: structlog.stdlib.BoundLogger,
    error: Exception,
    context: dict[str, Any],
) -> None:
    """
    Log an error with context.

    Args:
        logger: Structlog logger instance
        error: Exception that occurred
        context: Additional context information
    """
    logger.error(
        "error_occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        **context,
    )
