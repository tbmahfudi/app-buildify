---
status: approved
author: B1 (Architect), with A2 (Business Analyst) feature research
date: 2026-06-28
title: Module public pages — unauthenticated + patient-authenticated surfaces (static portal apps)
supersedes: []
related:
  - adr-module-frontend-integration.md
  - adr-010-public-portal-framework.md
  - adr-005-module-packaging-format.md
  - adr-008-submodule-deployment-topology.md
  - adr-tenant-isolation-22.md
---

# ADR: Module Public Pages (Public + Patient-Facing Surfaces)

## TL;DR

- **Architecture (one line):** Each module ships a **separate static portal app** under
  `frontend/public/`, served by nginx at the platform-owned `/portal/{module_slug}/` namespace
  (per ADR-010), with **two audiences inside one portal app** — unauthenticated *public* pages and
  *patient-authenticated* pages — declared in the manifest via a new `public_portal.routes[].audience`
  field. It is **not** part of the authenticated admin SPA.
- **Public-vs-patient serving decision:** **Single static portal app, two audiences** (public + patient),
  served at `/portal/{slug}/`; the **admin SPA stays a wholly separate app** at `/`. Public and patient
  pages share one deployable bundle but are gated at the *data* layer (anonymous vs patient JWT), not by
  serving different files.

---

## 1. Context

ADR-010 established the `/portal/{module_slug}/` namespace and the `public_portal` manifest field; the
approved **module-frontend ADR** (`adr-module-frontend-integration.md`) established the hard constraint
that the **entire frontend must be static-deployable on any web server (nginx / Apache / S3 / CDN), no
SSR, no server runtime to assemble HTML**, and a Web-Components/light-DOM, manifest-driven page contract
for the **authenticated admin SPA**.

This ADR reconciles the two and fills the gap they left: **how a module exposes public/patient-facing
surfaces that are distinct from its authenticated admin pages**, generalised beyond healthcare.

### 1.1 What already exists on disk (verified)

The healthcare module is far more built-out than the manifest suggests:

| Area | Status |
|------|--------|
| `frontend/public/` | `index.html` (clinic portal shell, Bootstrap), `clinics.{html,js}` (directory), `clinic-profile.{html,js}`, `portal.js`. Hash-routed SPA pages. |
| `frontend/patient/` | Full patient app: `portal.html` (mobile shell + bottom nav), `register`, `book`, `appointments`(+detail), `prescriptions`(+detail), `lab-results`(+detail), `invoices`(+detail), `records`, `profile`, `waitlist`, `review-new`, `encounter-detail`. i18n-enabled. |
| Public backend | `routes_public.py` — `GET /api/v1/clinics/search`, `/clinics/{slug}`, `/clinics/{slug}/branches/{branch_id}`. **No PHI**; Redis 60 req/IP/min rate-limit; 5-min per-slug cache; aggregates across **all tenants**. |
| Patient identity | `routes_patient_auth.py` + `sdk/patient_tokens.py` — **dedicated** OTP-based auth: `POST /patients/register`, `/patients/auth/otp/{send,verify}`, `/auth/token`, `/auth/refresh`, `/auth/logout`. Patient JWT (HS256, 15-min access / 7-day refresh, claims `{sub: patient_id, phone, roles:["patient"], type}`). Captcha, PHI crypto/audit, consent (`HCPatientConsent`), DPA gate. |
| Patient data APIs | `routes_patient_appointments.py`, `routes_patient_profile.py`, plus pharmacy/lab/billing reads scoped to the patient. |
| nginx | `/portal/{slug}/` location already present with `index.html` SPA fallback; admin SPA at `/`; `/modules/{m}/{file}` alias (rooted at `frontend/`); `/api/` proxy; OTP rate-limit zone. |

**Key finding:** the heavy lifting (patient auth, public clinic APIs, the actual public/patient pages)
is *done*. What is **missing** is the **declarative contract** that ties it together: the manifest still
declares only clinic-staff admin routes; there is no `public_portal` block, no audience taxonomy, no
install-time wiring of `frontend/public/` to `/portal/healthcare/`, and the patient app under
`frontend/patient/` is not addressed by ADR-010 at all (it only covered anonymous public pages).

---

## 2. Decision 1 — Architecture for module public pages (general)

### 2.1 The spectrum and the recommendation

There are three audiences a module surface can target:

| Audience | Example (healthcare) | Auth | Served from |
|----------|----------------------|------|-------------|
| **public** | clinic directory, clinic profile, booking landing | none (anonymous) | portal app |
| **patient** | my appointments, my prescriptions/lab results, refill requests | patient JWT (`roles:["patient"]`) | portal app |
| **staff** | clinic admin dashboard, schedules, billing admin | platform RBAC JWT | **admin SPA** (existing) |

**Recommendation: a single `frontend/public/` static portal app per module, hosting BOTH the
`public` and `patient` audiences, served at `/portal/{module_slug}/`. `staff` stays in the admin SPA.**

Rejected alternatives:

- **(A) Serve public/patient routes inside the admin SPA** (a public route area + patient-role pages).
  Rejected: the admin SPA boots the authenticated module loader, fetches the RBAC menu, and assumes a
  logged-in platform user; bending it to also serve anonymous SEO pages and a separate patient-token
  auth model bloats and *risks* it (one routing bug could expose an admin surface to an anonymous
  visitor). Blast-radius and trust separation argue for a distinct app. Consistent with ADR-010's
  Separation Rule.
- **(B) Two separate portal apps — one public, one patient.** Rejected: they share branding, the same
  tenant context, navigation (a patient lands from the public booking flow into their portal), and the
  same deploy unit. Splitting them doubles the deploy/routing surface for no isolation gain — the real
  trust boundary is **anonymous vs patient-token at the API**, not at the file-serving layer. One app,
  two audiences, gated by which token the page presents.

**Why this satisfies the constraints:**

- **Static-deployable / no-SSR:** the portal app is plain `.html/.js/.css` (hash-routed, per ADR-010),
  served by the nginx `alias`. Identical posture to the admin SPA. A module MAY use a Vite build
  (consistent with the FE ADR rev2) as long as the *output* is static. No server renders HTML.
- **Multi-tenant (which clinic?):** see 2.3 — tenant is resolved from the **URL** (clinic `slug`), never
  from a logged-in session, because public visitors have none.
- **SEO / shareable URLs:** public pages need crawlable, shareable URLs. Hash routing (`#clinic/medcare`)
  is acceptable for v1 (matches ADR-010 and the static fallback) but is **SEO-weak**. We add an
  **optional path-routing mode** (see 2.4) for modules that need real SEO, served by the same
  `try_files ... /index.html` fallback so deep links work without SSR.
- **Security:** public pages call only `get_current_user_optional` / anonymous APIs that return **no
  PHI** (already true of `routes_public.py`). Patient pages present a patient JWT; patient-data APIs
  scope every query to `sub = patient_id`. The admin SPA and its RBAC routes are a *different app on a
  different path* — not reachable by editing a portal URL.

### 2.2 Manifest contract additions (normative)

Extend ADR-010's `public_portal` object. `audience` is the new core concept.

```jsonc
"public_portal": {
  "enabled": true,
  "entry_point": "frontend/public/index.html",   // portal SPA shell
  "title": "Find a Clinic",
  "routing": "hash",                              // "hash" (default, SEO-weak) | "path" (SEO, opt-in)
  "tenant_resolution": "slug_in_path",            // how the portal picks the tenant (see 2.3)
  "routes": [
    { "path": "#search",            "audience": "public",  "title": "Find a clinic" },
    { "path": "#clinic/:slug",      "audience": "public",  "title": "Clinic profile" },
    { "path": "#register",          "audience": "public",  "title": "Register" },
    { "path": "#login",             "audience": "public",  "title": "Patient login" },
    { "path": "#portal",            "audience": "patient", "title": "My portal" },
    { "path": "#appointments",      "audience": "patient" },
    { "path": "#prescriptions",     "audience": "patient" },
    { "path": "#lab-results",       "audience": "patient" }
  ]
}
```

Rules:

- **`audience` is descriptive, not the security boundary.** Trust is enforced **server-side at the API**
  (anonymous vs patient JWT). `audience: patient` routes simply tell the portal shell to require a
  patient token client-side (redirect to `#login` if absent) — a UX guard, never the access control.
- `routes[].path` are **client-side** portal routes (hash by default), distinct from the admin SPA's
  `#/{module}/...` routes and from manifest `routes[]` (which remain staff/admin, RBAC-gated, unchanged).
- `entry_point` is relative to the module root and resolves under `frontend/public/`.
- A module with **no** `public_portal` block has no public surface (nginx returns 404 for its slug) —
  unchanged from ADR-010.
- The manifest validator (FE ADR) gains warnings: `public_portal.enabled` true but `entry_point` missing
  or file absent; `audience` not in `{public,patient}`; `routing:"path"` without a server alias entry.

### 2.3 Multi-tenant: which clinic/tenant?

A public visitor has no session, so tenant **cannot** come from auth. Resolution order:

1. **Directory pages (`#search`)** are **cross-tenant** — `GET /clinics/search` already aggregates all
   tenants. No single tenant.
2. **Clinic-scoped pages (`#clinic/:slug`, `#register`, `#book`)** resolve tenant from the **`slug` in
   the route/URL**, passed to the API path (`/clinics/{slug}`). The clinic slug **is** the tenant
   selector for the public surface. This is already how `routes_public.py` works.
3. **Patient pages** resolve tenant from the **patient JWT** — a patient belongs to a clinic/tenant
   (the `HCPatient` row carries `tenant_id`); the token's `sub` binds to that record, and patient-data
   APIs scope by it. The patient never selects a tenant; their identity carries it.

**Recommended addition:** the patient access token SHOULD carry a `tenant_id` (or `clinic_slug`) claim
so patient-data APIs can assert tenant scope from the token rather than re-deriving it (defence in
depth, and lets a future cross-clinic patient be modelled as multiple tokens). *Gap — see Decision 2.*

### 2.4 Routing / nginx (public vs authed traffic)

No new nginx work for hash mode — ADR-010's block already serves it:

```nginx
location ~ ^/portal/([a-z][a-z0-9-]*)/(.*)$ {
    alias /usr/share/nginx/html/modules/$1/public/$2;
    try_files $uri $uri/ /usr/share/nginx/html/modules/$1/public/index.html =404;
}
```

- Admin SPA = `/`; portal = `/portal/{slug}/`; APIs = `/api/`. Three disjoint path namespaces; the
  trust separation is structural.
- **Path-routing (SEO) mode** reuses the *same* block — `try_files ... /index.html` already gives deep-link
  fallback for clean paths like `/portal/healthcare/clinic/medcare`. The portal shell reads
  `location.pathname` instead of `location.hash`. No SSR; crawlers get a 200 + the shell, then JS
  hydrates. (Full pre-rendering, if ever needed, is a static build-time concern, not SSR — out of scope.)
- **Install pipeline** must copy `frontend/public/` to `/usr/share/nginx/html/modules/{slug}/public/`
  (ADR-010 checklist item, still open). **Decision:** the **patient** app under `frontend/patient/` is
  folded into the **same portal deploy** — either move patient pages under `frontend/public/` or have the
  install step copy both trees into `.../public/`. One portal app = one served tree.

### 2.5 Generalisation — a non-healthcare module

Any module declares public pages identically:

- Add a `public_portal` block to its manifest with `routes[].audience`.
- Ship a static `frontend/public/` SPA (hash or path routed).
- Expose anonymous APIs via `get_current_user_optional` for `public` routes; for `patient`-equivalent
  audiences, either reuse the platform end-user identity or define a module end-user token like
  healthcare's patient token. Examples: an **e-commerce** module to `public` storefront + `customer`
  account pages; a **support** module to `public` knowledge base + `requester` ticket portal; an
  **events** module to `public` event listing + `attendee` ticket portal. `audience` values beyond
  `public`/`patient` are allowed (e.g. `customer`); the platform treats any non-`public` audience as
  `client-token-required`.

> **Sub-module note (ADR-008):** sub-modules do **not** get their own `/portal/{sub_slug}/`. They surface
> public pages through the parent module's portal. One public URL per clinic service.

---

## 3. Decision 2 — Patient identity & access

### 3.1 What exists

A **complete, dedicated patient identity stack** already exists and is the right model — patients are
**not** platform users and SHOULD NOT enter the staff RBAC group chain:

- **Registration / login:** phone + OTP (`routes_patient_auth.py`), captcha-gated, Redis cooldown.
- **Tokens:** `sdk/patient_tokens.py` — separate HS256 patient JWT (`roles:["patient"]`), 15-min access /
  7-day refresh, refresh via cookie. **Distinct from the platform user JWT.**
- **Scoping:** patient-data routes scope every query to the patient (`sub`); tenant-scoped DB sessions;
  PHI crypto + audit + consent records + DPA gate.

### 3.2 Relationship to the `patient` RBAC role and the group chain

The RBAC chain (User to Group to Role to Permission) governs **platform users / the admin SPA**. The
**recommendation is to keep patients OUT of that chain** and use the dedicated patient token instead,
because:

- Patients vastly outnumber staff and would pollute the user/group tables and permission resolution.
- Patient access control is **data-scoped** ("only rows where patient_id = me"), not
  **permission-bit-scoped** — RBAC permission strings add nothing here.
- The patient token already encodes `roles:["patient"]`; treat that as a **claim**, not a row in
  `user_roles`. The minimal `patient` RBAC role can remain as a placeholder for any *staff-side* view
  of patients, but patient login does **not** flow through it.

So: **two parallel identity planes** — platform RBAC (staff, admin SPA) and module end-user tokens
(patients, portal). The portal's `patient`-audience pages authenticate against the latter.

### 3.3 Cross-tenant: a patient belongs to a clinic

`HCPatient.tenant_id` binds a patient to one clinic/tenant. A person who is a patient at two clinics is
two patient records (one per tenant) — acceptable for v1. Patient APIs must filter by the patient's
tenant; the token-carried `tenant_id` claim (3.4 gap) makes this robust.

### 3.4 Gaps to flag (do not over-design)

1. **`tenant_id`/`clinic_slug` claim in the patient access token** — add for defence-in-depth tenant
   scoping (currently scope is derived per-request).
2. **`audience` not yet in the manifest schema** — add to `manifest.schema.json` + the validator.
3. **Install pipeline** does not yet copy `frontend/public/` (and patient pages) to the served portal
   path (ADR-010 open item).
4. **Patient app not declared anywhere** — `frontend/patient/` exists but no manifest/route/portal entry
   references it. Decision 1 folds it into the portal deploy; the wiring is unbuilt.
5. **No platform-level patient-token verification dependency** — each module rolls its own; consider a
   shared `get_current_patient_optional` analogous to `get_current_user_optional` if a second module
   needs end-user tokens.

---

## 4. Decision 3 — Common online-clinic public/patient features (A2 research)

Prioritised for a **first credible release**. "Maps to" = existing healthcare frontend file(s);
**new** = not yet present.

### Public (unauthenticated)

| Feature | Description | MoSCoW | Maps to / new |
|---------|-------------|--------|----------------|
| Clinic directory & search | Browse/search/filter clinics by name, specialty, location | **Must** | `public/clinics.{html,js}` |
| Clinic profile | Single clinic: branches, hours, specialties, providers, ratings | **Must** | `public/clinic-profile.{html,js}`, API `/clinics/{slug}` |
| Services / doctors listing | Providers & services offered at a clinic | **Must** | within clinic-profile (`PublicProviderSummary`) |
| Online booking landing | Entry point to pick branch/provider/slot before/after login | **Must** | `public/portal.js` + `patient/book.{html,js}` |
| Self-registration (OTP) | Phone + OTP patient sign-up | **Must** | `patient/register.{html,js}`, `routes_patient_auth` |
| Patient login (OTP) | Phone + OTP login | **Must** | `public/index.html` login page, auth APIs |
| Reviews / ratings (read) | Show clinic ratings on profile | **Should** | `avg_rating` in public API; write: `patient/review-new` |
| SEO-friendly clinic URLs | Crawlable/shareable clinic pages | **Could** | new (path-routing mode, 2.4) |
| Multi-language | i18n of public pages | **Should** | i18n already wired (`i18n.js`) |

### Patient (authenticated)

| Feature | Description | MoSCoW | Maps to / new |
|---------|-------------|--------|----------------|
| Patient portal home | Dashboard: next appt, summary cards | **Must** | `patient/portal.{html,js}` |
| Book appointment (slot pick) | Choose branch/provider/slot, confirm | **Must** | `patient/book.{html,js}`, `routes_patient_appointments` |
| View own appointments | List + detail of own appointments | **Must** | `patient/appointments(.detail).{html,js}` |
| Cancel / reschedule | Manage own upcoming appointments | **Should** | partial (appointment-detail); reschedule = new |
| Prescriptions (view) | List/detail of own prescriptions | **Should** | `patient/prescriptions(.detail)` |
| Prescription refill request | Request a refill | **Could** | new (UI); needs backend action |
| Lab results (view) | List/detail of own lab results | **Should** | `patient/lab-results(.detail)` |
| Visit history / encounters | Past encounters/records | **Should** | `patient/records`, `encounter-detail` |
| Invoices / billing (view) | View own invoices | **Should** | `patient/invoices(.detail)` |
| Online payment | Pay invoice online | **Could** | new (payment gateway integration) |
| Profile management | Update contact/demographics | **Must** | `patient/profile.{html,js}` |
| Waitlist | Join/track waitlist for slots | **Could** | `patient/waitlist`, `waitlist-banner` |
| Write review / rating | Rate a visit | **Could** | `patient/review-new` |
| Notifications / reminders | Appt reminders (push/SMS/email) | **Should** | backend `reminder_scheduler` exists; UI new |
| Secure messaging | Patient-clinic messages | **Could** | new |
| Intake / pre-visit forms | Fill forms before visit | **Could** | new (could ride the no-code form pipeline) |
| Telehealth links | Join video visit | **Could** | new |
| Consent management | View/manage consents (DPA) | **Should** | `HCPatientConsent`, DPA gate exist; UI partial/new |

**Headline:** the existing files already cover nearly every **Must** and most **Should** items — the
release gap is *wiring + a few backend actions*, not greenfield UI.

---

## 5. Decision 4 — Recommendation & phased plan

### 5.1 Recommended approach (restated)

One **static portal app per module** at `/portal/{slug}/`, hosting `public` + `patient` audiences
declared via `public_portal.routes[].audience`; `staff` stays in the admin SPA; patients use the
**dedicated patient-token identity plane**, not the staff RBAC chain; tenant resolved from URL slug
(public) or token (patient). Fully consistent with ADR-010 and the static-deployable FE contract.

### 5.2 Phased roadmap

**Phase 1 — Minimal credible public + patient surface (healthcare as reference).** Reuse existing
`frontend/public` + `frontend/patient`. Deliver the **Must** features only:

- Public: **clinic directory & search, clinic profile (services/doctors), booking landing,
  self-registration (OTP), patient login (OTP)**.
- Patient: **portal home, book appointment (slot pick), view own appointments, profile management**.
- Platform plumbing: add `public_portal`+`audience` to manifest & schema/validator; install pipeline
  copies `frontend/public` (and patient pages) to `/portal/healthcare/`; add `tenant_id` claim to the
  patient token; client-side patient-token guard for `audience:patient` routes.

**Phase 2 — Should features.** Cancel/reschedule, prescriptions/lab results/encounters/invoices view,
reviews (read+write), reminders UI, consent management UI, multi-language polish, notifications.

**Phase 3 — Could features.** Online payment, refill requests, secure messaging, intake forms,
telehealth, waitlist, SEO path-routing mode, shared `get_current_patient_optional` platform dependency.

### 5.3 What every future module must provide to expose public pages

1. `public_portal` block in `manifest.json` with `entry_point`, `title`, and `routes[].audience`.
2. A static `frontend/public/` SPA (hash or path routed), light-DOM/static per the FE contract.
3. Anonymous APIs via `get_current_user_optional` for `public` routes; an end-user token (reuse
   patient-style) for non-`public` audiences, with **data-scoped** access (never platform RBAC for
   end-users).
4. No PHI/sensitive data from any anonymous endpoint; rate-limiting on public APIs.

### 5.4 Risks & open questions

- **SEO with hash routing** is weak; path-routing mode is opt-in but unproven here. Risk: clinics expect
  Google-indexable profiles. Mitigation: Phase-3 path mode; consider static pre-render at build time.
- **Patient-token model is healthcare-specific.** A second module needing end-user auth will duplicate it
  unless we promote it to a platform service (flagged Phase 3). Decide before the second consumer.
- **Two identity planes** (RBAC vs patient token) must never be confused — e.g. a patient JWT must never
  satisfy an admin-SPA route. Enforced by separate signing audiences/claims and separate dependencies.
- **Install pipeline** is the critical unbuilt piece; until `frontend/public`+`frontend/patient` are
  copied to the served path, the portal 404s despite the code existing.
- **`frontend/patient/` placement** — folding it into the portal deploy needs a concrete file move or
  install-copy rule; until decided, patient routes have no home.
