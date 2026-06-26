# impl-notes-T-24-022

**Task**: Add "History" button to job rows; open Job History FlexDrawer.

## Implementation location
`frontend/assets/js/scheduler-log-viewer.js` — already existed and was largely complete.
Enhancements added in this task:

### History button
- `attachButtons()` injects `.btn-view-history` button with `ph-clock-clockwise` icon into
  each `[data-job-id]` row's last cell. No duplicate injection (guard check).
- `currentJobId` module-scope var set in `openForJob(jobId, jobName)`.

### FlexDrawer
- `#job-history-drawer`: fixed right-side panel, width 680px, slide-in transition.
- `role="dialog"`, `aria-modal="true"` (implied by fixed overlay), `aria-labelledby` via
  `h2.text-lg` "Run history" heading.

### Focus management & Escape key (T-24.022 completion)
- `_setupEscapeAndFocus()` called on open: registers `keydown` Escape handler.
- Focuses `#drawer-close` button within 80ms of open.
- On close: removes Escape handler, returns focus to triggering button.

### FlexTable (compact, clickable rows)
- Started, Status (aria-label="Status: {value}"), Duration, Trigger columns.
- Keyboard: `tabindex=0` on each `<tr>`, Enter opens log, ArrowUp/Down navigates.

### Empty state
`ph-clock` icon + "No runs yet" text.

### FlexSpinner
`#exec-loading` div with `ph-spinner animate-spin` shown during fetch.

## Files changed
- `frontend/assets/js/scheduler-log-viewer.js`
