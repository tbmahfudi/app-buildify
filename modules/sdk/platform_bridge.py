"""
PlatformBridge — the only sanctioned way for modules to interact with platform services.

Module developers use this instead of importing platform internals directly.
If you need something that isn't here, file a platform request:
  platform-requests/open/REQ-NNN-your-feature.md
"""
from typing import Optional, List, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


class PlatformBridge:
    """
    Provides controlled access to platform capabilities for module code.
    Instantiated by the platform loader and injected into each module.
    """

    def __init__(self, platform_services: Dict[str, Any] = None):
        self._services = platform_services or {}

    # ── Audit logging ────────────────────────────────────────────────────────
    def audit_log(self, action: str, entity_type: str = None,
                  entity_id: str = None, details: dict = None,
                  user_id: str = None, tenant_id: str = None) -> None:
        """Write an entry to the platform audit log."""
        svc = self._services.get('audit')
        if svc:
            svc(action=action, entity_type=entity_type, entity_id=entity_id,
                details=details or {}, user_id=user_id, tenant_id=tenant_id)
        else:
            logger.info(f"[AUDIT] {action} entity={entity_type}:{entity_id}")

    # ── Notifications ────────────────────────────────────────────────────────
    def send_notification(self, user_id: str, title: str, message: str,
                          notification_type: str = "info",
                          tenant_id: str = None) -> bool:
        """Send an in-app notification to a user."""
        svc = self._services.get('notifications')
        if svc:
            return svc(user_id=user_id, title=title, message=message,
                       notification_type=notification_type, tenant_id=tenant_id)
        logger.warning("Notification service not available")
        return False

    # ── Email ────────────────────────────────────────────────────────────────
    def send_email(self, to: str, template_name: str,
                   context: Dict[str, Any] = None) -> bool:
        """Send an email using a platform email template."""
        svc = self._services.get('email')
        if svc:
            return svc(to=to, template_name=template_name, context=context or {})
        logger.warning("Email service not available")
        return False

    # ── Tenant context ───────────────────────────────────────────────────────
    def get_tenant_config(self, tenant_id: str, key: str,
                          default: Any = None) -> Any:
        """Read a tenant configuration value."""
        svc = self._services.get('tenant_config')
        if svc:
            return svc(tenant_id=tenant_id, key=key, default=default)
        return default

    # ── Event bus ────────────────────────────────────────────────────────────
    def emit_event(self, event_name: str, payload: Dict[str, Any],
                   tenant_id: str = None) -> None:
        """Emit a platform event other modules or automations can subscribe to."""
        svc = self._services.get('event_bus')
        if svc:
            svc(event_name=event_name, payload=payload, tenant_id=tenant_id)
        else:
            logger.debug(f"[EVENT] {event_name} payload={payload}")

    # ── Feature flags ────────────────────────────────────────────────────────
    def is_feature_enabled(self, flag: str, tenant_id: str = None) -> bool:
        """Check if a platform feature flag is enabled (for this tenant)."""
        svc = self._services.get('feature_flags')
        if svc:
            return svc(flag=flag, tenant_id=tenant_id)
        return False

    # ── Need something not listed here? ─────────────────────────────────────
    # File a platform request: platform-requests/open/REQ-NNN-description.md
    # The platform team will evaluate and add it to this bridge.
