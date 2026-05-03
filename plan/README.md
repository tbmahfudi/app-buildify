# App-Buildify — Product Backlog Index

> Scope: this folder covers the **platform** only. Module-specific plans live in their own `plan-mod-<name>/` folders (e.g. `/plan-mod-finance/`).

## Structure

```
plan/
├── README.md          ← this file (index)
├── BACKLOG.md         ← platform summary + all platform epics
├── MULTI_AGENT_SDLC.md ← multi-agent SDLC roles & document contracts
├── vision/            ← Product Vision Statements (A1 output)
│   └── vision-XX-<slug>.md
├── research/          ← Research Briefs — personas, journeys, competitor matrix (A2 output)
│   └── research-XX-<slug>.md
├── agents/            ← per-role AI agent definitions (13 roles)
│   ├── AGENT_STANDARD.md  ← agent file format spec
│   ├── README.md          ← roster + communication flow + artifact map
│   └── agent-XX-<role>.md ← one file per role (operational, with system prompt)
├── architecture/
│   ├── arch-platform.md       ← platform-wide software architecture (arch-00-platform)
│   ├── AUDIT_STANDARD.md      ← defines the reusable `audit` artifact type
│   ├── adr-001-deployment-modes.md  ← monolith ↔ microservices deployment ADR
│   └── audits/
│       └── audit-XX-<slug>.md ← per-epic code-vs-AC gap analysis
└── epics/
    ├── epic-01-authentication.md
    ├── epic-02-multi-tenancy.md
    ├── epic-03-user-management.md
    ├── epic-04-rbac-permissions.md
    ├── epic-05-nocode-entity-designer.md
    ├── epic-06-dynamic-crud-api.md
    ├── epic-07-workflow-engine.md
    ├── epic-08-automation-rules.md
    ├── epic-09-dashboard-analytics.md
    ├── epic-10-reporting.md
    ├── epic-11-module-system.md
    ├── epic-13-security-compliance.md
    ├── epic-14-notification-system.md
    ├── epic-15-flex-component-library.md
    ├── epic-16-internationalization.md
    ├── epic-17-settings-configuration.md
    ├── epic-18-developer-experience.md
    ├── epic-19-infrastructure-deployment.md
    └── epic-20-mobile-pwa.md
```

## Modules (separate plans)

| Module | Plan folder |
|--------|-------------|
| Financial Module | [`/plan-mod-finance/`](../plan-mod-finance/README.md) |

## Story Format

Each story in the epic files is split into two perspectives:

- **Backend** — technical API/service/model acceptance criteria
- **Frontend** — detailed user interaction: page, route, components, validation, states

Frontend sections follow the **UI Layout Description Convention (UILDC v1.0)** — see [LAYOUT_CONVENTION.md](LAYOUT_CONVENTION.md) for the full reference and examples.

## Status Legend

| Tag | Meaning |
|-----|---------|
| `[DONE]` | Fully implemented |
| `[IN-PROGRESS]` | Partially implemented or has known bugs |
| `[OPEN]` | Documented gap — design exists, code does not |
| `[PLANNED]` | Roadmap item — no code yet |

## Epic Summary

> Status reflects audit findings as of 2026-04-29 (commit cc47a54). See [`architecture/audits/`](architecture/audits/) for per-story evidence.

| # | Epic | Stories | Status |
|---|------|---------|--------|
| 1 | [Authentication & Identity](epics/epic-01-authentication.md) | 17 | Mixed (core auth DONE; sessions + policy admin OPEN) |
| 2 | [Multi-Tenancy & Org Management](epics/epic-02-multi-tenancy.md) | 11 | DONE |
| 3 | [User Management](epics/epic-03-user-management.md) | 6 | IN-PROGRESS (user CRUD MISSING) |
| 4 | [RBAC & Permissions](epics/epic-04-rbac-permissions.md) | 7 | Mixed (assignments DONE; role CRUD + wildcards + entity perms OPEN) |
| 5 | [NoCode Entity Designer](epics/epic-05-nocode-entity-designer.md) | 13 | Mixed |
| 6 | [Dynamic CRUD & API Layer](epics/epic-06-dynamic-crud-api.md) | 8 | Mostly DONE |
| 7 | [Workflow Engine](epics/epic-07-workflow-engine.md) | 5 | DONE |
| 8 | [Automation Rules](epics/epic-08-automation-rules.md) | 6 | Mixed (8.1 DONE; 8.2 webhooks MISSING) |
| 9 | [Dashboard & Analytics](epics/epic-09-dashboard-analytics.md) | 7 | DONE |
| 10 | [Reporting](epics/epic-10-reporting.md) | 5 | Mostly DONE |
| 11 | [Module System](epics/epic-11-module-system.md) | 7 | Mostly DONE (activation API drift) |
| 13 | [Security & Compliance](epics/epic-13-security-compliance.md) | 8 | Mostly DONE; Prometheus + Tests MISSING |
| 14 | [Notification System](epics/epic-14-notification-system.md) | 6 | Mixed (arch DONE; delivery MISSING) |
| 15 | [Flex Component Library](epics/epic-15-flex-component-library.md) | 10 | Mixed (Layout suite OPEN) |
| 16 | [Internationalization](epics/epic-16-internationalization.md) | 5 | Mixed |
| 17 | [Settings & Configuration](epics/epic-17-settings-configuration.md) | 6 | Mixed |
| 18 | [Developer Experience & SDK](epics/epic-18-developer-experience.md) | 6 | Mixed |
| 19 | [Infrastructure & Deployment](epics/epic-19-infrastructure-deployment.md) | 8 | Mixed (CI/CD MISSING) |
| 20 | [Mobile & PWA](epics/epic-20-mobile-pwa.md) | 3 | PLANNED |
| 21 | [🔴 Risk Retirement (Sprint 1)](epics/epic-21-risk-retirement.md) | 4 (slice; refs 15.1.1, 14.2.1, 4.1.1+4.2.1, 4.2.4) | Sequencing epic per [research-01](research/research-01-app-buildify.md) — must complete before next net-new feature epic |
