# impl-notes-T-22-019 -- Wire cleanup into T-23.025 + manage.sh subcommands

**Task**: T-22.019
**Files**: backend/app/routers/modules.py, manage.sh
**Status**: DONE

## What was implemented

### 1. T-23.025 stub wired (modules.py line ~2076)

Replaced the no-op comment in DELETE /api/v1/modules/admin/{module_id} (step 4)
with real wiring to cleanup_tenant_module_dbs. The script is imported at
call time by inserting the scripts/ directory into sys.path. This avoids
circular imports while keeping the script independently runnable.

Before deleting ModuleActivation rows (step 5), the handler queries all
tenant_ids that had the module activated and calls cleanup_tenant_module_dbs()
for each. Errors per tenant are logged at ERROR level but do not abort the
rest of the uninstall flow -- a partial cleanup is better than a failed
uninstall leaving the module row in place.

### 2. manage.sh tenant deactivate (already wired in earlier sprint)

manage.sh tenant deactivate <tenant_id> was already calling the cleanup
script via docker exec or direct python3 invocation. The script it calls
now has the full implementation from T-22.018, so the subcommand is now
fully functional.

### 3. manage.sh module migrate-tenant placeholder (arch-22 section 4.2)

Added migrate-tenant subcommand to the module case block in manage.sh.
Prints a clear placeholder message explaining that full wiring is deferred
to sprint N+1 (depends on T-22.016 ModuleScopeMiddleware full connection-
pool wiring, which is the L-1 tracked item).

## Files changed

- backend/app/routers/modules.py -- step 4 no-op replaced with cleanup wiring
- manage.sh -- module migrate-tenant subcommand added
