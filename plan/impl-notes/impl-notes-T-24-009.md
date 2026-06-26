# impl-notes-T-24-009

**Task**: Extend `password-strength-indicator.js` per T-24.003 verdict.

## Changes made

### Session-scope policy cache
Added module-level `let _policyCache = null;`. `_fetchPolicy()` now checks cache first,
fetching from `/api/v1/auth/password-policy` only on the first call in a browser session.
All subsequent `PasswordStrengthIndicator.attach()` calls reuse the cached policy.

### `static attach(inputEl, submitBtn, apiBase)` method
Added static factory method for the cleaner API specified in arch-24 section 3.2.
Internally calls `new PasswordStrengthIndicator(inputEl, submitBtn, apiBase)`.

### `aria-label` on rule list items (uildc-24 section 5.2)
- Initial render: each `<li>` gets `aria-label="{rule label}: not met"`
- `_evaluate()` updates aria-label to `"{rule label}: passed"` or `"{rule label}: not met"`
  on every keystroke.
- When input is empty: aria-label reset to `"{rule label}: not met"`.

### What was already correct (verified against Story 24.2.1 spec)
- `attach(inputEl, submitBtn)` public API (via constructor) ✓
- Rule checklist with `ph-circle` / `ph-x-circle` / `ph-check-circle` icons ✓
- `text-gray-300` / `text-red-400` / `text-green-500` colour classes ✓
- FlexProgress-style bar with red/amber/green colour mapping ✓
- Fail-open if policy fetch fails (submit button re-enabled, container cleared) ✓
- `ph-spinner animate-spin` loading state ✓

## Files changed
- `frontend/assets/js/password-strength-indicator.js`
