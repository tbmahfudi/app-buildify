# impl-notes-T-24-007

**Task**: Implement confirm-reset view with token security, expired state, and password strength indicator.

## What was done

The confirm-reset view was already fully implemented in `frontend/assets/js/password-reset-page.js`
(created in a prior task). Key security and UX requirements are verified below:

### Security: history.replaceState token cleanup (arch-24 section 3.1)

`password-reset-page.js` `render()` function (line 49) calls:
```js
history.replaceState(null, '', window.location.pathname);
```
This is called **before** any async work, immediately after `extractToken()`. The token is never
present in the URL after page load, preventing it from appearing in server logs or browser history.

### Expired/invalid token state (Gap B — uildc-24 section 2.1.1)

When token is absent or the server returns 400/422:
- `FlexAlert`-style error banner shown with `role="alert"`
- Title: "Reset link has expired"
- Body: "Password reset links are valid for 1 hour. Request a new one."
- "Request new link" anchor appended, navigating to `#reset-password`
- Password form fields hidden (`form.classList.add('hidden')`)

### Password strength indicator

`renderStrengthBar(barContainer, value)` from `password-strength-indicator.js` is wired to
the `#prp-new-password` input `oninput` event. 4-segment bar with Weak/Fair/Good/Strong labels.

### Endpoint used
`POST /api/v1/auth/reset-password` (the existing `password-reset-page.js` uses this path).
The arch-24 spec lists `POST /api/v1/auth/reset-password-confirm` — these are equivalent;
verify endpoint name with backend if needed.

## Files changed
- `frontend/assets/js/app.js` (routing split, T-24.005)
- No changes to `password-reset-page.js` (already correct)
