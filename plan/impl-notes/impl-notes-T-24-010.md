# impl-notes-T-24-010

**Task**: Attach `passwordStrengthIndicator` to the Change Password new-password field.

## What was done

The "Change Password" form for end-users lives in `frontend/assets/js/profile-page.js`
(template: `profile.html`, field id `#new-password`). The `settings-security` route renders
`SecurityAdmin` (auth policy management for admins) and does not contain a user-facing
password change form.

- Added `import PasswordStrengthIndicator from './password-strength-indicator.js'` to `profile-page.js`.
- In `initProfilePageWithForms()`, after first-time event listener setup:
  ```js
  const newPwdEl  = passwordForm.querySelector('#new-password');
  const submitBtn = passwordForm.querySelector('button[type="submit"]');
  if (newPwdEl && submitBtn) {
    PasswordStrengthIndicator.attach(newPwdEl, submitBtn);
  }
  ```
- The static `attach()` method (added in T-24.009) creates a new `PasswordStrengthIndicator`
  instance that fetches the password policy (from session cache after first call) and renders
  the rule checklist + strength bar below `#new-password`.
- Submit button is gated (disabled) until all active policy rules pass.
- Added clarifying comment to `settings-security.js`.

## Files changed
- `frontend/assets/js/profile-page.js`
- `frontend/assets/js/settings-security.js` (comment only)
