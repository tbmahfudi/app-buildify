---
artifact_id: epic-21-risk-retirement
type: epic
producer: A3 Product Owner
consumers: [B1 Software Architect, B2 Data Engineer, B3 UX Designer, C1 Tech Lead]
upstream: [vision-01-app-buildify, research-01-app-buildify]
downstream: []
status: review
created: 2026-04-29
updated: 2026-04-29
shape: slice
decisions:
  - Slice epic — sequences existing stories rather than redefining them (no scope overlap with epics 4, 14, 15)
  - Ordering reflects research-01 user-journey friction (steps 3, 7, 8 are emotionally broken)
  - Coordination AC ("all 5 constituent stories DONE") gates the next net-new feature epic
  - Existing story bodies in epics 4, 14, 15 remain the single source of truth — this epic does not duplicate them
open_questions:
  - Sprint length not yet decided — left for C1 Tech Lead during task breakdown
  - Should role CRUD (4.1.1) and wildcards (4.2.1) ship as one PR or two? — defer to C1
---

# Epic 21 — 🔴 Risk Retirement (Sprint 1)

> **Coordination / slice epic**, not a feature epic. Sequences five existing 🔴 risk stories from epics 4, 14, and 15 into a single pre-feature retirement sprint. Per `research-01-app-buildify.md` §5: this epic MUST complete before the next net-new feature epic is opened.

> **Scope discipline**: this epic does not redefine any story. Each work item below is a reference to the canonical story in its home epic. Backend AC and Frontend UILDC sections live in those files; only the *coordination* (ordering, dependencies, sprint-DoD) is new here.

---

## Why this epic exists

`research-01-app-buildify.md` graded the platform PROCEED-with-caveats. The caveat: the user journey for the primary persona (Maya the Power User) is structurally sound but **emotionally broken at steps 3, 7, and 8** of the 8-step "first business app" journey:

- Step 3 (roles & users) → broken because role CRUD is missing and wildcards don't wildcard
- Step 7 (hand-off with audit trail) → broken because per-entity perms are dead schema
- Step 8 (first password reset incident) → broken because no notification delivery exists
- Cross-cutting → every UILDC frontend story is blocked because the Flex layout suite is missing

Adding new features on top of these gaps is technical debt accumulation. This epic retires them first.

---

## Sprint Backlog (5 work items, sequenced)

### Item 21.1 — Layout Component Suite *(unblocks all UI work)*

- **References**: [Story 15.1.1](epic-15-flex-component-library.md) — Layout Component Suite `[OPEN]`
- **Why first**: every Frontend section in every other story depends on `FlexStack`, `FlexGrid`, `FlexSplitPane`, `FlexCard`, `FlexToolbar`, etc. Until these exist, no UILDC story is buildable.
- **Coordination AC**:
  - All 9 Flex layout components named in `audit-15-flex-component-library.md` story 15.1.1 are present in `frontend/components/flex-layout/`
  - At least one existing page (recommend `rbac-page.js` from item 21.3) is refactored to use the new components — proves they integrate
  - No regression in existing pages that already use other Flex components
- **Ready signal to next item**: 21.3 unblocked once layout suite components are usable.

### Item 21.2 — SMTP Email Delivery Adapter *(retires the password-reset deadletter)*

- **References**: [Story 14.2.1](epic-14-notification-system.md) — SMTP Email Delivery Adapter `[OPEN]`
- **Why second** (parallelizable with 21.1): pure backend work, no UI dependency, unblocks the user-journey emotional break at step 8 (password-reset email never arrives today).
- **Coordination AC**:
  - The `notifications` queue from `audit-14` Feature 14.1 (DONE) is consumed by a worker that delivers via SMTP
  - `POST /auth/forgot-password` results in a deliverable email within 60 s under normal load
  - SMTP credentials live in env vars; no secrets in code or DB
  - Failure mode: a transient SMTP failure is retried; a permanent failure surfaces in audit log
- **Ready signal**: closes the journey-step-8 gap independently of 21.1/21.3.

### Item 21.3 — Role CRUD + Wildcard Permissions *(retires journey step 3)*

- **References**:
  - [Story 4.1.1](epic-04-rbac-permissions.md) — System and Custom Role Definitions `[IN-PROGRESS]`
  - [Story 4.2.1](epic-04-rbac-permissions.md) — Permission Format and Wildcard Matching `[IN-PROGRESS]`
- **Why third**: depends on 21.1 (the Roles page uses FlexSplitPane, FlexStack, FlexToolbar, FlexCard, FlexModal). Bundled together because they ship as one user-visible capability ("manage roles end-to-end"); shipping role CRUD without working wildcards is a half-feature.
- **Coordination AC**:
  - All endpoints from Story 4.1.1 backend AC return non-404
  - `has_permission()` evaluates `*` segments correctly per Story 4.2.1 backend AC
  - The Roles page (Story 4.1.1 frontend) renders end-to-end against the new backend
  - `audit-04-rbac-permissions.md` story 4.1.1 and 4.2.1 can be retagged from `[IN-PROGRESS]` to `[DONE]`
- **Ready signal**: closes the journey-step-3 gap.

### Item 21.4 — Per-Entity Permission Enforcement *(retires journey step 7)*

- **References**: [Story 4.2.4](epic-04-rbac-permissions.md) — Per-Entity Permission Enforcement `[OPEN]`
- **Why last**: depends on 21.3 (uses the role list from `GET /rbac/roles`) and on 21.1 (the Access Control tab uses FlexCheckbox in a matrix layout).
- **Coordination AC**:
  - `DynamicEntityService` reads `EntityDefinition.permissions` JSONB before every CRUD op
  - When `permissions` is non-null and the user's role is not listed for the action → 403
  - When `permissions` is null → falls back to global RBAC (no behavior change)
  - The Access Control tab in the entity editor renders, saves, and re-loads the JSONB correctly
  - `audit-04-rbac-permissions.md` story 4.2.4 can be retagged to `[DONE]`
- **Ready signal**: closes the journey-step-7 gap; sprint complete.

---

## Sprint-level Definition of Done (epic-level AC)

This epic is `[DONE]` when **all** of the following hold:

- [ ] All 5 constituent stories (15.1.1, 14.2.1, 4.1.1, 4.2.1, 4.2.4) have their backend AC met
- [ ] All 5 constituent stories have their frontend UILDC sections rendered and functional
- [ ] Audits in `plan/architecture/audits/` for stories 15.1.1, 14.2.1, 4.1.1, 4.2.1, 4.2.4 retag to `[DONE]` (this is a tag-drift retag — A3 follow-up triggered by ✦ Code Auditor)
- [ ] No regression in any existing `[DONE]` story — verified by smoke test (`scripts/smoke-test.sh` per `audit-13`)
- [ ] At least one end-to-end Maya-journey walkthrough (sign-up → create entity → assign per-entity perms → invite user with custom role → trigger password reset → verify email arrives) passes manually

---

## What this epic explicitly is NOT

- **Not a feature epic**: it adds no new capability beyond what epics 4, 14, 15 already promised. It is a sequencing artifact.
- **Not a story redefinition**: if there's a conflict between this epic's coordination AC and the canonical story body, the canonical story body wins. File a clarifying question to A3 and the canonical body gets updated, not this epic.
- **Not a substitute for the canonical epic**: epics 4, 14, 15 remain the home for these stories' bodies. When constituent stories flip to `[DONE]`, the tag retags happen *in the canonical epic file*, not here.

---

## Hand-off

This epic is `status: review`. Once approved:
- **B1 Software Architect** — review for any new architectural decisions needed (likely: SMTP adapter belongs to which service in distributed mode? — small ADR may be needed)
- **B2 Data Engineer** — review for any schema work (likely: none — `EntityDefinition.permissions` JSONB already exists per `audit-05`)
- **B3 UX Designer** — produce design specs for the Roles page (Story 4.1.1) and entity Access Control tab (Story 4.2.4), citing UILDC v1.0
- **C1 Tech Lead** — break the 5 items into developer tasks; decide sprint length and whether 21.1 + 21.2 run in parallel
