# impl-notes-T-24-014

**Task**: Implement drag-reorder on entity field list in `nocode-data-model.js`.

## What was done

### Field list markup
- Changed `#fieldsList div.space-y-2` to `<ul id="entity-fields-list" class="space-y-2">`.
- Each field rendered as `<li class="field-list-item" draggable="true" tabindex="0">` via new
  `renderFieldItemDraggable(field, entityId, index, total)` method.
- Drag handle button (`ph-dots-six-vertical`, `aria-label="Drag to reorder {field name}"`).
  Visible on group-hover and keyboard focus.

### HTML5 DnD (uildc-24 section 2.3.1)
- `dragstart`: opacity-50 + ring-2 ring-blue-400 on dragged item.
- `dragover`: border-t-2 border-blue-500 drop indicator on target.
- `drop`: `insertBefore()` reorders items in DOM (array state reflected in DOM order).
- `dragend`: cleanup all visual indicators.

### Keyboard fallback: Alt+ArrowUp / Alt+ArrowDown
- Listener on `#entity-fields-list` for `keydown` with `e.altKey`.
- Moves focused `<li>` up or down one position using `insertBefore()`.
- Announces via `aria-live="polite"` region `#field-reorder-announce`:
  "Field {name} moved to position {n} of {total}".
- Focus returns to the moved item.

### Dirty state
After any reorder (DnD or keyboard): Publish button re-enabled, status badge set to "Draft".

### Empty state (uildc-24 section 2.3.1)
When entity has no fields: shows `ph-table` icon (text-gray-300), "No fields yet" heading,
description text, and "Add first field" FlexButton(variant=primary).

## Files changed
- `frontend/assets/js/nocode-data-model.js`
