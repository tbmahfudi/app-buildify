# Module SDK Reference

Module developers import exclusively from `modules.sdk`. This document covers every
public symbol.

---

## PlatformBridge

Injected into your module's constructor. Use it for all platform interactions.

### `audit_log(action, entity_type, entity_id, details, user_id, tenant_id)`

Write an entry to the platform audit log.

```python
self.bridge.audit_log(
    action="invoice.created",
    entity_type="invoice",
    entity_id=str(invoice.id),
    details={"amount": 1500.00},
    user_id=current_user.id,
    tenant_id=current_user.tenant_id,
)
```

### `send_notification(user_id, title, message, notification_type, tenant_id)`

Send an in-app notification to a specific user.

```python
self.bridge.send_notification(
    user_id=approver_id,
    title="Invoice awaiting approval",
    message=f"Invoice #{invoice.number} needs your review.",
    notification_type="info",
    tenant_id=tenant_id,
)
```

### `send_email(to, template_name, context)`

Send a templated email via the platform mailer.

```python
self.bridge.send_email(
    to=customer.email,
    template_name="invoice_sent",
    context={"invoice_number": invoice.number, "amount": invoice.total},
)
```

### `get_tenant_config(tenant_id, key, default)`

Read a configuration value set by the tenant admin.

```python
currency = self.bridge.get_tenant_config(tenant_id, "default_currency", "USD")
```

### `emit_event(event_name, payload, tenant_id)`

Emit an event on the platform event bus. Other modules or automations can subscribe.

```python
self.bridge.emit_event(
    event_name="invoice.paid",
    payload={"invoice_id": str(invoice.id), "amount": payment.amount},
    tenant_id=tenant_id,
)
```

### `is_feature_enabled(flag, tenant_id)`

Check whether a platform feature flag is on for this tenant.

```python
if self.bridge.is_feature_enabled("beta_ai_suggestions", tenant_id):
    # show AI panel
```

---

## BaseModule lifecycle hooks

Override these in your module class. Always call `super()` first.

| Hook | When called | Use for |
|------|-------------|---------|
| `pre_install(db)` | Before platform-wide install | Prerequisite checks |
| `post_install(db)` | After platform-wide install | Default data, reference seeds |
| `pre_enable(db, tenant_id)` | Before enabling for a tenant | Tenant-level checks |
| `post_enable(db, tenant_id)` | After enabling for a tenant | Per-tenant bootstrap data |
| `pre_disable(db, tenant_id)` | Before disabling for a tenant | Safety checks |
| `post_disable(db, tenant_id)` | After disabling for a tenant | Cleanup, archiving (no deletes) |
| `pre_uninstall(db)` | Before platform-wide uninstall | Check no tenants still enabled |
| `post_uninstall(db)` | After platform-wide uninstall | Final cleanup |

---

## Manifest format

`manifest.json` at the module root. Required fields:

```json
{
  "name": "my_module",
  "display_name": "My Module",
  "version": "1.0.0",
  "description": "What this module does",
  "author": "Team Name",
  "entry_point": "module.js",
  "routes": [...],
  "navigation": { "primary_menu": true, "menu_items": [...] },
  "dependencies": { "required_modules": [], "optional_modules": [] },
  "permissions": [
    {
      "code": "my_module:resource:action:scope",
      "name": "Human readable name",
      "description": "What it allows",
      "category": "my_module",
      "scope": "company"
    }
  ],
  "subscription_tier": "basic"
}
```

---

## Tenant isolation requirements

Every SQLAlchemy model MUST:

1. Set the class attribute `__tenant_scoped__ = True`
2. Include `tenant_id = Column(String(36), nullable=False, index=True)`

The platform's `TenantScopeListener` automatically filters all queries
by `tenant_id`. Superusers bypass this filter.

**Never** query across tenants from module code. If you have a genuine
cross-tenant need, file a platform request.

---

## Filing a platform request

When `PlatformBridge` doesn't expose a capability you need:

1. `cp platform-requests/template.md platform-requests/open/REQ-NNN-short-title.md`
2. Fill in all sections — be specific about the API shape you need
3. The platform team reviews `open/` in their regular sprint
4. Once implemented, the file moves to `resolved/` with notes

Do **not** work around this by importing from `backend.app`.
