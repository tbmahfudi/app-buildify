"""
Response builder functions for standardized API responses.

This module provides reusable response builders to eliminate duplicate
pagination and list response logic across routers. Consolidates ~75+ lines
of duplicate list endpoint implementations.

Key benefits:
- Consistent pagination format
- Standardized response structure
- Reduced boilerplate code
- Easy to update response format globally
"""
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Query, Session

from app.models.base import Base

# Type variables
ModelType = TypeVar("ModelType", bound=Base)
SchemaType = TypeVar("SchemaType", bound=BaseModel)


def build_list_response(
    query: Query,
    skip: int = 0,
    limit: int = 100,
    response_model: Optional[Type[SchemaType]] = None
) -> Dict[str, Any]:
    """
    Build a standardized paginated list response.

    Consolidates the pattern:
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return {"items": items, "total": total}

    Args:
        query: SQLAlchemy query object
        skip: Number of items to skip (default: 0)
        limit: Maximum items to return (default: 100)
        response_model: Optional Pydantic model for serialization

    Returns:
        Dictionary with 'items', 'total', 'skip', 'limit'

    Example:
        >>> query = db.query(Company).filter(Company.is_active == True)
        >>> return build_list_response(query, skip=0, limit=50)
    """
    total = query.count()
    items = query.offset(skip).limit(limit).all()

    # Convert to response models if provided
    if response_model:
        items = [response_model.from_orm(item) for item in items]

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": (skip + limit) < total
    }


def build_paginated_response(
    db: Session,
    model: Type[ModelType],
    skip: int = 0,
    limit: int = 100,
    filters: Optional[Dict[str, Any]] = None,
    order_by: Optional[Any] = None,
    response_model: Optional[Type[SchemaType]] = None
) -> Dict[str, Any]:
    """
    Build a paginated response with automatic filtering and ordering.

    Args:
        db: Database session
        model: SQLAlchemy model class
        skip: Number of items to skip (default: 0)
        limit: Maximum items to return (default: 100)
        filters: Optional dictionary of filters {"field": "value"}
        order_by: Optional order_by clause (e.g., Model.created_at.desc())
        response_model: Optional Pydantic model for serialization

    Returns:
        Dictionary with pagination metadata and items

    Example:
        >>> return build_paginated_response(
        ...     db, Company,
        ...     skip=0, limit=50,
        ...     filters={"is_active": True},
        ...     order_by=Company.created_at.desc()
        ... )
    """
    query = db.query(model)

    # Apply filters
    if filters:
        for field, value in filters.items():
            if hasattr(model, field):
                query = query.filter(getattr(model, field) == value)

    # Apply ordering
    if order_by is not None:
        query = query.order_by(order_by)

    return build_list_response(query, skip, limit, response_model)


def build_success_response(
    message: str,
    data: Optional[Any] = None,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build a standardized success response.

    Args:
        message: Success message
        data: Optional response data
        meta: Optional metadata dictionary

    Returns:
        Dictionary with success structure

    Example:
        >>> return build_success_response(
        ...     "Company created successfully",
        ...     data=company,
        ...     meta={"id": company_id}
        ... )
    """
    response = {
        "success": True,
        "message": message
    }

    if data is not None:
        response["data"] = data

    if meta:
        response["meta"] = meta

    return response


def build_delete_response(
    entity_name: str,
    entity_id: str
) -> Dict[str, Any]:
    """
    Build a standardized delete success response.

    Args:
        entity_name: Name of deleted entity
        entity_id: ID of deleted entity

    Returns:
        Dictionary with delete confirmation

    Example:
        >>> return build_delete_response("Company", company_id)
    """
    return {
        "success": True,
        "message": f"{entity_name} deleted successfully",
        "deleted_id": entity_id
    }


def build_bulk_response(
    created: Optional[int] = None,
    updated: Optional[int] = None,
    deleted: Optional[int] = None,
    failed: Optional[int] = None,
    errors: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Build a standardized bulk operation response.

    Args:
        created: Number of items created
        updated: Number of items updated
        deleted: Number of items deleted
        failed: Number of items that failed
        errors: Optional list of error details

    Returns:
        Dictionary with bulk operation summary

    Example:
        >>> return build_bulk_response(
        ...     created=5,
        ...     updated=2,
        ...     failed=1,
        ...     errors=[{"index": 7, "error": "Duplicate code"}]
        ... )
    """
    response = {
        "success": (failed or 0) == 0,
        "summary": {}
    }

    if created is not None:
        response["summary"]["created"] = created
    if updated is not None:
        response["summary"]["updated"] = updated
    if deleted is not None:
        response["summary"]["deleted"] = deleted
    if failed is not None:
        response["summary"]["failed"] = failed

    if errors:
        response["errors"] = errors

    return response


def build_search_response(
    query: Query,
    search_term: str,
    search_fields: List[str],
    skip: int = 0,
    limit: int = 100,
    response_model: Optional[Type[SchemaType]] = None
) -> Dict[str, Any]:
    """
    Build a search response with highlighting of matched fields.

    Args:
        query: Base SQLAlchemy query
        search_term: Search term
        search_fields: List of field names to search
        skip: Number of items to skip
        limit: Maximum items to return
        response_model: Optional Pydantic model for serialization

    Returns:
        Dictionary with search results and metadata

    Example:
        >>> query = db.query(Company)
        >>> return build_search_response(
        ...     query,
        ...     search_term="acme",
        ...     search_fields=["name", "code"],
        ...     skip=0, limit=50
        ... )
    """
    from sqlalchemy import or_

    # Build search filter
    model = query.column_descriptions[0]['entity']
    search_filters = []

    for field in search_fields:
        if hasattr(model, field):
            search_filters.append(
                getattr(model, field).ilike(f"%{search_term}%")
            )

    if search_filters:
        query = query.filter(or_(*search_filters))

    response = build_list_response(query, skip, limit, response_model)
    response["search_term"] = search_term
    response["search_fields"] = search_fields

    return response


def build_aggregation_response(
    data: List[Dict[str, Any]],
    aggregations: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build a response with aggregated data.

    Args:
        data: List of data items
        aggregations: Dictionary of aggregation results

    Returns:
        Dictionary with data and aggregations

    Example:
        >>> return build_aggregation_response(
        ...     data=companies,
        ...     aggregations={
        ...         "total_count": 100,
        ...         "active_count": 85,
        ...         "average_revenue": 1500000
        ...     }
        ... )
    """
    return {
        "data": data,
        "aggregations": aggregations,
        "count": len(data)
    }


def build_export_response(
    file_path: str,
    file_name: str,
    file_size: int,
    format: str,
    record_count: int
) -> Dict[str, Any]:
    """
    Build a response for data export operations.

    Args:
        file_path: Path to exported file
        file_name: Name of exported file
        file_size: Size of file in bytes
        format: Export format (csv, xlsx, pdf, etc.)
        record_count: Number of records exported

    Returns:
        Dictionary with export details

    Example:
        >>> return build_export_response(
        ...     file_path="/exports/companies_20231112.xlsx",
        ...     file_name="companies_20231112.xlsx",
        ...     file_size=45678,
        ...     format="xlsx",
        ...     record_count=150
        ... )
    """
    return {
        "success": True,
        "file_path": file_path,
        "file_name": file_name,
        "file_size": file_size,
        "format": format,
        "record_count": record_count,
        "download_url": f"/api/downloads/{file_name}"
    }


def build_validation_response(
    valid: bool,
    errors: Optional[Dict[str, List[str]]] = None,
    warnings: Optional[Dict[str, List[str]]] = None
) -> Dict[str, Any]:
    """
    Build a validation response.

    Args:
        valid: Whether validation passed
        errors: Optional dictionary of validation errors
        warnings: Optional dictionary of validation warnings

    Returns:
        Dictionary with validation results

    Example:
        >>> return build_validation_response(
        ...     valid=False,
        ...     errors={"email": ["Invalid format"], "age": ["Must be 18+"]},
        ...     warnings={"phone": ["Area code not recognized"]}
        ... )
    """
    response = {
        "valid": valid,
        "error_count": 0,
        "warning_count": 0
    }

    if errors:
        response["errors"] = errors
        response["error_count"] = sum(len(v) for v in errors.values())

    if warnings:
        response["warnings"] = warnings
        response["warning_count"] = sum(len(v) for v in warnings.values())

    return response


def build_batch_status_response(
    batch_id: str,
    status: str,
    total: int,
    completed: int,
    failed: int,
    progress_percentage: float
) -> Dict[str, Any]:
    """
    Build a batch operation status response.

    Args:
        batch_id: Unique batch identifier
        status: Batch status (pending, processing, completed, failed)
        total: Total number of items in batch
        completed: Number of completed items
        failed: Number of failed items
        progress_percentage: Progress as percentage (0-100)

    Returns:
        Dictionary with batch status

    Example:
        >>> return build_batch_status_response(
        ...     batch_id="batch-123",
        ...     status="processing",
        ...     total=1000,
        ...     completed=750,
        ...     failed=5,
        ...     progress_percentage=75.0
        ... )
    """
    return {
        "batch_id": batch_id,
        "status": status,
        "total": total,
        "completed": completed,
        "failed": failed,
        "pending": total - completed - failed,
        "progress_percentage": progress_percentage,
        "is_complete": status in ["completed", "failed"]
    }


# Convenience function for simple list responses
def list_response(items: List[Any], total: Optional[int] = None) -> Dict[str, Any]:
    """
    Simple list response builder.

    Args:
        items: List of items
        total: Optional total count (defaults to len(items))

    Returns:
        Dictionary with items and total

    Example:
        >>> return list_response(companies, total=100)
    """
    return {
        "items": items,
        "total": total if total is not None else len(items)
    }
