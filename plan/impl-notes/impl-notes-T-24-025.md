# impl-notes-T-24-025

**Task**: Add History toolbar button + version list drawer.

## What was done

Implemented in `frontend/assets/js/builder-version-history.js` (pre-existing file, extended).

### History button
`injectButton()` inserts `#btn-version-history` with `ph-clock-clockwise` icon into the
builder toolbar right cluster. Calls `open(pageId, pageName)`.

### FlexDrawer
`#version-history-drawer`: fixed right-side panel, w-80 (320px), slide-in transition,
`overlay=true` behaviour (no canvas reflow).

### Version list (uildc-24 section 5.2)
- `<ul id="vh-items" role="list">` added.
- Each `<li>` gets `role="listitem"` and `aria-label="Version {N}, saved {relative time} by {author}"`.

### Empty state
`ph-files` icon + "No versions saved yet" text.

### Escape key + focus management
- `_openEsc(btn)` registered on drawer open; `Escape` closes drawer.
- Focus moves to `#vh-close` on open.
- Focus returns to triggering button on close.

## Files changed
- `frontend/assets/js/builder-version-history.js`
