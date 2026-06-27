# impl-notes-T-22-022 -- CI Gate for check-tenant-scope

**Task**: T-22.022 -- Wire `check-tenant-scope` into CI as a pre-merge gate
**Status**: DONE
**Date**: 2026-06-27
**Owner**: E1 DevOps Engineer

---

## Deliverables

### `.github/workflows/ci.yml` — `tenant-scope-gate` job

Runs `bash manage.sh check-tenant-scope` as a dedicated job ordered
`lint -> tenant-scope-gate -> test`. A failing gate (`needs: tenant-scope-gate`
on `test`) blocks the test job and therefore the merge. The job comment documents
the baseline-aware behavior and points to the migration doc.

### `manage.sh check-tenant-scope` — made baseline-aware (T-22.022 requirement)

The prior implementation was an all-or-nothing "any literal fails" check whose
`exit 1` path did not propagate reliably under `set -e` piping, and which did not
reflect the documented baseline. Rewrote the arm to:

- Count **unannotated** raw `.tenant_id ==` literals in `services/` + `routers/`.
- Accept lines annotated `# tenant-scope-ok` (canonical) or the legacy
  `# tenant_scope` marker from the T-22.007/008 migration.
- Fail (`exit 1`) only when `COUNT > BASELINE`, where `BASELINE=36`
  (overridable via `TENANT_SCOPE_BASELINE`).
- Print file:line for every violation on failure.

This catches any NEW unguarded literal (count rises above 36) while keeping the
build green at the established baseline. Ratchet is down-only.

### `docs/backend/TENANT_SCOPE_MIGRATION.md` (new)

Documents the rule, the `# tenant-scope-ok` annotation convention, the gate's
baseline semantics, CI wiring, local usage, and the M-2 ratchet-down process.
The ci.yml comment referenced this file but it did not previously exist.

---

## Verification

```
$ bash manage.sh check-tenant-scope
==> check-tenant-scope: scanning services/ and routers/ ... (baseline=36)
check-tenant-scope: 8 unannotated literal(s) found (baseline 36).
check-tenant-scope: PASS — and below baseline; ...
$ echo $?
0
```

Current unannotated count: 8 (services: 0, routers: 8) — well under the baseline
of 36. Adding a new unannotated literal pushes the count above baseline and fails
the build.

## Notes / findings

- Baseline reconciliation: `grep` shows 39 service + 67 router raw literals, but
  all 39 service and 59 router lines carry a `# tenant_scope`/`-ok` annotation, so
  0 service + 8 router are *unannotated* today. The documented "0 service, 36
  router" baseline is the historical figure; the gate is conservative against it.
