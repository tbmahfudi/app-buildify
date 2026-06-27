# impl-notes-T-22-027 -- Release notes (epic-22)

**Task**: T-22.027 -- release notes for Epic 22
**Status**: DONE
**Date**: 2026-06-27
**Owner**: E2 Technical Writer

---

## Deliverable

`docs/release-notes/release-notes-epic-22.md`, following the epic-23 release-notes
format (front-matter, TL;DR, Overview, sectioned changes).

Covers: the fail-loud shared-core scope layer (helper + listener, 18 scoped
models, `before_flush` write guard), the single audited cross-tenant path
(`with_admin_cross_tenant_scope`), per-tenant module databases and cleanup, the
`check-tenant-scope` CI gate and new `manage.sh` subcommands, the three new
environment variables (`DATABASE_STRATEGY=per_tenant`, `MODULE_DB_POOL_MAX`,
`TENANT_DELETION_POLICY` — all defaulting to prior behavior), developer guidance,
the adversarial test suite, and known limitations (M-1, M-2, L-1, L-2, future
RLS).

States **no breaking changes** for tenant users; no required action for operators
to retain previous behavior.
