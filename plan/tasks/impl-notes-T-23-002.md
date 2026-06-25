---
task: T-23.002
author: C2 Backend Developer
date: 2026-06-25
status: DONE
---

# impl-notes — T-23.002: GET /api/v1/modules/{id}/activation-preview

## Summary

Added  to  in
. Returns a structured preview of what activating a
module will do for the requesting tenant.

## Files changed

| File | Change |
|------|--------|
|  | New endpoint on ; extended schema import block |
|  | , , ,  (already present from prior session; no changes needed) |

## Design decisions

### Lookup by UUID (not name)
The task spec uses  (UUID primary key). Consistent with the existing
 endpoint on the same .

### Permission extraction
 items are normalised: accepts both  and  keys
as the permission identifier.

### Menu items extraction
Tries  first, then falls back to .

### Dependency normalisation
 can be a plain list or a dict with /
sublists — both are flattened to a single list before resolution.

### Dependency status
For each dependency, queries  by name, then checks 
(alias for ) for a row matching
.

Status values:
-  — enabled  row exists for this tenant
-  — module registered but not enabled for this tenant
-  — no  row found for the dependency name

### Auth
Uses  (standard tenant-scoped auth). No superuser required per spec.

## Acceptance criteria check

| AC | Status |
|----|--------|
| Endpoint exists and returns correct shape | done |
| 404 on unknown module_id | done |
| Dependencies resolved against requesting tenant | done |
| Pydantic schemas added | done (pre-existing in schemas/module.py) |
| impl-notes written | done |
| T-23.002 DONE in tasks-23.md | done |
