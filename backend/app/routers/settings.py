import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import create_audit_log
from app.core.dependencies import get_current_user, get_db, has_permission
from app.models.settings import TenantSettings, UserSettings
from app.models.user import User
from app.schemas.settings import TenantSettingsResponse, TenantSettingsUpdate, UserSettingsResponse, UserSettingsUpdate

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

# ============= USER SETTINGS =============


@router.get("/user", response_model=UserSettingsResponse)
def get_user_settings(db: Session = Depends(get_db), current_user: User = Depends(has_permission("settings:read:own"))):
    """Get current user's settings - requires settings:read:own"""
    settings = db.query(UserSettings).filter(UserSettings.user_id == str(current_user.id)).first()

    if not settings:
        # Create default settings
        settings = UserSettings(
            id=str(uuid.uuid4()),
            user_id=str(current_user.id),
            theme="light",
            language="en",
            timezone="UTC",
            density="normal",
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
        id=str(settings.id),
        user_id=settings.user_id,
        theme=settings.theme,
        language=settings.language,
        timezone=settings.timezone,
        density=settings.density,
        preferences=preferences,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.put("/user", response_model=UserSettingsResponse)
def update_user_settings(
    updates: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("settings:update:own")),
):
    """Update current user's settings - requires settings:update:own"""
    settings = db.query(UserSettings).filter(UserSettings.user_id == str(current_user.id)).first()

    if not settings:
        # Create new settings
        settings = UserSettings(
            id=str(uuid.uuid4()),
            user_id=str(current_user.id),
            theme=updates.theme or "light",
            language=updates.language or "en",
            timezone=updates.timezone or "UTC",
            density=updates.density or "normal",
            preferences=json.dumps(updates.preferences) if updates.preferences else None,
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
        status="success",
    )

    preferences = None
    if settings.preferences:
        try:
            preferences = json.loads(settings.preferences)
        except:
            preferences = None

    return UserSettingsResponse(
        id=str(settings.id),
        user_id=settings.user_id,
        theme=settings.theme,
        language=settings.language,
        timezone=settings.timezone,
        density=settings.density,
        preferences=preferences,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


# ============= TENANT SETTINGS =============


@router.get("/tenant", response_model=TenantSettingsResponse)
def get_tenant_settings(
    tenant_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("settings:read:tenant")),
):
    """Get tenant settings (uses current user's tenant if not specified) - requires settings:read:tenant"""

    # Determine tenant_id
    target_tenant = tenant_id or str(current_user.tenant_id) if current_user.tenant_id else None

    if not target_tenant:
        # Return default settings for users without a tenant
        return TenantSettingsResponse(
            id=str(uuid.uuid4()),
            tenant_id=None,
            tenant_name="Default",
            logo_url=None,
            primary_color="#1976d2",
            secondary_color="#424242",
            theme_config=None,
            enabled_features=None,
            settings=None,
            created_at=None,
            updated_at=None,
            updated_by=None,
        )

    # Check permissions
    if tenant_id and str(tenant_id) != str(current_user.tenant_id) and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot access other tenant's settings")

    settings = db.query(TenantSettings).filter(TenantSettings.tenant_id == target_tenant).first()  # tenant_scope

    if not settings:
        # Create default settings
        settings = TenantSettings(id=str(uuid.uuid4()), tenant_id=target_tenant)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    # Parse JSON fields
    theme_config = json.loads(settings.theme_config) if settings.theme_config else None
    enabled_features = json.loads(settings.enabled_features) if settings.enabled_features else None
    tenant_settings = json.loads(settings.settings) if settings.settings else None

    return TenantSettingsResponse(
        id=str(settings.id),
        tenant_id=settings.tenant_id,
        tenant_name=settings.tenant_name,
        logo_url=settings.logo_url,
        primary_color=settings.primary_color,
        secondary_color=settings.secondary_color,
        theme_config=theme_config,
        enabled_features=enabled_features,
        settings=tenant_settings,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
        updated_by=settings.updated_by,
    )


@router.put("/tenant", response_model=TenantSettingsResponse)
def update_tenant_settings(
    updates: TenantSettingsUpdate,
    tenant_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("settings:update:tenant")),
):
    """Update tenant settings - requires settings:update:tenant"""

    # Determine tenant_id — always resolve to str so VARCHAR filter works (DEF-025)
    target_tenant = tenant_id or (str(current_user.tenant_id) if current_user.tenant_id else None)

    if not target_tenant:
        raise HTTPException(status_code=400, detail="No tenant context")

    # Check permissions — use str() on both sides to handle UUID vs str (DEF-026)
    if tenant_id and str(tenant_id) != str(current_user.tenant_id) and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot modify other tenant's settings")

    settings = db.query(TenantSettings).filter(TenantSettings.tenant_id == target_tenant).first()  # tenant_scope

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
            updated_by=str(current_user.id),
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
        context_info={"tenant_id": target_tenant},
        status="success",
    )

    # Parse for response
    theme_config = json.loads(settings.theme_config) if settings.theme_config else None
    enabled_features = json.loads(settings.enabled_features) if settings.enabled_features else None
    tenant_settings = json.loads(settings.settings) if settings.settings else None

    return TenantSettingsResponse(
        id=str(settings.id),
        tenant_id=settings.tenant_id,
        tenant_name=settings.tenant_name,
        logo_url=settings.logo_url,
        primary_color=settings.primary_color,
        secondary_color=settings.secondary_color,
        theme_config=theme_config,
        enabled_features=enabled_features,
        settings=tenant_settings,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
        updated_by=settings.updated_by,
    )


# ─── Story 14.2.2 — Email Template Endpoints ───────────────────────────────

AVAILABLE_EMAIL_TEMPLATES = [
    "welcome_user",
    "password_reset",
    "account_locked",
    "password_expiring",
    "workflow_approval_request",
]


@router.get("/email-templates")
def list_email_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List available email templates and any tenant overrides. Story 14.2.2"""
    from app.models.notification_config import NotificationConfig

    nc = (
        db.query(NotificationConfig)
        .filter(NotificationConfig.tenant_id == current_user.tenant_id)  # tenant_scope
        .first()
    )
    overrides = {}
    if nc and getattr(nc, "email_template_overrides", None):
        overrides = nc.email_template_overrides or {}
    return {
        "templates": [
            {
                "name": t,
                "has_override": t in overrides,
                "override": overrides.get(t),
            }
            for t in AVAILABLE_EMAIL_TEMPLATES
        ]
    }


@router.put("/email-templates/{template_name}")
def update_email_template(
    template_name: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("settings:update:tenant")),
):
    """Override subject/body for an email template per tenant. Story 14.2.2"""
    from app.models.notification_config import NotificationConfig

    if template_name not in AVAILABLE_EMAIL_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")

    nc = (
        db.query(NotificationConfig)
        .filter(NotificationConfig.tenant_id == current_user.tenant_id)  # tenant_scope
        .first()
    )
    if not nc:
        raise HTTPException(status_code=404, detail="Notification config not found for this tenant")

    overrides = {}
    if getattr(nc, "email_template_overrides", None):
        overrides = dict(nc.email_template_overrides)

    overrides[template_name] = {
        "subject": payload.get("subject"),
        "body": payload.get("body"),
    }

    # Store overrides — use JSON extra_config if email_template_overrides column absent
    if hasattr(nc, "email_template_overrides"):
        nc.email_template_overrides = overrides
    elif hasattr(nc, "extra_config"):
        extra = dict(nc.extra_config or {})
        extra["email_template_overrides"] = overrides
        nc.extra_config = extra
    else:
        raise HTTPException(status_code=500, detail="No suitable column to store template overrides")

    db.commit()
    return {"message": f"Template '{template_name}' updated", "template": overrides[template_name]}
