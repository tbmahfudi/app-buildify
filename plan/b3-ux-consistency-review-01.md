---
artifact_id: b3-ux-consistency-review-01
type: ux-review
producer: B3-ux-designer
consumers: [C3-frontend-developer, A1-product-manager, A3-product-owner]
status: review
created: 2026-06-19
---

# B3 UX Designer — Full-Screen Consistency & Capability Review

## Scope

All 36 production templates in `frontend/assets/templates/`. This review covers:
1. Layout pattern consistency across pages
2. Heading hierarchy and semantic markup
3. Colour / icon inconsistencies that break visual unity
4. Backend capabilities not surfaced in the UI (cross-referenced with PM review)
5. Placeholder / stub screens that mislead users

---

## 1. Layout Consistency Audit

### 1.1 Page wrapper — THREE competing patterns (Critical)

Every page should use the same outermost wrapper. Currently three are in use:

| Pattern | Pages using it | Problem |
|---|---|---|
| `<div class="space-y-6">` | audit, users, companies, profile, settings, settings-integration, settings-notifications, nocode-automations, nocode-workflows, nocode-lookups, nocode-data-model, reports-list | ✅ Dominant (12 pages) — adopt as canonical |
| `<section class="space-y-6">` | branches, departments | ❌ `<section>` without an accessible name is a lint warning; inconsistent with all other pages |
| `<div class="min-h-screen …">` or `<div class="h-screen flex flex-col">` | tenants, nocode-modules, builder, builder-pages, dashboard-designer, report-designer | ❌ Overrides the parent `#content` scroll container; causes double-scrollbar on some viewports |

**Fix (all pages):** standardise on `<div class="space-y-6">` as the outermost element. Designer-canvas pages (builder, report-designer, dashboard-designer) legitimately need `h-screen flex flex-col` *but only inside* the header strip — the outer wrapper should still not fight the parent container.

---

### 1.2 Page header — mostly consistent, three deviations

**Canonical pattern (11/14 list pages):**
```html
<div class="bg-white border-b border-gray-200 px-6 py-4">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-2xl font-bold text-gray-900 flex items-center gap-3">
        <i class="ph-duotone ph-{icon} text-blue-600"></i>
        Page Title
      </h1>
      <p class="text-sm text-gray-600 mt-1">Subtitle</p>
    </div>
    <button class="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg …">
      Primary CTA
    </button>
  </div>
</div>
```

**Deviations:**

| Page | Deviation | Fix |
|---|---|---|
| `companies.html` | Uses `h2` not `h1` | Change to `h1` |
| `audit.html` | Uses `h2` not `h1` | Change to `h1` |
| `profile.html` | Uses `h2` not `h1` | Change to `h1` |
| `settings.html` | Uses `h2` not `h1` | Change to `h1` |
| `dashboards-list.html` | No `bg-white border-b` header wrapper; uses raw `container mx-auto p-6` | Wrap in canonical header pattern |
| `nocode-modules.html` | Header uses `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8` and `py-6`; icon is `ph-bold` not `ph-duotone`; font-size `text-3xl` vs standard `text-2xl` | Normalise to canonical header |
| `branches.html` / `departments.html` | CTA is a non-interactive badge (`<span>`) instead of an action button | Replace with Add Branch / Add Department buttons — API endpoints exist |
| `tenants.html` | Adds `style="margin: -1.5rem"` to fight the parent padding | Remove inline style; fix at layout level |

---

### 1.3 Icon colour — inconsistent accent colours

Every page header icon should be `text-blue-600` (the brand primary) *unless* the page belongs to a specific NoCode domain with its own accent. Currently:

| Page | Icon colour | Status |
|---|---|---|
| Most pages | `text-blue-600` | ✅ Correct |
| `nocode-automations.html` | `text-green-600` | ⚠️ Acceptable (automation domain) — document as intentional |
| `nocode-workflows.html` | `text-purple-600` | ⚠️ Acceptable (workflow domain) |
| `nocode-lookups.html` | `text-orange-600` | ⚠️ Acceptable (lookup domain) |
| `report-designer.html` | `text-emerald-600` | ❌ Inconsistent — reports use blue everywhere else; change to `text-blue-600` |
| `dashboard-designer.html` | `text-violet-600` | ❌ Inconsistent — dashboards use blue everywhere else; change to `text-blue-600` |

**Colour-domain map (adopt as standard):**
- Blue (`blue-600`): default for all management pages
- Green (`green-600`): automation rules
- Purple (`purple-600`): workflows
- Orange (`orange-600`): lookups / reference data
- Emerald → consolidate to Blue for report/dashboard pages

---

### 1.4 CTA button style — two patterns in use

**Pattern A** (preferred — 8 pages): `inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 active:bg-blue-800 shadow-sm hover:shadow-md transition-all font-medium`

**Pattern B** (legacy — 5 pages): `px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2`

Differences: Pattern A has `shadow-sm hover:shadow-md`, `active:` state, `px-5 py-2.5` (larger touch target), `font-medium`. Both are functional but the visual weight differs visibly.

**Fix:** migrate all list-page CTAs to Pattern A. Designer-canvas pages (builder, report-designer) keep their context-specific toolbar buttons.

---

### 1.5 Card / content wrapper

All page body sections use `bg-white rounded-lg shadow-sm p-6` — consistent. One deviation:

- `dashboards-list.html`: uses `btn btn-primary` / `btn btn-secondary` CSS classes that do **not exist** in the Flex component system. These are global class names that likely resolve to nothing or are pulled from a stale stylesheet. **Fix:** replace with Tailwind utility classes matching Pattern A.

---

## 2. Heading Hierarchy

| Issue | Pages | Fix |
|---|---|---|
| `h2` used as page title (should be `h1`) | companies, audit, profile, settings | Change to `h1` |
| `h1` with `text-3xl` (should be `text-2xl`) | nocode-modules | Normalise to `text-2xl font-bold` |
| No heading at all (shell/dynamic mount) | modules, auth-policies, settings-security | These are JS-rendered — the component must inject an `h1` itself; verify SecurityAdmin does so |
| Dashboard home has no `h1` | dashboard | The welcome card uses `h3` as its first heading — add a visually-hidden `h1 class="sr-only"` for screen readers |

---

## 3. Backend Capabilities Not Surfaced

Cross-referenced with PM review findings and current implementation status:

### 🔴 Still missing (not yet implemented)

| Screen | Missing feature | Backend endpoint | Effort |
|---|---|---|---|
| `audit.html` | Summary stats bar (total events today, failures, top actors) | `GET /audit/stats/summary` | Low |
| `audit.html` | Row click → detail panel with full before/after diff | `GET /audit/{log_id}` | Low |
| `users.html` | Effective permissions panel on user detail | `GET /users/{id}/permissions` | Low |
| `dashboards-list.html` | Share + Snapshot actions on each dashboard | `POST /dashboards/{id}/shares`, `POST /dashboards/{id}/snapshots` | Medium |
| `reports-list.html` | Export button on report viewer | `POST /reports/{id}/execute/export` | Low |
| `scheduler.html` | Job execution log viewer | `GET /jobs/{id}/executions`, `GET /executions/{id}/logs` | Medium |
| `nocode-automations.html` | Execution history tab | `GET /automations/executions` | Medium |
| `nocode-automations.html` | Rule test panel (per-rule inline) | `POST /rules/{id}/test` | Medium |
| `builder.html` | Version history sidebar | `GET /builder-pages/{id}/versions` | Medium |
| `nocode-workflows.html` | Simulate workflow panel | `POST /workflows/{id}/simulate` | Medium |
| `rbac.html` | Permission matrix table (role × permission group) | `GET /permissions/grouped` | Medium |

### ✅ Confirmed implemented (close from backlog)

| Screen | Feature | Status |
|---|---|---|
| `nocode-data-model.html` | Publish button + migration diff modal | ✅ Fully implemented in `nocode-data-model.js` |
| `settings-notifications.html` | Honesty banner | ✅ Shipped in Epic 24 P0 |
| `login.html` | Forgot-password flow | ✅ Shipped in Epic 24 P0 |

---

## 4. Stub / Placeholder Screens

These screens show "Coming Soon" or static content where users expect functionality:

| Screen | Current state | Recommendation |
|---|---|---|
| `settings-integration.html` | Blue info box: "Coming Soon" | Either build OAuth/API-key cards or hide from nav entirely; do not show a placeholder — it damages trust |
| `settings-menu-sync.html` | Internal tool exposed in Settings nav | Move to superadmin-only area; remove from end-user Settings sidebar |
| `sample-reports-dashboards.html` | Purpose unclear from header scan | Audit: if it's a demo/seed page, hide from nav; if it's a real feature, give it a proper header |
| `builder-showcase.html` | Dev tool in nav | Remove from nav (Epic 24 story 24.7.1 — already designed) |
| `components-showcase.html` | Dev tool in nav | Same |
| `flex-layout-sandbox.html` | Dev tool in nav | Same |
| `datatable.html` | Dev tool in nav | Same |

---

## 5. Specific Per-Screen Recommendations

### `dashboard.html` (Home)
- No primary CTA or "quick action" buttons — users land here after login with nothing to do
- **Add:** 3-column quick-action row: "Create Entity", "Build Page", "New Report" → each linking to the respective route

### `branches.html` / `departments.html`
- CTA is a read-only badge ("Operations Network", "Workforce") not a button
- **Add:** "Add Branch" / "Add Department" primary action buttons — both routers support POST
- **Add:** breadcrumb showing parent Company (requires a GET /companies call on mount)

### `nocode-modules.html`
- Uses `text-3xl font-bold` header (vs standard `text-2xl`) and `ph-bold` icon variant
- Content area uses `max-w-7xl mx-auto` full-page centering that conflicts with the main content scroll area
- **Fix:** normalise header; remove max-w constraint from the outermost wrapper

### `rbac.html`
- Keyboard shortcut hint (`Shift+?`) is unique to this page — no other page exposes shortcuts
- Company selector dropdown is hidden by default for most users — good, but the hiding logic should be documented to prevent regression

### `auth-policies.html` / `settings-security.html`
- Both mount the same `SecurityAdmin` component
- No visible page `h1` until the component finishes loading (spinner shows first)
- **Fix:** inject a static `<h1>` in the HTML skeleton before the spinner, so heading is available immediately for screen readers and browser history

### `report-designer.html`
- Uses `<button id="back-to-reports">` ← back-navigation with no keyboard focus ring
- `text-xl` title (vs `text-2xl` everywhere else) — make it consistent
- Export button is missing from the toolbar (PM P1 item)

### `dashboard-designer.html`
- Same back-navigation issue as report-designer
- Share and Snapshot toolbar buttons missing (PM P1 item)

---

## 6. Accessibility Quick-Wins (0-effort fixes)

| Item | Fix |
|---|---|
| All `<i class="ph …">` icon buttons with no `aria-label` | Every icon-only button needs `aria-label` |
| `dashboard.html` missing `h1` | Add `<h1 class="sr-only">Dashboard</h1>` |
| `settings-integration.html` "Coming Soon" blue box | Add `role="status"` so screen readers announce it |
| `login.html` reset-confirm view | Already has `autofocus` on new-password input ✅ |

---

## 7. Priority Order for Fixes

| Priority | Item | Effort | Impact |
|---|---|---|---|
| P0 | `h2`→`h1` on companies, audit, profile, settings (4 files, 1-line each) | Trivial | SEO + a11y |
| P0 | `<section>`→`<div>` on branches, departments | Trivial | Semantic correctness |
| P0 | Remove `style="margin: -1.5rem"` from tenants.html | Trivial | Layout integrity |
| P0 | Add "Add Branch" / "Add Department" buttons | Low | Exposes existing API |
| P1 | Migrate remaining CTAs from Pattern B → Pattern A (5 pages) | Low | Visual consistency |
| P1 | `dashboards-list.html` — fix `btn btn-primary` to Tailwind classes | Low | Avoids broken styles |
| P1 | `nocode-modules.html` header normalisation | Low | Visual consistency |
| P1 | `report-designer.html` icon colour + font-size fix | Trivial | Visual consistency |
| P1 | `dashboard-designer.html` icon colour fix | Trivial | Visual consistency |
| P2 | Audit stats bar + row detail panel | Medium | Backend capability exposure |
| P2 | Job execution log viewer | Medium | Backend capability exposure |
| P2 | Automation execution history + test panel | Medium | Backend capability exposure |
| P2 | Builder version history sidebar | Medium | Backend capability exposure |
| P2 | Report export button | Low | Backend capability exposure |
| P3 | Hide stub/dev-tool screens from nav (24.7.1) | Low | Professionalism |
| P3 | Dashboard quick-action row | Low | Onboarding |
| P3 | settings-integration.html: build or hide | Medium | Trust |
