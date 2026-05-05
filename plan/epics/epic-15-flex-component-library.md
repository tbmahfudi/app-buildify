# Epic 15 — Flex Component Library

> Zero-dependency vanilla JS Web Components library forming the UI foundation for all platform pages.

---

## Feature 15.1 — Layout Components `[DONE]`

### Story 15.1.1 — Layout Component Suite `[OPEN]`

#### Backend
*No backend story — this is a frontend-only library.*

#### Frontend (UILDC v1.0 — meta-design)
*As a frontend developer building any platform page, I want 9 declarative layout primitives (FlexStack, FlexGrid, FlexSidebar, FlexSplitPane, FlexContainer, FlexSection, FlexCluster, FlexToolbar, FlexMasonry) that compose into any layout via HTML attributes alone, so that page structure is consistent, responsive, and free of bespoke CSS.*

- **No dedicated route** — these primitives are imported on every platform page. The "design" is the components themselves.
- **Identity (corrected 2026-04-29 by C3 build verification)**: Plain ES6 classes that **optionally** extend `BaseComponent` (`frontend/assets/js/core/base-component.js`) for state, events, and option-merging helpers. **NOT** Web Components / `customElements.define`. Existing components are mixed: `flex-alert.js`/`flex-badge.js`/`flex-checkbox.js`/`flex-accordion.js` extend `BaseComponent`; `flex-card.js`/`flex-modal.js`/`flex-tabs.js` are standalone with the same `(container, options)` ctor shape. New layout primitives in this story extend `BaseComponent` for consistency. Constructor signature: `new FlexFoo(containerSelectorOrElement, optionsObject)`. One file per component at `frontend/assets/js/components/flex-<name>.js` (flat — same directory as the existing UI suite from 15.1.2 DONE).
- **Canonical component list** (matches `audit-15` story 15.1.1 evidence): `flex-stack`, `flex-grid`, `flex-sidebar`, `flex-split-pane`, `flex-container`, `flex-section`, `flex-cluster`, `flex-toolbar`, `flex-masonry`. NOT in scope: `flex-modal`, `flex-drawer`, `flex-tabs`, `flex-card` — these are part of 15.1.2 (UI Component Suite, DONE) and 15.1.3 (Form Suite, DONE). See `> Open question` below.

##### Cross-cutting contracts (all 9 components) (corrected 2026-04-29)

- **Styling: Tailwind utility classes**, NOT CSS custom properties. Each component composes Tailwind classes from its options and applies them to `this.container`. The earlier UILDC draft promised a `--flex-<name>-*` custom-property API — that contradicts the existing convention (verified against `flex-alert.js`, `flex-card.js`). Spacing/color tokens map to Tailwind's existing scale (`gap-1..8`, `p-1..8`, `max-w-2xl..7xl`, etc.).
- **Responsive contract**: `FlexResponsive` singleton (already shipped per 15.1.2 DONE) at `frontend/assets/js/utilities/flex-responsive.js` — `getInstance()` returns the singleton; `.onBreakpointChange(callback)` subscribes; callback receives `(breakpoint, previousBreakpoint)` where breakpoint is `xs|sm|md|lg|xl|2xl`. Breakpoints come from `frontend/assets/js/core/constants.js BREAKPOINTS`. Layout components that depend on viewport size subscribe in `init()` and re-render in the callback.
- **Slot model**: layout primitives wrap their existing children in-place — they do NOT use `<slot>` (no Shadow DOM). Children stay in light DOM; the component just adds Tailwind classes to the container. Components needing distinct slots (FlexSidebar, FlexSplitPane, FlexSection actions, FlexToolbar start/end) read children by `data-slot="<name>"` attribute or by container index.
- **Accessibility default**: layout primitives carry no implicit ARIA role. Exceptions per-component (FlexToolbar `role="toolbar"`, FlexSplitPane drag handle `role="separator"`, FlexSection real heading element).
- **States**: presentation-only by default; interactive primitives (FlexSplitPane, FlexSidebar collapse, sticky FlexToolbar) declare states explicitly. **No `loading` / `empty` / `error` states** — these primitives wrap data UIs, they are not data UIs.

##### Per-component spec

- **`FlexStack`** — vertical or horizontal flex arrangement
  - attrs: `direction` (vertical/horizontal, default vertical) · `gap` (xs/sm/md/lg/xl, default md) · `align` (start/center/end/stretch, default stretch)
  - slot: default
  - states: none
  - edge cases: 0 children → empty container, no gap; 1 child → no gap applied

- **`FlexGrid`** — responsive CSS grid wrapper
  - attrs: `columns` (single number `"3"` OR responsive `"1 2 3"` mapping to sm/md/lg) · `gap` (token)
  - slot: default
  - states: none
  - edge cases: `columns="0"` → falls back to 1 column; fewer responsive entries than breakpoints → repeats last entry

- **`FlexSidebar`** — fixed-width sidebar + flex content
  - attrs: `side` (left/right, default left) · `sidebar-width` (CSS length) · `content-min-width` (CSS length — collapse threshold)
  - slots: named `sidebar`; default slot for content
  - states: `collapsed` when viewport < `sidebar-width` + `content-min-width` (sidebar hidden, content spans full width)
  - edge cases: missing `sidebar` slot → behaves as full-width content container

- **`FlexSplitPane`** — draggable two-pane split
  - attrs: `initial-split` (default `"50%"`) · `min-left` · `min-right` (CSS lengths)
  - slots: named `left`, `right`
  - methods: `setSplit(percent)` — programmatic resize
  - events: `split-change` (detail: `{ leftPct, rightPct }`)
  - states: `dragging` (cursor `col-resize`, transitions disabled) · `constrained` (drag clamped at min-left/min-right)
  - accessibility: drag handle has `role="separator"`, `aria-orientation="vertical"`, `aria-valuenow={percent}`
  - edge cases: viewport narrower than `min-left + min-right` → split forced to 50/50, drag disabled

- **`FlexContainer`** — bounded-width wrapper with horizontal centering
  - attrs: `max-width` (CSS length, default 1200px) · `padding` (token, default md)
  - slot: default
  - states: none
  - edge cases: viewport < `max-width` → spans full viewport with padding

- **`FlexSection`** — semantic section wrapper with optional title
  - attrs: `title` (string, optional) · `level` (h1–h6, default h2)
  - slots: default; named `actions` (rendered inline with title, right-aligned)
  - states: none
  - accessibility: renders a real heading element at the specified level when `title` is set

- **`FlexCluster`** — wrap-when-overflow inline cluster
  - attrs: `gap` (token) · `align` (start/center/end, default start) · `justify` (start/center/end/space-between, default start)
  - slot: default
  - states: none
  - edge cases: child with intrinsic min-width > container → wraps to its own line

- **`FlexToolbar`** — horizontal action bar
  - attrs: `position` (top/bottom, default top) · `sticky` (boolean — sticks to viewport edge on scroll)
  - slots: named `start` (left-aligned), `end` (right-aligned); default for inline children
  - states: `stuck` when `sticky=true` and scrolled past origin (adds shadow class)
  - accessibility: `role="toolbar"`; children should be buttons or links

- **`FlexMasonry`** — column-balanced masonry grid
  - attrs: `column-width` (CSS length, default 240px) · `gap` (token)
  - slot: default
  - states: none
  - edge cases: column count = `floor(viewport / column-width)`, minimum 1

##### Interactions (cross-cutting)

- drag `FlexSplitPane` handle: panes resize live; clamp at min-left/min-right; emits `split-change` on release
- viewport resize crossing `FlexSidebar` collapse threshold: sidebar collapses without explicit user action
- `FlexResponsive.breakpointChange`: subscribed primitives re-render their breakpoint-dependent attrs (`FlexGrid columns`, sticky `FlexToolbar` shadow)
- `FlexToolbar` `sticky=true` + scroll past origin: adds `stuck` class (CSS triggers shadow)

> **Escalation to B1 (Software Architect)**: `arch-21.md` §2.1 and §7 Reference Map list `flex-card`, `flex-modal`, `flex-drawer`, `flex-tabs` as NEW components for this story. They are NOT — they are part of stories 15.1.2 (UI Suite DONE) and 15.1.3 (Form Suite DONE). The canonical 9 layout-suite components are the ones above (matching `audit-15-flex-component-library.md` story 15.1.1). Also: `arch-21.md` §2.1 mentions a new directory `frontend/components/flex-layout/` — the actual convention is `frontend/assets/js/components/` (flat, alongside existing components). Recommend B1 correction to arch-21 §2.1 + §7. *Logged here per AGENT_STANDARD §6 anti-pattern "Escalation avoidance".*

---

### Story 15.1.2 — UI Component Suite `[DONE]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a frontend developer, I want 16 ready-made UI components (FlexModal, FlexDataGrid, FlexTable, etc.) that work consistently, emit standard events, and are accessible out of the box, so that I don't rebuild common interactions from scratch.*
- No dedicated route — UI components are used on every platform page; no isolated UI

- Component specs:

  - `FlexModal`: attrs — `size` (sm/md/lg/xl/full); methods — `open()` / `close()`; events — `confirm` / `cancel`; focus-trapped; backdrop click closes (configurable)
  - `FlexDrawer`: attrs — `position` (left/right/top/bottom) | `size`; events — `opened` / `closed`
  - `FlexTable`: attrs — `columns` (JSON array) | `data`; events — `sort` / `row-click` / `bulkAction`; optional checkbox column for bulk selection; sortable columns
  - `FlexDataGrid`: extends FlexTable — adds server-side pagination, filtering toolbar, loading skeleton
  - `FlexTabs`: attrs — `tabs` (JSON `[{label, id}]`); events — `tabChange`; keyboard: arrow-key navigation
  - `FlexStepper`: attrs — `steps` | `activeStep`; methods — `next()` / `prev()` / `goTo(n)`; events — `stepChange`
  - `FlexPagination`: attrs — `total` / `page` / `page-size`; events — `pageChange`
  - `FlexAlert`: attrs — `type` (info/success/warning/error) | `dismissible`; events — `dismissed`
  - `FlexBadge`: attrs — `variant` (solid/outline) | `color` (primary/success/warning/danger/info/neutral)
  - `FlexTooltip`: wraps any element; attrs — `content` | `position` (top/bottom/left/right); shown on hover/focus

---

### Story 15.1.3 — Form Component Suite `[DONE]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a frontend developer building forms, I want form input components (FlexInput, FlexSelect, FlexCheckbox, FlexRadio, FlexTextarea) that manage their own validation state and emit standard events, so that building forms is consistent and all edge cases are handled.*
- No dedicated route — form components are used in every create/edit form across the platform

- Shared base API (all form components):
  - attrs: `name` | `value` | `label` | `placeholder` | `disabled` | `required` | `error` | `helper`
  - events: `change` ({name, value}) | `blur` | `focus`
  - methods: `validate()` → `{valid: bool, message: string}`; `reset()` clears value and error state

- Component specs:

  - `FlexInput`: attrs — `type` (text/email/number/password/tel/url) | `icon-left` | `icon-right` | `max-length` (shows char counter); password type adds show/hide toggle
  - `FlexSelect`: attrs — `options` (JSON `[{value, label}]` or `[{value, label, group}]`) | `multiple` | `searchable` (adds filter input in dropdown) | `loading` (shows spinner)
  - `FlexTextarea`: attrs — `rows` | `max-length` (char counter) | `auto-resize` (grows with content)
  - `FlexCheckbox`: attrs — `indeterminate` (tri-state); supports `label` slot for rich label content
  - `FlexRadio`: attrs — `options` (JSON array) | `layout` (vertical/horizontal); emits `change` with selected value

---

## Feature 15.2 — Planned Components `[PLANNED]`

### Story 15.2.1 — FlexDatepicker Component `[PLANNED]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a frontend developer building a date input field, I want to use `<flex-datepicker>` instead of a plain text input, so that users get a calendar picker and I get ISO 8601 output without custom parsing.*
- No dedicated route — `FlexDatepicker` is a form component; used in any page with date/datetime fields

- `FlexDatepicker` component spec:
  - attrs: `type` (date/datetime/time) | `value` (ISO 8601) | `min` | `max` | `name` | `label` | `error` | `required` | `disabled`
  - events: `change` ({name, value: ISO string})
  - renders: text input that opens a calendar popup on focus
  - calendar header: left/right arrows (month navigation); click month/year header → year/decade selection mode
  - `min` / `max` enforcement: out-of-range dates shown muted + non-interactive

- Interactions:
  - focus input: calendar popup opens
  - arrow keys: move day cursor within calendar
  - Enter: selects focused date; popup closes; `change` emitted
  - Escape: closes popup without selecting
  - Tab (type=datetime): moves focus from date picker to time picker portion

- States:
  - disabled: input and calendar non-interactive; muted styling
  - error: red border + error message below input (via `error` attr)
  - out-of-range date: calendar cell muted; click is no-op

---

### Story 15.2.2 — FlexFileUpload Component `[PLANNED]`

#### Backend
*No backend story — frontend library (upload logic depends on the cloud storage API from Epic 19).*

#### Frontend
*As a user attaching a file to a record, I want to drag a file onto a drop zone or click to browse, see a thumbnail preview, and have the upload progress shown, so that attaching files is visual and transparent.*
- No dedicated route — `FlexFileUpload` is a form component; used wherever file attachment is needed

- `FlexFileUpload` component spec:
  - attrs: `accept` (file type filter, e.g. `.pdf,.docx`) | `max-size` (bytes) | `multiple` | `name`
  - events: `upload-complete` ({name, key, url}) | `upload-error`
  - renders: dashed drop zone "Drag files here or click to browse"
  - per-file chip: thumbnail (image) or file-type icon | file name | size | progress bar | × remove

- Interactions:
  - drag file onto drop zone or click to browse: file added to queue; chip renders
  - rejected file type: inline error below drop zone "File type not allowed"
  - file exceeds `max-size`: rejected before upload; chip shows "File too large (max Xmb)"
  - upload in progress: chip progress bar updates via `XMLHttpRequest.onprogress`; component calls `PUT [presigned_url]` directly
  - click × on chip: removes file; cancels in-progress upload

- States:
  - uploading: chip shows progress bar filling 0–100%
  - complete: chip changes to green "Uploaded" state; `upload-complete` event emitted
  - error: chip shows red border + "Retry" FlexButton(ghost)

---

### Story 15.2.3 — FlexForm Component `[PLANNED]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a frontend developer building a form, I want `<flex-form>` to orchestrate validation and error display across all its child Flex inputs, so that form submission logic is centralized and consistent.*
- No dedicated route — `FlexForm` is a form orchestration component; used on every create/edit page

- `FlexForm` component spec:
  - attrs: `loading` (disables all child inputs; shows spinner on submit button)
  - methods: `validate()` → `[{field, message}]`; `showFieldErrors(errors[])` → sets `error` attr on matching children by `name`; `reset()` → calls `reset()` on every child
  - events: `submit` (fired only when `validate()` returns empty array)
  - usage: `<flex-form><flex-input name="email"></flex-input>...</flex-form>`

- Interactions:
  - form submit attempt: `validate()` called on all children → if errors, each child's `error` attr set; first errored field scrolled into view; `submit` event NOT fired
  - API 400 response: caller calls `form.showFieldErrors(response.errors)` → per-field error states set
  - `loading` attr set: all child inputs disabled; submit button shows spinner

- States:
  - invalid: errored child inputs show red border + message; submit button inactive
  - loading: all child inputs disabled; spinner on submit button
  - reset: all child values and error states cleared

---

### Story 15.2.4 — FlexNotification Component `[PLANNED]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a frontend developer, I want to call `FlexNotification.show({type, message, duration})` and have a toast appear in the configured corner of the screen without managing DOM lifecycle myself, so that toast notifications are consistent across the entire platform.*
- No dedicated route — `FlexNotification` is a singleton mounted once in `main.html`; no isolated UI

- `FlexNotification` component spec:
  - singleton attrs: `position` (top-right/bottom-center/etc.)
  - static method: `FlexNotification.show({type: "success|error|warning|info", title, message, duration: 5000, dismissible: true})`
  - toast layout: colored left border (by type) | type icon | title (bold) | message | × dismiss button (if `dismissible`)
  - progress bar at toast bottom counts down `duration` ms remaining
  - ARIA: `role="alert"` for error/warning (assertive); `role="status"` for success/info (polite)
  - replaces `ui-utils.js` `showToast()`; backwards-compatible wrapper provided

- Interactions:
  - `FlexNotification.show(...)` called: toast animates in at configured position
  - auto-dismiss: toast fades out after `duration` ms
  - click × (dismissible toast): toast removed immediately
  - 6th concurrent toast: oldest toast evicted (FIFO); max 5 visible simultaneously

---

### Story 15.2.5 — FlexProgress Component `[PLANNED]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a frontend developer showing the progress of a CSV import, I want to use `<flex-progress>` with a `value` attribute that I update as chunks are processed, so that users see accurate progress feedback.*
- No dedicated route — `FlexProgress` is a UI component; used wherever progress feedback is needed

- `FlexProgress` component spec:
  - attrs: `type` (bar/circular) | `value` (0–100) | `max` (default 100) | `label` | `indeterminate` | `color` (success/warning/danger; default follows `--flex-color-primary`) | `complete`
  - bar type: filled track + percentage text inside (or label below if `label` set)
  - circular type: SVG ring with percentage in center
  - `indeterminate`: animated shimmer (bar) or spinning circle for unknown-duration operations
  - `complete`: snaps to 100% + brief green-flash "done" animation

---

## Feature 15.3 — Developer Experience for the Library `[PLANNED]`

### Story 15.3.1 — TypeScript Definitions `[PLANNED]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a TypeScript developer using the Flex library, I want `.d.ts` type declaration files for every component, so that I get compile-time type checking and IDE autocomplete.*
- No dedicated route — TypeScript definitions are a developer tooling concern; no UI involved

- Each component has a paired `.d.ts` file: `flex-input.d.ts`, `flex-modal.d.ts`, etc.
- Types cover: `constructor(options: FlexInputOptions)`, all public methods with parameter and return types, event payload types (`FlexInputChangeEvent`, `FlexModalConfirmEvent`, etc.)
- `index.d.ts` at the package root re-exports all component types
- Types validated with `tsc --strict --noEmit` in a CI step

---

### Story 15.3.2 — Storybook Component Explorer `[PLANNED]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a designer reviewing the component library, I want to open a Storybook browser, see each component in all its variants, and interact with them live, so that I can review the design system without running the full platform.*
- Route: `npm run storybook` → `http://localhost:6006` (developer tool; not part of the platform app)
- Layout: Storybook default shell — left sidebar (component tree) | main canvas (story preview) | right panel (Controls + A11y)

- Per component:
  - "Default" story: renders the component with baseline props
  - "Variants" story: renders all `type`, `size`, and `color` combinations in a grid
  - Controls panel: knob per documented attribute; changes reflected live in canvas
  - A11y addon: accessibility score + violation highlights per story

- Composite stories: "Form Example" story — `FlexForm` + multiple `FlexInput` / `FlexSelect` in a realistic layout

- Interactions:
  - click component in sidebar: canvas switches to that component's stories
  - change a Controls knob: canvas re-renders component with updated prop immediately
  - click A11y tab: violations listed with element references and fix suggestions
