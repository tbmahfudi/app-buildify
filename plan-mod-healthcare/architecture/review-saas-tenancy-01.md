---
artifact_id: review-saas-tenancy-01
type: product-review
module: healthcare
status: active
producer: A3 Product Owner
upstream: [BACKLOG.md (v3), adr-hc-005-org-linkage-departments, adr-hc-009-patient-identity-and-auth (v2), adr-hc-001-branch-isolation-strategy, adr-hc-002-phi-handling, epic-08-organization-departments (v2), epic-18-patient-portal-authentication, schema-hc-02, routes_public.py, routes_household.py, routes_clinic_signup.py, models.py]
created: 2026-07-06
---

# Review — Shared-Tenant SaaS Tenancy Model

## Status

Product review of a foundational tenancy decision. **No application code.** Produces the product
model, the disposition against current state, the risks (especially patient pooling), a
recommendation, and a **Hand-off to B1** with every architecture/security decision B1 must resolve
next. Backlog impact is flagged (not fully authored).

## The decision under review (from the product owner)

Move the healthcare product to a **shared-tenant SaaS** model:

- **ALL clinics on the SaaS live in ONE shared platform Tenant.**
- An owner with one or more clinics registers as a **Company**; each clinic **site is a Branch**
  under that Company (Company 1:N Branch).
- An owner who runs **multiple companies** and wants a single consolidated cross-company view (noted
  as *very rare*) may request their **own exclusive/dedicated Tenant**.

This concretizes ADR-HC-005's "everything under a Tenant; a dedicated tenant only on explicit
request" — but flips the **default**: today the default is tenant-per-clinic; the new default is a
single shared SaaS tenant, and a dedicated tenant is the rare exception.

## Current reality (verified against code)

| Aspect | Today | Source |
|---|---|---|
| Clinic ⇄ Tenant | **Each clinic is its own platform Tenant.** `MEDCARE` and `HEALTHPOINT` are separate tenants. | `routes_clinic_signup.py` creates a `tenants` row per `clinic_register`; `_get_profile` resolves clinic by tenant code. |
| Portal clinic resolution | **slug = `tenants.code`.** Public profile / search / slots all resolve a clinic by tenant code. | `routes_public.py` `_get_profile` (`WHERE UPPER(code)=UPPER(:slug)`); `/me/clinic` maps active patient's `tenant_id → tenants.code`. |
| `hc_branches` | Clinic sites, **tenant-scoped**. HealthPoint's rows already carry `platform_company_id`/`platform_branch_id` (partway to ADR-HC-005); MedCare's do not (legacy). | `models.py` `HCBranch`; ADR-HC-005 D1. |
| **`hc_patients`** | **Tenant-scoped, NOT branch-scoped.** `__tenant_scoped__ = True`; model comment: *"patients belong to tenant, not branch."* No `branch_id` column. | `models.py` `HCPatient` (line 371-376). |
| Staff | `hc_branch_staff` — tenant + branch scoped, `X-Branch-ID` header, `HCRole`. | `models.py` `HCBranchStaff`. |
| Isolation | ADR-HC-001 RLS on `tenant_id` + `branch_id`. Today `tenant_id` **is** the clinic boundary. | ADR-HC-001. |
| Household/proxy | ADR-HC-009 v2 + epic-18 F18.10. **Q2 ruling = "a household is within ONE tenant"**; cross-tenant register/link rejected 422. That rule **assumed tenant == clinic**. | `routes_household.py` (same-tenant check, line 247); ADR-HC-009 V-D6. |

**The pivot's core tension:** every existing isolation and identity boundary is keyed on
`tenant_id`, and today `tenant_id` == one clinic. Collapsing all clinics into one tenant removes
`tenant_id` as the clinic boundary. Everything that leaned on "tenant == clinic" must be re-derived
on **Company/Branch** — most urgently the patient store, which today pools per-tenant and would now
pool the **entire SaaS**.

---

## 1. Onboarding / product model under shared-tenant SaaS

### The model, as stated for the backlog

```
Platform Tenant  "SAAS" (single, shared)            ← default; NOT per-clinic anymore
  └── Company    = a clinic owner's legal entity / brand   (owner registers as a Company)
        └── Branch = a clinic SITE  (Company 1:N Branch; a clinic site IS a platform Branch — ADR-HC-005 D1)
              └── hc_departments (clinical) → hc_rooms
Dedicated Tenant "ACME-GROUP" (rare, on request)    ← only for an owner with MULTIPLE companies
  └── Company A / Company B / …                       wanting one consolidated cross-company view
```

- **Default topology (A):** the owner signs up → the platform provisions (or reuses) the shared
  SaaS Tenant → creates a **Company** for the owner → creates one **Branch per clinic site** →
  `hc_branches` links to that platform Branch (ADR-HC-005 8.1.1 linkage). A single owner with N
  clinic sites = one Company, N Branches.
- **Exception topology (B) — dedicated tenant:** only when an owner runs **multiple Companies** and
  needs a consolidated view across them. This is a **platform-org provisioning choice, out-of-band,
  approval-gated** (ADR-HC-005 A4 / Story 8.1.5-B). Healthcare records the request + the resulting
  ids; **no `hc_*` schema differs** between (A) and (B) (ADR-HC-005 A4 stands).

### Contrast with today's onboarding (`routes_clinic_signup.py`)

`clinic_register` today: **creates a new `tenants` row per clinic** (line 76-84), then a branch,
then an owner user, then `hc_branch_staff` (clinic_owner, `branch_id=NULL` sentinel), then DPA
consent. Under shared-tenant SaaS this flow must change:

- **Stop minting a tenant per clinic.** New signup attaches to the shared SaaS tenant and creates a
  **Company** (+ first Branch), not a Tenant. (The tenant is provisioned once for the whole SaaS.)
- **Company creation becomes the new onboarding root** — a self-service "register your clinic
  business" step that produces a `companies` row, then one-or-more Branch (clinic site) rows via the
  platform org API, then ADR-HC-005 8.1.1 linkage.
- The **dedicated-tenant path** (multi-company consolidated view) becomes an explicit,
  approval-gated request — surfaced in onboarding as the rare "I run multiple companies and need one
  tenant" option (epic-08 Story 8.1.5, topology B), routed to platform-admin provisioning.

**Product requirement:** a new self-service **company-signup / onboarding** flow (owner → Company →
Branches) replacing tenant-per-clinic `clinic_register`, with the dedicated-tenant exception as a
manual/approval path. This is large enough to warrant a **new onboarding epic** (see Backlog impact).

---

## 2. THE CRITICAL ISSUE — patient data scoping (make-or-break)

**The problem, stated plainly.** `hc_patients` is **tenant-scoped with no `branch_id`** (verified —
`models.py` line 371-376, "patients belong to tenant, not branch"). Today that means "all patients of
this one clinic." Under **one shared SaaS tenant**, tenant-scoping means **every patient of every
clinic on the whole SaaS is pooled into one set.** Any tenant-scoped patient list, search, or the
`from-platform` household resolver would span the entire SaaS. **Clinics must NOT see each other's
patients by default.** This is the make-or-break of the whole model; without a scoping fix, the
shared-tenant pivot is a data-isolation breach, not a feature.

### Recommended product rules (hand enforcement to B1)

**Rule P1 — a patient record is scoped to a Company (the clinic business), not the shared tenant.**
A patient belongs to the **Company** whose clinics registered/treat them. A Company's own Branches
(clinic sites) **share** that patient (one record across a Company's sites — the same real person at
"Downtown" and "Uptown" branches of the same business is one record). Patients are **isolated
between Companies** by default. Company becomes the effective "clinic business" isolation unit that
`tenant_id` used to be.

- **Why Company, not Branch, as the patient home:** today `hc_patients` is deliberately *not*
  branch-scoped because a patient belongs to the whole clinic business, not one site (ADR-HC-001 §D3
  keeps the patient registry tenant-wide; branch-scoped clinical tables reference the patient). That
  product intent is preserved by making **Company** the new "whole clinic business" boundary. Making
  patients strictly Branch-scoped would fragment a patient across a Company's own sites and break
  cross-site care — reject that.

**Rule P2 — a patient who visits two *unrelated* clinics (different Companies) has TWO records, not
one shared identity.** There is **no cross-Company shared patient identity** at the PHI level by
default. Each Company holds its own `hc_patients` row for that person; the two are isolated and must
not be silently merged or cross-visible. (A shared *platform login* may still front both — see the
household re-framing in §3 and the hand-off — but the **PHI records stay per-Company**.) This keeps
the isolation guarantee simple and defensible: Company A can never see Company B's patient, even for
the same human.

**Rule P3 — the default is deny-cross-Company.** Absent an explicit, audited, product-blessed
mechanism (none exists at MVP), no clinic can read, search, or list a patient outside its own
Company. Patient search/list/pooling operations that today rely on `tenant_id` must be re-scoped to
**Company** (and, where a view is site-specific, further filtered by Branch).

**Rule P4 (dedicated-tenant case).** In the rare dedicated-tenant topology, `tenant_id` still
isolates that owner's whole world, and Company scoping applies **within** it — so the same rules hold
one level down; the dedicated tenant just guarantees hard isolation from the shared SaaS.

### What this hands to B1 (enforcement design — B1 owns)

The **product rule is Company-scoped patient records, Branch-shared within a Company, Company-isolated
between Companies, two records for two unrelated Companies.** B1 must decide the **enforcement**:
whether `hc_patients` gains a `company_id` (or resolves Company via a Branch link), how RLS changes
from `tenant_id`-keyed to **Company-keyed** for the patient store, and how every tenant-scoped patient
query/pooling path (`from-platform` household resolver, any patient search) is re-scoped. See Hand-off
(a). **This is the top-priority B1 item — nothing else in the pivot is safe until it is resolved.**

---

## 3. Household / proxy re-examination (the just-built feature)

**Why it breaks.** ADR-HC-009 v2's Q2 ruling — *"a household is within ONE tenant"* — was chosen
precisely because **tenant == clinic**, so "one tenant" meant "one clinic boundary," and the token
could stay simple (`tenant_id: null`, single-tenant patient set). The code enforces it: `request_link`
and `register_dependent` reject/deny a cross-tenant target (`routes_household.py` line 247), and the
`from-platform` bridge resolves the household set *within the account holder's tenant* (ADR-HC-009
V-D7). **Under one shared SaaS tenant, "within one tenant" no longer isolates clinics** — it would let
an account holder's household span **every clinic on the SaaS**, and the same-tenant guard becomes a
no-op that guards nothing.

### Q2 re-framed for shared-tenant

**Recommended re-framing: Q2 becomes "a household is within one COMPANY" (not one tenant).** The
intent of Q2 was "confine the household to the account holder's clinic world so the token stays simple
and cross-clinic linkage is deliberate." The unit that now carries "one clinic world" is the
**Company** (per §2 Rule P1). So:

- A household (self + dependents + proxied patients) is confined to **one Company**. An account holder
  managing patients across two unrelated Companies is the multi-Company case — **not** a single
  household; it is either two households (one per Company) or, for the rare consolidated owner, the
  dedicated-tenant topology.
- The same-tenant checks in `routes_household.py` (link, register-dependent) and the `from-platform`
  set resolver must become **same-Company** checks; the 422 "cross-tenant" rejection becomes a 422
  "cross-Company" rejection.
- Q3 (clinic-staff approval to link an existing patient) already routes by `branch_id` — that keeps
  working, because the approving staff are at the patient's Branch, which is within the patient's
  Company. The staff-approval model is unaffected in shape; only the "same boundary" invariant moves
  from tenant to Company.
- The patient JWT can stay simple: the household set is single-Company by construction, so no
  multi-tenant/multi-company token machinery is needed (same payoff Q2 gave, one level down).

**Open sub-question for B1 (flag):** is the household scoped to **Company** or **Branch**? Recommend
**Company** (a household spanning a Company's own sites is legitimate — a parent managing a child
treated at two branches of the same clinic business). Branch would be too tight. B1 confirms and
amends ADR-HC-009 V-D6/V-D7 accordingly. This is Hand-off (b).

---

## 4. Portal clinic resolution

**Today:** slug = tenant code (`routes_public.py` `_get_profile`: `WHERE UPPER(code)=UPPER(:slug)`;
`/me/clinic` returns the active patient's `tenant_id → tenants.code`). The logged-out landing resolves
"the clinic" from the tenant code — which is why the user sees **only MedCare** (the landing defaults
to one tenant/clinic; there is no chooser across clinics).

**Under shared-tenant SaaS this must change:** with all clinics in one tenant, a **tenant code no
longer identifies a clinic.** The portal must resolve a clinic by **Company/Branch**, not tenant code:

- The public slug must become a **Company (or Branch) slug**, not `tenants.code`. `clinic_search`,
  `clinic_public_profile`, `clinic_branch_public`, and the public-slots endpoint all key off tenant
  code today and must re-key onto Company/Branch. (Note: `clinic_search` already groups by tenant to
  aggregate a "clinic" — that grouping must move to Company.)
- `/me/clinic` (the just-added resolver) currently maps active patient → `tenant_id → tenants.code`;
  it must map active patient → **Company/Branch → Company/Branch slug** instead.
- The **logged-out landing** ("only shows MedCare" complaint) becomes either a **clinic chooser**
  (list/search across Companies on the SaaS) or a **Company/Branch-scoped URL** (each clinic business
  has its own public URL under the shared SaaS). Product preference: a public **clinic directory /
  chooser** as the default landing, plus per-Company/Branch deep-link URLs — so no single clinic is
  hard-coded as "the" landing.

This is a required change, handed to B1 for the resolution design (Hand-off (d)).

---

## 5. Staff / RBAC & isolation shift

**With all clinics in one tenant, Branch (not Tenant) becomes the primary isolation boundary** — with
**Company** as the mid-level grouping. Implications:

- **`hc_branch_staff`** already scopes by `tenant_id` + `branch_id` with `X-Branch-ID` auth and
  `HCRole`. Under shared-tenant, `tenant_id` no longer separates clinics, so **Branch scoping does the
  real isolation work** — which is already the finer axis, so staff isolation largely *survives*, but:
  the `clinic_owner` row uses `branch_id=NULL` as a "whole clinic" sentinel (`routes_clinic_signup.py`
  line 120-128). A `NULL`-branch owner today means "owner of this tenant's one clinic"; under shared
  tenant it must mean "owner of this **Company's** branches," not "owner of everything in the shared
  tenant." That sentinel's meaning must be re-scoped to Company, or it becomes a SaaS-wide
  super-owner — a serious privilege-escalation risk. **Flag to B1.**
- **RBAC / roles:** platform RBAC resolves via User→Group→Role→Permission (per project memory) and is
  tenant-aware. With one tenant, role grants must not leak across Companies. Company must gate
  staff/role visibility so a Company-A branch manager cannot enumerate Company-B branches/staff.
- **Reporting:** the ADR-HC-008 read-only views are tenant + branch scoped. Tenant-scoped aggregates
  now span the whole SaaS — every cross-clinic report must be re-scoped to **Company** (and Branch).
  Any report that sums "per tenant" becomes "per SaaS" unless re-keyed. **Flag to B1.**

The RLS/security redesign (branch-as-primary + Company grouping, the owner-sentinel re-scope, RBAC
cross-Company gating, reporting re-scope) is handed to B1 (Hand-off (c)).

---

## 6. Migration

**Today:** MedCare and HealthPoint are **separate tenants**. HealthPoint's `hc_branches` already
carry `platform_company_id`/`platform_branch_id` (partway to ADR-HC-005); MedCare's do not (legacy,
unlinked).

**Target:** consolidate both into the **shared SaaS tenant** as **Companies**, with each clinic site
as a **Branch** under its Company.

**Product-level framing (details/DDL to B1):**

- MedCare-tenant → **Company "MedCare"** under the shared SaaS tenant; its clinic site(s) →
  Branch(es). MedCare needs the ADR-HC-005 linkage backfilled (it has none today).
- HealthPoint-tenant → **Company "HealthPoint"**; its already-linked `hc_branches` re-homed under the
  shared tenant. HealthPoint is closer (linkage columns populated) but its `tenant_id` still points at
  the old per-clinic tenant and must be re-pointed to the shared tenant.
- **Patient data (the risky part):** each old tenant's `hc_patients` must be re-scoped to its new
  **Company** (per §2). Because §2 Rule P2 says two unrelated Companies keep two records, the
  migration is a clean partition — MedCare patients → Company MedCare, HealthPoint patients → Company
  HealthPoint; **no merge**. But every `tenant_id` on `hc_patients` (and all branch-scoped clinical
  tables, `hc_patient_relationships`, consents, audit) changes from the old per-clinic tenant to the
  shared tenant, with Company as the new isolation key. This is a **high-risk, all-tables
  re-scoping** — B1 owns the sequencing, the RLS cutover, and the verification that no cross-Company
  leakage results.
- **Ordering constraint:** the patient-scoping enforcement (Hand-off (a)) must land **before** the
  data is consolidated into one tenant — otherwise there is a window where all patients are pooled in
  one tenant with no Company isolation. Migration is gated on the scoping model being enforced first.

This is framed at product level; the migration design is Hand-off (e).

---

## Risks

| Risk | Severity | Note |
|---|---|---|
| **Patient pooling across the whole SaaS** if `hc_patients` stays raw tenant-scoped | **Critical / make-or-break** | §2. Data-isolation breach; blocks the whole pivot until enforced. Migration must not run before this lands. |
| Household same-tenant guard becomes a no-op | High | §3. `routes_household.py` cross-tenant checks guard nothing under one tenant; must become same-Company. |
| `clinic_owner` `branch_id=NULL` sentinel = SaaS-wide super-owner | High | §5. Privilege escalation if not re-scoped to Company. |
| Portal landing hard-codes one clinic | Medium | §4. The "only MedCare" complaint; needs Company/Branch resolution + chooser. |
| Reporting aggregates span the whole SaaS | Medium | §5. Tenant-scoped views must re-scope to Company/Branch. |
| Migration re-scopes every `tenant_id` across all HC tables | High | §6. All-tables cutover; ordered after scoping enforcement. |

## Recommendation

**Adopt the shared-tenant SaaS model, conditional on the patient-scoping model being resolved and
enforced FIRST.** The onboarding simplification (owner → Company → Branches, one shared tenant) and
the "dedicated tenant only for the rare multi-company consolidated view" are sound and align with
ADR-HC-005's original "everything under a Tenant" intent — the pivot just makes the shared tenant the
*default* rather than the exception.

**But the model is not safe to ship until B1 resolves patient-data scoping (§2).** The recommended
product rules are: **patient record scoped to Company; shared across a Company's Branches; isolated
between Companies; two records for two unrelated Companies; deny-cross-Company by default.** With that
enforced, Q2 re-frames cleanly to "household within one Company," the portal re-resolves clinics by
Company/Branch, Branch becomes the primary isolation axis, and MedCare/HealthPoint consolidate as
Companies. Without it, the pivot is a breach. **Sequence: (a) patient-scoping → then everything else →
migration last.**

---

## Backlog impact (flagged, not fully authored)

| Artifact | Change | Disposition |
|---|---|---|
| **ADR-HC-005** | Make the **single shared SaaS tenant the explicit default** (today it's the exception). A4 said dedicated-vs-shared is a provisioning choice with no HC schema change — that stands, but the **default flips** and the **patient-scoping consequence** (Company as the new clinic boundary) is new and material. **B1 decides: amend (addendum) vs supersede** — see Hand-off (f). Recommend **amend with a shared-tenant-default addendum** unless the patient-scoping change forces a supersede. |
| **ADR-HC-009 v2 (Q2 / V-D6 / V-D7)** | Re-frame the household boundary from **"within one tenant" → "within one Company."** Same-tenant checks (link, dependent, `from-platform` set resolver) become same-Company. Token stays simple. B1 amends V-D6/V-D7. |
| **ADR-HC-001** | Patient store isolation key moves from `tenant_id` → **Company** (branch-shared within Company). Branch remains the primary axis for branch-scoped clinical tables. B1 revises the RLS story for the patient registry. |
| **epic-08 (org/onboarding)** | Story 8.1.5 (topology chooser) gains "shared tenant is the default; dedicated tenant is the rare multi-company exception." The `clinic_owner` NULL-branch sentinel re-scope (Company, not SaaS) is a new AC. |
| **NEW onboarding/company-signup epic** | **Warranted.** A self-service owner → Company → Branch(es) signup replacing tenant-per-clinic `clinic_register`, plus the dedicated-tenant approval path. Recommend a new epic (e.g. `epic-20-saas-onboarding`) — do not overload epic-08. |
| **Portal resolution (epic-18 / public routes)** | Public clinic resolution moves from tenant-code slug → Company/Branch slug; logged-out landing becomes a clinic chooser. New/changed stories. |
| **BACKLOG.md** | Short "SaaS tenancy" note added pointing at this review (done in this pass). |

---

## Hand-off to B1

B1 acts on this next. Every architecture/security decision B1 must resolve, in priority order:

**(a) Patient-data scoping under one shared tenant — TOP PRIORITY, blocks everything.**
Product rule (from §2): a patient record is **scoped to a Company**, **shared across that Company's
Branches**, **isolated between Companies**, and **two unrelated Companies keep two records** (no
cross-Company shared PHI identity); **deny-cross-Company by default.** B1 to design enforcement:
whether `hc_patients` gains a `company_id` (or derives Company from a Branch/site link), the RLS
rewrite from `tenant_id`-keyed to **Company-keyed** for the patient registry, and the re-scoping of
every tenant-scoped patient query/pool path (the `from-platform` household resolver in
`routes_patient_auth.py`/`routes_household.py`, any patient search/list). Nothing else is safe until
this is settled.

**(b) Household / proxy Q2 re-scope — Company vs Branch.**
Re-frame ADR-HC-009 Q2 from "within one tenant" to **"within one Company"** (recommended over Branch —
a household legitimately spans a Company's own sites). Convert the same-tenant checks in
`routes_household.py` (`request_link` line 247, `register_dependent`, and the `from-platform`
same-tenant set resolver, V-D7) to **same-Company**; the 422 "cross-tenant" becomes 422
"cross-Company." Confirm Company vs Branch and amend V-D6/V-D7. Q3 branch-scoped staff approval is
unaffected in shape.

**(c) Branch-as-primary isolation + RLS + RBAC changes.**
With one tenant, **Branch is the primary isolation boundary** and **Company the mid grouping**. Design:
the RLS changes for branch-scoped clinical tables (largely intact — `branch_id` already isolates);
re-scope the `clinic_owner` `branch_id=NULL` sentinel to **Company** (not the whole shared tenant —
`routes_clinic_signup.py` line 120-128) to prevent a SaaS-wide super-owner; RBAC gating so roles/staff
don't leak across Companies; and re-scope the ADR-HC-008 reporting views from tenant → Company/Branch.

**(d) Portal clinic resolution by Company/Branch.**
Re-key `routes_public.py` (`_get_profile`, `clinic_search` tenant-grouping, `clinic_public_profile`,
`clinic_branch_public`, public-slots) and `/me/clinic` (`routes_household.py` line 99-114) from **tenant
code** to **Company/Branch slug**. Design the logged-out landing as a **clinic chooser / directory**
(and/or Company/Branch-scoped public URLs), replacing the single-clinic default that shows "only
MedCare."

**(e) Migration of the separate-tenant clinics into the shared tenant.**
Consolidate MedCare (unlinked, legacy) and HealthPoint (already ADR-HC-005-linked) into the shared SaaS
tenant as **Companies**, each clinic site a **Branch**. Re-point every `tenant_id` (across `hc_patients`,
`hc_patient_relationships`, consents, all branch-scoped clinical tables, `hc_audit_log`) from the old
per-clinic tenant to the shared tenant, with **Company** as the new patient isolation key. Clean
partition per Rule P2 (no merge). **Ordering: (a) must be enforced before this migration runs** —
otherwise patients pool in one tenant with no Company isolation.

**(f) ADR-HC-005 amend vs supersede.**
Decide whether ADR-HC-005 is **amended** (a shared-tenant-default addendum + the patient-scoping
consequence) or **superseded** by a new tenancy ADR. Recommend **amend** unless the Company-scoped
patient-store change is large enough to warrant a fresh ADR; either way, record that the **default is now
one shared SaaS tenant** and that **Company is the new clinic-business isolation boundary for patients**,
with the dedicated tenant reserved for the rare multi-company consolidated-view owner.
