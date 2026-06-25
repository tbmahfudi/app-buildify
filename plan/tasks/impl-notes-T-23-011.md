# impl-notes-T-23-011 — Install Steps 5-8 + Rollback

**Task**: T-23.011  
**Owner**: E1 DevOps Engineer  
**Date**: 2026-06-26  
**Status**: DONE

## What Was Implemented

All install steps 5-8 and rollback are in manage.sh module_install() function.

### Step 5 — Copy backend files
Copies extracted/backend/ to /home/mahfudi/app-buildify/backend/modules/<name>/ on the host.
This path is bind-mounted into the backend container as /app/modules/<name>/ so no docker cp is needed.

### Step 6 — Copy frontend assets
Copies extracted/frontend/ to /home/mahfudi/app-buildify/frontend/assets/modules/<name>/.
Same bind-mount approach.

### Step 7 — Register via API
POST /api/v1/module-registry/register with {manifest: {...}, backend_service_url: ...}.
Auth header added if BUILDIFY_TOKEN or --token is set.
The /register endpoint (T-23.014) calls BaseModule.post_install(db) server-side — no separate CLI call needed.

Bug fixed: original code used eval curl with -d and JSON embedded in the shell string, causing malformed RCODE (concatenated 000 from curl output + shell || echo 000). Fixed by writing payload to a temp file and using curl --data @file with a bash array for curl args.

### Step 8 — Set install_status=ready
Direct DB write via docker exec app_buildify_backend python3. Sets install_status=ready, is_installed=True, installed_at, updated_at.

### Rollback (_module_rollback)
Called on any step 5-8 failure with BACKEND_DEST and FRONTEND_DEST paths:
- Removes backend dir with rm -rf
- Removes frontend dir with rm -rf
- Sets install_status=failed and install_error_message in DB via docker exec

Note: rm -rf on backend dir may leave __pycache__ files owned by root (Docker-created). These pre-exist and partial removal is acceptable.

## Test Result
With backend container partially available (no postgres):
- Steps 5-6: files copied successfully
- Step 7: API returns 500 -> rollback fires -> dirs removed -> exit 1
- Full stack: all 8 steps complete, status set to ready

## Key Files
- manage.sh: module_install() and _module_rollback()
