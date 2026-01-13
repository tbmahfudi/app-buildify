"""
Dynamic Data API Router - FastAPI endpoints for runtime CRUD operations

Provides complete CRUD functionality for nocode entities via REST API.
All endpoints are prefixed with /api/v1/dynamic-data
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import Optional
import json
from app.core.dependencies import get_db, get_current_user
from app.schemas.dynamic_data import (
    DynamicDataCreateRequest,
    DynamicDataUpdateRequest,
    DynamicDataResponse,
    DynamicDataListResponse,
    DynamicDataBulkCreateRequest,
    DynamicDataBulkUpdateRequest,
    DynamicDataBulkDeleteRequest,
    DynamicDataBulkResponse,
    ValidationErrorResponse,
    NotFoundResponse,
    ForbiddenResponse
)
from app.services.dynamic_entity_service import DynamicEntityService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/dynamic-data",
    tags=["Dynamic Data"]
)


# ==============================================================================
# CRUD Endpoints
# ==============================================================================

@router.post(
    "/{entity_name}/records",
    response_model=DynamicDataResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Record",
    description="Create a new record in the specified dynamic entity",
    responses={
        201: {"description": "Record created successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        403: {"model": ForbiddenResponse, "description": "Permission denied"},
        404: {"model": NotFoundResponse, "description": "Entity not found or not published"}
    }
)
async def create_record(
    entity_name: str = Path(..., description="Entity name"),
    request: DynamicDataCreateRequest = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new record in a dynamic entity.

    **Required Permission:** `{entity_name}:create:tenant`

    **Request Body:**
    ```json
    {
      "data": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com"
      }
    }
    ```

    **Response:**
    ```json
    {
      "id": "uuid...",
      "data": { ... full record ... }
    }
    ```
    """
    service = DynamicEntityService(db, current_user)

    try:
        result = await service.create_record(entity_name, request.data)
        return DynamicDataResponse(
            id=result['id'],
            data=result
        )
    except ValueError as e:
        logger.error(f"Validation error creating {entity_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating {entity_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{entity_name}/records",
    response_model=DynamicDataListResponse,
    summary="List Records",
    description="List records with filtering, sorting, search, and pagination",
    responses={
        200: {"description": "Records retrieved successfully"},
        400: {"model": ValidationErrorResponse, "description": "Invalid filter or sort parameters"},
        403: {"model": ForbiddenResponse, "description": "Permission denied"},
        404: {"model": NotFoundResponse, "description": "Entity not found"}
    }
)
async def list_records(
    entity_name: str = Path(..., description="Entity name"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page (max 100)"),
    sort: Optional[str] = Query(
        None,
        description="Sort specification (e.g., 'name:asc,created_at:desc')"
    ),
    filters: Optional[str] = Query(
        None,
        description="Filter specification as JSON string"
    ),
    search: Optional[str] = Query(
        None,
        description="Global search term (searches across all text fields)"
    ),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List records with optional filtering, sorting, and search.

    **Required Permission:** `{entity_name}:read:tenant`

    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 25, max: 100)
    - `sort`: Sort specification (e.g., "name:asc,created_at:desc")
    - `filters`: JSON string with filter specification
    - `search`: Global search term

    **Filter Format:**
    ```json
    {
      "operator": "AND",
      "conditions": [
        {"field": "email", "operator": "contains", "value": "@example.com"},
        {"field": "created_at", "operator": "gte", "value": "2026-01-01"}
      ]
    }
    ```

    **Operators:**
    - Comparison: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`
    - String: `contains`, `starts_with`, `ends_with`, `like`, `ilike`
    - List: `in`, `not_in`
    - Null: `is_null`, `is_not_null`

    **Response:**
    ```json
    {
      "items": [...],
      "total": 150,
      "page": 1,
      "page_size": 25,
      "pages": 6
    }
    ```
    """
    service = DynamicEntityService(db, current_user)

    try:
        # Parse filters
        filter_dict = None
        if filters:
            try:
                filter_dict = json.loads(filters)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid filters JSON"
                )

        # Parse sort
        sort_list = []
        if sort:
            for item in sort.split(','):
                item = item.strip()
                if ':' in item:
                    field, direction = item.split(':', 1)
                    sort_list.append((field.strip(), direction.strip()))
                else:
                    sort_list.append((item, 'asc'))

        result = await service.list_records(
            entity_name=entity_name,
            filters=filter_dict,
            sort=sort_list if sort_list else None,
            page=page,
            page_size=page_size,
            search=search
        )

        return DynamicDataListResponse(**result)

    except ValueError as e:
        logger.error(f"Error listing {entity_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing {entity_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{entity_name}/records/{record_id}",
    response_model=DynamicDataResponse,
    summary="Get Record",
    description="Get a single record by ID",
    responses={
        200: {"description": "Record retrieved successfully"},
        403: {"model": ForbiddenResponse, "description": "Permission denied"},
        404: {"model": NotFoundResponse, "description": "Record not found"}
    }
)
async def get_record(
    entity_name: str = Path(..., description="Entity name"),
    record_id: str = Path(..., description="Record ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get a single record by ID.

    **Required Permission:** `{entity_name}:read:tenant`

    **Response:**
    ```json
    {
      "id": "uuid...",
      "data": { ... full record ... }
    }
    ```
    """
    service = DynamicEntityService(db, current_user)

    try:
        result = await service.get_record(entity_name, record_id)
        return DynamicDataResponse(
            id=result['id'],
            data=result
        )
    except ValueError as e:
        logger.error(f"Record not found: {entity_name}/{record_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting {entity_name}/{record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put(
    "/{entity_name}/records/{record_id}",
    response_model=DynamicDataResponse,
    summary="Update Record",
    description="Update an existing record",
    responses={
        200: {"description": "Record updated successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        403: {"model": ForbiddenResponse, "description": "Permission denied"},
        404: {"model": NotFoundResponse, "description": "Record not found"}
    }
)
async def update_record(
    entity_name: str = Path(..., description="Entity name"),
    record_id: str = Path(..., description="Record ID"),
    request: DynamicDataUpdateRequest = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update an existing record (partial update supported).

    **Required Permission:** `{entity_name}:update:own` or `{entity_name}:update:tenant`

    **Request Body:**
    ```json
    {
      "data": {
        "phone": "+0987654321",
        "status": "active"
      }
    }
    ```

    **Response:**
    ```json
    {
      "id": "uuid...",
      "data": { ... updated record ... }
    }
    ```
    """
    service = DynamicEntityService(db, current_user)

    try:
        result = await service.update_record(entity_name, record_id, request.data)
        return DynamicDataResponse(
            id=result['id'],
            data=result
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating {entity_name}/{record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/{entity_name}/records/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Record",
    description="Delete a record (soft delete if supported, hard delete otherwise)",
    responses={
        204: {"description": "Record deleted successfully"},
        403: {"model": ForbiddenResponse, "description": "Permission denied"},
        404: {"model": NotFoundResponse, "description": "Record not found"}
    }
)
async def delete_record(
    entity_name: str = Path(..., description="Entity name"),
    record_id: str = Path(..., description="Record ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete a record.

    If the entity supports soft deletes (has `deleted_at` field), performs soft delete.
    Otherwise, performs hard delete.

    **Required Permission:** `{entity_name}:delete:own` or `{entity_name}:delete:tenant`
    """
    service = DynamicEntityService(db, current_user)

    try:
        await service.delete_record(entity_name, record_id)
        return None
    except ValueError as e:
        logger.error(f"Record not found: {entity_name}/{record_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting {entity_name}/{record_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==============================================================================
# Bulk Operation Endpoints
# ==============================================================================

@router.post(
    "/{entity_name}/records/bulk",
    response_model=DynamicDataBulkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk Create Records",
    description="Create multiple records in a single request"
)
async def bulk_create_records(
    entity_name: str = Path(..., description="Entity name"),
    request: DynamicDataBulkCreateRequest = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create multiple records in a single request.

    **Required Permission:** `{entity_name}:create:tenant`

    **Request Body:**
    ```json
    {
      "records": [
        {"first_name": "John", "last_name": "Doe", "email": "john@example.com"},
        {"first_name": "Jane", "last_name": "Smith", "email": "jane@example.com"}
      ]
    }
    ```

    **Response:**
    ```json
    {
      "created": 2,
      "failed": 0,
      "errors": [],
      "ids": ["uuid-1", "uuid-2"]
    }
    ```

    Note: Continues processing even if some records fail. Check `errors` array for details.
    """
    service = DynamicEntityService(db, current_user)

    try:
        result = await service.bulk_create(entity_name, request.records)
        return DynamicDataBulkResponse(**result)
    except Exception as e:
        logger.error(f"Error in bulk create for {entity_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put(
    "/{entity_name}/records/bulk",
    response_model=DynamicDataBulkResponse,
    summary="Bulk Update Records",
    description="Update multiple records in a single request"
)
async def bulk_update_records(
    entity_name: str = Path(..., description="Entity name"),
    request: DynamicDataBulkUpdateRequest = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update multiple records in a single request.

    **Required Permission:** `{entity_name}:update:tenant`

    **Request Body:**
    ```json
    {
      "records": [
        {"id": "uuid-1", "status": "active"},
        {"id": "uuid-2", "status": "inactive"}
      ]
    }
    ```

    Note: Each record must include an `id` field.

    **Response:**
    ```json
    {
      "updated": 2,
      "failed": 0,
      "errors": []
    }
    ```
    """
    service = DynamicEntityService(db, current_user)

    try:
        result = await service.bulk_update(entity_name, request.records)
        return DynamicDataBulkResponse(**result)
    except Exception as e:
        logger.error(f"Error in bulk update for {entity_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/{entity_name}/records/bulk",
    response_model=DynamicDataBulkResponse,
    summary="Bulk Delete Records",
    description="Delete multiple records in a single request"
)
async def bulk_delete_records(
    entity_name: str = Path(..., description="Entity name"),
    request: DynamicDataBulkDeleteRequest = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete multiple records in a single request.

    **Required Permission:** `{entity_name}:delete:tenant`

    **Request Body:**
    ```json
    {
      "ids": ["uuid-1", "uuid-2", "uuid-3"]
    }
    ```

    **Response:**
    ```json
    {
      "deleted": 3,
      "failed": 0,
      "errors": []
    }
    ```
    """
    service = DynamicEntityService(db, current_user)

    try:
        result = await service.bulk_delete(entity_name, request.ids)
        return DynamicDataBulkResponse(**result)
    except Exception as e:
        logger.error(f"Error in bulk delete for {entity_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==============================================================================
# Relationship Endpoints
# ==============================================================================

@router.get(
    "/{entity_name}/records/{record_id}/{relationship_name}",
    response_model=DynamicDataListResponse,
    summary="Get Related Records",
    description="Get records related to a specific record via a relationship"
)
async def get_related_records(
    entity_name: str = Path(..., description="Entity name"),
    record_id: str = Path(..., description="Record ID"),
    relationship_name: str = Path(..., description="Relationship name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get records related via a defined relationship.

    **Example:** `GET /api/v1/dynamic-data/customers/records/{id}/orders`

    This retrieves all orders for a specific customer.

    **Required Permission:** `{related_entity}:read:tenant`

    **Response:**
    ```json
    {
      "items": [...],
      "total": 5,
      "page": 1,
      "page_size": 25,
      "pages": 1
    }
    ```

    Note: This endpoint requires Phase 2 relationship support to be fully implemented.
    """
    # TODO: Implement relationship traversal
    # This requires:
    # 1. Loading RelationshipDefinition
    # 2. Determining target entity
    # 3. Building appropriate join query
    # 4. Applying RBAC for target entity

    raise HTTPException(
        status_code=501,
        detail="Relationship traversal not yet implemented in Phase 2"
    )


# ==============================================================================
# Metadata Endpoints
# ==============================================================================

@router.get(
    "/{entity_name}/metadata",
    summary="Get Entity Metadata",
    description="Get field definitions and relationship metadata for an entity"
)
async def get_entity_metadata(
    entity_name: str = Path(..., description="Entity name"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get metadata for a dynamic entity.

    Returns field definitions, relationships, and other entity metadata.

    **Response:**
    ```json
    {
      "entity_name": "customers",
      "display_name": "Customers",
      "fields": [...],
      "relationships": [...]
    }
    ```
    """
    from app.services.runtime_model_generator import RuntimeModelGenerator

    generator = RuntimeModelGenerator(db)
    tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None

    try:
        fields = generator.get_field_definitions(entity_name, tenant_id)
        relationships = generator.get_relationship_definitions(entity_name, tenant_id)

        # Get entity definition for display name
        entity_def = generator._load_entity_definition(entity_name, tenant_id)

        return {
            "entity_name": entity_name,
            "display_name": entity_def.label if entity_def else entity_name,
            "fields": fields,
            "relationships": relationships
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting metadata for {entity_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
