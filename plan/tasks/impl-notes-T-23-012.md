# impl-notes-T-23-012 — Idempotency + Structured Step Logging

**Task**: T-23.012  
**Owner**: E1 DevOps Engineer  
**Status**: DONE  
**Date**: 2026-06-26

## What was implemented

### 1. Idempotency check (PostgreSQL-based)

Replaced the previous Python/ORM-based idempotency check with a direct `psql` query against the `app_buildify_postgresql` container. The check runs after `MODULE_NAME` and `MODULE_VERSION` are extracted from the manifest, before step 2.

```bash
local _EXISTING
_EXISTING=$(docker exec app_buildify_postgresql psql -U appuser -d appdb -tAc \
  "SELECT install_status FROM modules WHERE name='$MODULE_NAME' AND version='$MODULE_VERSION' LIMIT 1" 2>/dev/null)
if [ "$_EXISTING" = "ready" ]; then
    echo "Module '$MODULE_NAME' v$MODULE_VERSION is already installed. Nothing to do."
    exit 0
fi
```

- Uses `psql -tAc` (unaligned, tuples-only) so the result is a bare string with no whitespace padding.
- `2>/dev/null` means if the DB container is not running the check silently fails (returns empty string) and install proceeds — safe-fail behaviour.
- Checks `install_status = ready` specifically; an `in_progress` or failed record does NOT short-circuit, allowing a retry.

### 2. Step output normalisation

All 8 steps now use a consistent format:

```
[N/8] Step description...
  + Done (optional context)
```

On failure:
```
[N/8] Step description...
  x Failed: <reason>
```

Previously steps 1-4 used `[N/4]` and steps 5-8 used `[INFO] Step N/8:`. All steps now use `[N/8]` and the `+ Done` / `x Failed:` suffixes.

## Files changed

- `manage.sh` — `module_install()` function: idempotency check + step output normalisation

## Syntax verification

```
bash -n manage.sh && echo "Syntax OK"
# -> Syntax OK
```
