---
id: adr-012
type: adr
status: Proposed
producer: C1 (Tech Lead)
upstream: [adr-hc-010, adr-hc-009, adr-011, adr-005, adr-010-public-portal-framework]
created: 2026-07-16
---

# ADR-012 — Module SaaS Tenancy & End-User RBAC Provisioning

## Status

**Proposed — design review. Do not merge as accepted.**

Opened because the D7 patient backfill (ADR-HC-009) cannot be built as written: the
decision it depends on was invalidated by ADR-HC-010, and the replacement is a
**platform** concern, not a healthcare one.

## Amends / supersedes

- **ADR-HC-009 §D7 step 2** ("assign the `patient` role + `patients` group") and **§D2**
  (same assignment on the OAuth-create path) — the tenancy those steps assume no longer
  exists. Superseded by **D5** below.
- **ADR-HC-010** — generalized. ADR-HC-010 decided shared-tenant SaaS *for healthcare*;
  this ADR lifts the mechanism to the platform so any module can declare it.
- **ADR-011 S1** (`account_service.create_patient_account`) — closes a shipped gap: it
  assigns **no** role or group at all (see Context).

Nothing about ADR-HC-010's isolation model changes: **Company remains the isolation
boundary**, RLS still re-keys to `app.company_id` (D2 there), and the patient token keeps
its `company_id` claim (D5 there). This ADR is about *where accounts and their RBAC live*,
not about how data is fenced.

## Context — verified against the running system (2026-07-16)

ADR-HC-009 §D7 was written when **tenant == clinic**. ADR-HC-010 then collapsed every
clinic into **one shared platform Tenant** (`tenants.code='SAAS'`), moving the clinic
boundary to **Company**. D7's backfill step was never revisited. The result is a
contradiction that only surfaces when you try to build it:

| Fact | Evidence |
|---|---|
| `hc_patients` live in the **SAAS** tenant | all 7 rows carry `tenant_id=5aa50000-…-0001` |
| New patient registrations resolve to the **SAAS** tenant | `routes_patient_auth._resolve_registration_scope` → `(saas_tenant_id, company_id)` via `saas_migration_map` |
| The `patient` role + `patients` group exist **only in the old per-clinic tenants** | 93 `patients` groups / 93 `patient` roles exist, none in SAAS; SAAS holds only `clinic_owners` |
| The 3 existing patient users sit in the **old HealthPoint tenant** | `users.tenant_id=f9026af6…` + that tenant's `patients` group — i.e. pre-SaaS shape |
| `create_patient_account` assigns **no role and no group** | `app/services/account_service.py` — no `UserRole` / `UserGroup` write |
| The SPA routes patients to the portal **by role** | `frontend/assets/js/app.js:112` — `roles.includes('patient')` |
| The shared tenant is resolved by a **healthcare-local hardcode** | `modules/healthcare/backend/sdk/hc_tenant.py` — `_SAAS_TENANT_CODE = "SAAS"` |
| ADR-HC-010 never considers other modules | no mention of `financial`/`template` or of generality |

So D7's "assign the `patient` role + `patients` group" is **unsatisfiable as written**:
in the tenant where the patients now live, those artifacts do not exist.

**Two live consequences, independent of D7:**

1. **A registered patient has no `patient` role**, so the moment they log in with a
   password the SPA does not recognise them as a patient and drops them in the **staff
   SPA** instead of the portal. This is shipped today; it is only masked because the
   register happy-path is Phase-5-blocked and portal users currently arrive via seeds.
2. Any second module wanting SaaS mode would have to **copy `hc_tenant.py`**, hardcode
   `'SAAS'` again, and re-solve RBAC provisioning by hand.

## Decision

### D1 — Tenancy is a **declared module capability**, not module-local code

A module declares its tenancy in its manifest (`backend/app/core/module_system/manifest.schema.json`,
validated by `manifest_validation.py`). Two modes:

```jsonc
// default when the block is absent — today's behaviour, unchanged
"tenancy": { "mode": "per_tenant" }

// opt in to shared-tenant SaaS
"tenancy": {
  "mode": "shared_saas",
  "end_user_rbac": {
    "role":  "patient",
    "group": "patients",
    "permissions": ["healthcare:portal:access"]   // module-declared, provisioned in the shared tenant
  }
}
```

`mode` is **`per_tenant` by default**, so every existing module (`financial`, `template`)
is unaffected and no migration is forced.

### D2 — **One** platform-owned shared SaaS tenant, not one per module

The shared tenant is a **platform singleton** (`tenants.code = 'SAAS'`), configurable per
deployment via `SAAS_SHARED_TENANT_CODE` (default `SAAS`). Modules **opt in** to it; they
do not each get their own.

**This is forced, not chosen.** `companies.tenant_id` is **singular** — a Company belongs to
exactly one Tenant. Per-module shared tenants (`SAAS_HEALTHCARE`, `SAAS_FINANCIAL`) would
mean a customer using two SaaS modules needs their Company to exist in two tenants at once,
which the schema cannot express. Isolation between modules is **not** the tenant's job here;
Company (ADR-HC-010 D1/D2) and permissions are.

### D3 — A platform resolver replaces the module-local hardcode

`hc_tenant.py`'s `resolve_shared_tenant_id` / `hc_shared_tenant_id` move to a platform seam
(`app.core.module_system`, re-exported through `modules.sdk`), keyed by module name:

```python
shared_tenant_id(module="healthcare") -> str   # resolve-once + cache, same as today
```

Behaviour is preserved verbatim — resolve from `tenants.code`, cache for the process, fall
back to a fixed provisioned id. `modules/healthcare/backend/sdk/hc_tenant.py` becomes a thin
deprecated wrapper (or is deleted; see Open Questions). The `HC_SHARED_TENANT_ID` env
fallback generalizes to `SAAS_SHARED_TENANT_ID`, with the old name honoured for one release.

### D4 — End-user RBAC is **provisioned into the shared tenant**, idempotently

For a `shared_saas` module, the platform provisions the declared `end_user_rbac` role +
group **in the shared tenant** at module install/upgrade (idempotent `INSERT … ON CONFLICT
DO NOTHING`, re-runnable). This is the missing piece that unblocks D7: it creates the
`patient` role + `patients` group in SAAS, where the patients actually live.

Provisioning is **additive** — it never touches the 93 legacy per-clinic `patients`
groups/roles (D6).

### D5 — End-user accounts: shared tenant + their Company + the declared group

**Supersedes ADR-HC-009 §D7 step 2 and §D2's assignment clause.** Every end-user account a
`shared_saas` module creates — backfilled, self-registered, or OAuth-created — is shaped:

- `tenant_id` = the module's **shared tenant** (D2),
- `default_company_id` = the end user's **Company** (their clinic), as
  `_resolve_registration_scope` already returns,
- membership in the declared **end-user group** (D4), which carries the declared role.

This makes the backfill consistent with what registration already does, and **fixes the
shipped gap** in `create_patient_account` (Context #1) rather than reproducing it in the
backfill. Group assignment belongs in `account_service` so both paths inherit it — the
platform's RBAC chain is User→Group→Role→Permission, so the group is the only write needed.

### D6 — Legacy per-tenant artifacts are left in place; legacy accounts are **not** silently re-pointed

The 93 per-clinic `patients` groups/roles and the 3 existing patient users on the old
HealthPoint tenant are **not** touched by this ADR. They keep working (RBAC resolves per
user, from whatever tenant that user is in). Re-pointing them to the shared tenant is a
**separate, opt-in data migration** with its own review — moving a live user between tenants
is exactly the kind of change that should not ride along inside a backfill PR.

Consequence, stated plainly: for a period, patient accounts exist in **two shapes** — legacy
(per-clinic tenant) and current (shared tenant). Both authenticate; both reach the portal.
That is acceptable and reversible. Pretending otherwise by bulk-moving users is not.

## Consequences

### Positive

- **D7 becomes buildable** — the backfill has a defined tenant and a role/group that exists.
- **The next SaaS module costs a manifest block**, not a copy of `hc_tenant.py`.
- **Fixes a live defect** (Context #1): registered/claimed patients get the `patient` role and
  therefore reach the portal instead of the staff SPA.
- Tenancy becomes **inspectable** (manifest + schema + validator) rather than implied by a
  constant buried in a module SDK.
- `per_tenant` default ⇒ **zero blast radius** for `financial` / `template`.

### Negative / risk

- **The shared tenant is a bigger blast radius.** Every SaaS module's end users share one
  tenant row; a tenant-scoped bug there reaches all of them. Mitigation: Company remains the
  isolation axis (ADR-HC-010 D2 RLS), and this ADR adds no tenant-scoped authority.
- **RBAC provisioning at install becomes a privileged write path.** It creates roles +
  permissions. It must be idempotent, additive-only, and never widen an existing role.
- **Two account shapes coexist** (D6) until/unless a migration runs. Anyone reasoning about
  "which tenant is a patient in?" must check, not assume.
- **`SAAS_SHARED_TENANT_CODE` is deployment config that must not drift** between the platform
  and a module service, or a module resolves a different tenant than the data. Worth a
  startup assertion.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| **Backfill into the old per-clinic tenant** (where the role/group already exist) | Moves against ADR-HC-010's whole direction and diverges from where new registrations already land. Would make the backfilled users the *only* new-but-legacy-shaped accounts, and guarantee a second migration later. |
| **Skip role/group entirely** (match `create_patient_account` today) | Smallest diff, but knowingly ships the Context #1 defect to every backfilled patient: claim a password → log in → land in the staff SPA. Encoding a known bug into a migration is worse than fixing it. |
| **A shared tenant per SaaS module** | `companies.tenant_id` is singular — a Company using two SaaS modules cannot exist in two tenants. Schema-impossible (D2). |
| **Keep it healthcare-specific; hardcode SAAS in the backfill** | Fastest path to D7, and exactly how we got here. The next SaaS module re-solves it from scratch, and the hardcode is invisible to review. |
| **Per-tenant `patients` group auto-created on demand at registration** | Puts a privileged RBAC write on an unauthenticated public path. Non-starter. |

## Open questions for review

1. **`hc_tenant.py`: thin wrapper or delete?** A wrapper is kinder to in-flight branches; a
   delete prevents the hardcode being reintroduced. Recommend **wrapper now, delete with S6b**.
2. **Where does provisioning run?** Module install/upgrade hook vs an explicit
   `seed_module_rbac` command. Recommend the **install/upgrade hook** (idempotent), with the
   command as the operational escape hatch.
3. **Should `end_user_rbac.permissions` be declarable at all**, or should the module ship a
   permission seed and the manifest only name the role/group? Declaring permissions in the
   manifest is more inspectable but widens what a manifest can grant itself.
4. **D6 follow-up**: do we ever re-point the 3 legacy patient users + retire the 93 per-clinic
   `patients` groups? Recommend filing it, not doing it now.
5. **Does `financial` actually want SaaS mode?** If yes, this ADR should be validated against
   its end-user shape before acceptance rather than after.

## Reference Map

| File | Relevance |
|---|---|
| `backend/app/core/module_system/manifest.schema.json` | gains the `tenancy` block (D1) |
| `backend/app/core/module_system/manifest_validation.py` | validates it (D1) |
| `modules/healthcare/backend/sdk/hc_tenant.py` | the hardcode this generalizes (D3) |
| `modules/healthcare/manifest.json` | first `shared_saas` declarant (D1) |
| `backend/app/services/account_service.py` | gains end-user group assignment (D5) |
| `modules/healthcare/backend/routes_patient_auth.py` | `_resolve_registration_scope` — already returns (shared tenant, company); becomes the shared shape (D5) |
| `frontend/assets/js/app.js:112` | the `roles.includes('patient')` redirect that D5 fixes |
| `plan-mod-healthcare/architecture/adr-hc-010-…md` | generalized by this ADR |
| `plan-mod-healthcare/architecture/adr-hc-009-…md` | §D7 step 2 / §D2 superseded by D5 |
| `plan/tasks/tasks-011-auth-mfa.md` | S6b unblocked once D7 can build |
| GH #692, #693 | the D7-blocked work this feeds |
