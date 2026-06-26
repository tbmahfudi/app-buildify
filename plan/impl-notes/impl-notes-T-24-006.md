# impl-notes-T-24-006

**Task**: Implement `login-page.js` request-reset view (email form + email-sent state).

## What was done

- Appended `export function renderRequestReset(container)` to `frontend/assets/js/login-page.js`.
- Renders an email input form; on submit calls `POST /api/v1/auth/reset-password-request`.
- On success (or any response), replaces form with the "Check your inbox" confirmation state (Gap A from uildc-24 section 2.1.1):
  - `ph-envelope-open` icon in `text-blue-500`
  - "Check your inbox" heading
  - User-enumeration-safe body copy
  - "Back to sign in" link (`#login`)
- Loading state: spinner on submit button, email input disabled.
- Error state: network error shown in `role="alert"` div.

## Files changed
- `frontend/assets/js/login-page.js`
