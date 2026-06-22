---
artifact_id: adr-hc-004
type: adr
module: healthcare
status: Accepted
producer: B1 Software Architect
upstream: [vision-02, research-02, epic-01-base-healthcare, BACKLOG.md]
created: 2026-06-21
---

# ADR-HC-004 — i18n Architecture

## Status

Accepted

## Context

The App-Buildify platform has **no existing i18n infrastructure** (arch-00-platform — not
mentioned in open questions, confirming absence). The Healthcare Module Suite mandates i18n as a
first-class feature from day one (vision-02 Guardrail 7: "i18n-first, not i18n-later").

Scope:
- **Launch locales:** `id-ID` (Bahasa Indonesia, default) and `en-US` (English).
- **Tenants** configure a default locale. **Users** override per their profile. Patients
  configure locale in their portal.
- **Additional locales** must be addable by dropping a translation file — no code changes
  required (vision-02).
- **Backend** must localise: API validation error messages, email/WhatsApp notification
  templates, PDF/printed document labels.
- **Frontend** must switch locale without full page reload.
- All timezone handling: WIB (UTC+7), WITA (UTC+8), WIT (UTC+9) as Indonesian defaults;
  arbitrary IANA timezone configurable per tenant/branch.

Design questions:
1. Translation file format and location?
2. Locale resolution order?
3. Backend localisation of validation errors and API responses?
4. Frontend locale switching without reload?

## Decision

### D1 — Translation File Format and Location

**Format: JSON, one file per locale per module.**

File structure:
```
modules/healthcare/i18n/
  id-ID.json          # Bahasa Indonesia (launch default)
  en-US.json          # English (launch)
  # future: ar-SA.json, zh-CN.json — no code changes required

modules/healthcare_scheduling/i18n/
  id-ID.json
  en-US.json

modules/healthcare_billing/i18n/
  id-ID.json
  en-US.json

# ... per sub-module
```

Frontend translation files are co-located with their module:
```
modules/healthcare/frontend/i18n/
  id-ID.json
  en-US.json
```

Key format: dot-notation namespaced by feature, e.g.:
```json
{
  "patient.registration.title": "Daftar Akun Pasien",
  "patient.registration.otp_hint": "Kode OTP dikirim ke {{phone}}",
  "validation.required": "Kolom ini wajib diisi",
  "validation.phone.invalid": "Nomor telepon tidak valid",
  "audit.phi_read": "Data pasien diakses oleh {{actor}}"
}
```

Translation keys must be **namespaced** (no bare keys like `"title"`). The linting gate
(`tools/lint/`) is extended to reject hardcoded Indonesian or English strings in Python source
and frontend JS/HTML files.

**Backend translation files** are loaded at module startup into memory (small footprint; hot-
reload in development via file watcher). **Frontend translation files** are served as static
JSON and loaded dynamically by the i18n client (see D4).

### D2 — Locale Resolution Order

Locale is resolved at request time with the following precedence chain
(highest priority first):

```
1. Authenticated user's profile locale    (users.locale column)
2. Tenant default locale                  (tenants.default_locale column, set by Clinic Owner)
3. Platform default                       (env var PLATFORM_DEFAULT_LOCALE, default: "id-ID")
```

For **unauthenticated** requests (patient registration, clinic discovery):
```
1. Accept-Language HTTP header (first matching supported locale)
2. Platform default ("id-ID")
```

Locale is resolved by a `resolve_locale(request, current_user=None, tenant=None)` utility in
`modules/healthcare/sdk/locale.py`. All response-generating code (API handlers, email
templates, PDF generators) calls this utility.

Supported locale list is maintained in `modules/healthcare/i18n/__init__.py`:
```python
SUPPORTED_LOCALES = ["id-ID", "en-US"]
DEFAULT_LOCALE = "id-ID"
```

Adding a new locale requires:
1. Drop `<locale>.json` files in each module's `i18n/` directory.
2. Add the locale code to `SUPPORTED_LOCALES`.
No other code changes.

### D3 — Backend Localisation of Validation Errors and API Responses

**Validation errors:** FastAPI's default Pydantic validation error responses contain
English-language messages. These are intercepted by a custom exception handler in
`modules/healthcare/backend/app/main.py`:

```python
@app.exception_handler(RequestValidationError)
async def localised_validation_error_handler(request, exc):
    locale = resolve_locale(request)
    errors = [
        {"field": e["loc"][-1], "message": t(locale, f"validation.{e['type']}")}
        for e in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"errors": errors})
```

`t(locale, key, **kwargs)` is a thin translation function in
`modules/healthcare/sdk/locale.py`. It looks up the key in the loaded JSON, performs
`str.format_map(kwargs)` for interpolation, and falls back to `en-US` if the key is missing in
the requested locale (never raises KeyError — missing key falls back, then logs a warning).

**API response bodies** must not contain localised strings except in error/message fields.
Resource data (patient name, clinic name, etc.) is stored as entered (no server-side
translation of user data). Only system-generated messages use the translation layer.

**Email and WhatsApp notification templates** are stored in `modules/healthcare/i18n/templates/`:
```
modules/healthcare/i18n/templates/
  appointment_confirmed/
    id-ID.txt
    en-US.txt
  otp_message/
    id-ID.txt
    en-US.txt
```

Note: WhatsApp/SMS message bodies are system-locked and contain no PHI per vision-02
Guardrail (WhatsApp PHI leakage risk row). Templates use only non-PHI placeholders
(`{{clinic_name}}`, `{{appointment_time}}` — no patient name, diagnosis, or doctor name).

**PDF documents** (invoices, lab result cover sheets) use locale-aware label rendering via
`reportlab` (or equivalent). Labels are loaded from the JSON translation files at render time.

### D4 — Frontend Locale Switching Without Page Reload

**Frontend i18n library: `i18next`** (lightweight, framework-agnostic, works with vanilla JS
ES modules — consistent with platform's no-bundler, no-framework approach per arch-00-platform
§4).

Locale switching flow:
1. User selects locale from the header dropdown (present on every page — staff and patient
   portals).
2. JavaScript calls `i18next.changeLanguage(locale)`.
3. `i18next` dynamically fetches `/modules/healthcare/i18n/{{locale}}.json` if not already
   cached (HTTP GET, cacheable with `Cache-Control: max-age=3600`).
4. All `t('key')` calls re-render with the new locale. Components using the `data-i18n`
   attribute are automatically updated by an `i18next` DOM observer (no framework required).
5. New locale is:
   - Stored in `localStorage` (unauthenticated users / immediate persistence).
   - `PUT /api/v1/users/me/locale` (authenticated users — persisted to profile, used for
     server-side locale resolution on next request).

Date, time, and number formatting uses the browser's `Intl.DateTimeFormat` and
`Intl.NumberFormat` APIs, parameterised with the active locale code. Branch timezone is passed
in API responses as an IANA timezone string (e.g. `"Asia/Jakarta"`) and applied client-side.

**No page reload is required.** The `i18next` DOM observer handles re-rendering for
non-SPA content; dynamic content (tables, forms) re-renders through normal JS data binding.

## Consequences

### Positive
- **Adding a locale is a content operation** — drop JSON files, add locale code to list.
  No Python or JS code changes required.
- **Consistent resolution chain** — backend and frontend both honour user > tenant > platform
  default; behaviour is predictable.
- **Backend fallback** prevents missing-key 500 errors in production.
- **`i18next`** is mature, small, and compatible with the platform's no-bundler JS approach.
- **Template isolation** for notifications ensures no PHI leaks into WhatsApp/SMS messages.

### Negative
- **Distributed translation files** (per module) risk key duplication and divergence. Mitigation:
  a shared `modules/healthcare/i18n/common.json` for cross-module keys (validation messages,
  common labels); module-specific files for domain keys.
- **Translation completeness** — at launch, `en-US.json` must be 100% complete; future locale
  additions may have gaps. Mitigation: CI check that counts keys in each locale JSON and alerts
  on missing keys vs. `id-ID.json` (the reference locale).
- **`i18next` dependency** — adds a client-side JS library. Size: ~13 KB gzipped. Acceptable
  for mobile-first patient portal (Lighthouse ≥ 80 target on mid-range Android / 4G).

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| Centralised single translation file for all modules | Merge conflicts and coordination overhead as module team grows; per-module files align with module ownership. |
| GNU gettext / .po files | Not native to JavaScript ecosystem; tooling friction with no-bundler JS approach; JSON is simpler and widely supported. |
| Server-side rendering of all localised content (no client-side i18n) | Requires page reload on locale switch; contradicts vision-02 Guardrail 7 and Story 1.7.1 AC ("instant re-render without page reload"). |
| React-intl / vue-i18n | Platform uses vanilla JS ES modules (no framework) — framework-specific i18n libraries are incompatible. |

## Reference Map

| File | Relevance |
|------|-----------|
| `plan/architecture/arch-platform.md` §4 | No-bundler, vanilla JS ES modules — constrains frontend i18n library choice |
| `plan-mod-healthcare/epics/epic-01-base-healthcare.md` | Story 1.7.1 — locale switching ACs; Stories 1.4.1, 1.1.1 — locale on public pages |
| `plan-mod-healthcare/vision/vision-02.md` | Guardrail 7 (i18n-first), Scope IN (launch locales), Risk table (WhatsApp PHI leakage) |
| `plan-mod-healthcare/research/research-02.md` | Indonesian market locale requirements |
