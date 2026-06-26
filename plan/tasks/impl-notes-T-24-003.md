# impl-notes-T-24-003 — Password Reset Page Implementation

**Task**: Create `frontend/assets/js/password-reset-page.js`
**Date**: 2026-06-27
**Owner**: C3 Frontend Developer

## File Created

`frontend/assets/js/password-reset-page.js`

## Implementation Summary

### Token extraction + security
- `extractToken()` parses `window.location.hash` looking for `?token=` parameter
- Supports both `#reset?token=xxx` and `#/reset-password?token=xxx` URL forms
- `render()` calls `extractToken()` FIRST, then immediately calls `history.replaceState(null, '', window.location.pathname)` to remove the token from the URL before any rendering or async work — satisfying arch-24 § 3.1

### Render states

| State | Trigger | UI |
|---|---|---|
| Idle (token present) | Normal load with valid token in hash | Two password fields + strength bar + submit button |
| Expired (no/bad token) | No token in hash, or API returns 400/422 | Error banner visible, form hidden, "Request new link" anchor to `#reset-password` |
| Loading | Submit clicked, fetch in-flight | Submit button disabled + spinner icon, inputs disabled |
| Success | API returns 2xx | Card replaced with check-circle icon + "Password updated" message + "Sign in" link |
| Inline error | Passwords don't match, too weak, network error, non-token API error | Error banner shows, form stays editable |

### Strength bar
- Imports `getStrength` and `renderStrengthBar` from `password-strength-indicator.js`
- Attached to `#prp-new-password` `input` event — live updates 4-segment bar below the field
- Client-side submit guard: rejects if `getStrength(password).score < 2` (score 1 = weak)

### API call
- `POST /api/v1/auth/reset-password` with `{ token, new_password }`
- Token is already cleared from URL before the fetch

### Route registered in app.js
- Route `reset-password` (and alias `reset-password-confirm`) registered in `loadRoute()` — both load `password-reset-page.js`
- Inserted before the Reports section in the route cascade

## Dependencies
- `password-strength-indicator.js` — `getStrength`, `renderStrengthBar` (added in T-24.004)
- No template file needed — page renders entirely via JS DOM construction

## Accessibility notes
- Error banner has `role="alert"`
- Form fields have explicit `<label for>` associations
- Submit button uses native `<button type="submit">` (keyboard-accessible)
- `history.replaceState` called synchronously before any async — token never exposed in subsequent navigation
