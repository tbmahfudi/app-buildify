import logging
import sys
import structlog
from typing import Any, Dict
from .config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """
    Configure structured logging with structlog for better log analysis.
    Outputs JSON logs in production, human-readable logs in development.
    """
    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    # Determine renderer based on environment
    if settings.ENVIRONMENT == "production":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


def add_request_context(
    request_id: str,
    method: str,
    path: str,
    user_id: str = None,
    tenant_id: str = None
) -> Dict[str, Any]:
    """
    Add request context to logs for better traceability.

    Args:
        request_id: Unique request identifier
        method: HTTP method
        path: Request path
        user_id: Authenticated user ID
        tenant_id: Tenant ID

    Returns:
        Context dictionary for logging
    """
    context = {
        "request_id": request_id,
        "method": method,
        "path": path,
    }

    if user_id:
        context["user_id"] = user_id
    if tenant_id:
        context["tenant_id"] = tenant_id

    return context
