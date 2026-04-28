# Financial Module — Plan Index

Module-specific backlog for the **Financial Module**, a pluggable module built on top of the App-Buildify platform.

## Structure

```
plan-mod-finance/
├── README.md          ← this file (index)
├── BACKLOG.md         ← full feature/story breakdown for the module
└── epics/
    └── epic-12-financial-module.md
```

## Relationship to the Platform Plan

This module depends on platform-level capabilities documented in `/plan/`:

- **Module System** (`/plan/epics/epic-11-module-system.md`) — registration, manifest, isolation
- **Multi-Tenancy** (`/plan/epics/epic-02-multi-tenancy.md`) — tenant scoping for all financial data
- **RBAC** (`/plan/epics/epic-04-rbac-permissions.md`) — permission format `financial:<resource>:<action>:<scope>`
- **Workflow Engine** (`/plan/epics/epic-07-workflow-engine.md`) — invoice and bill state transitions
- **Reporting** (`/plan/epics/epic-10-reporting.md`) — host for the standard financial report suite
- **Infrastructure** (`/plan/epics/epic-19-infrastructure-deployment.md`) — service deployed as `financial-module` container, routed via `/api/v1/financial/*`

The story format and frontend UILDC v1.0 conventions follow `/plan/LAYOUT_CONVENTION.md`.

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
| 12 | [Financial Module](epics/epic-12-financial-module.md) | 11 | DONE; AP/Budget PLANNED |

## Implementation Reference

- Backend code: `/modules/financial/` (or wherever the financial module is mounted)
- Module docs: `/docs/modules/FINANCIAL_MODULE.md`
- Setup scripts: `/setup_financial_module.sh`, `/enable_financial_module.sh`, `/enable_financial_module.sql`
