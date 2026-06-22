# TEMPLATE Module — Planning

This directory contains all planning artifacts for the TEMPLATE module.
It is entirely separate from the platform `plan/` directory — module developers own this space.

## Structure

| Path | Purpose |
|------|---------|
| `BACKLOG.md` | All module stories with status tags |
| `epics/` | One file per epic (A3 output) |
| `vision/` | Module vision docs (A1 output) |
| `architecture/` | Module ADRs and arch docs (B1/B2 output) |
| `research/` | Module research briefs (A2 output) |
| `tasks/` | Module task breakdowns (C1 output) |

## Agent hand-offs

```
A1 (vision/) → A2 (research/) → A3 (epics/ + BACKLOG.md)
→ B1 (architecture/arch-XX.md) → B2 (architecture/schema-XX.md) → B3 (UI spec in epics/)
→ C1 (tasks/) → C4 (modules/TEMPLATE/backend) / C5 (modules/TEMPLATE/frontend)
→ D1 (test plan) → D3 (security review)
→ E2 (modules/TEMPLATE/docs/)
```

All artifacts in this directory are scoped to this module.
Platform planning artifacts live in `plan/` and are off-limits to module agents (C4, C5).

## Cross-boundary requests

If a module story requires a new platform capability, file a request:
`platform-requests/open/REQ-NNN-description.md`

The platform team reviews and implements; you are notified via `platform-requests/resolved/`.
