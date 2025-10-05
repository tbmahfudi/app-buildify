from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
import json

from app.core.dependencies import get_db, get_current_user, has_role
from app.models.user import User
from app.models.settings import UserSettings, TenantSettings
from app.schemas.settings import (
    UserSettingsResponse, UserSettingsUpdate,
    TenantSettingsResponse, TenantSettingsUpdate
)
from app.core.audit import create_audit_log

router = APIRouter(prefix="/api/settings", tags=["settings"])

# ============= USER SETTINGS =============

@router.get("/user", response_model=UserSettingsResponse)
def get_user_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's settings"""
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == str(current_user.id)
    ).first()
    
    if not settings:
        # Create default settings
        settings = UserSettings(
            id=str(uuid.uuid4()),
            user_id=str(current_user.id),
            theme="light",
            language="en",
            timezone="UTC",
            density="normal"
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    # Parse preferences JSON
    preferences = None
    if settings.preferences:
        try:
            preferences = json.loads(settings.preferences)
        except:
            preferences = None
    
    return UserSettingsResponse(
        theme=settings.theme,
        language=settings.language,
        timezone=settings.timezone,
        density=settings.density,
        preferences=preferences,
        updated_at=settings.updated_at
    )

@router.put("/user", response_model=UserSettingsResponse)
def update_user_settings(
    updates: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user's settings"""
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == str(current_user.id)
    ).first()
    
    if not settings:
        # Create new settings
        settings = UserSettings(
            id=str(uuid.uuid4()),
            user_id=str(current_user.id),
            theme=updates.theme or "light",
            language=updates.language or "en",
            timezone=updates.timezone or "UTC",
            density=updates.density or "normal",
            preferences=json.dumps(updates.preferences) if updates.preferences else None
        )
        db.add(settings)
    else:
        # Update existing
        if updates.theme is not None:
            settings.theme = updates.theme
        if updates.language is not None:
            settings.language = updates.language
        if updates.timezone is not None:
            settings.timezone = updates.timezone
        if updates.density is not None:
            settings.density = updates.density
        if updates.preferences is not None:
            settings.preferences = json.dumps(updates.preferences)
    
    db.commit()
    db.refresh(settings)
    
    # Audit
    create_audit_log(
        db=db,
        action="UPDATE_USER_SETTINGS",
        user=current_user,
        entity_type="user_settings",
        entity_id=str(settings.id),
        status="success"
    )
    
    preferences = None
    if settings.preferences:
        try:
            preferences = json.loads(settings.preferences)
        except:
            preferences = None
    
    return UserSettingsResponse(
        theme=settings.theme,
        language=settings.language,
        timezone=settings.timezone,
        density=settings.density,
        preferences=preferences,
        updated_at=settings.updated_at
    )

# ============= TENANT SETTINGS =============

@router.get("/tenant", response_model=TenantSettingsResponse)
def get_tenant_settings(
    tenant_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tenant settings (uses current user's tenant if not specified)"""
    
    # Determine tenant_id
    target_tenant = tenant_id or current_user.tenant_id
    
    if not target_tenant:
        raise HTTPException(status_code=400, detail="No tenant context")
    
    # Check permissions
    if tenant_id and tenant_id != current_user.tenant_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot access other tenant's settings")
    
    settings = db.query(TenantSettings).filter(
        TenantSettings.tenant_id == target_tenant
    ).first()
    
    if not settings:
        # Create default settings
        settings = TenantSettings(
            id=str(uuid.uuid4()),
            tenant_id=target_tenant
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    # Parse JSON fields
    theme_config = json.loads(settings.theme_config) if settings.theme_config else None
    enabled_features = json.loads(settings.enabled_features) if settings.enabled_features else None
    tenant_settings = json.loads(settings.settings) if settings.settings else None
    
    return TenantSettingsResponse(
        tenant_id=settings.tenant_id,
        tenant_name=settings.tenant_name,
        logo_url=settings.logo_url,
        primary_color=settings.primary_color,
        secondary_color=settings.secondary_color,
        theme_config=theme_config,
        enabled_features=enabled_features,
        settings=tenant_settings,
        updated_at=settings.updated_at
    )

@router.put("/tenant", response_model=TenantSettingsResponse)
def update_tenant_settings(
    updates: TenantSettingsUpdate,
    tenant_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role("admin"))
):
    """Update tenant settings (admin only)"""
    
    # Determine tenant_id
    target_tenant = tenant_id or current_user.tenant_id
    
    if not target_tenant:
        raise HTTPException(status_code=400, detail="No tenant context")
    
    # Check permissions
    if tenant_id and tenant_id != current_user.tenant_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot modify other tenant's settings")
    
    settings = db.query(TenantSettings).filter(
        TenantSettings.tenant_id == target_tenant
    ).first()
    
    if not settings:
        # Create new
        settings = TenantSettings(
            id=str(uuid.uuid4()),
            tenant_id=target_tenant,
            tenant_name=updates.tenant_name,
            logo_url=updates.logo_url,
            primary_color=updates.primary_color,
            secondary_color=updates.secondary_color,
            theme_config=json.dumps(updates.theme_config) if updates.theme_config else None,
            enabled_features=json.dumps(updates.enabled_features) if updates.enabled_features else None,
            settings=json.dumps(updates.settings) if updates.settings else None,
            updated_by=str(current_user.id)
        )
        db.add(settings)
    else:
        # Update existing
        if updates.tenant_name is not None:
            settings.tenant_name = updates.tenant_name
        if updates.logo_url is not None:
            settings.logo_url = updates.logo_url
        if updates.primary_color is not None:
            settings.primary_color = updates.primary_color
        if updates.secondary_color is not None:
            settings.secondary_color = updates.secondary_color
        if updates.theme_config is not None:
            settings.theme_config = json.dumps(updates.theme_config)
        if updates.enabled_features is not None:
            settings.enabled_features = json.dumps(updates.enabled_features)
        if updates.settings is not None:
            settings.settings = json.dumps(updates.settings)
        
        settings.updated_by = str(current_user.id)
    
    db.commit()
    db.refresh(settings)
    
    # Audit
    create_audit_log(
        db=db,
        action="UPDATE_TENANT_SETTINGS",
        user=current_user,
        entity_type="tenant_settings",
        entity_id=str(settings.id),
        metadata={"tenant_id": target_tenant},
        status="success"
    )
    
    # Parse for response
    theme_config = json.loads(settings.theme_config) if settings.theme_config else None
    enabled_features = json.loads(settings.enabled_features) if settings.enabled_features else None
    tenant_settings = json.loads(settings.settings) if settings.settings else None
    
    return TenantSettingsResponse(
        tenant_id=settings.tenant_id,
        tenant_name=settings.tenant_name,
        logo_url=settings.logo_url,
        primary_color=settings.primary_color,
        secondary_color=settings.secondary_color,
        theme_config=theme_config,
        enabled_features=enabled_features,
        settings=tenant_settings,
        updated_at=settings.updated_at
    )