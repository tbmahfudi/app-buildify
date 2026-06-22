# D1 Frontend Test Plan — Healthcare Module

## Issues Found

### ISSUE-FE-001: Raw fetch() in i18n.js -- not using window.apiFetch
- Severity: HIGH
- File: `i18n.js` (line 143)
- Problem: `i18n.js` calls the browser native `fetch()` to persist locale settings instead of routing through `window.apiFetch`. The `api-endpoint.js` usage is the legitimate internal implementation. The `i18n.js` call bypasses the standard auth/error wrapper, meaning the locale-persist POST lacks token injection and consistent 401 handling.
- Fix: Replace `fetch(LOCALE_PERSIST_URL, {...})` in `i18n.js` with `window.apiFetch(LOCALE_PERSIST_URL, {...})`.

### ISSUE-FE-002: Token key mismatch -- register stores `hc_access_token`, guards read `access_token`
- Severity: CRITICAL
- File: `patient/register.js` (line 191) vs. `patient/appointments.js` (line 2), `patient/portal.js` (line 2), and all other guarded pages
- Problem: After OTP registration, `register.js` calls `sessionStorage.setItem('hc_access_token', res.access_token)`. Every other patient page reads `sessionStorage.getItem('access_token')` for its auth guard. The key names do not match, so all guarded pages immediately redirect the newly registered user back to login -- the auth flow is completely broken for new registrations.
- Fix: Standardise on `access_token`. Change `register.js` line 191 to `sessionStorage.setItem('access_token', res.access_token)`.

### ISSUE-FE-003: Eight patient pages missing auth guards entirely
- Severity: CRITICAL
- Files: `patient/appointment-detail.js`, `patient/invoices.js`, `patient/invoice-detail.js`, `patient/lab-results.js`, `patient/lab-result-detail.js`, `patient/prescriptions.js`, `patient/prescription-detail.js`, `patient/waitlist.js`
- Problem: None of these files read from `sessionStorage` or redirect to login. An unauthenticated user who navigates directly to `/patient/invoices`, `/patient/lab-results`, etc. loads the page and fires API calls without a client-side auth check. PHI endpoints are hit from unauthenticated browser sessions.
- Fix: Add the standard guard at the top of each IIFE (same pattern as `appointments.js` lines 2-4): `const token = sessionStorage.getItem('access_token'); if (!token) { location.href = '/patient/register'; return; }`

### ISSUE-FE-004: Hardcoded hex colours throughout patient and clinic files
- Severity: MEDIUM
- Files: `patient/register.js` (line 158), `patient/invoice-detail.js` (lines 49-50), `patient/encounter-detail.html` (line 10), `patient/review-new.html` (line 10), `patient/appointments.html` (line 10), `patient/records.html` (line 10), `patient/portal.html` (line 10), `patient/waitlist.html` (lines 35-39, 44), `patient/appointment-detail.html` (lines 23-27), `public/clinic-profile.html` (lines 71, 157-158, 186, 200), `public/clinics.html` (line 119)
- Problem: Dozens of hex colour literals (#dc2626, #f59e0b, #16a34a, #007bff, #1d4ed8, #ccc, #f0f0f0, etc.) appear in inline styles and JS-injected markup. Dark-mode support, brand retheming, and accessibility adjustments are impossible without touching every occurrence.
- Fix: Define all colours as CSS custom properties in each file's `:root` block and reference `var(--color-*)` everywhere. Most HTML files already declare a `:root` block -- extend it. JS-injected styles should delegate to CSS classes.

### ISSUE-FE-005: Hardcoded English status strings bypassing i18n
- Severity: MEDIUM
- Files: `patient/lab-results.js` (line 17) -- `ordered: 'Ordered'`; `patient/prescriptions.js` (line 5) -- `pending: 'Pending'`, `dispensed: 'Dispensed'`
- Problem: Status label maps contain English literals mixed with Indonesian translations. These render directly to users without going through `t()`. In an `id-ID` locale session, English words appear in an otherwise Indonesian UI.
- Fix: Add status keys to both i18n JSON files and replace the static string maps with `t('lab.status_ordered')`, `t('rx.status_pending')` etc.

### ISSUE-FE-006: Hardcoded Indonesian month names in appointment-detail.js
- Severity: LOW
- File: `patient/appointment-detail.js` (line 13)
- Problem: `MONTH_NAMES` is hardcoded as an Indonesian array (`['Januari','Februari',...]`). When locale is `en-US` the reschedule calendar still shows Indonesian month names.
- Fix: Use `new Date(year, month).toLocaleString(currentLocale, { month: 'long' })` or add month name keys to both i18n files.

### ISSUE-FE-007: console.error logs raw error objects that may carry PHI response bodies
- Severity: MEDIUM
- Files: `patient/prescriptions.js` (line 11) -- `console.error(e)`, `patient/register.js` (lines 136, 156, 199) -- `console.error('OTP send failed', err)` etc.
- Problem: Several catch blocks call `console.error(e)` where `e` is the raw caught value from a failed `apiFetch`. If the server returns a JSON error body containing patient identifiers (name, phone, NIK) those values appear in browser DevTools and can be scraped by extensions or captured by monitoring tools.
- Fix: Log only `err.message` or a sanitised error code. Never log the full error object from a patient-data endpoint.

### ISSUE-FE-008: Unhandled rejection risk in i18n.js locale persistence
- Severity: LOW
- File: `i18n.js` (line 143)
- Problem: The locale persistence `fetch()` call is fire-and-forget. The comment acknowledges network failure is acceptable, but there is no `.catch()` attached, so a network error produces an unhandled Promise rejection warning and may surface in error monitoring as a false alarm.
- Fix: Add `.catch(() => {})` after the fetch call to suppress the unhandled rejection.

---

## Test Suites

### Suite 1: API Call Safety (no raw fetch, no manual auth headers)
Goal: Verify every network call routes through window.apiFetch.

| TC | File | Action | Expected |
|----|------|--------|---------|
| TC-1.1 | `api-endpoint.js` | Code review -- confirm single fetch() is the apiFetch implementation itself | PASS (exemption) |
| TC-1.2 | `i18n.js` | Code review -- locale persist call | Must use window.apiFetch, not raw fetch |
| TC-1.3 | All patient/*.js, clinic/*.js | grep -rn "fetch(" --include="*.js" | Zero results beyond api-endpoint.js |
| TC-1.4 | Network tab -- book appointment | Inspect request headers | Authorization: Bearer injected by apiFetch |
| TC-1.5 | Network tab -- clinic invoice creation | Inspect request headers | Authorization: Bearer injected by apiFetch |

### Suite 2: Token Storage Safety (sessionStorage only for patient tokens)
Goal: Patient access_token never touches localStorage; key name is consistent across all files.

| TC | File | Action | Expected |
|----|------|--------|---------|
| TC-2.1 | `patient/register.js` | Code review line 191 | Key must be 'access_token', not 'hc_access_token' |
| TC-2.2 | All patient/*.js | grep -rn "localStorage.*token" | Zero matches |
| TC-2.3 | Register flow E2E | Complete OTP registration, navigate to /patient/portal | Portal loads without redirect loop |
| TC-2.4 | DevTools Application tab | After login, inspect Storage | Token in sessionStorage, absent in localStorage |
| TC-2.5 | `i18n.js` | grep localStorage | Only 'locale' key stored; no auth material |

### Suite 3: CSS Variable Compliance
Goal: No hex colour literals in JS or inline HTML styles.

| TC | File | Action | Expected |
|----|------|--------|---------|
| TC-3.1 | All JS files | grep -rn "#[0-9a-fA-F]{3,6}" --include="*.js" | Zero matches |
| TC-3.2 | All HTML files | grep -rn "#[0-9a-fA-F]{3,6}" --include="*.html" | Zero matches |
| TC-3.3 | Visual -- dark mode toggle | Apply prefers-color-scheme:dark via DevTools | All elements reflect CSS variables |
| TC-3.4 | `patient/invoice-detail.js` print template | Review generated style block | No #ccc, #f0f0f0 literals |

### Suite 4: i18n Coverage
Goal: All user-visible strings go through t(); both locale files are in sync.

| TC | File | Action | Expected |
|----|------|--------|---------|
| TC-4.1 | id-ID.json vs en-US.json | Key-count comparison | Both: 182 leaf keys -- currently PASS |
| TC-4.2 | `patient/lab-results.js` | Check statusLabel map | All values must be t('...') calls |
| TC-4.3 | `patient/prescriptions.js` | Check SL status map | All values must be t('...') calls |
| TC-4.4 | `patient/appointment-detail.js` | Check MONTH_NAMES | Must use locale-aware date formatting |
| TC-4.5 | E2E -- locale en-US | /patient/lab-results | Status labels display in English |
| TC-4.6 | E2E -- locale id-ID | /patient/lab-results | Status labels display in Indonesian |

### Suite 5: Auth Guard Coverage (patient pages)
Goal: Every authenticated patient page redirects to login when no token present.

| TC | Page | Action | Expected |
|----|------|--------|---------|
| TC-5.1 | /patient/portal | Open in private window | Redirect to /patient/register |
| TC-5.2 | /patient/appointments | Open in private window | Redirect (guard present) |
| TC-5.3 | /patient/appointments/:id | Open in private window | FAIL -- no guard -- must redirect |
| TC-5.4 | /patient/invoices | Open in private window | FAIL -- no guard -- must redirect |
| TC-5.5 | /patient/invoices/:id | Open in private window | FAIL -- no guard -- must redirect |
| TC-5.6 | /patient/lab-results | Open in private window | FAIL -- no guard -- must redirect |
| TC-5.7 | /patient/lab-results/:id | Open in private window | FAIL -- no guard -- must redirect |
| TC-5.8 | /patient/prescriptions | Open in private window | FAIL -- no guard -- must redirect |
| TC-5.9 | /patient/prescriptions/:id | Open in private window | FAIL -- no guard -- must redirect |
| TC-5.10 | /patient/waitlist | Open in private window | FAIL -- no guard -- must redirect |
| TC-5.11 | /patient/records | Open in private window | Redirect (guard present) |
| TC-5.12 | /patient/profile | Open in private window | Redirect (guard present) |

### Suite 6: Error Handling
Goal: All apiFetch calls have try/catch or .catch(); errors surface gracefully to the user.

| TC | File | Action | Expected |
|----|------|--------|---------|
| TC-6.1 | `patient/invoices.js` | Code review loadInvoices | Has try/catch -- PASS |
| TC-6.2 | `patient/waitlist.js` | Code review all apiFetch calls | All 4 calls wrapped in try/catch -- PASS |
| TC-6.3 | `patient/appointment-detail.js` | Code review | All apiFetch calls wrapped -- PASS |
| TC-6.4 | `patient/prescriptions.js` | Simulate 500 response | User sees error message, not blank page |
| TC-6.5 | `i18n.js` locale persist | Code review | Add .catch(() => {}) to prevent unhandled rejection |
| TC-6.6 | `clinic/write-prescription.js` | Interaction-check catch | Gracefully degrades -- PASS |
| TC-6.7 | Any guarded patient page | Force 401 from API | Redirect to login handled by apiFetch |

### Suite 7: PHI Safety (no patient data in logs or console)
Goal: No Protected Health Information appears in console output.

| TC | File | Action | Expected |
|----|------|--------|---------|
| TC-7.1 | `patient/prescriptions.js` line 11 | Code review catch(e){console.error(e)} | Replace with message-only log; no raw error object |
| TC-7.2 | `patient/register.js` lines 136, 156, 199 | Code review | Errors are generic strings; response body not logged |
| TC-7.3 | `patient/lab-results.js` line 57 | Code review | Message-only log -- PASS |
| TC-7.4 | All clinic/*.js | grep -rn "console.log\b" | Zero console.log (non-error) calls |
| TC-7.5 | E2E -- DevTools during booking | Complete appointment booking | Console shows no patient name, phone, NIK, or diagnosis |
| TC-7.6 | E2E -- DevTools during prescriptions load | /patient/prescriptions | Console shows no medication or dosage data |

---

## Summary

| Category | Status | Count |
|----------|--------|-------|
| CRITICAL issues | Failing | 2 (token key mismatch FE-002, missing auth guards on 8 pages FE-003) |
| HIGH issues | Failing | 1 (raw fetch in i18n.js FE-001) |
| MEDIUM issues | Failing | 3 (hardcoded colours FE-004, hardcoded i18n strings FE-005, PHI in console.error FE-007) |
| LOW issues | Failing | 2 (hardcoded month names FE-006, unhandled rejection FE-008) |
| i18n completeness | Passing | id-ID and en-US both have 182 leaf keys -- in sync |
| PHI in console.log | Passing | No console.log calls found; all logging uses console.error/console.warn |
| apiFetch adoption | Mostly passing | All patient/clinic pages use window.apiFetch; 1 violation in i18n.js |
| Error handling | Mostly passing | Most pages have try/catch; 1 low-severity gap in i18n locale persist |

Blocking before release: ISSUE-FE-002 and ISSUE-FE-003 are security issues that allow unauthenticated access to patient health records and break the post-registration auth flow for all new users. ISSUE-FE-001 should also be resolved before release. All three must be fixed before the healthcare module goes to production.
