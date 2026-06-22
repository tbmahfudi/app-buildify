# Healthcare Module Suite — Changelog

## [1.0.0] - 2026-06-22

### Base Module (`healthcare`)
- Patient self-registration with OTP (Redis-backed, 5 attempts/10 min, 60s resend cooldown) and hCaptcha
- Clinic onboarding with 4-step wizard and DPA consent gate
- Multi-location branch management (up to 20 branches per tenant, soft-delete)
- Staff management: invite by email, 7 RBAC roles (Clinic Owner, Branch Manager, Doctor, Nurse, Pharmacist, Lab Tech, Billing Staff)
- PHI encryption at rest: Fernet AES-256 via `EncryptedPHIType` SQLAlchemy TypeDecorator; key fail-fast at startup
- Phone deduplication via HMAC-SHA256 hash (raw phone never stored in queryable column)
- Append-only audit log (`hc_audit_log`) with INSERT-only DB grant
- 3-layer branch isolation: BranchScopeListener (ORM) + PostgreSQL RLS + `X-Branch-ID` header (fail-closed: missing header → HTTP 422)
- Public clinic discovery: search by specialty and city; 60s server-side cache; zero PHI in response
- Public clinic profile: branch list, provider name+specialty only (no license number)
- Multilingual support: Bahasa Indonesia (default) and English; per-module JSON translation files; locale resolved user → tenant → platform
- Patient portal: profile editing (email/address/locale), encounter history with year grouping, cross-tenant appointment aggregation, clinic reviews with 24h moderation hold
- Two-sided auth: same JWT issuer; patient role namespace `{roles: ["patient"], tenant_id: null}`; patient tokens in sessionStorage only
- Redis-based public endpoint rate limiting: 60 req/min/IP, fail-open

### Scheduling Sub-module (`healthcare_scheduling`)
- Provider weekly schedule editor: day-of-week blocks, slot duration (15/30/60 min), appointment types, overlap detection
- Provider date/time blocking with recurrence (none/annual); existing appointments flagged for review (no auto-cancel)
- Slot generation with branch timezone support
- Appointment booking: atomic SELECT FOR UPDATE slot reservation; status machine (confirmed → checked_in → in_progress → completed / no_show)
- Patient booking wizard: 4-step mobile-first UI (type → date → slot → confirmation) with ICS calendar download
- Reschedule and cancel: configurable cancellation policy (minimum hours before appointment)
- Waitlist FIFO: auto-offer on cancellation, 15-min claim window, Redis-backed expiry stubs
- PHI-safe notifications: WhatsApp Business API (primary) + SMS (60s fallback); 6 system-locked templates; no patient name/diagnosis/provider in body
- Appointment queue: live queue with WebSocket primary / 30s polling fallback; PHI mask toggle

### Billing Sub-module (`healthcare_billing`)
- Service item catalog per branch (code, name, category, unit price IDR)
- Invoice lifecycle: draft → finalized (immutable) → void (manager only); amendments via void + new invoice
- Line items auto-calculate subtotals and total
- Payment recording: cash/transfer/BPJS/insurance/other; multiple payments per invoice
- Patient invoice access: read-only, own invoices only, locale-aware
- BPJS Kesehatan export: CSV format with HMAC-anonymised patient names (no raw PHI); file-based (no live API)
- Insurance profile management: insurance numbers encrypted at rest
- RLS on all billing tables

### Pharmacy Sub-module (`healthcare_pharmacy`)
- Branch medication catalog: stock management with atomic adjustment (SELECT FOR UPDATE)
- Drug interaction checker: severity levels (mild/moderate/severe); severe interactions block prescription creation unless doctor overrides (`?force=true`)
- Prescription lifecycle: pending → dispensed / partially_dispensed / cancelled
- Dispensing workflow: per-line quantity tracking, batch number, expiry date; stock decremented atomically
- Patient prescription access: read-only, dosage instructions visible, own prescriptions only
- CSPRNG OTP generation (secrets.choice)

### Laboratory Sub-module (`healthcare_lab`)
- Test panel catalog: category, sample type, turnaround hours, fasting requirement
- Lab order lifecycle: ordered → specimen_collected → processing → resulted / cancelled
- Specimen collection with auto-generated barcode
- Result entry: per-line values, reference ranges, abnormal and critical flags
- Critical value alert: immediate PHI-safe notification to ordering provider (not patient) on is_critical=True
- Result release gate: patients see results only after explicit lab_tech/manager release
- Patient lab results: read-only, released results only, abnormal/critical badges

### Security Baseline
- Zero `from backend.app` imports in module code (sandbox enforced)
- All secrets fail-fast at startup if unset (PHI_ENCRYPTION_KEY, PHONE_HASH_SECRET, BPJS_EXPORT_HMAC_KEY)
- SET LOCAL replaced with parameterized set_config() (SQL injection prevention)
- RLS applied to all 17 module tables
- OTP logging stripped of sensitive values
- D2 code review: PASS | D3 security review: PASS | D1 QA: PASS
