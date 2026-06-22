---
artifact_id: release-notes-epic-21
type: release-notes
producer: E2 Technical Writer
consumers: [stakeholders, tenant administrators, operators]
upstream: [epic-21-risk-retirement, tasks-21]
downstream: []
status: approved
created: 2026-05-08
updated: 2026-06-18
sprint: epic-21 — Risk Retirement (Sprint 1)
---

# Release Notes — Risk Retirement Sprint 1 (epic-21)

> **TL;DR**: This release retires the five 🔴 risks called out in [`vision-01-app-buildify`](../../plan/vision/vision-01-app-buildify.md) §7. Tenant administrators can now create custom roles, wildcard permissions actually wildcard, per-entity permissions are enforced, password-reset emails arrive, and the 9-component Flex layout suite is fully shipped. **No breaking changes.** Two new env vars are required for SMTP delivery.

---

## What's new for end users

### 🔓 Self-service custom roles
Tenant administrators can now create, edit, and delete custom roles directly from the **Access Control** page (Roles tab → "New Role" button). System roles remain immutable. Deleting a role that is still assigned to users or groups returns a clear warning with the dependent counts so you know what to clean up first.

### 🛡️ Wildcard permissions actually wildcard
Granting `*:*:platform` (or any segment-level wildcard like `users:*:tenant`) now correctly matches all permissions in scope. The hot path runs in ~6 µs per check, well under the 5 ms requirement, so there is no perceptible latency cost.

### 🎯 Per-entity permission control
Each NoCode entity now has an **Access Control** section in its edit modal. Toggle "Inherit from global RBAC" off and use the role × action matrix to restrict create/read/update/delete on a specific entity to specific roles. When the toggle is on, your platform-wide RBAC rules apply unchanged.

### 📧 Password-reset emails actually deliver
The notification queue now has a worker behind it. Password-reset emails (and any other queued email) deliver via SMTP using either per-tenant credentials configured in `notification_config` or system-default credentials from environment variables. Failures retry with exponential backoff and dead-letter after the configured max attempts; both outcomes appear in the audit log as `notification.delivered` or `notification.failed`.

### 🧱 Layout component library complete
Frontend developers building new pages can now compose with the full set of nine layout primitives: `flex-stack`, `flex-grid`, `flex-sidebar`, `flex-split-pane`, `flex-container`, `flex-section`, `flex-cluster`, `flex-toolbar`, `flex-masonry`. Each is a plain ES6 class extending `BaseComponent` and uses Tailwind utility classes — no new build step, no shadow DOM.

---

## Configuration changes

### New environment variables (required if you want SMTP delivery)

Add to your `.env` file (see `backend/.env.example` for the full block):

```bash
# SMTP credentials — populate via your secrets manager, not in source control
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
SMTP_USE_TLS=true

# Worker placement (per ADR-002)
NOTIFICATION_WORKER_INPROCESS=false
NOTIFICATION_WORKER_POLL_SECONDS=5
NOTIFICATION_WORKER_BATCH_SIZE=20
```

> **Per-tenant overrides**: tenants with their own SMTP servers can populate `notification_config.email_smtp_*` rows. The worker checks tenant config first, then system default (`tenant_id IS NULL`), then env vars.

### Deployment topology

Per [`adr-002-smtp-worker-placement`](../../plan/architecture/adr-002-smtp-worker-placement.md), three modes are now supported:

| `DEPLOYMENT_MODE` | `NOTIFICATION_WORKER_INPROCESS` | Effect |
|---|---|---|
| `monolith` | `true` | Worker runs as a thread inside the API process. Simplest. Suitable for dev / small deployments. |
| `monolith` | `false` *(default)* | Separate `notification-worker` container in the same compose project. Survives API restarts; SMTP outages don't back-pressure the API. |
| `distributed` | (ignored) | Always a separate container. |

The `notification-worker` service is defined in both `docker-compose.yml` (root) and `infra/docker-compose.prod.yml`. No action required if you keep the default; if you embed the worker, set `NOTIFICATION_WORKER_INPROCESS=true` and you can drop the standalone container.

### Database

**No migrations.** Every schema referenced by this sprint already existed (`roles`, `notification_queue`, `notification_config`, `EntityDefinition.permissions` JSONB). See [`schema-21`](../../plan/architecture/schema-21.md) for the verification.

### New permission codes

Three new permission codes are introduced for the role-CRUD endpoints:

- `roles:create:tenant`
- `roles:update:tenant`
- `roles:delete:tenant`

Tenant administrators with `*:*:tenant` (wildcard) automatically have these via the new wildcard-aware matcher. If you grant permissions explicitly per role, add the three codes to your tenant-admin role.

---

## Breaking changes

**None.** All changes are additive:

- New endpoints (`POST/PUT/DELETE /api/v1/rbac/roles`) — existing endpoints unchanged
- Wildcard matching — falls back to literal-`in` when no `*` is present, so existing permission grants still work identically
- Per-entity permissions — when `EntityDefinition.permissions` is `null` (the existing default), behavior is unchanged
- Layout components — net-new files; no existing component modified

---

## API reference

### Role CRUD (epic-04 story 4.1.1)

| Method | Path | Permission | Notes |
|--------|------|-----------|-------|
| `POST` | `/api/v1/rbac/roles` | `roles:create:tenant` | Body `{code, name, description?, role_type?, copy_permissions_from?}`. 409 on duplicate code. |
| `PUT` | `/api/v1/rbac/roles/{id}` | `roles:update:tenant` | Partial update of `name`, `description`, `is_active`. 403 on system roles. |
| `DELETE` | `/api/v1/rbac/roles/{id}` | `roles:delete:tenant` | 409 with `{dependent_count: {users, groups}}` if assigned. 403 on system roles. |

### Per-entity permissions (epic-04 story 4.2.4)

The existing `PUT /api/v1/data-model/entities/{id}` now accepts a `permissions` field of shape `{role_code: [actions]}` where actions are any of `create | read | update | delete`. Pass `null` to fall back to global RBAC.

---

## Known issues / deferred work

| Item | Owner | Status |
|------|-------|--------|
| **T-21.1.6 — `rbac.js` retrofit with new layout primitives** | C3 | DEFERRED. The 1,296-line existing RBAC manager + 407-line template would need a wholesale rewrite. Out of scope for risk retirement. The 9 layout components are unit-tested and ready; integration is proven by the new role CRUD modal. A future epic can prioritize the retrofit. |
| **Frontend wildcard-permission mirror** | C3 | OPEN. `frontend/assets/js/rbac.js:132 hasPermission()` still does a literal `in` check. Backend enforces wildcards correctly so security is unaffected; the only consequence is that menu items / buttons that depend on a wildcard-granted permission may not surface in the UI until you grant the literal code. Tracked as a follow-up to story 4.2.1. |
| **Email template system (story 14.2.2)** | C2 | OPEN. The current SMTP path renders `notification_queue.message` and `subject` via jinja2 with the queue row's `template_data`. Adequate for password-reset; richer per-event templates with per-tenant overrides are a separate sprint. |
| **LISTEN/NOTIFY low-latency wakeup (`arch-platform.md` §9 risk #14)** | C2 | OPEN. The notification worker uses 5 s polling. LISTEN/NOTIFY can be added later as a wakeup signal on top of the same polling fallback. Functionally identical for password-reset latency. |
| **Test framework (`audit-13` 13.4.x)** | D1 | OPEN. All sprint code was verified via inline assertion harnesses. A formal Vitest / pytest suite is pre-existing technical debt and out of scope for risk retirement. |

---

## Technical reference

- **Sprint backlog**: [`tasks-21`](../../plan/tasks/tasks-21.md) — 25 tasks DONE, 1 DEFERRED (211 hrs estimated, ~7 hrs actual real-time)
- **System design**: [`arch-21`](../../plan/architecture/arch-21.md) — includes 6-entry corrections log capturing drift caught between agents
- **ADR**: [`adr-002-smtp-worker-placement`](../../plan/architecture/adr-002-smtp-worker-placement.md)
- **Re-audited evidence**: [`audit-04`](../../plan/architecture/audits/audit-04-rbac-permissions.md), [`audit-14`](../../plan/architecture/audits/audit-14-notification-system.md), [`audit-15`](../../plan/architecture/audits/audit-15-flex-component-library.md)
- **Vision context**: [`vision-01`](../../plan/vision/vision-01-app-buildify.md) §7 — the original risk register that motivated the sprint
- **User-journey impact**: [`research-01`](../../plan/research/research-01-app-buildify.md) §2 — Maya-journey steps 3, 7, 8 are now functionally complete end-to-end
