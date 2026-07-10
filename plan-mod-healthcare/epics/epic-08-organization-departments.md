---
artifact_id: epic-08-organization-departments
status: active
version: 2
module: healthcare
launch_phase: MVP
producer: A3 Product Owner
upstream: BACKLOG v3
created: 2026-07-02
updated: 2026-07-06
changelog:
  - "v2 (2026-07-06, A3): Added explicit Hierarchy Correspondence section (level-by-level
     platform-org ⇄ healthcare mapping with cardinalities + link ownership). Clarified the
     two-'department' ambiguity (platform org Department vs clinical hc_department). Appended
     linkage-lifecycle stories 8.1.3 (unlink), 8.1.4 (tenant/company invariant validation),
     8.1.5 (onboarding topology choice: clinic-as-company vs dedicated-tenant) and clinical-dept
     roll-up story 8.2.4 (optional hc_departments ⇄ platform departments link — decision pending
     B1). Existing Feature/story numbering preserved; nothing renumbered."
---

# Epic 08 — Organization: Departments & Platform-Org Linkage

**Module:** `healthcare` (extends epic-01 base)
**Launch Phase:** MVP
**Summary:** Links each healthcare clinic/branch to the existing platform Company/Branch/Department
hierarchy (a clinic **is** a platform branch) and introduces `hc_departments` as the intra-branch
organizational unit that downstream modules route by. Covers linkage of `hc_branches` to
`platform_company_id` / `platform_branch_id` / `platform_department_id`, department CRUD across the
six kinds (medical, pharmacy, laboratory, radiology, administration, finance), provider/staff
assignment to departments, department-scoped list views, and the clinic settings surface for the
linkage.

**References:** ADR-HC-005 (org linkage & departments), schema-hc-02 (`hc_departments`,
`hc_branches.platform_*` columns).

**Invariants (reused, not re-specified):** platform Auth/RBAC/Audit; branch isolation per adr-hc-001;
PHI via SDK readers + audit per adr-hc-002; i18n id-ID (default) + en-US per adr-hc-004; mobile-first.
Departments carry `tenant_id` + `branch_id`; RLS per schema-hc-01. Departments are **not PHI** — no
encrypted columns on this epic — but every write emits a standard change-audit event.

---

## Hierarchy correspondence (normative)

The platform org hierarchy is `Tenant → Company → Branch → Department`. The healthcare hierarchy is
`hc_branches (clinic SITE) → hc_departments (clinical dept) → hc_rooms`. **A clinic site is equal to
a platform Branch.** The two trees join **at the Branch level only**: one `hc_branches` row ⇄ one
platform `branches` row (1:1). Everything above the Branch is inherited from the platform side via
`tenant_id` + `hc_branches.platform_company_id`; everything at or below `hc_departments` is
healthcare-owned.

The word "department" is **overloaded** and this epic disambiguates it:

- **Platform org Department** (`departments` table) — a generic, self-nesting org-chart / HR node
  (`company_id`, `branch_id`, `parent_department_id`, `head_user_id`). A clinic *site* may optionally
  roll up under one for reporting, via `hc_branches.platform_department_id`.
- **Clinical `hc_department`** — a functional unit **inside** a clinic site (medical, pharmacy,
  laboratory, radiology, administration, finance) that drives queue routing / coding / reporting.
  This is **not** the platform `departments` table (ADR-HC-005 D2).

### Level-by-level mapping

| Platform-org level | Healthcare correspondence | Cardinality | Link carrier | Which side owns the link |
|---|---|---|---|---|
| **Tenant** | healthcare `tenant_id` (every `hc_*` row) | 1 platform Tenant : N healthcare rows | shared `tenant_id` value (no FK column — implicit) | Platform owns the Tenant; healthcare copies the id onto every row |
| **Company** | clinic legal entity / brand — **no HC table**; referenced by `hc_branches.platform_company_id` | 1 Company : N clinic sites | `hc_branches.platform_company_id` → `companies.id` (nullable FK) | Healthcare owns the column; platform owns the Company row |
| **Branch** | **`hc_branches`** — the clinic **SITE** (top of the HC tree) | **1:1** (a clinic *is* a platform Branch) | `hc_branches.platform_branch_id` → `branches.id` (nullable FK, unique) | Healthcare owns the column; platform owns the Branch row |
| **Department** (org-chart) | **(A) roll-up:** `hc_branches.platform_department_id` → `departments.id` — the org-chart node a *whole clinic site* reports under. **(B) clinical:** `hc_departments` — functional units *inside* a site. **(A) and (B) are different concepts.** Optional (B)⇄platform link is **decision pending B1** (see Story 8.2.4). | (A) N clinic sites : 1 platform Department; (B) 1 clinic site : N clinical depts | (A) `hc_branches.platform_department_id` → `departments.id` (nullable FK). (B) proposed `hc_departments.platform_department_id` → `departments.id` (nullable FK — B1 to accept/reject) | Healthcare owns both columns; platform owns the `departments` rows |
| **(no platform equivalent)** | **`hc_departments`** (clinical) then **`hc_rooms`** | 1 clinical dept : N rooms | `hc_departments.branch_id` → `hc_branches.id`; `hc_rooms.department_id` → `hc_departments.id` | Fully healthcare-owned; no platform link |

**Ownership rule (normative):** every cross-tree link column lives **on the healthcare side** and is
**nullable + read-only** toward platform. Platform `tenants`/`companies`/`branches`/`departments`
tables are **never** modified (no reverse FK) — consistent with ADR-HC-005 D1 and BACKLOG v3
"Healthcare-side change only."

**Two `branch_id`s coexist (do not conflate):** the healthcare `branch_id` used for isolation/RLS is
**`hc_branches.id`** (ADR-HC-001), NOT the platform `branches.id`. `hc_branches.platform_branch_id`
is used **only** for platform-org roll-up and reporting joins, never for RLS scoping.

**Product recommendation on the clinical-dept ⇄ platform-dept question:** keep the two department
concepts **structurally separate** (ADR-HC-005 D2 stands), but add an **optional, nullable
`hc_departments.platform_department_id` FK** so a customer who maintains a platform org-chart can line
up clinical departments with org-chart nodes for reporting/head-of-department roll-up — **without**
making the clinical taxonomy depend on the platform tree. Default is NULL (unlinked); the clinical
`kind` taxonomy and branch-scoping are unaffected whether or not the link is set. **Final call is
B1's** (Story 8.2.4 / ADR-HC-005 D2 addendum); this epic specifies the story both ways so B1 can
accept or drop the column with no story rewrite.

---

## Feature 8.1 — Platform-Org Linkage

### Story 8.1.1 [OPEN]
**As a** Clinic Owner,
**I want to** link my clinic branch to the platform Company/Branch it corresponds to,
**so that** healthcare records inherit the platform org hierarchy without provisioning a separate tenant.

**Backend AC:**
- `PUT /api/v1/tenants/:tenant_id/branches/:branch_id/org-linkage` — auth: Clinic Owner (platform RBAC);
  payload: `platform_company_id`, `platform_branch_id`, optional `platform_department_id`.
- Writes `hc_branches.platform_company_id`, `hc_branches.platform_branch_id`,
  `hc_branches.platform_department_id` (nullable); values validated against the platform org service
  (`/api/v1/org/companies`, `/api/v1/org/branches`) — 422 if the referenced platform entity does not
  exist or is not under the caller's tenant.
- A given `platform_branch_id` may link to at most one `hc_branches` row (a clinic **is** a platform
  branch); duplicate linkage returns 409.
- Linkage emits a `hc_branch.org_linked` change-audit event (platform audit) with old/new JSON diff.
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/org-linkage` — returns current linkage with
  resolved platform company/branch/department display names.

**Frontend AC:**
- Route: `/clinic/settings/organization`
- Read the current linkage; three cascading selectors: platform Company → platform Branch → platform
  Department (optional), each populated from the platform org service and filtered to the caller's tenant.
- "Not linked yet" banner when unlinked; explains a clinic is a platform branch.
- Save disabled until Company + Branch are chosen; unsaved-changes warning on navigate-away.
- All labels in active locale; validation and duplicate-linkage errors surfaced inline.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/settings/organization`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Pengaturan > Organisasi) + main content; single-column card with a
  "Tautan Organisasi Platform" (Platform Org Linkage) section; desktop max-width 720 px.
- **Components:**
  - `FlexSidebar` — clinic portal nav; branch context badge in header
  - `FlexForm` — linkage form
  - `FlexSelect` — platform Company (searchable), platform Branch (searchable, filtered by Company),
    platform Department (searchable, optional, filtered by Branch)
  - `FlexBadge` — "Belum Tertaut" (Not Linked) / "Tertaut" (Linked) status indicator
  - `FlexButton` — "Simpan Tautan" (Save Linkage), "Batal"
  - `FlexAlert` — not-linked explainer banner; duplicate-linkage / validation errors
- **Key interactions:**
  - Company select loads Branch options on change; Branch select loads Department options on change
    (cascading; child selectors disabled until parent chosen).
  - Choosing a `platform_branch_id` already linked to another `hc_branches` row shows inline error
    "Cabang platform ini sudah tertaut ke klinik lain" (This platform branch is already linked).
  - "Simpan Tautan" → success toast "Tautan organisasi disimpan" (Org linkage saved); status badge
    flips to "Tertaut".
  - No PHI on this page.
- **Empty state:** Unlinked branch shows `FlexAlert` "Cabang ini belum tertaut ke organisasi platform.
  Sebuah klinik adalah cabang platform." (This branch is not yet linked to the platform org. A clinic
  is a platform branch.)
- **Error state:** Inline validation per selector; API/validation error `FlexAlert` at top of form;
  duplicate linkage 409 shown inline on the Branch selector.
- **i18n:** Section labels, selector labels/placeholders, status badges, toast, validation/error strings
  translated (ID default / EN). Platform company/branch/department names served as-is from platform.
- **Mobile:** Secondary (owner task, likely desktop); selectors stack single-column full-width; save
  button pinned to bottom on narrow viewport.

### Story 8.1.2 [OPEN]
**As a** Clinic Owner,
**I want to** view the resolved platform org context on the clinic settings surface,
**so that** I can confirm the linkage is correct and understand which platform entities own this branch.

**Backend AC:**
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/org-context` — auth: Clinic Owner or Branch
  Manager; returns resolved chain: platform Tenant → Company → Branch → Department (where linked) plus
  the count of `hc_departments` under this branch.
- Response includes a `linkage_health` flag: `ok` when all linked platform IDs still resolve, `stale`
  when a referenced platform entity was archived/deleted (surfaced for re-linking).
- Read-only; no writes; access logged as a standard read-audit event (non-PHI).

**Frontend AC:**
- Route: `/clinic/settings/organization` (context panel alongside the linkage form from 8.1.1)
- Displays the resolved org chain as a breadcrumb-style read-only summary; shows department count.
- "Stale linkage" warning with a "Perbaiki Tautan" (Fix Linkage) action pointing back to 8.1.1 when
  `linkage_health = stale`.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/settings/organization` (org context panel)
- **Portal:** Clinic Portal
- **Layout:** Read-only summary panel above/beside the linkage form; horizontal breadcrumb chain on
  desktop, stacked list on mobile.
- **Components:**
  - `FlexCard` — org context card: Tenant › Company › Branch › Department chain
  - `FlexBadge` — `linkage_health` badge ("Sehat" / "Perlu Diperbaiki")
  - `FlexButton` — "Perbaiki Tautan" (Fix Linkage) shown only when stale
  - `FlexAlert` — stale-linkage warning
- **Key interactions:**
  - Renders the resolved chain read-only; department count shown as "N departemen".
  - When `linkage_health = stale`, warning `FlexAlert` appears and "Perbaiki Tautan" scrolls to /
    focuses the linkage form.
  - No PHI on this page.
- **Empty state:** If unlinked, panel shows "Konteks organisasi akan muncul setelah cabang tertaut."
  (Org context appears once the branch is linked.)
- **Error state:** Context load failure: inline `FlexAlert` "Gagal memuat konteks organisasi."
  (Failed to load org context.)
- **i18n:** Chain labels, health badge, button, empty/error strings translated (ID / EN).
- **Mobile:** Chain stacks vertically; each level on its own line with a connector glyph.

### Story 8.1.3 [OPEN]
**As a** Clinic Owner,
**I want to** unlink a clinic site from its platform Branch (and optional Company/Department),
**so that** I can correct a mistaken linkage or re-point the site when the platform org is restructured.

**Backend AC:**
- `DELETE /api/v1/tenants/:tenant_id/branches/:branch_id/org-linkage` — auth: Clinic Owner (platform
  RBAC); clears `hc_branches.platform_company_id` / `platform_branch_id` / `platform_department_id`
  back to NULL (does **not** delete the `hc_branches` row or any platform row).
- Unlink is blocked with 409 when downstream artifacts depend on the resolved platform org for the
  current period — specifically when a platform-org-scoped report/export is pinned to this linkage
  (surfaced with a reason); otherwise it succeeds. If B1 decides no such hard dependency exists at MVP,
  the 409 guard is dropped and unlink is always allowed.
- Emits a `hc_branch.org_unlinked` change-audit event with the old linkage JSON.
- Re-linking is Story 8.1.1 (`PUT`); unlink + re-link is the supported "re-point" flow — the unique
  index on `platform_branch_id` frees the old platform branch for reuse once cleared.

**Frontend AC:**
- Route: `/clinic/settings/organization` (an "Unlink" affordance on the linkage card from 8.1.1).
- Confirmation modal explaining the site will revert to "Not linked" and org context will disappear
  until re-linked; blocked-unlink 409 surfaces the pinned-report reason.
- After success, status badge flips to "Belum Tertaut" (Not Linked) and the context panel (8.1.2)
  empties. All labels in active locale.

**Architecture note for B1:** confirm whether any MVP artifact hard-depends on a live linkage (pinned
platform-org reports/exports). If none, drop the 409 unlink guard and document unlink as always-allowed
in ADR-HC-005 D1.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/settings/organization` (unlink action on the linkage card)
- **Portal:** Clinic Portal
- **Layout:** Reuses the 8.1.1 linkage card; "Putuskan Tautan" (Unlink) as a secondary/destructive
  button beside "Simpan Tautan", shown only when the site is currently linked.
- **Components:**
  - `FlexButton` — "Putuskan Tautan" (Unlink, destructive style)
  - `FlexModal` — unlink confirmation: "Putuskan tautan cabang ini dari organisasi platform? Konteks
    organisasi akan hilang sampai ditautkan kembali." (Unlink this branch from the platform org? Org
    context will disappear until re-linked.)
  - `FlexBadge` — status flips to "Belum Tertaut" on success
  - `FlexAlert` — blocked-unlink 409 reason
- **Key interactions:**
  - "Putuskan Tautan" opens the confirmation modal; confirm → `DELETE` → success toast "Tautan
    organisasi diputus" (Org linkage removed); badge and context panel reset.
  - 409 shows the pinned-dependency reason inside the modal; unlink is not performed.
  - No PHI on this page.
- **Empty state:** Button hidden when the site is already unlinked.
- **Error state:** 409/other errors surfaced in the modal footer.
- **i18n:** Button, modal text, toast, error strings translated (ID / EN).
- **Mobile:** Unlink button full-width below Save; confirmation modal full-screen.

### Story 8.1.4 [OPEN]
**As the** platform (linkage service),
**I want to** enforce the 1:1 clinic-site⇄platform-branch rule and the `tenant_id` invariant at
link time,
**so that** a clinic site can never be linked to a platform branch under a different tenant or to a
platform branch another site already owns.

**Backend AC:**
- On the 8.1.1 `PUT` linkage, the service validates, in order: (1) `platform_branch_id` resolves to an
  existing `branches` row; (2) `branches.tenant_id == hc_branches.tenant_id` — 422
  `tenant_mismatch` otherwise; (3) `platform_company_id`, when supplied, resolves and its
  `tenant_id` matches — 422 otherwise; (4) `platform_department_id`, when supplied, resolves and
  belongs to the same tenant/company — 422 otherwise.
- **1:1 enforcement:** a `platform_branch_id` already present on another `hc_branches` row returns 409
  `platform_branch_already_linked`; backed by the partial unique index
  `uq_hc_branches_platform_branch` (schema-hc-02 A.1) so the race also fails closed at the DB.
- The `tenant_id` cross-table equality is **application-validated** (a cross-FK DB CHECK is not
  expressible); covered by an integration test that attempts a cross-tenant link and expects 422.
- Validation failures emit no linkage write and are returned as structured, translatable error codes
  (not raw DB errors).

**Frontend AC:**
- Route: `/clinic/settings/organization` — the 8.1.1 form surfaces each validation error inline on the
  offending selector: `tenant_mismatch` on the Branch selector, `platform_branch_already_linked` on the
  Branch selector, company/department mismatches on their respective selectors.
- The Branch selector's options are pre-filtered to the caller's tenant so `tenant_mismatch` is a
  guard-rail, not the normal path. All labels in active locale.

**Architecture note for B1:** finalize **where** the `tenant_id` equality + 1:1 uniqueness are enforced
when platform-org and healthcare live in **separate databases** — options: (a) app-layer validation
against the platform org API + the healthcare partial unique index (single-DB fallback), or (b) a
synchronous platform-org SDK check returning the branch's `tenant_id`. Specify the authoritative
uniqueness owner and the failure mode if the platform lookup is unavailable (recommend fail-closed →
422/503, never silently link).

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/settings/organization` (validation feedback on the 8.1.1 form)
- **Portal:** Clinic Portal
- **Layout:** No new screen — inline error slots on the existing cascading selectors.
- **Components:**
  - `FlexSelect` — Branch/Company/Department selectors gain inline error text slots
  - `FlexAlert` — top-of-form summary for non-field errors (e.g. platform lookup unavailable)
- **Key interactions:**
  - Save attempt with a cross-tenant branch → inline "Cabang platform ini berada di tenant lain."
    (This platform branch belongs to another tenant.)
  - Save attempt on an already-linked branch → inline "Cabang platform ini sudah tertaut ke klinik
    lain." (This platform branch is already linked — reused from 8.1.1.)
  - Platform lookup unavailable → top `FlexAlert` "Tidak dapat memverifikasi organisasi platform saat
    ini. Coba lagi." (Cannot verify platform org right now. Try again.) and Save stays disabled.
  - No PHI on this page.
- **Empty state:** N/A (validation layer).
- **Error state:** Per-selector inline + top-of-form summary as above.
- **i18n:** All validation strings translated (ID / EN).
- **Mobile:** Inline errors render under each stacked selector.

### Story 8.1.5 [OPEN]
**As a** Clinic Owner onboarding a new clinic,
**I want to** choose whether my clinic is a Branch under a shared Company/Tenant or gets its own
dedicated Tenant,
**so that** the platform org topology matches my isolation needs before I create clinical data.

**Backend AC:**
- `GET /api/v1/tenants/:tenant_id/onboarding/org-topology` — returns the two supported topologies and
  the current default: **(A) clinic-as-Company/Branch** (default — the clinic is a platform Branch
  under an existing Company in the current Tenant) and **(B) dedicated Tenant** (hard isolation,
  provisioned only on explicit request).
- `POST /api/v1/tenants/:tenant_id/onboarding/org-topology` — records the chosen topology and, for (A),
  ensures/reuses the target platform Company + creates the platform Branch via the existing platform
  org API (`/api/v1/org/companies`, `/api/v1/org/branches`); for (B), flags the request for
  platform-org dedicated-tenant provisioning (out-of-band, platform-owned) and does **not** itself
  create a tenant. Either way the resulting `platform_company_id` / `platform_branch_id` are handed to
  the 8.1.1 linkage step.
- Healthcare creates **no** platform org rows directly beyond calling the platform org API; no
  healthcare schema change is required for either topology (ADR-HC-005 D1 rationale).
- Choice emits a `hc_branch.onboarding_topology_selected` change-audit event.

**Frontend AC:**
- Route: `/clinic/onboarding/organization` — a two-option chooser (Shared Company vs Dedicated Tenant)
  with plain-language trade-offs (shared = simpler/faster; dedicated = hard isolation, on request,
  slower to provision).
- Selecting (A) proceeds inline to Company pick/create + auto-branch-create then hands off to the 8.1.1
  linkage confirmation; selecting (B) shows a "request submitted, provisioning is handled by platform
  admin" state.
- All labels in active locale.

**Architecture note for B1:** confirm the dedicated-tenant path is **platform-org-owned provisioning**
(healthcare only records the request + resulting ids) and that no `hc_*` schema differs between the two
topologies — carry this as an explicit line in ADR-HC-005 D1 ("everything under a Tenant; a dedicated
tenant only on explicit request").

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/onboarding/organization`
- **Portal:** Clinic Portal (onboarding flow)
- **Layout:** Full-width onboarding step; two selectable `FlexCard` options side by side on desktop,
  stacked on mobile; primary "Lanjutkan" (Continue) at the bottom.
- **Components:**
  - `FlexCard` ×2 — "Cabang di bawah Perusahaan Bersama" (Branch under a shared Company, default,
    recommended badge) and "Tenant Khusus" (Dedicated Tenant, "atas permintaan" / on-request badge)
  - `FlexSelect` — Company pick/create (topology A only), populated from platform org, tenant-filtered
  - `FlexButton` — "Lanjutkan", "Kembali"
  - `FlexAlert` — dedicated-tenant "request submitted" info state
- **Key interactions:**
  - Choosing (A) reveals the Company selector and, on Continue, creates the platform Branch then routes
    to `#/clinic/settings/organization` with the linkage pre-filled (8.1.1).
  - Choosing (B) → Continue shows "Permintaan tenant khusus dikirim. Penyediaan ditangani admin
    platform." (Dedicated-tenant request submitted. Provisioning handled by platform admin.)
  - No PHI on this page.
- **Empty state:** Default selection is topology (A) with the recommended badge.
- **Error state:** Company create/branch create failures surfaced as `FlexAlert`; retry preserves the
  chosen topology.
- **i18n:** Card titles + trade-off copy, badges, selector, buttons, info/error strings translated
  (ID / EN).
- **Mobile:** Cards stack; recommended card first; Continue pinned to bottom.

## Feature 8.2 — Department Management

### Story 8.2.1 [OPEN]
**As a** Branch Manager,
**I want to** create a department of a specific kind within my branch,
**so that** staff, providers, and visits can be organized and routed by department.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/departments` — auth: Clinic Owner or Branch
  Manager for that branch; payload: `code`, `name`, `kind` ∈ {medical, pharmacy, laboratory, radiology,
  administration, finance}, optional `is_active` (default true).
- Creates `hc_departments` row `(id, tenant_id, branch_id, code, name, kind, is_active)`; `code` unique
  per `(tenant_id, branch_id)` — 409 on duplicate; `kind` validated against the enum — 422 otherwise.
- Department creation emits `hc_department.created` change-audit event with JSON diff.
- Branch scoping enforced by RLS per schema-hc-01; no cross-branch create.

**Frontend AC:**
- Route: `/clinic/departments/new`
- Form: department code, name, kind selector (six kinds, locale-labelled), active toggle.
- Kind selector shows an icon + description per kind; code auto-suggested from name (editable).
- Success → redirect to department list; duplicate-code error inline.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/departments/new`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Departemen > Tambah) + main content; single-page form; desktop
  max-width 640 px.
- **Components:**
  - `FlexSidebar` — clinic portal nav; branch context badge
  - `FlexForm` — department form
  - `FlexInput` — code, name
  - `FlexSelect` — kind (Medis / Farmasi / Laboratorium / Radiologi / Administrasi / Keuangan) with
    per-option icon + short description
  - `FlexToggle` — "Aktif" (Active) status
  - `FlexButton` — "Simpan Departemen" (Save Department), "Batal"
  - `FlexAlert` — success / duplicate-code / validation errors
- **Key interactions:**
  - Typing a name auto-suggests a `code` (slugified, uppercase); user can override.
  - Selecting a kind shows a one-line description of what the kind is used for downstream (routing,
    reporting).
  - On save: redirect to `#/clinic/departments` with success toast "Departemen ditambahkan".
  - No PHI on this page.
- **Empty state:** N/A (creation form).
- **Error state:** Duplicate code inline "Kode departemen sudah dipakai di cabang ini" (Department code
  already used in this branch); other errors `FlexAlert` at top.
- **i18n:** Field labels, kind labels + descriptions, toggle label, buttons, error strings translated
  (ID / EN).
- **Mobile:** Secondary; single-column; kind select as full-screen sheet on narrow viewport; save
  button pinned bottom.

### Story 8.2.2 [OPEN]
**As a** Branch Manager,
**I want to** edit a department's name/code and enable or disable it,
**so that** I can keep the org structure current without losing historical references.

**Backend AC:**
- `PUT /api/v1/tenants/:tenant_id/branches/:branch_id/departments/:department_id` — auth: Clinic Owner
  or Branch Manager; editable: `code`, `name`, `is_active`; `kind` is **immutable** after create (422 if
  changed) because downstream routing/reporting depend on it.
- `is_active = false` (disable) is a soft state: the department is retained for historical references and
  reporting but hidden from active assignment/queue-routing pickers; disabling a department that still
  has active staff assignments or open queue tickets returns 409 with a reason payload.
- Edits emit `hc_department.updated` change-audit event with old/new JSON diff.

**Frontend AC:**
- Route: `/clinic/departments/:department_id/edit`
- Editable code, name, active toggle; kind shown read-only with an explanatory tooltip.
- Disable action shows a confirmation modal warning about downstream effects and blocks disable when the
  department has active assignments/open tickets (surfacing the count).
- All labels in active locale; unsaved-changes warning.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/departments/:department_id/edit`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Departemen) + main content; single-page edit form mirroring 8.2.1.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexForm` — edit form
  - `FlexInput` — code, name
  - `FlexBadge` — kind (read-only) with `FlexTooltip` "Jenis tidak dapat diubah" (Kind cannot be changed)
  - `FlexToggle` — "Aktif" active/disable
  - `FlexModal` — disable-confirmation "Nonaktifkan departemen ini? Penugasan aktif harus dipindahkan
    dulu." (Disable this department? Active assignments must be moved first.)
  - `FlexButton` — "Simpan", "Batal"
  - `FlexAlert` — unsaved-changes / block-disable / validation errors
- **Key interactions:**
  - Toggling to inactive opens the disable-confirmation modal; if the API returns 409 the modal shows
    the blocking count "N staf & M tiket antrean aktif" (N staff & M active queue tickets).
  - Kind badge is read-only with tooltip.
  - Save → success toast; navigating away with unsaved changes triggers a confirmation modal.
  - No PHI on this page.
- **Empty state:** N/A (edit form always populated).
- **Error state:** Duplicate-code inline; block-disable 409 surfaced in the modal with counts; other
  errors `FlexAlert` at top.
- **i18n:** Field labels, read-only kind tooltip, modal text, buttons, error strings translated (ID / EN).
- **Mobile:** Secondary; single-column; disable modal full-screen on narrow viewport.

### Story 8.2.3 [OPEN]
**As a** Branch Manager,
**I want to** browse a department-scoped list of all departments in my branch,
**so that** I can see the org structure and drill into any department's staff and providers.

**Backend AC:**
- `GET /api/v1/tenants/:tenant_id/branches/:branch_id/departments?kind=&is_active=&q=&page=` — auth:
  Clinic Owner, Branch Manager, or any staff member of the branch; returns paginated `hc_departments`
  filtered by kind, active status, and free-text (`code`/`name`); branch-scoped by RLS.
- Each row includes derived counts: assigned providers, assigned staff (from the assignment join in
  Feature 8.3) — no PHI.
- Read access logged as a standard read-audit event.

**Frontend AC:**
- Route: `/clinic/departments`
- Filterable, searchable table of departments with kind badge, active status, provider/staff counts.
- Kind filter chips and active/inactive toggle; row click → department detail.
- Empty state: "No departments yet. Create one to organize your branch."
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/departments`
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Departemen) + main content; filter toolbar above a paginated table;
  "Tambah Departemen" (Add Department) button top-right.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexToolbar` — search `FlexInput`, kind filter `FlexCluster` chips, active/inactive `FlexToggle`
  - `FlexTable` — columns: Kode, Nama, Jenis, Status, Provider, Staf, Tindakan; sortable by name/kind
  - `FlexBadge` — kind badge (color-coded per kind); active/inactive status badge
  - `FlexButton` — "Tambah Departemen"; per-row "Edit"
  - `FlexPagination` — table pagination
- **Key interactions:**
  - Search debounced (300 ms) over code/name; kind chips filter immediately (multi-select); active
    toggle filters status.
  - Row click navigates to `#/clinic/departments/:department_id` detail (staff/providers).
  - Provider/staff counts render as small numeric badges.
  - No PHI on this page.
- **Empty state:** "Belum ada departemen. Buat departemen untuk menata cabang Anda." (No departments yet.
  Create one to organize your branch.)
- **Error state:** Load failure `FlexAlert` "Gagal memuat departemen. Coba lagi." (Failed to load
  departments. Try again.)
- **i18n:** Column headers, kind/status labels, filter chip labels, empty/error strings translated
  (ID / EN).
- **Mobile:** Table collapses to card list; each card shows code, name, kind badge, status, counts, and
  an Edit action; filter toolbar collapses into a `FlexDrawer`.

### Story 8.2.4 [OPEN — decision pending B1]
**As a** Clinic Owner who maintains a platform org-chart,
**I want to** optionally link a clinical `hc_department` to a platform `departments` org-chart node,
**so that** org-chart reporting and head-of-department roll-up line up with the clinical structure —
without making the clinical taxonomy depend on the platform tree.

> **Disambiguation (see Hierarchy correspondence):** this links concept **(B) clinical `hc_department`**
> to a platform org **Department**. It is distinct from `hc_branches.platform_department_id`
> (Story 8.1.1), which rolls up the *whole clinic site*. This story rolls up an *individual clinical
> department*. **A3 recommends implementing this as an optional, nullable FK; final accept/reject is B1's.**

**Backend AC (conditional on B1 accepting the column):**
- Schema addendum: `hc_departments` gains a nullable `platform_department_id` (VARCHAR(36),
  FK → `departments.id`) — **default NULL**; the clinical `kind` taxonomy and branch-scoping are
  unchanged whether set or not.
- `PUT /api/v1/tenants/:tenant_id/branches/:branch_id/departments/:department_id/org-link` — auth:
  Clinic Owner or Branch Manager; payload `platform_department_id` (or null to clear). Validates the
  referenced `departments` row exists and shares the site's `tenant_id` (and, if the site is linked,
  its `platform_company_id`) — 422 otherwise. Many clinical depts MAY map to one platform Department;
  no uniqueness is imposed (unlike the 1:1 site⇄branch rule).
- Emits `hc_department.org_linked` / `hc_department.org_unlinked` change-audit events.
- **If B1 rejects the column:** this story is dropped from MVP and the two department concepts stay
  fully separate; mark 8.2.4 as `[SUPERSEDED — clinical/platform depts kept separate per ADR-HC-005 D2]`
  rather than deleting it.

**Frontend AC (conditional):**
- Route: `/clinic/departments/:department_id/edit` — an optional "Tautan Org-Chart Platform" (Platform
  Org-Chart Link) selector, only visible when the clinic site itself is linked (8.1.1); populated from
  the platform `departments` under the site's Company.
- Clearly labelled as optional and for reporting roll-up only; empty = "Tidak tertaut" (Not linked).
  All labels in active locale.

**Architecture note for B1:** **decide whether `hc_departments` gets the optional
`platform_department_id` FK.** If yes: add it to schema-hc-02 A.2 (nullable, no unique constraint,
FK → `departments.id`), add an ADR-HC-005 D2 addendum, and keep this story `[OPEN]`. If no: record the
rejection rationale in ADR-HC-005 D2 (clinical depts intentionally decoupled from org-chart) and mark
this story superseded. A3's recommendation: **accept as optional/nullable** — low cost, unblocks
org-chart reporting, does not couple lifecycles.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/departments/:department_id/edit` (optional org-link selector; only if 8.2.4 accepted)
- **Portal:** Clinic Portal
- **Layout:** An additional optional field within the 8.2.2 edit form, below the read-only kind badge.
- **Components:**
  - `FlexSelect` — platform org-chart Department (searchable, optional, filtered to the site's Company);
    only rendered when the site is linked
  - `FlexBadge` / helper text — "Opsional · untuk pelaporan bagan organisasi" (Optional · for org-chart
    reporting)
  - `FlexAlert` — validation error if the chosen platform department is out of tenant/company
- **Key interactions:**
  - Choosing a platform department saves via the dedicated `org-link` endpoint (or as part of the edit
    save, per B1); clearing sets it back to "Tidak tertaut".
  - Hidden entirely when the site is unlinked, with helper text "Tautkan cabang ke organisasi platform
    dulu." (Link the branch to the platform org first.)
  - No PHI on this page.
- **Empty state:** "Tidak tertaut" when `platform_department_id` is NULL.
- **Error state:** Out-of-tenant/company selection → inline `FlexAlert`.
- **i18n:** Field label, optional/helper text, error strings translated (ID / EN).
- **Mobile:** Renders as a stacked optional field; full-screen select sheet.

## Feature 8.3 — Provider & Staff Assignment to Departments

### Story 8.3.1 [OPEN]
**As a** Branch Manager,
**I want to** assign providers and staff to a department,
**so that** encounters, queues, and reports can be attributed to the correct department.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/departments/:department_id/members` — auth:
  Clinic Owner or Branch Manager; payload: `user_id` (existing `hc_branch_staff` member) or
  `provider_id` (existing `hc_providers`), plus `member_role` ∈ {provider, staff}.
- Assignment is validated: the user/provider must already belong to this branch (`hc_branch_staff` /
  `hc_providers` scoped to `branch_id`) — 422 if not; a member may belong to multiple departments.
- `DELETE /api/v1/.../departments/:department_id/members/:member_id` — removes the assignment (keeps the
  underlying staff/provider record); blocked with 409 if the member has an open queue ticket in this
  department.
- Assignment/removal emit `hc_department.member_assigned` / `hc_department.member_removed` change-audit
  events. Reuses platform RBAC — no new roles defined here.

**Frontend AC:**
- Route: `/clinic/departments/:department_id` (Members tab)
- Two lists: Providers and Staff, each with an "Add member" picker restricted to branch members not yet
  in the department.
- Remove action per member with confirmation; blocked-removal surfaces the open-ticket reason.
- All labels in active locale.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/clinic/departments/:department_id` (Anggota / Members tab)
- **Portal:** Clinic Portal
- **Layout:** Sidebar nav (active: Departemen) + main content; department header (name + kind badge)
  above `FlexTabs`: Anggota (Members), Ringkasan (Overview); Members tab has two sections — Provider and
  Staf — side by side on desktop, stacked on mobile.
- **Components:**
  - `FlexSidebar` — nav; branch context badge
  - `FlexTabs` — Anggota / Ringkasan
  - `FlexTable` — providers list; staff list (columns: Nama, Peran, Tindakan)
  - `FlexModal` — "Tambah Anggota" (Add Member) picker: searchable `FlexSelect` of branch members not
    already assigned, with member_role choice (Provider / Staf)
  - `FlexBadge` — role badge per member; kind badge in header
  - `FlexButton` — "Tambah Provider", "Tambah Staf", per-row "Hapus" (Remove)
  - `FlexAlert` — success / blocked-removal feedback
- **Key interactions:**
  - "Tambah Provider"/"Tambah Staf" opens the picker modal filtered to eligible branch members.
  - "Hapus" opens a confirmation; if the API returns 409 the blocked reason is shown "Anggota memiliki
    tiket antrean aktif di departemen ini" (Member has an active queue ticket in this department).
  - Names shown are staff/provider names (not PHI) but a mask toggle is available for screen privacy in
    crowded areas.
- **Empty state:** Providers/Staff sections each: "Belum ada anggota. Tambahkan dari staf cabang." (No
  members yet. Add from branch staff.)
- **Error state:** Add/remove API errors `FlexAlert` in the modal footer / above the list.
- **i18n:** Tab labels, section titles, table headers, picker labels, role badges, empty/error strings
  translated (ID / EN).
- **Mobile:** Provider and Staff sections stack; tables collapse to card lists; add-member picker is a
  full-screen sheet.

## Story Count: Feature 8.1 (5: 8.1.1–8.1.5) + 8.2 (4: 8.2.1–8.2.4) + 8.3 (1) = **10 stories**

> v1 had 6 (8.1×2, 8.2×3, 8.3×1). v2 appends 8.1.3 (unlink), 8.1.4 (1:1 + tenant-invariant
> enforcement), 8.1.5 (onboarding topology choice), and 8.2.4 (optional clinical-dept ⇄ platform-dept
> link — pending B1). No existing story renumbered or removed.
