"""
Lookup Configuration API Router

API endpoints for the Lookup Configuration feature.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import json

from app.core.dependencies import get_db, get_current_user
from app.schemas.lookup import (
    LookupConfigurationCreate,
    LookupConfigurationUpdate,
    LookupConfigurationResponse,
    LookupDataResponse,
    CascadingLookupRuleCreate,
    CascadingLookupRuleUpdate,
    CascadingLookupRuleResponse,
)
from app.services.lookup_service import LookupService


router = APIRouter(prefix="/api/v1/lookups", tags=["Lookup Configuration"])


# ==================== Lookup Configuration Endpoints ====================

@router.post("/configurations", response_model=LookupConfigurationResponse)
async def create_lookup_configuration(
    config: LookupConfigurationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new lookup configuration"""
    service = LookupService(db, current_user)
    return await service.create_configuration(config)


@router.get("/configurations", response_model=List[LookupConfigurationResponse])
async def list_lookup_configurations(
    source_type: Optional[str] = Query(None),
    entity_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all lookup configurations"""
    service = LookupService(db, current_user)
    return await service.list_configurations(source_type, entity_id)


@router.get("/configurations/{config_id}", response_model=LookupConfigurationResponse)
async def get_lookup_configuration(
    config_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get lookup configuration"""
    service = LookupService(db, current_user)
    return await service.get_configuration(config_id)


@router.put("/configurations/{config_id}", response_model=LookupConfigurationResponse)
async def update_lookup_configuration(
    config_id: UUID,
    config: LookupConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update lookup configuration"""
    service = LookupService(db, current_user)
    return await service.update_configuration(config_id, config)


@router.delete("/configurations/{config_id}")
async def delete_lookup_configuration(
    config_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete lookup configuration"""
    service = LookupService(db, current_user)
    return await service.delete_configuration(config_id)


# ==================== Lookup Data Endpoints ====================

@router.get("/configurations/{config_id}/data", response_model=LookupDataResponse)
async def get_lookup_data(
    config_id: UUID,
    search: Optional[str] = Query(None),
    filters: Optional[str] = Query(None),  # JSON string
    parent_value: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get lookup data (dropdown options)"""
    service = LookupService(db, current_user)

    # Parse filters if provided
    filters_dict = None
    if filters:
        try:
            filters_dict = json.loads(filters)
        except json.JSONDecodeError:
            pass

    return await service.get_lookup_data(
        config_id,
        search=search,
        filters=filters_dict,
        parent_value=parent_value,
        page=page,
        page_size=page_size
    )


# ==================== Cascading Lookup Rule Endpoints ====================

@router.post("/cascading-rules", response_model=CascadingLookupRuleResponse)
async def create_cascading_rule(
    rule: CascadingLookupRuleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a cascading lookup rule"""
    service = LookupService(db, current_user)
    return await service.create_cascading_rule(rule)


@router.get("/cascading-rules", response_model=List[CascadingLookupRuleResponse])
async def list_cascading_rules(
    parent_lookup_id: Optional[UUID] = Query(None),
    child_lookup_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List cascading lookup rules"""
    service = LookupService(db, current_user)
    return await service.list_cascading_rules(parent_lookup_id, child_lookup_id)
