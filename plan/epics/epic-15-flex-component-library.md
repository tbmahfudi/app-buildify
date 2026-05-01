# Epic 15 — Flex Component Library

> Zero-dependency vanilla JS Web Components library forming the UI foundation for all platform pages.

---

## Feature 15.1 — Layout Components `[DONE]`

### Story 15.1.1 — Layout Component Suite `[OPEN]`

#### Backend
*No backend story — this is a frontend-only library.*

#### Frontend
*As a frontend developer building a new page, I want to compose complex layouts using declarative HTML elements (FlexStack, FlexGrid, FlexSidebar, etc.) rather than writing custom CSS, so that page structure is consistent and maintainable.*
- No dedicated route — layout components are used on every platform page; no isolated UI

- Component specs:

  - `FlexStack`: attrs — `direction` (vertical/horizontal) | `gap` (xs/sm/md/lg/xl) | `align` (start/center/end/stretch)
  - `FlexGrid`: attrs — `columns` (number or responsive e.g. `"1 2 3"` for sm/md/lg) | `gap`
  - `FlexSidebar`: attrs — `side` (left/right) | `sidebar-width` | `content-min-width`
  - `FlexSplitPane`: attrs — `initial-split` (default "50%") | `min-left` | `min-right`; drag handle resizes panes
  - `FlexContainer`, `FlexSection`, `FlexCluster`, `FlexToolbar`, `FlexMasonry` — general-purpose layout wrappers

- All components expose a `--flex-*` CSS custom property API for spacing and color overrides
- `FlexResponsive` singleton dispatches `breakpointChange` events; layout components re-render at breakpoints sm(640)/md(768)/lg(1024)/xl(1280)

- Interactions:
  - drag `FlexSplitPane` handle: left and right pane widths update live; constrained by `min-left` / `min-right`
  - `FlexResponsive` breakpoint change: layout components receive `breakpointChange` event → re-render to match active breakpoint column config

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
