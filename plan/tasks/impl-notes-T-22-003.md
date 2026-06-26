# impl-notes-T-22-003 -- Update manage.sh: check-tenant-scope subcommand

**Status**: DONE
**Date**: 2026-06-26
**Owner**: C2 Backend Developer

## What was implemented

Rewrote the manage.sh check-tenant-scope subcommand (previously duplicated 3x from
an incomplete earlier attempt) with a single, correct implementation.

## Behaviour

- Scans backend/app/services/ and backend/app/routers/ for raw .tenant_id == literals
- Exits 0 (PASS) when no unguarded literals are found
- Exits 1 (FAIL) when any unguarded literal is found; prints file:line for each violation
- Excludes lines annotated with # tenant-scope-ok (intentional exceptions)
- Excludes scope.py itself to avoid self-matching the helper

## Usage

    ./manage.sh check-tenant-scope

## Annotation convention

Lines that intentionally use raw literals (e.g. inside apply_tenant_scope itself)
should end with:  # tenant-scope-ok

## Current state

Running check-tenant-scope against the current codebase shows violations in
routers/ and services/ because T-22.007/T-22.008 (service and router migration)
are not yet done. The gate is intended to be wired into CI after those sprints
complete (T-22.022). All current violations carry # tenant_scope comments so they
are visible but will need the # tenant-scope-ok annotation or migration before CI
goes green.
