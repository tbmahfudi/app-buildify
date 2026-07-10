---
artifact_id: adr-hc-003
type: adr
module: healthcare
status: Accepted
producer: B1 Software Architect
upstream: [vision-02, research-02, epic-01-base-healthcare, arch-platform]
created: 2026-06-21
---

# ADR-HC-003 — Two-Sided Access Architecture

## Status

Accepted

## Context

The App-Buildify platform currently serves a single access surface: authenticated clinic staff
(B2B users) who log in via the platform's JWT-based auth flow. The Healthcare Module Suite
introduces a second, public-facing surface: the **patient portal**, where Indonesian residents
self-register, search for clinics, and book appointments (vision-02, epic-01 Feature 1.4).

Key tensions:
- Platform auth issues a JWT containing `(user_id, tenant_id, roles[])`. A `patient` role does
  not fit this model cleanly — patients are not employees of a tenant; they have a
  platform-level identity that spans tenants.
- The patient registration and clinic discovery endpoints (`POST /api/v1/patients/register`,
  `GET /api/v1/clinics/search`) are public (unauthenticated). This is a new attack surface on a
  platform that previously had no public endpoints.
- Public endpoints carry PHI risk (phone OTP, date of birth) and are abuse targets (bot
  registration, scraping, rate-limit bypass).

Design questions:
1. How does patient authentication work — separate JWT issuer, same issuer with different
   claims, or a different session mechanism?
2. How does the API gateway and platform router distinguish clinic-staff routes from patient
   routes?
3. What rate limiting and abuse protection applies to public registration and discovery
   endpoints?

## Decision

### D1 — Same JWT Issuer, Separate Role Namespace

> **⚠ PARTIALLY SUPERSEDED (2026-07-05) by `epic-18-patient-portal-authentication` +
> `adr-hc-009-patient-identity-and-auth` (B1).** The **claim shape below is retained** (patient JWT: `roles: ["patient"]`,
> `tenant_id: null`, minted via the `from-platform` bridge). What is **superseded is the OTP/phone-only
> authentication flow** (register/token steps 1–2 below): patient auth now supports **three** methods —
> email/username + password, Google OAuth, and OTP. **OTP is now optional** (a passwordless option and an
> optional MFA second factor), no longer mandatory. Identity is a platform `User(role=patient)`; PHI stays
> in `hc_patient` linked by `user_id`. See `epics/epic-18-patient-portal-authentication.md` and
> `architecture/adr-hc-009-patient-identity-and-auth.md` (the superseding record for this §D1 flow;
> schema deltas in `architecture/schema-hc-03.md`).

Patient authentication uses the **same JWT issuer** (platform `JWT_SECRET_KEY`) but a
**distinct role namespace**:

- Clinic staff JWT claims: `{ "sub": user_id, "tenant_id": "...", "roles": ["doctor", ...] }`
- Patient JWT claims: `{ "sub": patient_id, "patient_id": "...", "roles": ["patient"],
  "tenant_id": null }`

The `patient_id` claim is the platform-issued UUID for the patient's universal health profile.
`tenant_id` is null because patients are not scoped to a single tenant.

A new `get_current_patient` FastAPI dependency (in `modules/healthcare/sdk/`) validates the JWT
and asserts `"patient" in roles` and `patient_id` is present. It is distinct from the platform's
`get_current_user` dependency.

Patient auth flow:
1. `POST /api/v1/patients/register` — OTP-verified phone → creates patient profile → returns
   short-lived JWT (15-minute access token, 7-day refresh token in `HttpOnly` cookie).
2. `POST /api/v1/patients/auth/token` — phone + OTP → JWT for returning patients.
3. `POST /api/v1/patients/auth/refresh` — refresh token → new access token.

Clinic staff auth flow is unchanged (platform `POST /api/v1/auth/token`).

Rationale for same issuer: avoids operating a second signing infrastructure in v1. The role
namespace cleanly separates the two populations. If patient auth needs to scale independently
in a future phase, extraction to a dedicated auth service is possible without breaking clients
(same JWT format).

### D2 — Route Namespace Separation at the Gateway

Nginx gateway routing (extending `infra/nginx/nginx.conf`):

| Path prefix | Upstream | Session type |
|------------|----------|-------------|
| `/api/v1/patients/` | `healthcare-module` | Patient JWT or unauthenticated (registration/discovery) |
| `/api/v1/clinics/search` | `healthcare-module` | Unauthenticated (public) |
| `/api/v1/clinics/:slug/` | `healthcare-module` | Unauthenticated (public profile) |
| `/api/v1/tenants/` | `core-platform` | Clinic staff JWT |
| `/api/v1/modules/healthcare/` | `healthcare-module` | Clinic staff JWT |

The separation is enforced at two levels:
1. **Route prefix** — Nginx routes patient-facing paths to the healthcare module before they
   reach core-platform.
2. **FastAPI dependency** — patient routes use `get_current_patient`; clinic-staff routes use
   `get_current_user` + `healthcare_branch_session` (ADR-HC-001). A patient JWT presented to
   a clinic-staff endpoint will be rejected by `has_permission` (no tenant_id → 403).

Patient portal frontend is served from `/patient/` path; clinic portal from `/clinic/` path.
A single-page app can serve both surfaces; route guards enforce the correct auth context
client-side.

### D3 — Rate Limiting and Abuse Protection for Public Endpoints

Public endpoints (no authentication required):

| Endpoint | Rate limit | Additional protection |
|----------|-----------|----------------------|
| `POST /api/v1/patients/register` | 5 req/IP/10 min | Phone OTP: 5 attempts/phone/10 min; 60 s cooldown between resends |
| `POST /api/v1/patients/auth/token` | 10 req/IP/min | Same OTP limits |
| `GET /api/v1/clinics/search` | 60 req/IP/min | Results cache 60 s (Redis); no PHI in response |
| `GET /api/v1/clinics/:slug/*` (public profile) | 120 req/IP/min | Results cache 5 min (Redis); no PHI |

Implementation: `slowapi` (already in platform stack, arch-00-platform §3.1) with Redis backend
for distributed rate limit state. Public endpoints additionally require a **CAPTCHA token**
(hCaptcha, free tier) for registration — verified server-side before OTP is sent.

All public endpoints return consistent error shapes regardless of failure reason (phone not
found, OTP invalid, rate limited) to prevent user enumeration.

CORS policy for patient-facing paths:
- Allow-Origin: explicit patient portal domain only (not `*`)
- Allow-Methods: GET, POST, OPTIONS
- Credentials: true (for refresh-token cookie)

The existing gateway CORS `*` policy (arch-00-platform §2.1) must NOT apply to patient paths.
This is a security regression that must be fixed as part of the healthcare module rollout.

## Consequences

### Positive
- **Single JWT infrastructure** — no second signing service in v1; simpler operational footprint.
- **Clear namespace separation** — `/api/v1/patients/` vs `/api/v1/tenants/` makes routing
  intent explicit and easy to audit.
- **Rate limiting is layered** — Nginx connection limits + `slowapi` application limits +
  OTP-level limits + CAPTCHA provide overlapping abuse prevention.

### Negative
- **`tenant_id: null` in patient JWT** is an unusual claim that every middleware must handle
  correctly (not treat as "all tenants"). All existing platform middleware must be audited.
  Mitigation: integration tests with patient JWT against every clinic-staff endpoint.
- **CORS `*` regression fix** — closing the existing wildcard CORS at the gateway is a
  breaking change for any development tooling that relies on it. Mitigation: document the
  change in the platform changelog; development environments use an env-var to allow localhost
  origins explicitly.
- **hCaptcha dependency** — adds third-party dependency for registration flow. Mitigation:
  adapter pattern; replaceable with Cloudflare Turnstile or self-hosted alternative without
  code changes.

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| Separate JWT issuer (dedicated patient auth service) | Operational overhead in v1; premature extraction. Deferred to future phase. |
| Patient uses platform role in staff JWT (`"roles": ["patient"]` without separate claim) | Ambiguous `tenant_id`; platform middleware would need extensive changes. Role namespace isolation is cleaner. |
| Cookie-only session for patients (no JWT) | Inconsistent with platform auth pattern; harder to use from mobile-first web with SPA routing. |
| No CAPTCHA on registration | Acceptable for internal tools; unacceptable for a public-facing health platform with patient PII at registration. |

## Reference Map

| File | Relevance |
|------|-----------|
| `infra/nginx/nginx.conf` | Gateway routing — must be extended for patient paths |
| `modules/sdk/dependencies.py` | `get_current_user`, `has_permission` — patient dependency mirrors these |
| `plan/architecture/arch-platform.md` §2.1 | CORS `*` policy — must be narrowed |
| `plan-mod-healthcare/epics/epic-01-base-healthcare.md` | Stories 1.4.1, 1.4.2, 1.5.1 — patient registration and RBAC ACs |
| `plan-mod-healthcare/vision/vision-02.md` | Guardrail 5 (patient portal authenticated, not anonymous) |
