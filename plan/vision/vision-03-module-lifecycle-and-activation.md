---
artifact_id: vision-03-module-lifecycle-and-activation
type: vision
producer: A1 Product Manager
consumers: [A2 Business Analyst]
upstream: [audit-11-module-system, epic-11-module-system, arch-00-platform, vision-01-app-buildify]
downstream: []
status: approved
created: 2026-06-18
updated: 2026-06-18
---

# Vision 03 — Module Lifecycle & Tenant Activation

> **Product Vision Box** (Geoffrey Moore):
> *For **the platform developer** who needs to ship new SaaS modules reliably, and for **tenant and company administrators** who need to switch module features on or off for their organisation, the **Module Lifecycle & Activation** system is a **zero-touch deployment pipeline paired with a self-service activation layer** that lets the developer package and deploy a tested module to production with a single command, and lets tenants activate or deactivate any installed module without engineering involvement. Unlike the current fragmented activation API, broken uninstall path, and manual deployment process, this system gives the developer a repeatable CI/CD-grade packaging and install pipeline, and gives tenants a clean activate/deactivate toggle backed by a complete lifecycle state machine.*

---

## 1. Problem

App-Buildify is a SaaS platform. The platform developer (operator) builds and ships modules; tenants and companies consume them by toggling activation. Two separate problems block this from working end-to-end today:

### Developer side — no reliable packaging and production install pipeline

- There is no defined process for packaging a developed and tested module into a deployable artifact.
- Deploying a new module version to production requires manual steps (copy files, run migrations by hand, restart services). This is error-prone and does not scale.
- Module manifest validation is a presence check on required fields only -- a malformed manifest can be registered and break activation (audit-11 finding: story 11.1.1 PARTIAL).
- The `BaseModule.post_install` / `post_enable` hooks exist in code but the event subscription that fires them is not wired (audit-11 cross-cutting gap). New modules therefore cannot run initialisation logic on installation.

### Tenant / company side -- no coherent activate/deactivate lifecycle

- The backend has the right shape (`/install`, `/enable`, `/disable`) but the platform's own epic claimed a `/activate` path that does not exist. The frontend was built against the wrong contract (audit-11 story 11.1.2 DRIFT). Activation is broken end-to-end.
- There is no `uninstall` path. Disabling a module hides its features but leaves RBAC seeds, menu items, and database rows in place. The tenant footprint cannot be cleaned up.
- There is no tenant-facing UI to see which modules are available to activate or what each module adds (permissions, menu items) before activating it.
- Activation has no audit trail. Every other lifecycle event on the platform produces an `audit_logs` row; module state changes do not.

---

## 2. Target Users

| User | Role | Need |
|---|---|---|
| **Platform Developer (you)** | Builds and ships modules on the SaaS platform | Package a tested module once; deploy to production automatically with no manual steps; be confident the install runs migrations and wires hooks correctly |
| **Tenant Administrator** | Manages which modules are active for their tenant | See which modules are available, activate a module and immediately see its features, deactivate cleanly with no residue |
| **Company Administrator** | Manages which modules are active for their company within a tenant | Same as tenant admin but scoped to their company |

---

## 3. Problem Statement

The platform developer has no repeatable, automated path to deploy a new or updated module to production. Tenant and company admins have no working activate/deactivate flow and cannot cleanly remove a module once enabled. The module system architecture is sound but neither the developer pipeline nor the tenant activation surface is functional end-to-end.

---

## 4. Success Metrics (SMART)

| Metric | Target | Measurement |
|---|---|---|
| **Zero-touch production install** | A packaged module deployed to production with no manual file moves, no manual migration runs, no service restarts beyond the defined rolling restart | Deployment runbook step count = 1 (run the install command) |
| **Developer cycle time** | From `git tag vX.Y.Z` on a module repo to the module appearing as available in production: <= 10 minutes | CI pipeline duration log |
| **Activation reliability** | >= 99% of tenant activation attempts succeed on first try (no 5xx, no silent partial activation) | `module_activation_events` error rate |
| **Clean deactivation** | Zero orphaned RBAC seeds, menu items, or DB rows after deactivation, verified by an automated post-deactivation integrity check | Integrity check script exit code in CI |
| **Audit coverage** | 100% of module lifecycle state transitions (install, activate, deactivate, uninstall) produce an `audit_logs` row | Audit log query coverage assertion |

---

## 5. Scope IN

### Developer pipeline
- **Module packaging format:** a defined artifact format (tarball or OCI image layer) produced by a `manage.sh module pack` command that bundles the module backend, frontend assets, manifest, and Alembic migrations.
- **Automated production install:** `manage.sh module install <package>` on the production host (or as a CI/CD step) -- validates the manifest against a JSON schema, runs the module Alembic migrations, registers the module in `module_registry`, wires `BaseModule` hooks, and confirms readiness without a full platform restart.
- **Manifest JSON schema validation:** full validation at install time with structured per-field errors (fixing audit-11 story 11.1.1 gap).
- **`BaseModule` hook wiring:** `post_install` and `post_enable` hooks fire reliably on the correct lifecycle event (fixing audit-11 cross-cutting gap).
- **Idempotent re-install:** re-running install on the same version is a no-op; installing a newer version upgrades in place (migration fan-out only).

### Tenant / company activation layer
- **Coherent lifecycle API:** align the API contract -- decide on the canonical paths (`/install`, `/enable`, `/disable`, `/uninstall`) and fix the frontend `module-manager.js` to use them (fixing audit-11 story 11.1.2 DRIFT).
- **Activate UI:** tenant and company admins see a list of installed modules with name, description, category, and current status. A single "Activate" / "Deactivate" toggle per module. A pre-activation summary modal shows what the module will add (RBAC permissions, menu items) before the admin confirms.
- **Clean deactivation:** deactivation removes the module menu items and disables its RBAC seeds for the tenant/company. Data rows written by the module are preserved (they belong to the tenant, not the platform).
- **Uninstall (operator only):** full removal path for the platform operator -- deactivates for all tenants, revokes RBAC seeds, removes menu registrations, drops per-tenant module DB if `DATABASE_STRATEGY=per_tenant`. Requires explicit confirmation. Tenant admins cannot uninstall; they can only deactivate.
- **Dependency enforcement:** a module with declared dependencies cannot be activated until its dependencies are active. Deactivating a module that others depend on is blocked unless dependents are deactivated first.
- **Audit trail:** every state transition (install, activate, deactivate, uninstall) writes an `audit_logs` row with `entity_type=module`, `entity_id=module_id`, full context.

## 6. Scope OUT

- **Module marketplace / catalog browsing UI** -- there is no browsable store. The list of available modules is determined by what the platform developer has installed. Tenants see only installed modules.
- **Third-party module development** -- no external developers package or distribute modules. The platform developer is the only module author.
- **Module version upgrade UI** -- in-place version upgrades (with migration rollback) are deferred to a future vision. This vision covers install of a given version and uninstall; version management is out of scope.
- **NoCode module export/import** -- story 11.3.2 drift (nocode module ZIP packaging) is a separate concern and out of scope here. This vision covers code modules only.
- **Per-company module DB provisioning** -- the per-tenant DB strategy (Epic 22 story 22.4.2) is a dependency this vision respects but does not redesign. Provisioning is Epic 22's concern.
- **Paid module billing or entitlements** -- no billing gate on activation. Any installed module can be activated by any tenant.

---

## 7. Guardrails

- **No manual production steps.** The install command must be the single human action. Any process requiring SSH, manual SQL, or file copy is a design failure.
- **Production install must be reversible.** If the install command fails partway (e.g. migration error), it must roll back cleanly and leave the platform in the pre-install state.
- **Tenant data is never deleted by deactivation.** Deactivating a module hides features; it does not delete records the tenant created using the module. Only the operator-level `uninstall` (with explicit confirmation) may affect platform-managed rows.
- **API contract must be decided before any UI work.** The 11.1.2 drift (wrong endpoint paths in the frontend) must be resolved as the first story. No new activation UI can be built against an unfixed contract.
- **Epic 22 compatibility.** Module install and uninstall must call the same provisioning/cleanup service as Epic 22 story 22.4.2 / 22.4.5 when `DATABASE_STRATEGY=per_tenant`. The two epics must not create parallel provisioning code paths.

---

## 8. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Partial install leaves platform in inconsistent state** | Medium -- migrations can fail mid-run | High -- platform may be unbootable | Wrap install in a transaction where possible; record install progress in `module_registry.install_status`; rollback on failure |
| **Deactivation leaves orphaned RBAC / menu data** | High -- no cleanup path exists today | High -- tenant RBAC and navigation corrupted | Implement cleanup as a transactional unit; run automated integrity check after every deactivation in CI |
| **API contract disagreement blocks frontend work** | Confirmed -- 11.1.2 drift is a known blocker | Medium -- UI and backend cannot be developed in parallel | Resolve and document the canonical API contract as story 1 before any other story starts |
| **Epic 22 per-tenant DB provisioning not ready** | Medium -- Epic 22 in-flight | Low for activation, Medium for full install testing | Activation can be built and tested without `per_tenant` strategy; note dependency explicitly in tasks |
| **`post_install` hook wiring missed again** | Low -- known gap, easy to verify | Medium -- modules cannot run init logic | Add a hook-fires integration test as part of the install pipeline CI gate |

---

## 9. Open Questions

- Should the pre-activation summary modal be required (blocking confirmation) or optional (can be skipped by admins who have activated the module before)? Recommend: required on first activation per tenant; skippable on subsequent re-activations.
- Should deactivation be immediate or deferred (e.g. "deactivation takes effect at next login")? Recommend: immediate for menu items; session tokens may retain cached permissions until expiry (document this behaviour explicitly).
- Is `manage.sh module install` the right UX for the developer pipeline, or should it be triggered by a CI/CD webhook? Recommend: both -- `manage.sh` for local testing; CI/CD webhook for production. Same underlying command, different trigger.
- Who decides whether a module is "available for activation" after install -- all tenants by default, or requires an operator opt-in per tenant? Recommend: available to all tenants by default; operator can restrict to a whitelist if needed (data model must support this even if UI is deferred).
