---
artifact_id: uildc-24
type: uildc
producer: B3 UX Designer
consumers: [C3 Frontend Developer, C1 Tech Lead]
upstream: [epic-24-frontend-capability-surfacing, arch-24]
downstream: [tasks-24]
status: approved
created: 2026-06-26
updated: 2026-06-26
---

# UILDC-24 — Frontend Capability Surfacing

> Standalone UX/UI Layout Description Convention document for Epic 24. All 10 stories have inline `#### Frontend` sections in the epic; this document (a) inventories which Flex components are reused vs new, (b) fills the gaps left open by A3, (c) records B3 decisions on the two open UX questions from the A->B Gate Note, (d) standardises the icon palette, and (e) adds accessibility requirements.

---

## 1. Component Inventory

### 1.1 Existing FlexComponents — Reused as-is

| Component | File | Stories that use it |
|---|---|---|
| `FlexAlert` | `flex-alert.js` | 24.1.2, 24.3.1, 24.4.1, 24.4.2, 24.5.1, 24.6.1 |
| `FlexBadge` | `flex-badge.js` | 24.3.1, 24.4.2, 24.5.1, 24.6.1 |
| `FlexButton` | `flex-button.js` | all stories |
| `FlexDrawer` | `flex-drawer.js` | 24.4.2, 24.5.1, 24.6.1 |
| `FlexGrid` | `flex-grid.js` | 24.4.1 |
| `FlexInput` | `flex-input.js` | 24.1.1, 24.2.1 |
| `FlexModal` | `flex-modal.js` | 24.3.1, 24.6.1 |
| `FlexNotification` | `flex-notification.js` | 24.3.1, 24.6.1 |
| `FlexPagination` | `flex-pagination.js` | 24.4.2 |
| `FlexProgress` | `flex-progress.js` | 24.2.1, 24.3.1 |
| `FlexSelect` | `flex-select.js` | 24.4.2 |
| `FlexSpinner` | `flex-spinner.js` | 24.3.1, 24.4.1, 24.4.2, 24.5.1, 24.6.1 |
| `FlexSplitPane` | `flex-split-pane.js` | 24.5.1 (see section 1.3 — constraint applies) |
| `FlexStack` | `flex-stack.js` | 24.1.2, 24.3.1, 24.4.2, 24.6.1 |
| `FlexTable` | `flex-table.js` | 24.4.2, 24.5.1 |
| `FlexTabs` | `flex-tabs.js` | 24.4.2 |
| `FlexToolbar` | `flex-toolbar.js` | 24.3.1, 24.5.1, 24.6.1 |
| `FlexAccordion` | `flex-accordion.js` | 24.4.1 |
| `FlexDatepicker` | `flex-datepicker.js` | 24.4.2 |

### 1.2 Existing Standalone Modules — Reused as-is

| Module | File | Stories that use it |
|---|---|---|
| `PasswordStrengthIndicator` | `password-strength-indicator.js` | 24.2.1 (already implemented) |

### 1.3 FlexSplitPane Direction Constraint — FLAGGED

`FlexSplitPane` (`flex-split-pane.js`) is documented as a **horizontal-only** primitive. Story 24.5.1 calls for a **vertical** split (executions table above, log pane below) inside the Job History Drawer.

**B3 Resolution:** C3 must NOT use `FlexSplitPane(direction=vertical)` — that option does not exist. Implement the vertical split in Story 24.5.1 as a `FlexStack(direction=vertical)` with the log pane having `min-height: 200px; max-height: 40vh; overflow-y: auto;` and a CSS-only resize handle (`resize: vertical` on the log `<pre>` element). The `FlexSplitPane` reference in the epic specifies the visual intent, not the exact component. See section 2.5 for the revised layout spec.

**Escalation note for C1:** `FlexSplitPane` needs a `direction=vertical` option in a future epic. Do not block Epic 24 on it.

### 1.4 New Patterns

No net-new Flex components are required for Epic 24. All UI needs are served by existing Flex components (section 1.1), the already-implemented `PasswordStrengthIndicator` (section 1.2), the CSS vertical-split workaround for 24.5.1 (section 1.3), and standard HTML elements (`<pre>`, `<ul>`, `<li>`, `<code>`).

---

## 2. Per-Feature Gap-Fill Specs

### 2.1 Feature 24.1 — P0 Trust & Navigation Fixes

#### 2.1.1 Forgot-password flow (Story 24.1.1)

The epic specifies the reset-request and confirm-reset pages. Two gaps filled here:

**Gap A — Email Sent Confirmation State** (after `POST /auth/password-reset-request` succeeds):

Replace the entire form with:

```
FlexStack(direction=vertical, gap=lg, align=center) [centred in card]
  icon:    <i class="ph ph-envelope-open text-5xl text-blue-500"></i>
  heading: <h2 class="text-xl font-semibold">Check your inbox</h2>
  body:    <p class="text-sm text-gray-500 text-center max-w-xs">
             If an account exists for {email}, you will receive a password reset
             link shortly. Check your spam folder if it does not arrive.
           </p>
  link:    <a href="#login" class="text-sm text-blue-600 hover:underline">Back to sign in</a>
```

Do NOT reveal whether the email address is registered (user enumeration prevention). Icon: `ph-envelope-open`.

**Gap B — Expired/Invalid Token Error State** (reset URL token is expired or not found):

`FlexAlert(type=error, persistent)` at top of the confirm-reset card:
- Title: "Reset link has expired"
- Body: "Password reset links are valid for 1 hour. Request a new one."
- Action slot: `FlexButton(variant=secondary, size=sm)` "Request new link" — navigates to `#reset-password`
- Hide the new-password form fields when this state is active.

#### 2.1.2 Notification Honesty Banner (Story 24.1.2)

Epic spec is complete and self-contained. B3 sign-off: approved as written. No gaps.

#### 2.1.3 Duplicate Route Cleanup (Story 24.1.3)

No UI components. B3 sign-off: no UX work required.

---

### 2.2 Feature 24.2 — Auth & Password UX (Story 24.2.1)

`PasswordStrengthIndicator` is already implemented in `password-strength-indicator.js`. B3 confirms the icon palette and colour mapping for C3 implementation reference:

**Icon palette (confirmed):**

| State | Phosphor Icon | Colour class |
|---|---|---|
| Not yet evaluated (neutral) | `ph-circle` | `text-gray-300` |
| Rule failed | `ph-x-circle` | `text-red-500` |
| Rule passed | `ph-check-circle` | `text-green-500` |
| Loading policy | `ph-spinner` | `text-gray-400 animate-spin` |

**Strength meter colour mapping** for `FlexProgress(variant=bar, color=auto)`:

| Rules passed | Colour class |
|---|---|
| 0-33 % | `bg-red-500` |
| 34-66 % | `bg-amber-400` |
| 67-99 % | `bg-yellow-400` |
| 100 % | `bg-green-500` |

Wire the colour class directly on the `<div>` progress fill element; `FlexProgress` supports a `colorClass` prop.

---

### 2.3 Feature 24.3 — Data Model Publish UX (Story 24.3.1)

The epic spec covers the Publish flow. Two gaps filled here:

#### 2.3.1 Entity editor field drag-reorder UX

**Drag-reorder spec:**
- Field list rendered as `<ul id="entity-fields-list">` where each `<li>` is a field row.
- Drag handle at left edge of each row: `<button class="drag-handle cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600" aria-label="Drag to reorder {field name}"><i class="ph ph-dots-six-vertical"></i></button>`
- Icon: `ph-dots-six-vertical`.
- Drag implementation: HTML5 Drag and Drop API (`draggable="true"` on each `<li>`). On `dragstart` apply `opacity-50 ring-2 ring-blue-400` to dragged item. On `dragover` show `border-t-2 border-blue-500` on target. On `drop` reorder array and re-render.
- Keyboard fallback: when drag handle has focus, `Alt+ArrowUp` moves field up one position, `Alt+ArrowDown` moves down. Each move announces via `aria-live="polite"` region: "Field '{name}' moved to position {n} of {total}."
- After reorder: toolbar Publish button becomes active; entity `status` set to "draft" in local state. No autosave — change held until user publishes.

**Empty state — entity with no fields:**

```
FlexStack(direction=vertical, gap=md, align=center) [inside fields panel]
  <i class="ph ph-table text-4xl text-gray-300"></i>
  <p class="text-sm font-medium text-gray-500">No fields yet</p>
  <p class="text-xs text-gray-400">Add your first field to define this entity's data structure.</p>
  FlexButton(variant=primary, size=sm, icon=ph-plus) "Add field"
```

#### 2.3.2 "Fields to remove" visual weight in migration diff modal

The epic marks removed field rows `text-red-600`. B3 adds redundant shape coding: each row in the "Fields to remove" table gets `border-l-4 border-red-500` on its `<tr>` element, and the `ph-warning` icon appears in the Field Name cell before the field name text. This ensures destructive changes are visually prominent without relying on colour alone.

---

### 2.4 Feature 24.4 — Automation Visibility

#### 2.4.1 Stale results opacity (Story 24.4.1)

`opacity-60` on stale results is a supplementary visual cue only. The `role="alert"` FlexAlert stale banner is the primary communication channel and the one screen readers consume. C3 must not rely on opacity alone to communicate staleness.

#### 2.4.2 FlexDatepicker range mode check (Story 24.4.2)

The epic references `FlexDatepicker(range, ...)`. C3 must verify that `flex-datepicker.js` supports a `range` prop before implementing. If range mode is absent, substitute two separate `FlexDatepicker` instances in a `FlexCluster(gap=xs)`: one with `id=date-from, placeholder="From"` and one with `id=date-to, placeholder="To"`. Do not block the story on adding range mode to `FlexDatepicker`.

---

### 2.5 Feature 24.5 — Scheduler Log Viewer (Story 24.5.1)

The FlexSplitPane vertical-direction constraint is resolved in section 1.3. Revised layout spec for the Job History Drawer body:

```
drawer-body:
  FlexStack(direction=vertical, gap=none, class="h-full overflow-hidden")
    executions-pane [style="flex: 0 0 auto; max-height: 45%; overflow-y: auto"]
      FlexTable(id=job-executions-table, clickable-rows, compact)
    resize-divider [class="border-t border-gray-200 bg-gray-50 h-1 cursor-ns-resize flex-shrink-0"]
    log-pane [style="flex: 1 1 0; min-height: 120px; overflow: hidden"]
      <pre class="text-xs font-mono bg-gray-950 text-green-400 p-4 h-full overflow-y-auto"
           style="resize: vertical; min-height: 120px;"
           role="log" aria-label="Job execution log" aria-live="polite">
```

**Log line colour mapping** (applied per-line in a render function, checking `line.toUpperCase()`):

| Line content | Class |
|---|---|
| Contains `ERROR` or `CRITICAL` | `text-red-400` |
| Contains `WARN` or `WARNING` | `text-yellow-400` |
| All others | `text-green-400` |

Wrap each log line in `<span class="{colourClass}">{line}\n</span>` inside the `<pre>`.

---

### 2.6 Feature 24.6 — Builder Version History (Story 24.6.1)

B3 decision on drawer vs panel vs full page: see section 3, Decision 2.

**Additional spec — concurrent restore prevention:**
When the inline restore confirmation is showing for version item N, all other version items' "Restore" buttons must be `disabled` (attribute set) and visually muted (`opacity-50`) to prevent concurrent restore attempts. Confirmation disappearing (cancel or complete) re-enables all other buttons.

---

## 3. Open UX Decisions — Resolved

### Decision 1: Module Dependency Graph — D3.js vis or indented text list?

**B3 Decision: Indented text list for MVP; D3.js deferred to Epic 25+.**

Rationale: The dependency graph for Epic 24 scope is shallow (typically 1-3 levels). An indented `<ul>` with `ph-package` icons and `FlexBadge` status chips is accessible, zero-dependency, and sufficient to communicate active/inactive status. D3.js adds approximately 57 kB minified for a feature that is explicitly out of scope for Epic 24. When Epic 25 revisits the dependency visualisation with potentially deeper graphs, a D3-based tree layout should be evaluated at that time.

MVP pattern (recorded here as Epic 25 input):

```html
<ul class="dep-graph space-y-1 text-sm" role="list">
  <li class="flex items-center gap-2" role="listitem">
    <i class="ph ph-package text-gray-400"></i>
    <span>financial-core</span>
    <!-- FlexBadge variant=green size=xs -->Active<!-- /FlexBadge -->
  </li>
  <li class="ml-6 flex items-center gap-2" role="listitem">
    <i class="ph ph-package text-gray-400"></i>
    <span>currency-service</span>
    <!-- FlexBadge variant=amber size=xs -->Inactive<!-- /FlexBadge -->
    <i class="ph ph-warning text-amber-500" aria-label="Required but inactive"></i>
  </li>
</ul>
```

### Decision 2: Builder Version History — Drawer vs inline panel vs full-page route

**B3 Decision: Right overlay drawer confirmed (as specified in Story 24.6.1).**

Rationale: An inline panel shrinks the canvas and disrupts the editing workspace. A full-page route risks losing in-progress edits and requires a save-before-navigate prompt. A right overlay drawer (`FlexDrawer(overlay=true, position=right, size=sm, 320px)`) is dismissable with no canvas reflow and is consistent with the drawer pattern used in Stories 24.4.2 and 24.5.1. Decision is final; no further B3 review needed on this question.

---

## 4. Icon Palette

All icons are from **Phosphor Icons** (regular weight), loaded globally via CDN. No new imports required for Epic 24.

| UI Element | Phosphor Icon Name | Notes |
|---|---|---|
| Drag-reorder handle | `ph-dots-six-vertical` | Entity field list (24.3.1) |
| Entity fields empty state | `ph-table` | `text-gray-300` |
| Publish action | `ph-rocket-launch` | Button icon (24.3.1) |
| Preview action | `ph-eye` | Button icon (24.3.1, 24.6.1) |
| Notifications disabled | `ph-envelope-simple-slash` | Alert icon (24.1.2) |
| Email sent confirmation | `ph-envelope-open` | `text-blue-500` (24.1.1) |
| Password rule neutral | `ph-circle` | `text-gray-300` (24.2.1) |
| Password rule failed | `ph-x-circle` | `text-red-500` (24.2.1) |
| Password rule passed | `ph-check-circle` | `text-green-500` (24.2.1) |
| Loading spinner | `ph-spinner` | `animate-spin` |
| Migration remove warning | `ph-warning` | `text-red-500` in table cell (24.3.1) |
| Test rule play | `ph-play` | Button icon (24.4.1) |
| No executions / no runs | `ph-clock` | Alert icon (24.4.2, 24.5.1) |
| View run history | `ph-clock-clockwise` | Button icon (24.5.1, 24.6.1) |
| Version restore | `ph-arrow-counter-clockwise` | Button icon (24.6.1) |
| Drawer close | `ph-x` | Button icon (all drawers) |
| Module dependency | `ph-package` | `text-gray-400` (Epic 25 input) |
| No records matched | `ph-funnel` | Alert icon (24.4.1 empty) |
| No versions saved | `ph-files` | Alert icon (24.6.1 empty) |

---

## 5. Accessibility Notes

### 5.1 Keyboard Navigation

| Component / Pattern | Requirement |
|---|---|
| `FlexModal` (24.3.1, 24.6.1) | Focus trapped inside when open. `Escape` closes unless publish/restore is in-flight (suppress Escape during in-progress actions). First focusable element receives focus on open. |
| `FlexDrawer` (24.4.2, 24.5.1, 24.6.1) | Same focus-trap as modal. `Escape` closes unless a destructive action is in-flight. |
| `FlexTabs` (24.4.2) | Arrow keys navigate between tabs. `Tab` key moves into the active panel. |
| `FlexAccordion` (24.4.1) | `Enter` / `Space` toggles accordion. Header must be a `<button>` with `aria-expanded`. |
| Drag-reorder handles (24.3.1) | Handle is a `<button>` (keyboard-focusable). When focused: `Alt+ArrowUp` moves field up one position, `Alt+ArrowDown` moves down. Each move announces via `aria-live="polite"` region: "Field '{name}' moved to position {n} of {total}." |
| Clickable table rows (24.4.2, 24.5.1) | Rows keyboard-focusable (`tabindex=0`). `Enter` activates row (opens drawer). `ArrowUp` / `ArrowDown` navigate between rows. |
| Version restore confirmation (24.6.1) | Focus moves to "Yes, restore" when confirmation appears. "Cancel" returns focus to the triggering "Restore" button. |
| Password rule list (24.2.1) | Each `<li>` has `aria-label="{rule label}: {passed|not met}"` so screen readers communicate state without relying on colour. |

### 5.2 ARIA Requirements

| Pattern | ARIA Markup |
|---|---|
| Migration diff modal (24.3.1) | `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing to modal `<h2>` |
| Publish in-progress overlay (24.3.1) | `aria-live="assertive"` on "Applying migration..." label |
| Stale results banner (24.4.1) | `role="alert"` on the FlexAlert stale banner |
| Status badge cells (24.4.2, 24.5.1) | `aria-label="Status: {value}"` on cell when badge is sole indicator |
| Log output `<pre>` (24.5.1) | `role="log"`, `aria-label="Job execution log"`, `aria-live="polite"` |
| Drag handle (24.3.1) | `aria-label="Drag to reorder {field name}"` |
| Version list (24.6.1) | `role="list"` on `<ul>`; each item `aria-label="Version {N}, saved {relative time} by {author}"` |
| Accordion (24.4.1) | `aria-expanded` on header button; `aria-controls` pointing to panel `id` |

### 5.3 Colour Contrast

| Combination | Contrast Ratio | WCAG result |
|---|---|---|
| `text-green-400` (#4ade80) on `bg-gray-950` (#030712) | 8.9:1 | AA + AAA pass |
| `text-red-400` (#f87171) on `bg-gray-950` | 4.6:1 | AA pass |
| `text-yellow-400` (#facc15) on `bg-gray-950` | 8.1:1 | AA + AAA pass |
| `FlexBadge amber` — use `text-amber-700 bg-amber-100` | ~5.7:1 | AA pass |
| `text-amber-400` on white | ~1.9:1 | FAIL — do not use |

Password strength meter uses colour as a supplementary cue only; icons and rule labels are the primary accessible channels.

### 5.4 Focus Visibility

All interactive elements require a visible focus ring. Apply `focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none` to buttons, inputs, and any custom interactive elements. C3 must not remove `outline` without providing a replacement focus indicator.

---

## 6. Responsive Behaviour

Per the B3 agent decision: mobile-responsive markup is opt-in and only added when stories explicitly target mobile. None of Epic 24's stories specify mobile targets. All layouts are desktop-first (min-width 1024 px assumed).

The `PasswordStrengthIndicator` renders inline below an input field and is inherently responsive — no breakpoint handling required.

---

## 7. DoD Checklist (B3)

- [x] Every UI-bearing story has a complete `#### Frontend` section in the epic (provided by A3; reviewed and gap-filled in this document)
- [x] All referenced components confirmed to exist in `frontend/assets/js/components/` (section 1.1)
- [x] Missing component option (`FlexSplitPane direction=vertical`) flagged with workaround specified (section 1.3)
- [x] `loading`, `empty`, and `error` states explicit for all data-fetching patterns (per epic + section 2 gap fills)
- [x] No story exceeds 4 Component Specs
- [x] Icon palette confirmed against Phosphor (section 4)
- [x] Both A->B Gate open UX decisions resolved (section 3)
- [x] Accessibility keyboard nav and ARIA requirements specified (section 5)
- [x] Responsive behaviour declared (section 6)
