# impl-notes-T-24-027

**Task**: Implement inline restore confirmation.

## What was done

### Inline confirm row (no second modal)
Each version item has `.action-row` (Preview + Restore buttons) and `.confirm-row` (hidden by
default). Clicking Restore shows confirm-row and hides action-row for that item only.

### Concurrent restore prevention (uildc-24 section 2.6)
When confirm is showing for item N:
- All other `.restore-btn` elements in `#vh-items` get `disabled` attribute + `opacity-50`.
- On Cancel or successful restore, all buttons re-enabled.

### Focus management (uildc-24 section 5.1)
- "Yes, restore" button (`confirm-yes`) receives focus when confirm row appears.
- "Cancel" returns focus to the triggering `restoreBtn`.

### FlexNotification success toast
`showNotification()` renders a green toast with `ph-check-circle` icon.
`builder:version-restored` CustomEvent dispatched so builder.js can reload canvas.

## Files changed
- `frontend/assets/js/builder-version-history.js`
