import traceback

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .logging_config import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Base exception for application-specific errors"""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class TenantAccessDenied(AppException):
    """Raised when user tries to access data from another tenant"""
    def __init__(self, message: str = "Access denied to tenant data"):
        super().__init__(message, status_code=403)


class ResourceNotFound(AppException):
    """Raised when requested resource is not found"""
    def __init__(self, resource: str, resource_id: str):
        message = f"{resource} with ID {resource_id} not found"
        super().__init__(message, status_code=404)


class DuplicateResource(AppException):
    """Raised when attempting to create a duplicate resource"""
    def __init__(self, resource: str, field: str, value: str):
        message = f"{resource} with {field}='{value}' already exists"
        super().__init__(message, status_code=409)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions"""
    logger.error(
        "Application error",
        exc_message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(
        "Validation error",
        errors=errors,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": errors,
        },
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handle database integrity errors (e.g., unique constraint violations)"""
    logger.error(
        "Database integrity error",
        error=str(exc.orig),
        path=request.url.path,
        method=request.method,
    )

    # Try to extract meaningful error message
    error_msg = str(exc.orig)
    if "unique constraint" in error_msg.lower() or "duplicate" in error_msg.lower():
        message = "A record with this value already exists"
        status_code = status.HTTP_409_CONFLICT
    elif "foreign key" in error_msg.lower():
        message = "Referenced resource does not exist"
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        message = "Database constraint violation"
        status_code = status.HTTP_400_BAD_REQUEST

    return JSONResponse(
        status_code=status_code,
        content={
            "error": message,
            "details": {"database_error": error_msg},
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle general SQLAlchemy database errors"""
    logger.error(
        "Database error",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        traceback=traceback.format_exc(),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database error occurred",
            "details": {"message": "An internal database error occurred. Please try again later."},
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        traceback=traceback.format_exc(),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "details": {"message": "An unexpected error occurred. Please try again later."},
        },
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app"""
    from fastapi.exceptions import RequestValidationError
    from sqlalchemy.exc import IntegrityError, SQLAlchemyError

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
