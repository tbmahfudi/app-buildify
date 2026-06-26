# impl-notes-T-24-004 — Password Strength Indicator Update

**Task**: Create or update `frontend/assets/js/password-strength-indicator.js` with standalone strength logic
**Date**: 2026-06-27
**Owner**: C3 Frontend Developer

## File Updated

`frontend/assets/js/password-strength-indicator.js` — two new named exports appended (original class preserved intact)

## What was added

### `getStrength(password: string) → { level, score }`

Pure function — no DOM, no network. Classification rules:

| Level | Criteria | Score |
|---|---|---|
| weak | length < 8 | 1 |
| fair | length >= 8 | 2 |
| good | length >= 8 + mixed case (upper+lower) + digit | 3 |
| strong | length >= 12 + mixed case + digit + special char | 4 |

Special character defined as any character not in `[A-Za-z0-9]`.

Note: "strong" requires all four conditions simultaneously. "good" requires mixed case + digit but no special char requirement and no 12-char minimum.

### `renderStrengthBar(containerEl, password: string) → void`

Renders (or updates in-place) a 4-segment horizontal progress bar inside `containerEl`.

- Calls `getStrength(password)` internally
- On first call: injects `.psi-standalone-bar` HTML (4 `<div class="psi-seg">` segments + label `<p>`)
- On subsequent calls: updates segment colour classes and label text in-place (no full re-render)
- Empty password → all segments grey, no label

Segment colour mapping:

| Level | Score | Active segments | Colour class |
|---|---|---|---|
| weak | 1 | 1 of 4 | `bg-red-500` |
| fair | 2 | 2 of 4 | `bg-orange-400` |
| good | 3 | 3 of 4 | `bg-yellow-400` |
| strong | 4 | 4 of 4 | `bg-green-500` |

## What was preserved

The existing `PasswordStrengthIndicator` class (API-policy-driven, rule checklist, submit-button gating) is unchanged. Default export is still the class. The two new functions are named exports alongside it.

## Consumers

- `password-reset-page.js` — imports `getStrength` for client-side submit guard and `renderStrengthBar` for live bar below the new-password input
- Future: T-24.009 may call `renderStrengthBar` as supplementary UI if the API policy fetch fails
