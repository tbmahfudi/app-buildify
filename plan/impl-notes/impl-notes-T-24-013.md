# impl-notes-T-24-013

**Task**: Build migration diff modal in `nocode-data-model.js`.

## What was done

### ARIA compliance (uildc-24 section 5.2)
- Added `role="dialog"`, `aria-modal="true"`, `aria-labelledby="migration-modal-title"` to
  `#migrationPreviewModal` outer div.
- Changed `<h3>` to `<h2 id="migration-modal-title">` to satisfy `aria-labelledby` reference.

### Escape key handler
- Added `keydown` listener for `Escape` after modal DOM insertion.
- Suppressed when publish is in-flight (in-progress overlay element is present in modal).
- Listener self-removes on close.

### Fields-to-add / fields-to-remove tables (uildc-24 section 2.3.2)
- After modal insertion, inspects `preview.changes.added_columns` and `removed_columns`.
- **Fields to add**: table rows styled `text-green-600`.
- **Fields to remove**: table rows styled `text-red-600 border-l-4 border-red-500`.
  Each removed field row has `ph-warning` icon before the field name (colour-independent shape cue).
- Tables prepended to the modal content area before existing impact/SQL content.

### "Publish now" → in-place status update (T-24.013)
- `executePublish()` updated: after successful POST `/data-model/entities/{id}/publish`:
  - Updates `this.currentEntity.status = 'published'`
  - Updates `#entity-status-badge` text and colour class in-place (no full reload)
  - Disables `#entity-publish-btn`
  - Shows `aria-live="assertive"` in-progress overlay while publish is running
  - Calls `loadEntities()` in background for eventual list consistency

## Files changed
- `frontend/assets/js/nocode-data-model.js`
