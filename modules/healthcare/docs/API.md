# Healthcare Module Suite — API Reference

Base URL: `/api/v1/`

## Authentication
- **Staff**: `Authorization: Bearer <platform_jwt>` + `X-Branch-ID: <uuid>` (branch-scoped endpoints)
- **Patient**: `Authorization: Bearer <patient_jwt>` (obtained via OTP flow)
- **Public**: No auth required. Rate limited: 60 req/min/IP.

---

## Public Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/clinics/search` | Search clinics by specialty, city. Zero PHI. |
| GET | `/clinics/{slug}` | Clinic public profile. |
| GET | `/clinics/{slug}/branches/{branch_id}` | Branch public profile. Providers: name+specialty only. |
| GET | `/clinics/{slug}/branches/{branch_id}/reviews` | Approved reviews. No patient identifying info. |
| GET | `/modules/healthcare/i18n/{locale}` | Translation strings (id-ID, en-US). |

## Patient Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/patients/register` | Register patient account. Requires hCaptcha token. |
| POST | `/patients/auth/otp/send` | Send OTP to phone. 60s cooldown, 5 attempts/10 min. |
| POST | `/patients/auth/otp/verify` | Verify OTP, returns access_token (15 min) + refresh_token (7 days). |
| POST | `/patients/auth/token/refresh` | Refresh access token. |
| POST | `/patients/auth/logout` | Invalidate refresh token. |

## Patient — Profile & Records

| Method | Path | Description |
|--------|------|-------------|
| GET | `/patients/me/profile` | Patient profile (PHI, audited). |
| PUT | `/patients/me/profile` | Update email, address, locale only. |
| GET | `/patients/me/summary` | Aggregate counts (visits, upcoming appts). No PHI. |
| GET | `/patients/me/encounters` | Encounter history, paginated, year-grouped. |
| GET | `/patients/me/encounters/{id}` | Single encounter detail. |
| GET | `/patients/me/appointments` | Cross-tenant appointments (upcoming/past). |
| GET | `/patients/me/appointments/{id}` | Appointment detail. |
| POST | `/patients/me/reviews` | Submit clinic review (requires completed encounter). |
| GET | `/patients/me/consents` | Own consent records. |
| POST | `/patients/me/waitlist` | Join waitlist. |
| GET | `/patients/me/waitlist` | List waitlist entries. |
| DELETE | `/patients/me/waitlist/{id}` | Leave waitlist. |

## Patient — Billing

| Method | Path | Description |
|--------|------|-------------|
| GET | `/patients/me/invoices` | Own finalized invoices. |
| GET | `/patients/me/invoices/{id}` | Invoice detail. |
| GET | `/patients/me/invoices/{id}/pdf` | Invoice PDF data (JSON format, v1). |
| POST | `/patients/me/insurance` | Add insurance profile. |
| GET | `/patients/me/insurance` | List insurance profiles. |
| PUT | `/patients/me/insurance/{id}` | Update insurance profile. |

## Patient — Pharmacy & Lab

| Method | Path | Description |
|--------|------|-------------|
| GET | `/patients/me/prescriptions` | Own prescriptions. |
| GET | `/patients/me/prescriptions/{id}` | Prescription detail with dosage instructions. |
| GET | `/patients/me/lab-orders` | Own lab orders with released results. |
| GET | `/patients/me/lab-orders/{id}/results` | Released lab results. |

## Clinic Onboarding

| Method | Path | Description |
|--------|------|-------------|
| POST | `/clinics/register` | Register clinic (creates tenant, branch, owner). Requires hCaptcha. |
| GET | `/modules/healthcare/dpa/status` | DPA acceptance status for tenant. |

## Staff — Branches & People

| Method | Path | Description |
|--------|------|-------------|
| POST/GET | `/modules/healthcare/branches` | Create/list branches. Auth: Clinic Owner. |
| GET/PUT/DELETE | `/modules/healthcare/branches/{id}` | Branch detail/update/soft-delete. |
| POST | `/modules/healthcare/branches/{id}/staff/invite` | Invite staff member. |
| GET | `/modules/healthcare/branches/{id}/staff` | List staff. Auth: Branch Manager+. |
| DELETE | `/modules/healthcare/branches/{id}/staff/{id}` | Remove staff. |
| POST/GET/PUT/DELETE | `/modules/healthcare_scheduling/branches/{id}/providers` | Provider CRUD. |

## Staff — Scheduling

| Method | Path | Description |
|--------|------|-------------|
| POST/GET | `/modules/healthcare_scheduling/branches/{id}/schedules` | Provider schedule CRUD. |
| GET/PUT/DELETE | `/modules/healthcare_scheduling/branches/{id}/schedules/{id}` | Schedule detail. |
| POST | `/modules/healthcare_scheduling/branches/{id}/schedules/{pid}/blocks` | Block date/time range. |
| GET | `/clinics/{slug}/branches/{id}/slots` | Available slots. Auth: Patient. |
| PUT | `/modules/healthcare_scheduling/branches/{id}/appointments/{id}/status` | Status transition. Auth: Nurse, Manager. |

## Staff — Billing

| Method | Path | Description |
|--------|------|-------------|
| POST/GET/PUT | `/modules/healthcare_billing/branches/{id}/service-items` | Service catalog CRUD. |
| POST/GET | `/modules/healthcare_billing/branches/{id}/invoices` | Invoice create/list. |
| GET | `/modules/healthcare_billing/branches/{id}/invoices/{id}` | Invoice detail. |
| POST | `/modules/healthcare_billing/branches/{id}/invoices/{id}/finalize` | Finalize (immutable). |
| POST | `/modules/healthcare_billing/branches/{id}/invoices/{id}/void` | Void. Auth: Manager+. |
| POST | `/modules/healthcare_billing/branches/{id}/invoices/{id}/payments` | Record payment. |
| POST/GET | `/modules/healthcare_billing/branches/{id}/bpjs-exports` | BPJS export generate/list. |
| GET | `/modules/healthcare_billing/branches/{id}/bpjs-exports/{id}/download` | Download CSV. |

## Staff — Pharmacy

| Method | Path | Description |
|--------|------|-------------|
| POST/GET/PUT | `/modules/healthcare_pharmacy/branches/{id}/medications` | Medication catalog CRUD. |
| POST | `/modules/healthcare_pharmacy/branches/{id}/medications/{id}/stock-adjust` | Stock adjustment. |
| POST | `/modules/healthcare_pharmacy/branches/{id}/interactions/check` | Drug interaction check. |
| POST/GET | `/modules/healthcare_pharmacy/branches/{id}/prescriptions` | Prescriptions. |
| GET | `/modules/healthcare_pharmacy/branches/{id}/prescriptions/{id}` | Detail. |
| POST | `/modules/healthcare_pharmacy/branches/{id}/prescriptions/{id}/dispense` | Dispense. Auth: Pharmacist. |

## Staff — Laboratory

| Method | Path | Description |
|--------|------|-------------|
| POST/GET/PUT | `/modules/healthcare_lab/branches/{id}/test-panels` | Test panel catalog. |
| POST/GET | `/modules/healthcare_lab/branches/{id}/orders` | Lab order create/list. |
| GET | `/modules/healthcare_lab/branches/{id}/orders/{id}` | Order detail. |
| PUT | `/modules/healthcare_lab/branches/{id}/orders/{id}/status` | Status transition. |
| POST | `/modules/healthcare_lab/branches/{id}/orders/{id}/specimens` | Record specimen. |
| POST | `/modules/healthcare_lab/branches/{id}/orders/{id}/results` | Enter results. Critical → immediate provider alert. |
| POST | `/modules/healthcare_lab/branches/{id}/orders/{id}/results/release` | Release to patient. |
| GET | `/modules/healthcare_lab/branches/{id}/orders/{id}/results` | View results (staff). |
