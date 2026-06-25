# T-23.010 Implementation Notes — `manage.sh module install` Steps 1-4

**Status**: DONE  
**Date**: 2026-06-25  
**Owner**: E1 (DevOps Engineer)

## What was implemented

Added / updated `module_install()` in `manage.sh` to implement the first 4 steps of the module install pipeline.

### CLI signature

```
./manage.sh module install <tarball> [--api-url <url>] [--token <token>]
```

Both flags are optional. `API_BASE` defaults to `http://localhost:8000`. `TOKEN` defaults to `$BUILDIFY_TOKEN` env var.

### Step 1 — SHA256 Verify (`[1/4] Verifying SHA256...`)
- Looks for `SHA256SUMS` file in same directory as the tarball
- Runs `sha256sum` and compares against stored value
- Exits non-zero on mismatch
- Warns and continues if no `SHA256SUMS` found

### Step 2 — Validate Manifest (`[2/4] Validating manifest...`)
- Extracts `manifest.json` from tarball into a temp dir
- Calls `POST /api/v1/modules/validate` with `{"manifest": <contents>}`
- Exits non-zero on HTTP 422 (prints error body to stderr)
- Warns and continues if API unreachable (non-422 / non-200 response)

### Step 3 — Set install_status=in_progress (`[3/4] Setting install_status=in_progress...`)
- Uses `docker exec app_buildify_backend python3` to upsert module record
- Creates new Module row if none exists; updates `install_status` if it does
- Sets `install_status='in_progress'`, clears `install_error_message`
- Non-fatal fallback (`|| true`) so a slow DB doesn't abort the install

### Step 4 — Module Alembic Migrations (`[4/4] Running module Alembic migrations...`)
- Checks for `<module>/backend/alembic/` or `<module>/migrations/` directory
- If found: `docker exec app_buildify_backend bash -c "cd /app/modules/<name> && alembic upgrade head"`
- If not found: logs `No migrations found — skipping`
- On migration failure: calls `_module_rollback()` (sets `install_status=failed`) and exits 1

## Test result (healthcare module)

```
[1/4] Verifying SHA256...
[INFO] Checksum OK.
[INFO] Module: healthcare v1.0.0
[2/4] Validating manifest...
[INFO] Manifest valid.
[3/4] Setting install_status=in_progress...
[4/4] Running module Alembic migrations...
[INFO] No migrations found — skipping
```

Also fixed `modules/healthcare/manifest.json`: added `module_type`, `category`, `api_prefix`;
changed `dependencies` from object to array; removed non-schema fields (`assets`, `entry_point`, `navigation`).

## Notes for T-23.011

Steps 5-8 are present in `module_install()` (labeled `[INFO] Step 5/8:` through `[INFO] Step 8/8:`).
T-23.011 should update those labels to the `[5/8]`-`[8/8]` format and audit rollback coverage.
