# Known Gaps — Documented but Not Implemented

This document lists features, components, and infrastructure items that appear in documentation or specifications but **do not exist in the current codebase**. Use this as a backlog reference.

Last audited: 2026-03-23

---

## Frontend Components

These components are referenced in `PHASE4_PLAN.md`, `CHANGELOG.md` (roadmap), and the component library docs but are **not present** in `frontend/assets/js/components/`:

| Component | Priority | Source Reference |
|-----------|----------|-----------------|
| `FlexDatepicker` | High | PHASE4_PLAN.md, CHANGELOG roadmap |
| `FlexFileUpload` | High | PHASE4_PLAN.md |
| `FlexForm` | High | PHASE4_PLAN.md — form container with validation orchestration |
| `FlexNotification` | Medium | CHANGELOG roadmap v1.2.0 |
| `FlexProgress` | Medium | PHASE4_PLAN.md — progress bar and circular indicator |

**Note**: All other Phase 4 components (`FlexInput`, `FlexSelect`, `FlexCheckbox`, `FlexRadio`, `FlexTextarea`, `FlexAccordion`, `FlexBreadcrumb`, `FlexTooltip`, `FlexPagination`) **are implemented**.

---

## Backend Infrastructure

### Prometheus Monitoring

- **Documented in**: `TECHNICAL_SPECIFICATION.md`, backend `requirements.txt` (`prometheus-client`)
- **Status**: `prometheus-client` is listed as an optional dependency but no `/metrics` endpoint is wired up, and no Prometheus scrape config or Docker service exists in `infra/`
- **To implement**: Add `from prometheus_client import make_asgi_app` to `main.py`, mount at `/metrics`, add a Prometheus service to `docker-compose.dev.yml`

### Redis Token Revocation

- **Documented in**: `TECHNICAL_SPECIFICATION.md`, `AUTH_SECURITY.md`
- **Status**: Redis is referenced in docs as the token blacklist store, but the `infra/docker-compose.dev.yml` has **no Redis service**. The backend code references Redis for token revocation — this will silently fail if `REDIS_URL` is not set
- **To implement**: Add a `redis` service to `docker-compose.dev.yml` and set `REDIS_URL` in the dev environment

---

## Security Features

| Feature | Documented In | Status |
|---------|--------------|--------|
| Two-Factor Authentication (TOTP/SMS) | `FUNCTIONAL_SPECIFICATION.md` (short-term roadmap) | Not implemented |
| SSO / SAML / OAuth2 provider | `FUNCTIONAL_SPECIFICATION.md` (long-term) | Not implemented |
| Webhook outbound integration | `FUNCTIONAL_SPECIFICATION.md` | Not implemented |

---

## Subscription Tiers

- **Documented in**: `FUNCTIONAL_SPECIFICATION.md` — defines Free, Basic, Premium, Enterprise tiers with user limits, module limits, storage limits, and API rate limits
- **Status**: Tier definitions exist in the specification but there is no `subscription_tier` field on the `Tenant` model, and no enforcement middleware checking tier limits
- **Impact**: All tenants currently have unlimited access to all features regardless of tier

---

## Module Marketplace UI

- **Documented in**: `FUNCTIONAL_SPECIFICATION.md` — describes a module marketplace where tenants can browse and enable modules
- **Status**: Module registration and enable/disable API endpoints exist (`/api/v1/modules/`), but there is no frontend marketplace page. The current UI allows enabling modules by direct API call only

---

## TypeScript Definitions

- **Documented in**: `CHANGELOG.md` roadmap (v1.1.0)
- **Status**: No `.d.ts` files exist for any Flex components
- **Impact**: TypeScript users get no type safety when consuming the component library

---

## Automated Test Coverage

- **Documented in**: `PHASE4_PLAN.md`, `CHANGELOG.md` roadmap, `vitest.config.js` (80% thresholds)
- **Status**:
  - 5 frontend component tests exist (`tests/components/`)
  - No backend tests are present in the `tests/` directory
  - Coverage thresholds are configured but not enforced in CI
- **Impact**: The 80% coverage target in `vitest.config.js` is not met by current tests

---

## Storybook Component Explorer

- **Documented in**: `CHANGELOG.md` roadmap (v1.2.0)
- **Status**: Not set up
- **Impact**: No interactive component showcase for developers

---

## Cloud Storage Integration

- **Documented in**: `FUNCTIONAL_SPECIFICATION.md` — S3/GCS integration for file attachments
- **Status**: Not implemented. No file storage service, no presigned URL generation

---

## Notification Delivery

- **Documented in**: `AUTH_SECURITY.md`, `FUNCTIONAL_SPECIFICATION.md`
- **Status**: `notification_service.py` exists with a queue-based architecture and supports email, SMS, webhook, and push notification types — but the **actual delivery adapters are stubs**. No SMTP client, no SMS provider (Twilio, etc.), no push notification service is wired up
- **To implement**: Configure at minimum an SMTP client for email delivery

---

## HR and Clinic Modules

- **Referenced in**: `infra/nginx/app.conf` — the Nginx config includes route patterns for `hr` and `clinic` modules:
  ```nginx
  location ~ ^/api/(v[0-9]+)/(financial|hr|clinic)/(.+)$ {
  ```
- **Status**: Only the `financial` module exists. `hr` and `clinic` modules are **not implemented**

---

## Production Docker Compose

- **Documented in**: `infra/docker-compose.prod.yml`
- **Status**: The production compose is a skeleton placeholder:
  - References `ghcr.io/YOUR_GH_OWNER/app-backend:${TAG}` — organization name not filled in
  - No database service (assumes external managed DB — intentional but undocumented)
  - No financial module service entry
  - No environment configuration
- **To implement**: Fill in actual image registry, add financial-module service, add env_file configuration

---

## Summary Table

| Gap | Effort | Priority |
|-----|--------|----------|
| FlexDatepicker component | Medium | High |
| FlexFileUpload component | Medium | High |
| FlexForm component | Medium | High |
| Redis service in dev compose | Low | High |
| Prometheus metrics endpoint | Low | Medium |
| FlexNotification component | Low | Medium |
| FlexProgress component | Low | Medium |
| Notification email delivery | Medium | Medium |
| 2FA authentication | High | Medium |
| Test coverage (backend) | High | Medium |
| Subscription tier enforcement | High | Low |
| Module marketplace UI | Medium | Low |
| TypeScript definitions | Medium | Low |
| Storybook setup | Low | Low |
| HR module | Very High | Low |
| Clinic module | Very High | Low |
| Cloud storage integration | High | Low |
| SSO / SAML | Very High | Low |
