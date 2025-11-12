"""
HTTP Exception helper functions for standardized error responses.

This module provides reusable exception builders to eliminate duplicate
error handling code across routers. Consolidates ~188 HTTPException occurrences.

Key benefits:
- Consistent error message formatting
- Standardized HTTP status codes
- Reduced boilerplate code
- Easy to update error handling globally
"""
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status


def not_found_exception(
    entity_name: str,
    entity_id: Optional[str] = None,
    detail: Optional[str] = None
) -> HTTPException:
    """
    Create a standardized 404 Not Found exception.

    Args:
        entity_name: Name of the entity (e.g., "Company", "User")
        entity_id: Optional entity ID to include in message
        detail: Optional custom detail message

    Returns:
        HTTPException with 404 status

    Example:
        >>> raise not_found_exception("Company", company_id)
        >>> raise not_found_exception("User", detail="User account not found")
    """
    if detail:
        msg = detail
    elif entity_id:
        msg = f"{entity_name} with ID '{entity_id}' not found"
    else:
        msg = f"{entity_name} not found"

    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=msg
    )


def bad_request_exception(
    message: str,
    errors: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """
    Create a standardized 400 Bad Request exception.

    Args:
        message: Error message
        errors: Optional dictionary of field-specific errors

    Returns:
        HTTPException with 400 status

    Example:
        >>> raise bad_request_exception("Invalid email format")
        >>> raise bad_request_exception("Validation failed", {"email": "Required"})
    """
    detail = {"message": message}
    if errors:
        detail["errors"] = errors

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail if errors else message
    )


def duplicate_exception(
    entity_name: str,
    field_name: str = "code",
    field_value: Optional[str] = None
) -> HTTPException:
    """
    Create a standardized exception for duplicate entries.

    Args:
        entity_name: Name of the entity (e.g., "Company")
        field_name: Name of the duplicate field (default: "code")
        field_value: Optional value that's duplicated

    Returns:
        HTTPException with 400 status

    Example:
        >>> raise duplicate_exception("Company", "code", "ACME")
        >>> raise duplicate_exception("User", "email")
    """
    if field_value:
        msg = f"{entity_name} with {field_name} '{field_value}' already exists"
    else:
        msg = f"{entity_name} {field_name} already exists"

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=msg
    )


def permission_denied_exception(
    action: Optional[str] = None,
    resource: Optional[str] = None,
    detail: Optional[str] = None
) -> HTTPException:
    """
    Create a standardized 403 Forbidden exception.

    Args:
        action: Action that was attempted (e.g., "delete")
        resource: Resource name (e.g., "company")
        detail: Optional custom detail message

    Returns:
        HTTPException with 403 status

    Example:
        >>> raise permission_denied_exception("delete", "company")
        >>> raise permission_denied_exception(detail="Admin access required")
    """
    if detail:
        msg = detail
    elif action and resource:
        msg = f"Permission denied: cannot {action} {resource}"
    else:
        msg = "Permission denied"

    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=msg
    )


def unauthorized_exception(
    detail: str = "Authentication required"
) -> HTTPException:
    """
    Create a standardized 401 Unauthorized exception.

    Args:
        detail: Error detail message

    Returns:
        HTTPException with 401 status

    Example:
        >>> raise unauthorized_exception()
        >>> raise unauthorized_exception("Invalid token")
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"}
    )


def conflict_exception(
    message: str,
    conflicts: Optional[List[str]] = None
) -> HTTPException:
    """
    Create a standardized 409 Conflict exception.

    Args:
        message: Error message
        conflicts: Optional list of conflicting items

    Returns:
        HTTPException with 409 status

    Example:
        >>> raise conflict_exception("Cannot delete company with active branches")
        >>> raise conflict_exception("Resource conflicts", ["branch-1", "branch-2"])
    """
    detail = {"message": message}
    if conflicts:
        detail["conflicts"] = conflicts

    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail if conflicts else message
    )


def validation_error_exception(
    errors: Dict[str, Any]
) -> HTTPException:
    """
    Create a standardized validation error exception.

    Args:
        errors: Dictionary of field-level validation errors

    Returns:
        HTTPException with 422 status

    Example:
        >>> raise validation_error_exception({
        ...     "email": "Invalid email format",
        ...     "age": "Must be at least 18"
        ... })
    """
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "message": "Validation failed",
            "errors": errors
        }
    )


def internal_server_error_exception(
    detail: str = "Internal server error",
    error_id: Optional[str] = None
) -> HTTPException:
    """
    Create a standardized 500 Internal Server Error exception.

    Args:
        detail: Error detail message
        error_id: Optional error tracking ID

    Returns:
        HTTPException with 500 status

    Example:
        >>> raise internal_server_error_exception("Database connection failed")
        >>> raise internal_server_error_exception("Error processing request", "ERR-12345")
    """
    msg = detail
    if error_id:
        msg = f"{detail} (Error ID: {error_id})"

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=msg
    )


def relationship_violation_exception(
    parent: str,
    child: str,
    detail: Optional[str] = None
) -> HTTPException:
    """
    Create an exception for invalid parent-child relationships.

    Args:
        parent: Parent entity name
        child: Child entity name
        detail: Optional custom detail message

    Returns:
        HTTPException with 400 status

    Example:
        >>> raise relationship_violation_exception("Company", "Branch",
        ...     "Branch does not belong to this company")
    """
    msg = detail or f"{child} does not belong to the specified {parent}"

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=msg
    )


def rate_limit_exception(
    retry_after: Optional[int] = None
) -> HTTPException:
    """
    Create a standardized 429 Too Many Requests exception.

    Args:
        retry_after: Optional seconds until retry is allowed

    Returns:
        HTTPException with 429 status

    Example:
        >>> raise rate_limit_exception(60)  # Retry after 60 seconds
    """
    headers = {}
    if retry_after:
        headers["Retry-After"] = str(retry_after)

    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Rate limit exceeded. Please try again later.",
        headers=headers if headers else None
    )


def service_unavailable_exception(
    service_name: Optional[str] = None
) -> HTTPException:
    """
    Create a standardized 503 Service Unavailable exception.

    Args:
        service_name: Optional name of unavailable service

    Returns:
        HTTPException with 503 status

    Example:
        >>> raise service_unavailable_exception("Database")
        >>> raise service_unavailable_exception()
    """
    msg = "Service temporarily unavailable"
    if service_name:
        msg = f"{service_name} service is temporarily unavailable"

    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=msg
    )


def gone_exception(
    entity_name: str,
    reason: Optional[str] = None
) -> HTTPException:
    """
    Create a standardized 410 Gone exception.

    Args:
        entity_name: Name of the entity
        reason: Optional reason for removal

    Returns:
        HTTPException with 410 status

    Example:
        >>> raise gone_exception("Account", "Account has been permanently deleted")
    """
    msg = f"{entity_name} is no longer available"
    if reason:
        msg = f"{msg}. {reason}"

    return HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=msg
    )


def method_not_allowed_exception(
    method: str,
    allowed_methods: Optional[List[str]] = None
) -> HTTPException:
    """
    Create a standardized 405 Method Not Allowed exception.

    Args:
        method: HTTP method that was attempted
        allowed_methods: Optional list of allowed methods

    Returns:
        HTTPException with 405 status

    Example:
        >>> raise method_not_allowed_exception("DELETE", ["GET", "POST"])
    """
    msg = f"Method {method} not allowed"

    headers = {}
    if allowed_methods:
        headers["Allow"] = ", ".join(allowed_methods)

    return HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail=msg,
        headers=headers if headers else None
    )


# Convenience aliases for common patterns
EntityNotFoundError = not_found_exception
DuplicateEntityError = duplicate_exception
InvalidRelationshipError = relationship_violation_exception
