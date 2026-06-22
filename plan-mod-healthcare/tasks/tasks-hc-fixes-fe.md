# Frontend Fix Tasks (from D1 audit)

| ID | Severity | Issue | File(s) | Owner | Status |
|----|----------|-------|---------|-------|--------|
| FIX-FE-001 | CRITICAL | Token key mismatch — newly registered users immediately logged out | patient/register.js | C5 | OPEN |
| FIX-FE-002 | CRITICAL | 8 patient PHI pages missing auth guard | patient/appointment-detail.js, invoices.js, invoice-detail.js, lab-results.js, lab-result-detail.js, prescriptions.js, prescription-detail.js, waitlist.js | C5 | OPEN |
| FIX-FE-003 | HIGH | Raw fetch() in i18n.js bypasses auth token injection | modules/healthcare/frontend/i18n.js | C5 | OPEN |
| FIX-FE-004 | MEDIUM | PHI risk — full error objects logged via console.error | patient/prescriptions.js, patient/register.js | C5 | OPEN |
| FIX-FE-005 | MEDIUM | Hardcoded hex colours — not using CSS variables | 12+ JS/HTML files | C5 | OPEN |
| FIX-FE-006 | MEDIUM | Hardcoded English status strings not via t() | patient/lab-results.js, patient/prescriptions.js | C5 | OPEN |
| FIX-FE-007 | LOW | Hardcoded Indonesian month names — breaks en-US locale | patient/appointment-detail.js | C5 | OPEN |
| FIX-FE-008 | LOW | Unhandled promise rejection in i18n.js locale-persist call | modules/healthcare/frontend/i18n.js | C5 | OPEN |

> **Dependency note**: FIX-FE-001 (token key fix) MUST land and be verified before FIX-FE-002 (auth guards) can be meaningfully tested.
> Without the correct token key, newly registered users have no valid token in sessionStorage and every guard will fire as a false positive.
> FIX-FE-008 should be applied after FIX-FE-003 (swap fetch -> window.apiFetch in same location).

---

## FIX-FE-001 — Token key mismatch in register.js
**Severity**: CRITICAL
**File(s)**: `modules/healthcare/frontend/patient/register.js` line 191
**Issue**: Registration stores the auth token under the key `hc_access_token` in sessionStorage, but every other patient page reads `access_token`.
As a result, any user who registers is immediately treated as unauthenticated when redirected to any other page.

### Steps for C5
1. Open `modules/healthcare/frontend/patient/register.js` and go to line 191.
2. Locate: `sessionStorage.setItem('hc_access_token', ...)`.
3. Change the key to `access_token`:
   ```javascript
   sessionStorage.setItem('access_token', token);
   ```
4. Search the same file for any other `hc_access_token` references (getItem / removeItem) and update them to `access_token`.
5. Smoke-test: register a new user, confirm you are not immediately redirected back to login.

---

## FIX-FE-002 — 8 patient PHI pages missing auth guard
**Severity**: CRITICAL
**File(s)**:
- `modules/healthcare/frontend/patient/appointment-detail.js`
- `modules/healthcare/frontend/patient/invoices.js`
- `modules/healthcare/frontend/patient/invoice-detail.js`
- `modules/healthcare/frontend/patient/lab-results.js`
- `modules/healthcare/frontend/patient/lab-result-detail.js`
- `modules/healthcare/frontend/patient/prescriptions.js`
- `modules/healthcare/frontend/patient/prescription-detail.js`
- `modules/healthcare/frontend/patient/waitlist.js`

**Issue**: None of these files perform any sessionStorage check or redirect.
An unauthenticated user can navigate directly to any of these URLs and view Protected Health Information (PHI) without logging in.

> **Depends on**: FIX-FE-001 must be merged first so the token key is consistent before guards are tested.

### Steps for C5
For **each** of the eight files above:
1. Open the file and locate the `DOMContentLoaded` handler (or the top of module scope if there is no such handler).
2. Insert the following guard as the very first statement inside that handler (or at the very top of module scope):
   ```javascript
   const token = sessionStorage.getItem('access_token');
   if (!token) { window.location.href = '/patient/login'; }
   ```
3. Ensure the guard runs before any API calls or DOM writes that could expose PHI.
4. Test by opening each page in an incognito window (no session) and confirming immediate redirect to `/patient/login`.
5. Test again while logged in to confirm normal functionality is unaffected.

---

## FIX-FE-003 — Raw fetch() in i18n.js bypasses auth token injection
**Severity**: HIGH
**File(s)**: `modules/healthcare/frontend/i18n.js` line 143
**Issue**: The locale-persist POST uses native `fetch()` instead of `window.apiFetch`.
This bypasses the centralised auth-token injection middleware, so the request is sent without an `Authorization` header.

### Steps for C5
1. Open `modules/healthcare/frontend/i18n.js` and go to line 143.
2. Locate: `fetch(LOCALE_PERSIST_URL, { ... })`.
3. Replace `fetch` with `window.apiFetch`:
   ```javascript
   window.apiFetch(LOCALE_PERSIST_URL, { ... });
   ```
4. Confirm `window.apiFetch` is available in the execution context (it should be — every other page uses it).
5. Apply FIX-FE-008 (.catch handler) to this same call after making the replacement.

---

## FIX-FE-004 — PHI risk in console.error calls
**Severity**: MEDIUM
**File(s)**: `modules/healthcare/frontend/patient/prescriptions.js`, `modules/healthcare/frontend/patient/register.js`
**Issue**: `console.error(e)` logs the full raw error object. API error responses can embed server-returned patient data
(names, IDs, prescription info) which then appears in the browser console, accessible to devtools and browser extensions.

### Steps for C5
1. In both files, search for every `console.error(e)` call.
2. Replace each with:
   ```javascript
   console.error(e?.message || 'Request failed');
   ```
3. Do not log `e.response`, `e.data`, `e.body`, or any property that may carry server payload.
4. Verify no other `console.log` / `console.warn` calls in these files log raw error objects or response bodies.

---

## FIX-FE-005 — Hardcoded hex colours not using CSS variables
**Severity**: MEDIUM
**File(s)**: 12+ JS files and inline HTML styles across `modules/healthcare/frontend/`
**Issue**: Hex literals are scattered through JS and inline styles. This breaks theming, dark-mode support, and future brand refreshes.

### Steps for C5
1. Run a project-wide search for the following hex values in `modules/healthcare/frontend/`:
   `#dc2626`, `#f59e0b`, `#007bff`, `#16a34a`, `#6b7280`
2. For every occurrence, replace with the corresponding CSS variable:

   | Hex | CSS variable |
   |-----|-------------|
   | `#dc2626` | `var(--color-danger)` |
   | `#f59e0b` | `var(--color-warning)` |
   | `#007bff` | `var(--color-primary)` |
   | `#16a34a` | `var(--color-success)` |
   | `#6b7280` | `var(--color-muted)` |

3. Verify the CSS variables are declared in the relevant stylesheet (`:root` block). Add any that are missing.
4. Spot-check the UI visually to confirm colours render correctly.

---

## FIX-FE-006 — Hardcoded English status strings not using i18n t() helper
**Severity**: MEDIUM
**File(s)**: `modules/healthcare/frontend/patient/lab-results.js`, `modules/healthcare/frontend/patient/prescriptions.js`
**Issue**: Status display strings (`'Ordered'`, `'Pending'`, `'Dispensed'`, etc.) are hardcoded in English inside status-map objects,
never passed through the `t()` translation helper, so they always appear in English regardless of locale.

### Steps for C5
1. In `lab-results.js`, locate the status map containing `ordered: 'Ordered'` (and any sibling statuses).
2. In `prescriptions.js`, locate the status map containing `pending: 'Pending'`, `dispensed: 'Dispensed'` (and any sibling statuses).
3. Replace each hardcoded string with a `t()` call:
   ```javascript
   ordered: t(locale, 'status.ordered'),
   pending: t(locale, 'status.pending'),
   dispensed: t(locale, 'status.dispensed'),
   ```
4. Add the corresponding keys to every i18n locale file (at minimum `en` and `id`):
   ```json
   "status": {
     "ordered": "Ordered",
     "pending": "Pending",
     "dispensed": "Dispensed"
   }
   ```
   Add translations for Indonesian and any other supported locales.
5. Test by switching locale in the UI and confirming status labels change.

---

## FIX-FE-007 — Hardcoded Indonesian month names break en-US locale
**Severity**: LOW
**File(s)**: `modules/healthcare/frontend/patient/appointment-detail.js`
**Issue**: Month names are hardcoded in Bahasa Indonesia. English-locale users will see Indonesian month names in appointment dates.

### Steps for C5
1. Open `appointment-detail.js` and locate the hardcoded month-name array or lookup.
2. Replace it with a call to the Intl API, using the current locale:
   ```javascript
   // `locale` should already be in scope (e.g. 'id-ID' or 'en-US')
   const monthName = new Date(year, monthIndex).toLocaleDateString(locale, { month: 'long' });
   ```
3. Remove the now-unused hardcoded month array.
4. Test with both `id-ID` and `en-US` locale settings to confirm correct month names appear in each.

---

## FIX-FE-008 — Unhandled promise rejection in i18n.js locale-persist call
**Severity**: LOW
**File(s)**: `modules/healthcare/frontend/i18n.js`
**Issue**: The locale-persist call (fire-and-forget by design) has no `.catch()` handler.
A network failure or server error causes an unhandled promise rejection, appearing as a console error and potentially triggering global `unhandledrejection` listeners.

> **Depends on**: Apply after FIX-FE-003 (replace `fetch` with `window.apiFetch` in the same location).

### Steps for C5
1. Open `modules/healthcare/frontend/i18n.js` and locate the locale-persist call (line 143 area, after FIX-FE-003 is applied).
2. Append `.catch(() => {})` to silence the rejection:
   ```javascript
   window.apiFetch(LOCALE_PERSIST_URL, { ... }).catch(() => {});
   ```
3. Do NOT log or re-throw inside the catch — this call is intentionally fire-and-forget.
4. Verify no unhandled rejection warnings appear in the browser console when the locale-persist request fails
   (simulate via devtools network throttle / block).
