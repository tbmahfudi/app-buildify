"""
Generic CRUD helper functions to eliminate code duplication.

This module provides reusable functions for common database operations:
- Entity lookup by ID with automatic 404 handling
- Duplicate code checking
- Parent entity validation
- Generic entity creation with UUID generation

These helpers consolidate ~200+ lines of duplicate code across routers.
"""
import uuid
from typing import Any, Dict, List, Optional, Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.base import Base

# Type variable for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)


def get_entity_by_id(
    db: Session,
    model: Type[ModelType],
    entity_id: str,
    error_msg: Optional[str] = None
) -> ModelType:
    """
    Get an entity by ID with automatic 404 handling.

    Consolidates the pattern:
        entity = db.query(Model).filter(Model.id == id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")

    Args:
        db: Database session
        model: SQLAlchemy model class
        entity_id: Entity ID to lookup
        error_msg: Custom error message (default: "{Model} not found")

    Returns:
        Model instance

    Raises:
        HTTPException: 404 if entity not found

    Example:
        >>> company = get_entity_by_id(db, Company, company_id)
        >>> user = get_entity_by_id(db, User, user_id, "User not found")
    """
    entity = db.query(model).filter(model.id == entity_id).first()

    if not entity:
        msg = error_msg or f"{model.__name__} not found"
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg
        )

    return entity


def check_duplicate_code(
    db: Session,
    model: Type[ModelType],
    code: str,
    parent_field: Optional[str] = None,
    parent_id: Optional[str] = None,
    exclude_id: Optional[str] = None,
    error_msg: Optional[str] = None
) -> None:
    """
    Check if a code already exists for an entity.

    Consolidates the pattern:
        existing = db.query(Model).filter(Model.code == code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Code already exists")

    Args:
        db: Database session
        model: SQLAlchemy model class
        code: Code value to check
        parent_field: Optional parent field name (e.g., "company_id")
        parent_id: Optional parent ID for scoped uniqueness
        exclude_id: Optional ID to exclude (for updates)
        error_msg: Custom error message

    Raises:
        HTTPException: 400 if duplicate code found

    Example:
        >>> # Simple check
        >>> check_duplicate_code(db, Company, "ACME")

        >>> # Scoped to parent
        >>> check_duplicate_code(db, Branch, "MAIN", "company_id", company_id)

        >>> # Exclude current entity (for updates)
        >>> check_duplicate_code(db, Company, "ACME", exclude_id=company_id)
    """
    query = db.query(model).filter(model.code == code)

    # Scope to parent if provided
    if parent_field and parent_id:
        query = query.filter(getattr(model, parent_field) == parent_id)

    # Exclude current entity (for updates)
    if exclude_id:
        query = query.filter(model.id != exclude_id)

    existing = query.first()

    if existing:
        msg = error_msg or f"{model.__name__} code already exists"
        if parent_field:
            msg = f"{model.__name__} code already exists in this {parent_field.replace('_id', '')}"

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )


def validate_parent_exists(
    db: Session,
    parent_model: Type[ModelType],
    parent_id: str,
    parent_name: Optional[str] = None
) -> ModelType:
    """
    Validate that a parent entity exists before creating/updating child.

    Consolidates the pattern:
        parent = db.query(ParentModel).filter(ParentModel.id == parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent not found")

    Args:
        db: Database session
        parent_model: Parent model class
        parent_id: Parent entity ID
        parent_name: Optional custom name for error message

    Returns:
        Parent model instance

    Raises:
        HTTPException: 404 if parent not found

    Example:
        >>> company = validate_parent_exists(db, Company, company_id)
        >>> validate_parent_exists(db, Branch, branch_id, "Branch")
    """
    parent_name = parent_name or parent_model.__name__
    return get_entity_by_id(db, parent_model, parent_id, f"{parent_name} not found")


def validate_parent_relationship(
    db: Session,
    child_entity: Any,
    parent_field: str,
    grandparent_field: str,
    parent_model: Type[ModelType],
    error_msg: Optional[str] = None
) -> None:
    """
    Validate that a parent entity belongs to the correct grandparent.

    Consolidates the pattern:
        if branch.company_id != department.company_id:
            raise HTTPException(status_code=400, detail="Branch does not belong to this company")

    Args:
        db: Database session
        child_entity: Child entity being created/updated
        parent_field: Field name linking to parent (e.g., "branch_id")
        grandparent_field: Field name linking to grandparent (e.g., "company_id")
        parent_model: Parent model class
        error_msg: Custom error message

    Raises:
        HTTPException: 400 if relationship invalid

    Example:
        >>> # Ensure branch belongs to the same company as department
        >>> validate_parent_relationship(
        ...     db, department, "branch_id", "company_id", Branch,
        ...     "Branch does not belong to this company"
        ... )
    """
    parent_id = getattr(child_entity, parent_field)
    expected_grandparent_id = getattr(child_entity, grandparent_field)

    parent = get_entity_by_id(db, parent_model, parent_id)
    actual_grandparent_id = getattr(parent, grandparent_field)

    if actual_grandparent_id != expected_grandparent_id:
        msg = error_msg or f"{parent_model.__name__} does not belong to the specified {grandparent_field.replace('_id', '')}"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )


def create_entity_with_uuid(
    db: Session,
    model: Type[ModelType],
    data: Dict[str, Any],
    commit: bool = True
) -> ModelType:
    """
    Create an entity with automatic UUID generation.

    Consolidates the pattern:
        entity = Model(id=str(uuid.uuid4()), **data)
        db.add(entity)
        db.commit()
        db.refresh(entity)

    Args:
        db: Database session
        model: SQLAlchemy model class
        data: Entity data as dictionary
        commit: Whether to commit immediately (default: True)

    Returns:
        Created model instance

    Example:
        >>> company = create_entity_with_uuid(db, Company, {
        ...     "code": "ACME",
        ...     "name": "Acme Corp"
        ... })
    """
    # Generate UUID if not provided
    if 'id' not in data:
        data['id'] = str(uuid.uuid4())

    entity = model(**data)
    db.add(entity)

    if commit:
        try:
            db.commit()
            db.refresh(entity)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database integrity error: {str(e)}"
            )

    return entity


def soft_delete_entity(
    db: Session,
    entity: ModelType,
    commit: bool = True
) -> ModelType:
    """
    Soft delete an entity by setting is_active to False.

    Args:
        db: Database session
        entity: Entity to soft delete
        commit: Whether to commit immediately (default: True)

    Returns:
        Updated entity

    Example:
        >>> company = get_entity_by_id(db, Company, company_id)
        >>> soft_delete_entity(db, company)
    """
    if hasattr(entity, 'is_active'):
        entity.is_active = False

        if commit:
            db.commit()
            db.refresh(entity)
    else:
        raise ValueError(f"{entity.__class__.__name__} does not support soft delete")

    return entity


def hard_delete_entity(
    db: Session,
    entity: ModelType,
    commit: bool = True
) -> None:
    """
    Hard delete an entity from the database.

    Args:
        db: Database session
        entity: Entity to delete
        commit: Whether to commit immediately (default: True)

    Example:
        >>> company = get_entity_by_id(db, Company, company_id)
        >>> hard_delete_entity(db, company)
    """
    db.delete(entity)

    if commit:
        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete entity: {str(e)}"
            )


def update_entity_fields(
    entity: ModelType,
    data: Dict[str, Any],
    exclude_fields: Optional[List[str]] = None
) -> ModelType:
    """
    Update entity fields from a dictionary.

    Consolidates the pattern:
        for field, value in data.dict(exclude_unset=True).items():
            setattr(entity, field, value)

    Args:
        entity: Entity to update
        data: Data dictionary with new values
        exclude_fields: Fields to exclude from update

    Returns:
        Updated entity (not committed)

    Example:
        >>> company = get_entity_by_id(db, Company, company_id)
        >>> update_entity_fields(company, {"name": "New Name"}, exclude_fields=["id", "created_at"])
        >>> db.commit()
    """
    exclude_fields = exclude_fields or ["id", "created_at"]

    for field, value in data.items():
        if field not in exclude_fields and hasattr(entity, field):
            setattr(entity, field, value)

    return entity


def bulk_create_entities(
    db: Session,
    model: Type[ModelType],
    data_list: List[Dict[str, Any]],
    commit: bool = True
) -> List[ModelType]:
    """
    Bulk create multiple entities with UUID generation.

    Args:
        db: Database session
        model: SQLAlchemy model class
        data_list: List of entity data dictionaries
        commit: Whether to commit immediately (default: True)

    Returns:
        List of created entities

    Example:
        >>> companies = bulk_create_entities(db, Company, [
        ...     {"code": "ACME", "name": "Acme Corp"},
        ...     {"code": "INITECH", "name": "Initech Inc"}
        ... ])
    """
    entities = []

    for data in data_list:
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        entities.append(model(**data))

    db.add_all(entities)

    if commit:
        try:
            db.commit()
            for entity in entities:
                db.refresh(entity)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bulk create failed: {str(e)}"
            )

    return entities
