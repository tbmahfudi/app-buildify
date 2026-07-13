"""
Lookup Configuration API Router

API endpoints for the Lookup Configuration feature.
"""

import json
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.schemas.lookup import (
    CascadingLookupRuleCreate,
    CascadingLookupRuleResponse,
    LookupConfigurationCreate,
    LookupConfigurationResponse,
    LookupConfigurationUpdate,
    LookupDataResponse,
)
from app.services.lookup_service import LookupService

router = APIRouter(prefix="/api/v1/lookups", tags=["Lookup Configuration"])


# ==================== Lookup Configuration Endpoints ====================


@router.post("/configurations", response_model=LookupConfigurationResponse)
async def create_lookup_configuration(
    config: LookupConfigurationCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """Create a new lookup configuration"""
    service = LookupService(db, current_user)
    return await service.create_configuration(config)


@router.get("/configurations", response_model=List[LookupConfigurationResponse])
async def list_lookup_configurations(
    source_type: Optional[str] = Query(None),
    entity_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all lookup configurations"""
    service = LookupService(db, current_user)
    return await service.list_configurations(source_type, entity_id)


@router.get("/configurations/{config_id}", response_model=LookupConfigurationResponse)
async def get_lookup_configuration(
    config_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """Get lookup configuration"""
    service = LookupService(db, current_user)
    return await service.get_configuration(config_id)


@router.put("/configurations/{config_id}", response_model=LookupConfigurationResponse)
async def update_lookup_configuration(
    config_id: UUID,
    config: LookupConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update lookup configuration"""
    service = LookupService(db, current_user)
    return await service.update_configuration(config_id, config)


@router.delete("/configurations/{config_id}")
async def delete_lookup_configuration(
    config_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)
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
    current_user=Depends(get_current_user),
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

    # Story 5.2.5 — apply filter_expression from cascading depends_on_field
    if parent_value is not None:
        from app.models.lookup import LookupConfiguration

        cfg = db.query(LookupConfiguration).filter(LookupConfiguration.id == config_id).first()
        if cfg and getattr(cfg, "filter_expression", None) and getattr(cfg, "depends_on_field", None):
            try:
                import json as _json

                fe = cfg.filter_expression
                # Replace placeholder with actual parent_value
                fe_resolved = fe.replace("{parent_value}", str(parent_value))
                extra_filter = _json.loads(fe_resolved) if isinstance(fe_resolved, str) else fe_resolved
                if filters_dict:
                    filters_dict.update(extra_filter)
                else:
                    filters_dict = extra_filter
            except Exception:
                pass

    return await service.get_lookup_data(
        config_id, search=search, filters=filters_dict, parent_value=parent_value, page=page, page_size=page_size
    )


# ==================== Cascading Lookup Rule Endpoints ====================


@router.post("/cascading-rules", response_model=CascadingLookupRuleResponse)
async def create_cascading_rule(
    rule: CascadingLookupRuleCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """Create a cascading lookup rule"""
    service = LookupService(db, current_user)
    return await service.create_cascading_rule(rule)


@router.get("/cascading-rules", response_model=List[CascadingLookupRuleResponse])
async def list_cascading_rules(
    parent_lookup_id: Optional[UUID] = Query(None),
    child_lookup_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List cascading lookup rules"""
    service = LookupService(db, current_user)
    return await service.list_cascading_rules(parent_lookup_id, child_lookup_id)
