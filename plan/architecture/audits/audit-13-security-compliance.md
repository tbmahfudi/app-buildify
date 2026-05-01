---
artifact_id: audit-13-security-compliance
type: audit
producer: Code Auditor
consumers: [Tech Lead, Product Owner, Security Reviewer]
upstream: [epic-13-security-compliance, arch-platform]
downstream: []
status: approved
created: 2026-04-29
updated: 2026-04-29
audit_target: epic-13-security-compliance
auditor: Claude (Opus 4.7)
commit_sha: cc47a54
coverage_pct: 100
---

# Audit — Epic 13: Security & Compliance (audit-13-security-compliance)

## 1. Summary

- Stories audited: **8** (Features 13.1–13.4)
- DONE: **5** • PARTIAL: **1** • DRIFT: **0** • MISSING: **2**
- Tag-drift count: **3** (test stories tagged `[IN-PROGRESS]` actually MISSING; 13.2.2 PARTIAL)
- Recommended `BACKLOG.md` tag: **Mostly DONE; Prometheus + Test Suites MISSING** (currently "Mostly DONE; Prometheus/Tests OPEN" — accurate)

## 2. Story-by-story

| Story | Title | Claimed | Verified | Backend evidence | Frontend evidence | Gaps | 🚦 |
|-------|-------|---------|----------|------------------|-------------------|------|----|
| 13.1.1 | Comprehensive Audit Trail | DONE | DONE | `app/models/audit.py:6 AuditLog`, `app/routers/audit.py:17 list_audit_logs`, `app/core/audit.py:13 create_audit_log` | `frontend/assets/js/audit.js` | — | — |
| 13.1.2 | Entity-Level Audit Logging | DONE | DONE | `app/models/audit.py changes`, `app/core/audit.py:57 compute_diff` | — | — | — |
| 13.2.1 | Per-Tenant Security Policy Configuration | DONE | DONE | `app/models/security_policy.py:7 SecurityPolicy` (NULL=default, tenant-scoped) | — | — | — |
| 13.2.2 | Sensitive Operation Re-Authentication | DONE | PARTIAL | `app/core/security_middleware.py` checks token age | — | `POST /auth/reauth` and `reauth_token` (5 min, single-use) flow not implemented | 🟡 |
| 13.2.3 | Security Headers Middleware | DONE | DONE | `app/core/security_middleware.py`; gateway also sets headers (`infra/nginx/nginx.conf`) | — | CSP value not verified by inspection — recommend explicit assertion in test | 🟢 |
| 13.2.4 | Rate Limiting | DONE | DONE | `app/core/rate_limiter.py:32 limiter (slowapi)`, `RATE_LIMIT_ENABLED` config | — | — | — |
| 13.3.1 | Prometheus `/metrics` Endpoint | OPEN | MISSING | — | — | No `/metrics` endpoint, no `prometheus-client` import wired, `ENABLE_METRICS` flag unused | 🔴 |
| 13.3.2 | Grafana Dashboard Template | OPEN | MISSING | — | — | No `infra/grafana/` directory | 🟡 |
| 13.4.1 | Backend Unit and Integration Test Suite | IN-PROGRESS | MISSING | `backend/tests/` directory exists per arch-platform §8.2 but per the gap-analysis traversal no `.test.py` files were located | — | Coverage infra unverified; conftest.py not surfaced | 🔴 |
| 13.4.2 | Frontend Component Test Coverage | IN-PROGRESS | MISSING | — | `vitest.config.js` exists but no `.test.js` files located | — | 🔴 |

## 3. Gaps

### 🔴 High
- [ ] **13.3.1** Add `/metrics` endpoint exposing standard Prometheus counters/gauges/histograms; respect `ENABLE_METRICS` env flag. **Files**: `backend/app/main.py`, `backend/app/core/metrics.py` (new). **Effort**: M.
- [ ] **13.4.1** Stand up backend test suite with `tests/conftest.py` fixtures (SQLite + Postgres modes), `tests/unit/`, `tests/integration/`, `tests/features/`. **Effort**: L.
- [ ] **13.4.2** Stand up frontend Vitest suite with `tests/setup.js` and `*.test.js` for FlexComponents. **Effort**: L.

### 🟡 Medium
- [ ] **13.2.2** Implement `POST /auth/reauth` returning a 5-minute single-use `reauth_token`, and a dependency to require it on sensitive routes. **Files**: `backend/app/routers/auth.py`, `backend/app/core/dependencies.py`. **Effort**: M.
- [ ] **13.3.2** Ship `infra/grafana/` with a starter dashboard JSON wired to `/metrics`. **Effort**: M.

### 🟢 Low
- [ ] **13.2.3** Add a unit test asserting CSP and X-Frame-Options headers are present on every response. **Effort**: XS.

## 5. Verdict

Audit + policies + rate-limiting are real. Observability and tests are not. `BACKLOG.md` is honest about the gap; the priority is **13.4.1/13.4.2 (test suites)** before any further `[DONE]` claims can be trusted.

## Decisions

- 13.4.1/13.4.2 marked MISSING (not PARTIAL) — `[IN-PROGRESS]` overstates the state; no test files were located in the audit traversal.

## Open Questions

- Are there test files outside `backend/tests/` and `frontend/tests/` that this audit missed?
- Should the test suites block merges via a new GitHub Action (cross-cutting with Epic 19)?
