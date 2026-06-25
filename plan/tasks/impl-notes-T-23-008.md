# impl-notes-T-23-008 — manage.sh module pack

**Task**: T-23.008
**Status**: DONE
**Date**: 2026-06-25
**Owner**: E1 DevOps Engineer

## What was implemented

`module_pack()` function in `manage.sh` (around line 723) implements `./manage.sh module pack <module_dir> [--out <output_dir>]`.

### Behaviour

1. Validates `<module_dir>` exists and contains `manifest.json`
2. Reads `name` and `version` from `manifest.json` via `python3`
3. Creates `$OUT_DIR` if it does not exist (defaults to `.`)
4. Normalises all file timestamps to `2020-01-01 00:00:00` (excluding `__pycache__` and `*.pyc`) for deterministic builds
5. Creates tarball with `tar --sort=name` — consistent entry order
6. Generates `SHA256SUMS` via `sha256sum`
7. Prints `Packed: <name>_<version>.tar.gz` and `SHA256: <hash>`

### Dispatch

Wired in the `case $COMMAND in ... module)` block:
```
pack) module_pack "$@" ;;
```

## Determinism verification

Two consecutive pack runs on `modules/healthcare` produce identical SHA256:
`92aa6ee7fca5aacd446dea07108ecbb2b91ac06db056898cd297052a08bc5798`

## Scope note

Pre-pack manifest validation (`POST /modules/validate`) is intentionally excluded — that is T-23.009 scope.

## Files changed

- `manage.sh` — `module_pack()` function (lines ~723-780)
- `plan/tasks/tasks-23.md` — T-23.008 marked DONE
