# Multi-Agent SDLC System — Roles & Document Contracts

## Context

This document recommends a full-cycle software development process for **App-Buildify** (multi-tenant NoCode/LowCode platform, FastAPI + Vanilla JS) using a team of cooperating AI agents. It is intended to be simulated manually first, then automated.

> **Operationalized in `plan/agents/`**: every role described below has a per-role definition file (e.g. `agent-A3-product-owner.md`) with read scope, write scope, DoR/DoD, and a system prompt skeleton ready for an orchestrator. See [`plan/agents/README.md`](agents/README.md) for the roster and the artifact-driven communication graph.

It builds on what already exists:
- **20 epics** in `/plan/epics/epic-XX-*.md` with backend + frontend acceptance criteria
- **UILDC v1.0** frontend layout convention in `/plan/LAYOUT_CONVENTION.md`
- **`BACKLOG.md`** master index
- Status tags: `[DONE] [IN-PROGRESS] [OPEN] [PLANNED]`

The starting point is a **vision/idea** (e.g. "add a chat module") and the cycle runs end-to-end through to **production + feedback loop**. Existing formats (epic markdown + UILDC) are reused as-is; new artifact standards are proposed only where none exists today.

---

## 1. Recommended Agent Roles (12 agents in 5 stages)

Grouped by SDLC stage. Each stage has clear handoff artifacts so any agent can be replaced without breaking the chain.

### Stage A — Discovery & Product (idea → "what to build")
| # | Role | Responsibility |
|---|------|---------------|
| A1 | **Vision Strategist** (PM) | Turns a 1-line idea into a vision brief: problem, target users, success metrics, scope guardrails. |
| A2 | **Business Analyst / Researcher** | Competitive scan, user-journey hypotheses, constraint discovery. Validates that the vision is worth building. |
| A3 | **Product Owner** | Decomposes the validated vision into **epics + features + stories** with acceptance criteria, using the existing epic format. |

### Stage B — Design (what to build → how it should work)
| # | Role | Responsibility |
|---|------|---------------|
| B1 | **Software Architect** | System design, integration points, ADRs (Architectural Decision Records), tech-stack choices, non-functional requirements. |
| B2 | **Data Modeler** | Entity relationships, schema diffs, migration strategy, multi-tenant scoping rules. |
| B3 | **UX Designer** | Writes the `#### Frontend` UILDC v1.0 sections for each story (page layout, zones, components, states, interactions). |

### Stage C — Build (design → code)
| # | Role | Responsibility |
|---|------|---------------|
| C1 | **Tech Lead / Planner** | Splits stories into ordered tasks with dependencies, picks the right engineer agent for each task, owns the WIP queue. |
| C2 | **Backend Engineer** | Implements FastAPI endpoints, services, RBAC checks against the story + ADR. |
| C3 | **Frontend Engineer** | Implements pages/components matching the UILDC spec. |

### Stage D — Quality (code → trustworthy code)
| # | Role | Responsibility |
|---|------|---------------|
| D1 | **QA Engineer** | Builds the test plan from acceptance criteria, writes/runs unit + integration tests, signs off on the story. |
| D2 | **Code Reviewer** | PR review: correctness, simplicity, conventions, no dead code. |
| D3 | **Security Reviewer** | OWASP scan, RBAC enforcement check, secrets/PII review. |

### Stage E — Release & Operate (code → production + feedback)
| # | Role | Responsibility |
|---|------|---------------|
| E1 | **DevOps / Release Engineer** | CI/CD pipeline, build, deploy, rollback strategy, version bump. |
| E2 | **Tech Writer** | Updates `/docs/` (API ref, user guide, module README), syncs `CHANGELOG.md`. |
| E3 | **SRE / Product Analyst** | Monitors logs, SLOs, usage metrics. Produces the **feedback report** that loops back to A1 to start the next cycle. |

> **Total: 12 agent roles** — many can be merged for early simulations (e.g. one "Engineer" that handles both backend + frontend, one "Reviewer" that handles code + security). See section 5.

---

## 2. Document / Artifact Catalog

All artifacts are **markdown with YAML frontmatter** (so agents can parse metadata deterministically while humans can read the body). Reuse existing files where possible; new artifact types are marked **[NEW STANDARD]**.

### 2.1 Standard frontmatter for every artifact (proposed standard)

```yaml
---
artifact_id: <type>-<n>           # e.g. vision-014, adr-007, audit-04
type: vision | research | prd | epic | story | adr | arch | schema | uildc | tasks | impl-notes | test-plan | test-report | sec-review | release-notes | feedback | audit
producer: <agent role>
consumers: [<role>, <role>]
upstream: [<artifact_id>, ...]    # what this was derived from
downstream: []                    # filled when handed off
status: draft | review | approved | superseded
created: YYYY-MM-DD
updated: YYYY-MM-DD
decisions: [...]                  # short list of key choices
open_questions: [...]             # unresolved items for human or upstream agent
---
```

This envelope is the **only new mandatory standard** — it makes every artifact addressable, traceable, and machine-routable.

### 2.2 Artifact flow (input → output per agent)

| # | Agent | Reads (input) | Writes (output) | Format |
|---|-------|---------------|-----------------|--------|
| A1 | Vision Strategist | 1-line idea + previous **feedback report** (if iteration) | `vision-XX.md` | **[NEW]** Vision Brief: problem, users, success metrics, scope in/out, guardrails |
| A2 | Business Analyst | `vision-XX.md` | `research-XX.md` | **[NEW]** Research Brief: competitor matrix, user journeys, constraints, recommendation (proceed/pivot/kill) |
| A3 | Product Owner | `vision-XX.md` + `research-XX.md` | `epic-XX-*.md` + entries in `BACKLOG.md` | **EXISTING** epic format with backend + frontend stories |
| B1 | Software Architect | `epic-XX-*.md` | `adr-XXX.md` (per decision) + `arch-XX.md` (per epic) | **[NEW]** ADR (Michael Nygard format) + System Design doc (context, components, data flow, NFRs) |
| B2 | Data Modeler | `epic-XX-*.md` + `arch-XX.md` | `schema-XX.md` + Alembic migration in `/modules/.../migrations/` | **[NEW]** Schema doc: ER diagram (mermaid), tables, tenant-scoping, indexes; **EXISTING** Alembic for the migration itself |
| B3 | UX Designer | `epic-XX-*.md` (story bodies) | Updated `#### Frontend` sections in same story | **EXISTING** UILDC v1.0 |
| C1 | Tech Lead | `epic-XX-*.md` + `arch-XX.md` + `schema-XX.md` | `tasks-XX.md` | **[NEW]** Ordered task list: id, title, owner-role, depends-on, est-hours, acceptance-link |
| C2 | Backend Engineer | One task from `tasks-XX.md` + linked story + ADRs + schema | Code (PR) + `impl-notes-<task>.md` | **EXISTING** FastAPI code; **[NEW]** impl-notes (deviations from spec, follow-ups) |
| C3 | Frontend Engineer | One task + UILDC frontend section | Code (PR) + `impl-notes-<task>.md` | **EXISTING** Vanilla JS / Flex components |
| D1 | QA Engineer | Story + PR diff | `test-plan-XX.md` + tests in `/tests/` + `test-report-XX.md` | **[NEW]** Test plan (cases mapped to AC); **EXISTING** Vitest / pytest |
| D2 | Code Reviewer | PR + ADRs | PR review comments + verdict (approve / request-changes) | **EXISTING** GitHub PR review |
| D3 | Security Reviewer | PR + ADRs + `schema-XX.md` | `sec-review-XX.md` + PR comments | **[NEW]** Security review checklist (auth, RBAC, input validation, secrets, PII, OWASP top 10) |
| E1 | DevOps | Approved PRs in release window | Updated CI/CD config + deployment log | **EXISTING** GitHub Actions / Docker / Makefile |
| E2 | Tech Writer | Merged stories | Updated `/docs/**/*.md` + `CHANGELOG.md` + `release-notes-vX.Y.Z.md` | **EXISTING** docs structure; **[NEW]** release-notes file per version |
| E3 | SRE / Analyst | Production telemetry + user feedback | `feedback-XX.md` (loops back to A1) | **[NEW]** Feedback report: SLO status, top errors, usage metrics, user requests |
| ✦ | Code Auditor (cross-cutting) | `epic-XX-*.md` + `/backend/` + `/frontend/` | `audits/audit-XX-*.md` | **[NEW]** Reproducible epic-vs-code gap analysis per `architecture/AUDIT_STANDARD.md` |

### 2.3 Where artifacts live (proposed directory layout)

```
/plan/                                ← EXISTING, expanded
├── BACKLOG.md
├── README.md
├── LAYOUT_CONVENTION.md              ← UILDC v1.0
├── MULTI_AGENT_SDLC.md               ← this file
├── epics/                            ← EXISTING
│   └── epic-XX-*.md                  (PO output, contains UX-written frontend sections)
├── vision/                           ← NEW
│   └── vision-XX.md
├── research/                         ← NEW
│   └── research-XX.md
├── architecture/                     ← NEW
│   ├── AUDIT_STANDARD.md             (defines the `audit` artifact type)
│   ├── arch-XX.md                    (per epic; arch-platform = whole system)
│   ├── adr-XXX.md                    (per decision, global numbering)
│   ├── schema-XX.md
│   └── audits/
│       └── audit-XX-<slug>.md        (per epic — gap analysis vs code)
├── tasks/                            ← NEW
│   └── tasks-XX.md
└── feedback/                         ← NEW
    └── feedback-XX.md

/docs/                                ← EXISTING (Tech Writer target)
├── release-notes/                    ← NEW
│   └── release-notes-vX.Y.Z.md
└── CHANGELOG.md                      ← NEW (or top-level)

/tests/                               ← EXISTING (QA target)
└── test-plans/                       ← NEW
    └── test-plan-XX.md
```

---

## 3. Inter-Agent Communication Pattern

Three principles make the chain reliable:

1. **One artifact = one source of truth.** No agent rewrites another agent's artifact; it produces a *new* downstream artifact that references upstream via `upstream:` in frontmatter.
2. **Handoff gate.** Each artifact has a `status:` field. Downstream agents only consume `approved` artifacts. The `Tech Lead` (C1) acts as the orchestrator that flips status during the build stage; for product/design stages the human flips it during simulation.
3. **Decisions and open questions are explicit.** Every artifact ends with a `## Decisions` and `## Open Questions` section. This is the cheap mechanism that prevents agents from silently disagreeing.

### Minimum viable simulation loop (manual, for the first run)

```
1-line idea
   ↓
A1 → vision-01.md
   ↓
A2 → research-01.md
   ↓
A3 → epic-21-chat-module.md  (uses existing format)
   ↓
B1 + B2 + B3 (parallel)
   → arch-21.md, adr-021.md, schema-21.md, UILDC sections
   ↓
C1 → tasks-21.md
   ↓
C2 + C3 (parallel per task) → PRs + impl-notes
   ↓
D1 + D2 + D3 → test-report-21.md, review verdict, sec-review-21.md
   ↓
E1 → deploy
E2 → release-notes-v1.X.0.md, /docs updates
   ↓
E3 → feedback-21.md  →  loops back to A1
```

---

## 4. Critical Files to Reference (existing, do not duplicate)

When designing or running each agent, read these first:

| Agent | Must-read files |
|-------|-----------------|
| A3 Product Owner | `/plan/README.md`, `/plan/BACKLOG.md`, any existing `/plan/epics/epic-*.md` for tone/format |
| B3 UX Designer | `/plan/LAYOUT_CONVENTION.md`, `/plan/layout-convention/01..07-*.md` |
| B1 Architect | `/docs/platform/OVERVIEW.md`, `/docs/backend/README.md`, `/docs/backend/AUTH_SECURITY.md`, `/docs/backend/RBAC.md`, `/docs/backend/DYNAMIC_ENTITIES.md` |
| B2 Data Modeler | `/modules/MODULE_ALEMBIC_SETUP.md`, `/docs/backend/DYNAMIC_ENTITIES.md` |
| C2 Backend Engineer | `/backend/`, `/docs/backend/API_REFERENCE.md` |
| C3 Frontend Engineer | `/frontend/`, `/docs/frontend/COMPONENT_LIBRARY.md`, `/docs/frontend/I18N.md` |
| D1 QA | `/tests/`, `/vitest.config.js` |
| E1 DevOps | `/docker-compose.yml`, `/Makefile`, `/manage.sh`, `/infra/`, `/docs/deployment/*` |
| E2 Tech Writer | `/docs/` (mirrors output target) |

---

## 5. Suggested Simplifications for the First Simulation

To avoid drowning in role overhead on day one, collapse to **5 super-agents** and expand later:

| Super-agent | Covers |
|-------------|--------|
| **Product** | A1 + A2 + A3 |
| **Designer** | B1 + B2 + B3 |
| **Engineer** | C1 + C2 + C3 |
| **Reviewer** | D1 + D2 + D3 |
| **Releaser** | E1 + E2 + E3 |

Same artifact contracts apply; one persona just produces several documents. Once the loop works, split each super-agent back into its specialists.

---

## 6. Verification (how to test the simulation works)

This document is a recommendation — the "test" is running the loop once manually and checking the chain holds together.

1. **Pick a real idea**, e.g. "Add an in-app chat module so users in the same tenant can DM each other."
2. **Run the loop manually**, with one Claude instance per role producing each artifact in order.
3. **Success criteria for the simulation:**
   - Every artifact has valid frontmatter and a populated `upstream:` chain back to `vision-XX.md`.
   - Every story acceptance criterion appears in `test-plan-XX.md` and is marked PASS in `test-report-XX.md`.
   - The merged code passes `make test` (or `pytest` + `vitest`) and the existing CI pipeline.
   - `release-notes-vX.Y.Z.md` references every merged story.
   - `feedback-XX.md` produces at least one item that could plausibly start a new `vision-XX.md`.
4. **Iterate**: any handoff that required ad-hoc clarification = a gap in the artifact spec; tighten the template for that artifact type and re-run.

Once the manual loop is reliable, automate it by giving each role a Claude Agent SDK subagent with: (a) its read scope (which files it may consume), (b) its write scope (which artifact it produces), and (c) a system prompt grounded in the templates above.
