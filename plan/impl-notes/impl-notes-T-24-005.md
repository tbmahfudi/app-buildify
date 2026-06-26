# impl-notes-T-24-005

**Task**: Add routes `#reset-password` and `#reset-password-confirm` in app.js with mode discriminator.

## What was done

- Updated `loadRoute()` in `frontend/assets/js/app.js`:
  - `#reset-password` now imports `renderRequestReset` from `login-page.js` (email-form view)
  - `#reset-password-confirm` (and `#reset-password-confirm?token=xxx`) imports `render` from `password-reset-page.js` (set-new-password view)
- Previously both routes pointed to `password-reset-page.js` (confirm-only view), leaving the request-reset flow unreachable via `#reset-password`.

## Files changed
- `frontend/assets/js/app.js` — split reset-password routing into two distinct branches
- `frontend/assets/js/login-page.js` — added `renderRequestReset` export (T-24.006)
