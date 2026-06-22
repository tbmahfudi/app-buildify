# Module Planning & Documentation Guide

This guide explains how planning and documentation work for module developers.
Module planning is **entirely separate** from the platform's `plan/` directory.

---

## Directory structure

```
plan-mod-{name}/              ← Module planning (you own this)
  BACKLOG.md                  ← Module story backlog
  README.md                   ← Planning overview
  epics/                      ← Epic definitions with AC (A3 output)
  vision/                     ← Module vision docs (A1 output)
  architecture/               ← ADRs and schema docs (B1/B2 output)
  research/                   ← Research briefs (A2 output)
  tasks/                      ← Task breakdowns (C1 output)

modules/{name}/
  docs/                       ← Module developer documentation (E2 output)
    API.md                    ← Endpoint reference
    ARCHITECTURE.md           ← Module internals
    CHANGELOG.md              ← Version history
```

### Shared module documentation (read-only for module agents)

| File | Contents |
|------|---------|
| `docs/modules/SDK_REFERENCE.md` | PlatformBridge and BaseModule API reference |
| `docs/modules/CREATING_A_MODULE.md` | Step-by-step guide to scaffold and install a module |
| `docs/modules/MODULE_PLANNING.md` | This file |

---

## Separation from the platform

| What | Platform | Module |
|------|----------|--------|
| Backlog | `plan/BACKLOG.md` | `plan-mod-{name}/BACKLOG.md` |
| Epics | `plan/epics/` | `plan-mod-{name}/epics/` |
| Architecture | `plan/architecture/` | `plan-mod-{name}/architecture/` |
| Docs | `docs/platform/`, `docs/backend/`, `docs/frontend/` | `modules/{name}/docs/` |

Module agents (C4, C5) are **forbidden** from reading or writing `plan/` or `docs/platform/`.

---

## Agent hand-offs for module development

All agents operating on a module write to `plan-mod-{name}/`:

```
A1  → plan-mod-{name}/vision/vision-XX.md
A2  → plan-mod-{name}/research/research-XX.md
A3  → plan-mod-{name}/epics/ + BACKLOG.md
B1  → plan-mod-{name}/architecture/arch-XX.md
B2  → plan-mod-{name}/architecture/schema-XX.md
B3  → updates epics/ with Frontend UILDC specs
C1  → plan-mod-{name}/tasks/tasks-XX.md
C4  → modules/{name}/backend code
C5  → modules/{name}/frontend code
D1  → plan-mod-{name}/architecture/test-plan-XX.md
D3  → plan-mod-{name}/architecture/sec-review-XX.md
E2  → modules/{name}/docs/
```

---

## Requesting platform capabilities

If a module story requires a platform feature not available in the SDK:

1. Create `platform-requests/open/REQ-NNN-description.md` from the template
2. Describe what you need and why (link to the relevant epic story)
3. The platform team reviews, implements, and moves the file to `platform-requests/resolved/`
4. The new capability appears in `modules/sdk/platform_bridge.py`

---

## Scaffolding a new module

```bash
./manage.sh module new my_module
```

This creates both:
- `modules/my_module/` — code scaffold (from `modules/template/`)
- `plan-mod-my_module/` — planning scaffold (from `plan-mod-template/`)
