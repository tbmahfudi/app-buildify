# impl-notes-T-24-012

**Task**: Add FlexToolbar row above entity field editor in `nocode-data-model.js`.

## What was done

Added a publish toolbar row inside `showFieldManager()`, prepended to the modal body before
the field list. The toolbar contains:

- **Entity status badge** (`#entity-status-badge`): FlexBadge-style span showing entity.status.
  Colour: green for "published", amber for "draft".
- **"Preview changes" button** (`ph-eye` icon): calls `DataModelApp.previewMigration(entityId)`.
- **"Publish" button** (`ph-rocket-launch`, `#entity-publish-btn`): calls
  `DataModelApp.publishEntity(entityId)`; disabled when entity.status === 'published'.

Both buttons are focus-visible with `focus-visible:ring-2 focus-visible:ring-blue-500`.

## Files changed
- `frontend/assets/js/nocode-data-model.js`
