# impl-notes-T-22-028 -- Runbook: tenant isolation

**Task**: T-22.028 -- operations runbook for tenant isolation
**Status**: DONE
**Date**: 2026-06-27
**Owner**: E2 Technical Writer

---

## Deliverable

`docs/runbooks/runbook-tenant-isolation.md` (new `docs/runbooks/` directory).

Four operational sections for on-call:

1. **Diagnose `TenantScopeMissingError` (HTTP 500)** — what it means (fail-loud
   guarantee working), the three common root causes (`get_db` vs
   `tenant_scoped_session`, unscoped background `SessionLocal`, newly-flagged
   model), diagnosis greps, and fixes. Includes the cross-tenant-write rejection
   case.
2. **Check violation counts** — running `manage.sh check-tenant-scope`, the
   baseline=36 semantics, `TENANT_SCOPE_BASELINE` override, and how to clear a
   gate failure (migrate or annotate `# tenant-scope-ok`).
3. **Module databases** — inspecting `tenant_module_databases`, **dry-run
   cleanup first** (`cleanup_tenant_module_dbs.py --dry-run`), `manage.sh tenant
   deactivate`, archive vs drop policy, the audit-before-destructive guarantee,
   and a `drop`-policy safety checklist.
4. **Escalation** — rollback guidance and the security-incident path for a
   suspected real cross-tenant exposure.
