# App-Buildify — Product Backlog Index

## Structure

```
plan/
├── README.md          ← this file (index)
├── BACKLOG.md         ← full summary table (all 20 epics at a glance)
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
    ├── epic-12-financial-module.md
    ├── epic-13-security-compliance.md
    ├── epic-14-notification-system.md
    ├── epic-15-flex-component-library.md
    ├── epic-16-internationalization.md
    ├── epic-17-settings-configuration.md
    ├── epic-18-developer-experience.md
    ├── epic-19-infrastructure-deployment.md
    └── epic-20-mobile-pwa.md
```

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

| # | Epic | Stories | Status |
|---|------|---------|--------|
| 1 | [Authentication & Identity](epics/epic-01-authentication.md) | 17 | Mostly DONE |
| 2 | [Multi-Tenancy & Org Management](epics/epic-02-multi-tenancy.md) | 11 | Mostly DONE |
| 3 | [User Management](epics/epic-03-user-management.md) | 6 | DONE |
| 4 | [RBAC & Permissions](epics/epic-04-rbac-permissions.md) | 7 | Mostly DONE |
| 5 | [NoCode Entity Designer](epics/epic-05-nocode-entity-designer.md) | 13 | Mixed |
| 6 | [Dynamic CRUD & API Layer](epics/epic-06-dynamic-crud-api.md) | 8 | Mostly DONE |
| 7 | [Workflow Engine](epics/epic-07-workflow-engine.md) | 5 | DONE |
| 8 | [Automation Rules](epics/epic-08-automation-rules.md) | 6 | Mixed |
| 9 | [Dashboard & Analytics](epics/epic-09-dashboard-analytics.md) | 7 | DONE |
| 10 | [Reporting](epics/epic-10-reporting.md) | 5 | DONE |
| 11 | [Module System](epics/epic-11-module-system.md) | 7 | Mostly DONE |
| 12 | [Financial Module](epics/epic-12-financial-module.md) | 11 | Mixed |
| 13 | [Security & Compliance](epics/epic-13-security-compliance.md) | 8 | Mostly DONE |
| 14 | [Notification System](epics/epic-14-notification-system.md) | 6 | Mixed |
| 15 | [Flex Component Library](epics/epic-15-flex-component-library.md) | 10 | Mixed |
| 16 | [Internationalization](epics/epic-16-internationalization.md) | 5 | Mixed |
| 17 | [Settings & Configuration](epics/epic-17-settings-configuration.md) | 6 | Mixed |
| 18 | [Developer Experience & SDK](epics/epic-18-developer-experience.md) | 6 | Mixed |
| 19 | [Infrastructure & Deployment](epics/epic-19-infrastructure-deployment.md) | 8 | Mixed |
| 20 | [Mobile & PWA](epics/epic-20-mobile-pwa.md) | 3 | PLANNED |
