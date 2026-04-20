# Epic 15 — Flex Component Library

> Zero-dependency vanilla JS Web Components library forming the UI foundation for all platform pages.

---

## Feature 15.1 — Layout Components `[DONE]`

### Story 15.1.1 — Layout Component Suite `[DONE]`

#### Backend
*No backend story — this is a frontend-only library.*

#### Frontend
*As a frontend developer building a new page, I want to compose complex layouts using declarative HTML elements (FlexStack, FlexGrid, FlexSidebar, etc.) rather than writing custom CSS, so that page structure is consistent and maintainable.*
- 9 layout components available: `FlexStack`, `FlexGrid`, `FlexContainer`, `FlexSection`, `FlexSidebar`, `FlexCluster`, `FlexToolbar`, `FlexMasonry`, `FlexSplitPane`
- `FlexStack`: `direction` attr (vertical/horizontal), `gap` attr (xs/sm/md/lg/xl), `align` attr (start/center/end/stretch)
- `FlexGrid`: `columns` attr (number or responsive e.g. `"1 2 3"` for sm/md/lg), `gap` attr
- `FlexSidebar`: `side` attr (left/right), `sidebar-width` attr, `content-min-width` attr
- `FlexSplitPane`: resizable via drag handle; `initial-split` attr (default "50%"); `min-left` and `min-right` attrs
- All components expose a `--flex-*` CSS custom property API for spacing and color overrides
- `FlexResponsive` singleton dispatches `breakpointChange` events; layout components listen and re-render at breakpoints sm(640)/md(768)/lg(1024)/xl(1280)

---

### Story 15.1.2 — UI Component Suite `[DONE]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a frontend developer, I want 16 ready-made UI components (FlexModal, FlexDataGrid, FlexTable, etc.) that work consistently, emit standard events, and are accessible out of the box, so that I don't rebuild common interactions from scratch.*
- **FlexModal**: `open()` / `close()` methods; `size` attr (sm/md/lg/xl/full); focus-trapped; `confirm` and `cancel` events; backdrop click closes (configurable)
- **FlexDrawer**: `position` attr (left/right/top/bottom); `size` attr; `opened`/`closed` events
- **FlexTable**: `columns` attr (JSON array); `data` attr; sortable columns (click header); `sort` event; `row-click` event; optional checkbox column for bulk selection; `bulkAction` event
- **FlexDataGrid**: extends FlexTable with server-side pagination, filtering toolbar, loading skeleton
- **FlexTabs**: `tabs` attr (JSON array of `{label, id}`); `tabChange` event; keyboard navigation (arrow keys)
- **FlexStepper**: `steps` attr; `activeStep` attr; `next()` / `prev()` / `goTo(n)` methods; `stepChange` event
- **FlexPagination**: `total` / `page` / `page-size` attrs; `pageChange` event
- **FlexAlert**: `type` attr (info/success/warning/error); `dismissible` attr; `dismissed` event
- **FlexBadge**: `variant` attr (solid/outline); `color` attr (primary/success/warning/danger/info/neutral)
- **FlexTooltip**: wraps any element; `content` attr; `position` attr (top/bottom/left/right); shown on hover/focus

---

### Story 15.1.3 — Form Component Suite `[DONE]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a frontend developer building forms, I want form input components (FlexInput, FlexSelect, FlexCheckbox, FlexRadio, FlexTextarea) that manage their own validation state and emit standard events, so that building forms is consistent and all edge cases are handled.*
- All form components share a common base API:
  - Attributes: `name`, `value`, `label`, `placeholder`, `disabled`, `required`, `error`, `helper`
  - Events: `change` (fires with `{name, value}` on every value change), `blur`, `focus`
  - Methods: `validate()` returns `{valid: bool, message: string}`; `reset()` clears value and error
- **FlexInput**: `type` attr (text/email/number/password/tel/url); `icon-left`/`icon-right` attrs; `max-length` attr shows character counter; password type adds show/hide toggle button
- **FlexSelect**: `options` attr (JSON array `[{value, label}]` or `[{value, label, group}]`); `multiple` attr for multi-select; `searchable` attr adds a filter input inside the dropdown; `loading` attr shows a spinner while options load
- **FlexTextarea**: `rows` attr; `max-length` attr with char counter; `auto-resize` attr grows with content
- **FlexCheckbox**: `indeterminate` attr for tri-state; supports `label` slot for rich label content
- **FlexRadio**: `options` attr (JSON array); `layout` attr (vertical/horizontal); emits `change` with selected value

---

## Feature 15.2 — Planned Components `[PLANNED]`

### Story 15.2.1 — FlexDatepicker Component `[PLANNED]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a frontend developer building a date input field, I want to use `<flex-datepicker>` instead of a plain text input, so that users get a calendar picker and I get ISO 8601 output without custom parsing.*
- `<flex-datepicker type="date|datetime|time">` renders a text input that opens a calendar popup on focus
- Calendar navigation: left/right arrows to change month; clicking month/year header enters year/decade selection mode
- `value` attribute: always ISO 8601 (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`)
- `min` / `max` attributes: dates outside range shown in a muted, disabled style; clicking them is a no-op
- Keyboard: arrow keys move the day cursor; Enter selects; Escape closes without selecting; Tab moves to the time picker (if `type=datetime`)
- Integrated in dynamic entity forms for `date` and `datetime` field types
- Shares the same base API (name, value, label, error, required, disabled, change event) as existing form components

---

### Story 15.2.2 — FlexFileUpload Component `[PLANNED]`

#### Backend
*No backend story — frontend library (upload logic depends on the cloud storage API from Epic 19).*

#### Frontend
*As a user attaching a file to a record, I want to drag a file onto a drop zone or click to browse, see a thumbnail preview, and have the upload progress shown, so that attaching files is visual and transparent.*
- `<flex-file-upload>` renders a dashed drop zone: "Drag files here or click to browse"
- `accept` attribute: file type filter (e.g. `.pdf,.docx`); rejected types show an inline error
- `max-size` attribute: files exceeding the limit are rejected before upload with error "File too large (max Xmb)"
- `multiple` attribute enables selecting multiple files; each file shown as a chip with: thumbnail (image) or file-type icon, file name, size, progress bar, × remove button
- Upload progress: the component calls `PUT [presigned_url]` directly; progress bar updates via `XMLHttpRequest.onprogress`
- On upload complete: chip changes to a green "Uploaded" state; emits `upload-complete` event with `{name, key, url}`
- Error state: failed upload shows a red chip with retry button

---

### Story 15.2.3 — FlexForm Component `[PLANNED]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a frontend developer building a form, I want `<flex-form>` to orchestrate validation and error display across all its child Flex inputs, so that form submission logic is centralized and consistent.*
- `<flex-form>` wraps any combination of Flex form components as child elements
- `form.validate()` calls `validate()` on each child component and aggregates `{field, message}` errors; returns the array
- `form.showFieldErrors(errors)` iterates an error array (from the API response), finds each child by `name`, and sets its `error` attribute
- `form.reset()` calls `reset()` on every child component
- `submit` event fired from the form element only when `validate()` returns an empty array
- `loading` attribute disables all child inputs and shows a spinner on the submit button
- Usage pattern: `<flex-form id="myForm"><flex-input name="email" ...></flex-input>...</flex-form>`

---

### Story 15.2.4 — FlexNotification Component `[PLANNED]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a frontend developer, I want to call `FlexNotification.show({type, message, duration})` and have a toast appear in the configured corner of the screen without managing DOM lifecycle myself, so that toast notifications are consistent across the entire platform.*
- `<flex-notification>` is a singleton element mounted once in `main.html`; configured by `position` attribute (top-right/bottom-center/etc.)
- `FlexNotification.show({type: "success|error|warning|info", title, message, duration: 5000, dismissible: true})`
- Toast renders with: colored left border by type, appropriate icon, title (bold), message, × dismiss button (if dismissible)
- Auto-dismiss after `duration` ms; progress bar at the bottom of the toast counts down the remaining time
- Max 5 concurrent toasts; 6th evicts the oldest (FIFO)
- ARIA: `role="alert"` for error/warning (assertive), `role="status"` for success/info (polite)
- Replaces the existing `ui-utils.js` `showToast()` function; backwards-compatible wrapper provided

---

### Story 15.2.5 — FlexProgress Component `[PLANNED]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a frontend developer showing the progress of a CSV import, I want to use `<flex-progress>` with a `value` attribute that I update as chunks are processed, so that users see accurate progress feedback.*
- `<flex-progress type="bar|circular">` with `value` (0–100), `max` (default 100), `label` attributes
- `indeterminate` attribute: animated shimmer (bar) or spinning circle — for operations with unknown duration
- Bar type: shows a filled track with the percentage text inside (or as a label below if `label` set)
- Circular type: SVG ring with percentage in the center
- Color follows CSS custom properties: `--flex-color-primary` by default; `color` attribute overrides (`success`/`warning`/`danger`)
- `complete` attribute: snaps to 100% and plays a brief "done" animation (green flash)

---

## Feature 15.3 — Developer Experience for the Library `[PLANNED]`

### Story 15.3.1 — TypeScript Definitions `[PLANNED]`

#### Backend
*No backend story — frontend library.*

#### Frontend
*As a TypeScript developer using the Flex library, I want `.d.ts` type declaration files for every component, so that I get compile-time type checking and IDE autocomplete.*
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
- Storybook configured in `frontend/storybook/` with `npm run storybook`
- Every implemented component has at minimum a "Default" story and a "Variants" story showing all `type`, `size`, and `color` combinations
- Controls panel: knobs for every documented attribute/property; changes reflected live
- A11y addon: each story displays an accessibility score and highlights any violations
- Story for composite examples: "Form Example" story showing `FlexForm` + multiple `FlexInput` / `FlexSelect` components in a realistic layout
