# impl-notes-T-23-009 — Pre-pack manifest validation

**Task**: T-23.009  
**Status**: DONE  
**Date**: 2026-06-25

## What was done

Added an optional pre-pack validation block in `manage.sh` `module_pack()`, inserted before the timestamp normalisation step (before any files are written to disk).

## Behaviour

The block checks three conditions in order:

1. **Backend reachable AND `BUILDIFY_TOKEN` set** — POSTs `{"manifest": <manifest.json contents>}` to `POST /api/v1/modules/validate`.
   - HTTP 200 — prints "Manifest valid." and continues.
   - HTTP 422 — prints the error body to stderr and exits non-zero (exit 1).
   - HTTP 401/403 — prints auth warning and continues (not a manifest error).
   - Other — prints unexpected-response warning and continues.

2. **Backend reachable but `BUILDIFY_TOKEN` not set** — warns "BUILDIFY_TOKEN not set — skipping pre-pack validation" and continues.

3. **Backend not reachable** — warns "Backend not reachable — skipping pre-pack validation" and continues.

Backend reachability is checked via `curl --max-time 2` against `$BUILDIFY_API_URL/api/v1/health` (falling back to `/`). Default API base is `http://localhost:8000`; override with `BUILDIFY_API_URL` env var.

## Why this approach

The pack command is run locally (outside Docker). Making validation optional with a clear warning when skipped keeps the command useful in both environments: dev without backend running, and CI/CD with backend running and a valid token.

## Test run

```
bash manage.sh module pack modules/healthcare --out /tmp/test-pack
```

Without `BUILDIFY_TOKEN` set: warns and packs successfully, producing `healthcare_1.0.0.tar.gz` + `SHA256SUMS`.
