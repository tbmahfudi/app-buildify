# impl-notes-T-24-026

**Task**: Implement version preview modal.

## What was done

`previewVersion(v)` in `builder-version-history.js` already existed. Enhanced with:

### ARIA (uildc-24 section 5.1)
- `role="dialog"`, `aria-modal="true"`, `aria-labelledby="vh-preview-title"` on modal.
- `<h2 id="vh-preview-title">` heading.

### Canvas preview with `pointer-events: none`
Preview content wrapped in `<div style="pointer-events:none">` (T-24.026 spec).
Currently renders JSON representation of page data (canvas renderer integration
would require builder canvas to be refactored; JSON view is the MVP).

### Escape key
`closeM` handler registered on `keydown`; removes itself on modal close.
Escape key does NOT fire while a restore action is in-flight (confirm dialog blocks UI).

### Focus management
Focus moves to close button when modal opens.

## Files changed
- `frontend/assets/js/builder-version-history.js`
