# impl-notes-T-24-002 — Pre-existing File Audit

**Task**: Check if `password-strength-indicator.js` and `builder-version-history.js` exist; read them; issue reuse verdict.
**Date**: 2026-06-27
**Owner**: C3 Frontend Developer

---

## 1. password-strength-indicator.js

**Status**: EXISTS at `frontend/assets/js/password-strength-indicator.js`

### What it does (as found)
- Class `PasswordStrengthIndicator(inputEl, submitBtn, apiBase)`
- On construct: renders a loading placeholder, fetches `GET /api/v1/auth/password-policy`
- Builds a rule checklist from the policy response (length, uppercase, lowercase, digit, special, common-password)
- Renders each rule as a `<li>` with ph-circle / ph-check-circle / ph-x-circle icons matching uildc-24 § 2.2 palette
- Renders a single `<div>` progress bar (width % + colour class swap: red/amber/green)
- Disables `submitBtn` until all rules pass
- `destroy()` method cleans up the event listener and removes the DOM container
- Exported as `default` ES module class
- **Fail-open**: if policy fetch fails, removes loading indicator and enables submit

### Match to Story 24.2.1 spec
| Requirement | Status |
|---|---|
| Attach to password input | MATCH — constructor takes `inputEl` |
| Policy fetch + session cache | PARTIAL — fetches per-instance, no session-scope cache yet |
| Rule checklist with correct icons | MATCH — ph-circle / ph-x-circle / ph-check-circle |
| Strength progress bar | MATCH — single bar, colour-coded |
| Fail-open if policy fetch fails | MATCH |
| aria-label per rule item | MISSING — T-24.009 must add this |
| 4-segment standalone bar | ADDED by T-24.004 (this sprint) |

### T-24.004 additions (applied in this sprint)
Two new named exports appended to the file:
- `getStrength(password)` — pure function, returns `{ level, score }` based on length/mixed-case/digit/special rules
- `renderStrengthBar(containerEl, password)` — renders/updates a 4-segment coloured progress bar + label in a container element; used by `password-reset-page.js`

### Verdict: **EXTEND** (do not rewrite)
The existing class is well-structured, matches the icon/colour palette, and is fail-open. T-24.009 should extend it to add per-rule `aria-label` attributes, session-scope policy cache, and confirm the `attach(inputEl, submitBtn)` public API alias.

---

## 2. builder-version-history.js

**Status**: EXISTS at `frontend/assets/js/builder-version-history.js`

### What it does (as found)
- Named export `initBuilderVersionHistory()`
- Builds a slide-in drawer (`#version-history-drawer`) with header, scrollable version list, and footer close button
- Fetches `GET /builder-pages/{pageId}/versions` and renders version items with Preview and Restore actions
- Preview opens a FlexModal-style overlay with JSON diff view
- Restore shows an inline confirm row; calls `POST /builder-pages/{pageId}/restore/{versionId}`
- On success: closes drawer, shows green notification toast, dispatches `builder:version-restored` CustomEvent
- Injects a "History" toolbar button (`#btn-version-history`) via `injectButton()`
- Listens on `route:loaded` event to re-inject button when builder route loads

### Match to Story 24.6.1 spec
| Requirement | Status |
|---|---|
| History button in builder toolbar | MATCH |
| Version list drawer | MATCH |
| Preview modal | MATCH (custom overlay, not FlexModal) |
| Inline restore confirmation | MATCH |
| Concurrent restore prevention (disable other Restore buttons) | MISSING |
| aria-label per version item | MISSING |
| FlexSpinner loading state | PARTIAL (custom inline spinner text) |
| ph-files empty state | MISSING |
| Focus trap + aria-modal on drawer | MISSING |

### Verdict: **EXTEND** (do not supersede/delete)
Core logic (fetch, render, preview, restore) is solid and maps directly to the epic spec. T-24.025–T-24.027 should extend it to add the missing accessibility attributes, empty state, concurrent-restore lock, and FlexDrawer wrapper. File should NOT be deleted; T-24.028 deletion condition is not met.
