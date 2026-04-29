---
artifact_id: audit-08-automation-rules
type: audit
producer: Code Auditor
consumers: [Tech Lead, Product Owner]
upstream: [epic-08-automation-rules, arch-platform]
downstream: []
status: approved
created: 2026-04-29
updated: 2026-04-29
audit_target: epic-08-automation-rules
auditor: Claude (Opus 4.7)
commit_sha: cc47a54
coverage_pct: 100
---

# Audit — Epic 08: Automation Rules (audit-08-automation-rules)

## 1. Summary

- Stories audited: **6**
- DONE: **2** • PARTIAL: **1** • DRIFT: **0** • MISSING: **3**
- Tag-drift count: **1** (story 8.1.3 PARTIAL on frontend)
- Recommended `BACKLOG.md` tag: **Feature 8.1 DONE; Feature 8.2 (Webhooks) MISSING** (currently "DONE; Webhooks PLANNED" — accurate but understates how much webhook work is needed)

## 2. Story-by-story

| Story | Title | Claimed | Verified | Backend evidence | Frontend evidence | Gaps | 🚦 |
|-------|-------|---------|----------|------------------|-------------------|------|----|
| 8.1.1 | Database Event Triggers | DONE | DONE | `app/models/automation.py:26 AutomationRule`, `app/routers/automations.py:33 create_automation_rule` | — | — | — |
| 8.1.2 | Scheduled Triggers | DONE | DONE | `app/models/automation.py:59 schedule_type`, `app/routers/scheduler.py:11 create_scheduler_job` | — | — | — |
| 8.1.3 | Automation Actions | DONE | PARTIAL | `app/models/automation.py:71 actions` (JSONB array) | — | Frontend builder UI (action cards, drag reorder) not located in code | 🟡 |
| 8.2.1 | Webhook Endpoint Registration | PLANNED | MISSING | `app/routers/automations.py:115 create_webhook_config` (skeleton only) | — | Echo-back validation challenge, `webhook` table schema not implemented | 🔴 |
| 8.2.2 | Webhook Delivery and Retry | PLANNED | MISSING | — | — | No async delivery worker, no retry schedule (1s/5s/30s/5m/30m/1h), no `webhook_deliveries` table, no auto-disable | 🔴 |
| 8.2.3 | Webhook Payload Signing | PLANNED | MISSING | — | — | No HMAC-SHA256 signing, no `X-Signature` header, no secret rotation endpoint, no dual-signing window | 🔴 |

## 3. Gaps

### 🔴 High
- [ ] **8.2.1** Implement webhook validation challenge (echo-back). **Files**: `backend/app/routers/automations.py`, `backend/app/models/automation.py`. **Effort**: M.
- [ ] **8.2.2** Build the webhook delivery worker + retry queue. **Files**: `backend/app/services/webhook_delivery.py` (new), `backend/app/models/automation.py`. **Effort**: L.
- [ ] **8.2.3** HMAC-SHA256 signing + secret rotation with 24 h dual-sign window. **Files**: `backend/app/core/security.py`, `backend/app/routers/automations.py`. **Effort**: M.

### 🟡 Medium
- [ ] **8.1.3** Add the action-builder frontend (cards, drag reorder). **Files**: `frontend/assets/js/automations.js` (or new). **Effort**: M.

## 5. Verdict

`BACKLOG.md` row currently reads "DONE; Webhooks PLANNED" — accurate but the webhook work is L-effort and load-bearing for any external integration story. Single most impactful next action: spec and ship Feature 8.2 end-to-end (webhooks).

## Decisions

- Story 8.1.3 marked PARTIAL (not DONE) because the model exists but the configurable action UI does not.

## Open Questions

- Should webhook delivery use the existing APScheduler in `SchedulerEngine`, or a dedicated worker pool?
