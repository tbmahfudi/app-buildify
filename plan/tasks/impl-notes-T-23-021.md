# impl-notes-T-23-021 — ActivationModal

**Task**: T-23.021
**Owner**: C3 Frontend Developer
**Status**: DONE
**Date**: 2026-06-26

## What was implemented

ActivationModal class in frontend/assets/js/modules-page.js.

### API helpers (top of file)

- getActivationPreview(moduleId) — GET /api/v1/modules/{moduleId}/activation-preview
- enableModule(moduleId) — POST /api/v1/modules/{moduleId}/enable

### ActivationModal states

| State | Behaviour |
|-------|-----------|
| preview-loading | _skeletonHTML() renders 3 animate-pulse rows; Confirm disabled |
| preview-loaded | _renderPreview(data) shows permissions, menu_items, dependencies sections |
| deps-unmet | Warning banner rendered; Confirm button stays disabled |
| activating | Both buttons disabled; Confirm shows SVG spinner + "Activating..." |
| activated | Modal closes via close(); module:activated CustomEvent dispatched |
| error | _showErrorInZone(message) renders red banner above footer; buttons re-enabled |

### Key design decisions

- backdropDismiss: false on FlexModal — user must explicitly cancel or confirm
- Confirm button is disabled on modal open; enabled only after preview loads AND all deps are active
- depsUnmet = deps.filter(d => d.status !== active) — strict active check per spec
- Error zone sits above the footer button row; cleared before each confirm attempt
- module:activated and modules:refresh both dispatched on success

### Files changed

- frontend/assets/js/modules-page.js — ActivationModal class (lines ~88-325)

## Acceptance criteria verified

- [x] fetch GET /modules/{id}/activation-preview on open
- [x] skeleton (3 rows) while loading; Confirm disabled
- [x] permissions, menu_items, dependencies rendered from preview response
- [x] any dep with status !== "active" triggers warning alert + Confirm disabled
- [x] Confirm calls POST /modules/{id}/enable
- [x] on success: modal closes, module:activated CustomEvent dispatched with detail.moduleId
- [x] on error: error banner shown above footer, buttons re-enabled
