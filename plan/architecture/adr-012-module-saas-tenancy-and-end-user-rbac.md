---
id: adr-012
type: adr
status: Accepted
producer: C1 (Tech Lead)
upstream: [adr-hc-010, adr-hc-009, adr-011, adr-005, adr-010-public-portal-framework]
created: 2026-07-16
---

# ADR-012 — Module SaaS Tenancy & End-User RBAC Provisioning

## Status

**Accepted — 2026-07-17.**

Opened because the D7 patient backfill (ADR-HC-009) cannot be built as written: the
decision it depends on was invalidated by ADR-HC-010, and the replacement is a
**platform** concern, not a healthcare one.

**Review round 1 (2026-07-17):** all five open questions answered and accepted — see
*Review round 1 — resolutions*. Q2 **reversed** the original install-hook recommendation;
Q4 and Q5 revised D3 and D6. D1–D6 as written below are binding.

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
deprecated **wrapper** delegating to it — not a delete, because it has ~100 call sites across
19 files (Resolution Q4); it is removed with S6b. The wrapper still achieves the point: the
`"SAAS"` hardcode ends up in exactly one place, the platform. The `HC_SHARED_TENANT_ID` env
fallback generalizes to `SAAS_SHARED_TENANT_ID`, with the old name honoured for one release.

### D4 — End-user RBAC is **provisioned into the shared tenant**, idempotently

For a `shared_saas` module, the platform provisions the declared `end_user_rbac` role +
group **in the shared tenant** (idempotent `INSERT … ON CONFLICT DO NOTHING`,
re-runnable). This is the missing piece that unblocks D7: it creates the
`patient` role + `patients` group in SAAS, where the patients actually live.

Provisioning is **additive** — it never touches the 93 legacy per-clinic `patients`
groups/roles (D6).

**An explicit `seed_module_rbac` command is the source of truth** (see Resolution Q2);
`post_install` calls it best-effort. Crucially, the invariant is **enforced at the point of
use, not at install**: `account_service` and the backfill **resolve-or-fail** on the declared
group — they never create an end user without it. A missed provisioning step must surface as
a loud error when an account is created, never as a silently role-less user.

`end_user_rbac.permissions` codes MUST be namespaced to the declaring module
(`healthcare:*`); the validator rejects foreign or platform namespaces (see Resolution Q1).

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

### D6 — Legacy groups stay; the 3 legacy patient users are re-pointed **as demo fixtures** (revised, review round 1)

The 93 per-clinic `patients` groups/roles are **not** touched by this ADR. They keep working
(RBAC resolves per user, from whatever tenant that user is in). Retiring them is a separate,
opt-in migration with its own review.

**Revised on review:** the original D6 declined to re-point the 3 `patient1..3@healthpoint.com`
users, on the grounds that silently moving *live* users inside a backfill PR is wrong. The
review established they are **demo/test fixtures, not live users**, so that objection does not
apply — there is no one to protect. They are re-pointed to the shared tenant + the HealthPoint
Company + the SAAS `patients` group.

**This is a seed concern, not a backfill concern**, and the split is load-bearing:

| | Backfill (`scripts/`, production path) | Demo fixtures (`seed_demo.py`, dev only) |
|---|---|---|
| Target | legacy `hc_patients` with no owner | the 3 `patient*@healthpoint.com` users |
| Password | none usable; `must_set_password=True` | the seeded `password123` |
| Email | synthetic → real at claim | already real |
| Login | OTP → `/patient/claim-account` | **password only** (no OTP) |

**"No OTP" requires no product change and no bypass.** The MFA gate is
`mfa_service.has_active_factor(db, user.id)` (`app/routers/auth.py:392`) — MFA is **opt-in per
user**. A demo patient with a password and no enrolled factor logs in with the password alone.
No per-account OTP-skip flag is introduced: such a flag would be a login bypass one config
mistake away from production, and it is not needed to get the demo behaviour asked for.

Consequence, stated plainly: production patient accounts still exist in **two shapes** for a
period — legacy (per-clinic tenant) and current (shared tenant). Both authenticate; both reach
the portal. That remains acceptable and reversible.

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
- **RBAC provisioning becomes a privileged write path.** It creates roles + permissions. It
  must be idempotent, additive-only, and never widen an existing role. It is deliberately kept
  out of `post_install` as the *sole* mechanism (Resolution Q2), because that hook swallows its
  own failures and runs unscoped (`sec-review-23` L-2).
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

## Review round 1 — resolutions (2026-07-17)

All five open questions were answered. Q4/Q5 changed decisions above; **Q2 reversed the
original recommendation** once the hook was actually read.

**Q1 — may a manifest declare `end_user_rbac.permissions`? → Yes, namespace-constrained.**
The question was partly malformed: the manifest **already** has a `permissions[]` array
(`manifest.schema.json:50`), and healthcare's `get_permissions()` returns
`self.manifest.get("permissions", [])` (`module.py:57`) — so manifest-declared permissions are
existing precedent. (Healthcare's manifest has no `permissions` block, so it declares zero.)
The real distinction is **define vs grant**: defining a code creates an inert row nobody holds;
*granting* it to a role end users are auto-joined to is the new authority. Resolution: allow it,
but the validator accepts only codes namespaced to the declaring module (`healthcare:*`) and
rejects platform/foreign namespaces (`system:*`, `financial:*`). A module may grant its own end
users its own permissions; it may not grant itself anything else.

**Q2 — where does provisioning run? → Explicit command is the source of truth; the hook is a
convenience. (Reverses the original "install hook" recommendation.)** Evidence:
- `post_install` fires **only** from `POST /modules/register` (`app/routers/modules.py:812`),
  not at startup — a DB provisioned any other way never runs it.
- **Its failure is swallowed**: *"log but do NOT roll back — hook failure is non-fatal per
  T-23.014"* (`modules.py:819`). RBAC provisioning failing there = module installs "successfully"
  with no `patient` role = the backfill silently creates role-less users. Context #1 at scale.
- `sec-review-23` **L-2** already flags these hooks as running with a **fully unscoped DB
  session** (accepted, insider-threat-only). A privileged RBAC write lands inside an open finding.
- `post_enable` is **per-tenant** — structurally wrong for a shared-tenant singleton.

Hence D4's resolve-or-fail rule: the invariant is enforced where accounts are created, so a
missed provisioning step is a loud error, not silent data corruption.

**Q3 — does `financial` want SaaS mode? → "Possibly; there could be other modules in SaaS
mode."** D1 therefore stays **general** (manifest-declared capability), which is what justifies
the manifest route over a healthcare-specific code seed. `per_tenant` remains the default, so
nothing is forced on `financial`/`template` before anyone has validated their end-user shape.

**Q4 — `hc_tenant.py` wrapper or delete? → Wrapper now, delete with S6b.** The steer was "if not
affecting anything, delete" — but it affects **~100 call sites across 19 files**
(`routes_visits`, `routes_schedules`, `routes_branches`, `branch_scope`, `hc_permissions`,
`routes_public`, `app/main.py`, …), so the condition is not met and a delete would ride a
19-file refactor inside a backfill PR. The intent is met anyway by delegation: the `"SAAS"`
constant then lives in exactly **one** place (the platform), every call site is untouched, and
the file is removed by a mechanical import rewrite with S6b.

**Q5 — re-point the legacy patient users? → Yes; they are demo/test fixtures. See revised D6.**
"Make it no OTP" needs **no product change**: MFA is opt-in per user (`auth.py:392`), so a demo
patient with a password and no factor logs in with the password alone. No OTP-skip flag is added.

## Reference Map

| File | Relevance |
|---|---|
| `backend/app/core/module_system/manifest.schema.json` | gains the `tenancy` block (D1); already carries `permissions[]` (Q1) |
| `backend/app/core/module_system/manifest_validation.py` | validates it + the namespace rule (D1, Q1) |
| `backend/app/routers/modules.py:812` | `post_install` call site — fires only on `/register`, swallows failures (Q2) |
| `plan/architecture/sec-review-23.md` (L-2) | hooks run with an unscoped DB session (Q2) |
| `backend/app/routers/auth.py:392` | `has_active_factor` — MFA is opt-in, so demo patients need no OTP bypass (D6) |
| `modules/healthcare/backend/seed_demo.py` | owns the 3 demo-fixture patient users (D6) |
| `modules/healthcare/backend/sdk/hc_tenant.py` | the hardcode this generalizes (D3) |
| `modules/healthcare/manifest.json` | first `shared_saas` declarant (D1) |
| `backend/app/services/account_service.py` | gains end-user group assignment (D5) |
| `modules/healthcare/backend/routes_patient_auth.py` | `_resolve_registration_scope` — already returns (shared tenant, company); becomes the shared shape (D5) |
| `frontend/assets/js/app.js:112` | the `roles.includes('patient')` redirect that D5 fixes |
| `plan-mod-healthcare/architecture/adr-hc-010-…md` | generalized by this ADR |
| `plan-mod-healthcare/architecture/adr-hc-009-…md` | §D7 step 2 / §D2 superseded by D5 |
| `plan/tasks/tasks-011-auth-mfa.md` | S6b unblocked once D7 can build |
| GH #692, #693 | the D7-blocked work this feeds |
