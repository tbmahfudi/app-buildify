# impl-notes-T-22-026 -- ADR: tenant isolation enforcement

**Task**: T-22.026 -- ADR for ContextVar + ORM listener vs middleware vs DB RLS
**Status**: DONE
**Date**: 2026-06-27
**Owner**: E2 Technical Writer

---

## Deliverable

`plan/architecture/adr-tenant-isolation-22.md`.

Records the decision to enforce shared-core tenant scope with two cooperating
layers — a `ContextVar` (`_current_tenant_id`) for per-context scope and a
SQLAlchemy `TenantScopeListener` (`do_orm_execute` + `before_flush`) — plus the
`apply_tenant_scope()` helper and the `check-tenant-scope` CI gate.

Alternatives weighed and rejected (with rationale):

- **A. Middleware-only** — necessary for *setting* scope but cannot enforce on
  background tasks, direct `session.query`, or flushes. Kept for setting, not
  enforcement.
- **B. PostgreSQL row-level security** — strongest guarantee but PG-only (kills
  SQLite test coverage), heavy DDL/migration surface, pooling discipline, opaque
  denials. Recommended as future defense-in-depth.
- **C. Per-model `.scoped()` mixin** — opt-in, so it reproduces today's silent
  failure mode.

Documents consequences, the opt-in `__tenant_scoped__` risk (M-1), bypass
surfaces (`text()`, `bulk_insert_mappings`, `Connection.execute(insert())`), and
follow-ups (M-1, RLS, L-2).
