# Healthcare Backend — Test Plan (D1 QA Engineer)

Generated: 2026-06-22

---

## Issues Found

### ISSUE-BE-001: Sandbox violation — `sdk/patient_auth.py` imports directly from `backend.app`
- **Severity**: HIGH
- **File**: `sdk/patient_auth.py` (line 21)
- **Problem**: `from backend.app.core.auth import decode_token` crosses the module sandbox boundary. Module SDK files must not import from `backend.app` directly; they must use the SDK wrapper only.
- **Fix**: C4 should expose a `modules.sdk.auth.decode_token` re-export and replace the direct `backend.app` import in `sdk/patient_auth.py` with that wrapper.

---

### ISSUE-BE-002: Broken auth logic in `list_patient_consents` — patient JWT never recognized
- **Severity**: CRITICAL
- **File**: `routes_patients.py` (approx line 97–145)
- **Problem**: The endpoint accepts only `get_current_user` (staff dependency). It attempts to detect a patient caller by checking `staff_roles == ["patient"]` on a staff token object — this comparison will never be true because `get_current_user` rejects patient JWTs at the dependency level per the module SDK contract. The result is that a legitimate patient can never read their own consents; all requests fall through to the staff path and fail with 403 unless the caller is a `clinic_owner`.
- **Fix**: Add `get_current_patient` as an optional dependency (use FastAPI's `Optional` pattern or a dual-token resolver), or split the endpoint into two: one under patient auth and one under staff auth. The existing heuristic must be removed.

---

### ISSUE-BE-003: Missing `write_phi_read_audit` on `list_patient_appointments` (routes_appointments.py)
- **Severity**: HIGH
- **File**: `routes_appointments.py` (approx line 155–175)
- **Problem**: `GET /api/v1/patients/me/appointments` returns `AppointmentResponse` rows that include a `notes` field (Optional[str]) which may contain clinical notes (PHI). The function returns the data without calling `write_phi_read_audit()`. The cross-tenant counterpart in `routes_patient_appointments.py` does call the audit; this older route does not.
- **Fix**: Add `write_phi_read_audit()` call before the return statement, mirroring the pattern in `routes_patient_appointments.py`.

---

### ISSUE-BE-004: Public endpoint exposes branch `contact_phone` without classification
- **Severity**: MEDIUM
- **File**: `routes_public.py` (approx line 255, 320) / `schemas/public.py` (line 49)
- **Problem**: `GET /api/v1/clinics/{slug}` and `GET /api/v1/clinics/{slug}/branches/{branch_id}` return `contact_phone` for every branch. The file header says "No PHI is returned" but a branch phone number is a business-contact field that could be considered PII/PHI under certain DPA classifications. More concretely, the `PublicBranchDetail` schema makes `contact_phone` a non-optional `str`, meaning a missing phone becomes a blank string rather than being omitted — a minor schema correctness issue. The TODO for rate limiting (slowapi) is also unimplemented.
- **Fix**: Confirm with legal/DPA that branch `contact_phone` is classified as public business data (not PHI). Make the field `Optional[str]` in the schema so branches with no phone don't break serialization. Implement slowapi rate limiting per the existing TODO.

---

### ISSUE-BE-005: `list_patient_consents` missing `write_phi_read_audit` when returning consent records
- **Severity**: HIGH
- **File**: `routes_patients.py` (approx line 137–145)
- **Problem**: The GET consents endpoint returns `HCPatientConsent` records which contain `consent_type`, `consent_version`, `ip`, `user_agent`, and `accepted_at` — all patient-linked data that constitutes a PHI audit trail. Neither the patient path nor the staff path calls `write_phi_read_audit()` before returning results.
- **Fix**: Call `write_phi_read_audit()` at the end of both branches of the auth check, passing the appropriate `actor_type` and `actor_id`.

---

### ISSUE-BE-006: `list_available_slots` leaks `provider_name` (full_name) in slot listing without PHI audit
- **Severity**: LOW
- **File**: `routes_appointments.py` (approx line 35–65)
- **Problem**: The slot query joins `hc_providers` and returns `p.full_name AS provider_name`. Provider names are not patient PHI, but the endpoint does not audit the access. The endpoint is patient-auth gated correctly. This is a low-severity audit gap, not a data leak.
- **Fix**: Add `write_event_audit()` for slot listing so access is traceable. Confirm `provider.full_name` is the display name column and not a PHI column on the patient record.

---

## Clean Files — No Issues Found

- `routes_patient_profile.py` — PHI audit present on GET and PUT; ownership via `patient.patient_id` filter; no raw `get_db`.
- `routes_encounter_history.py` — PHI audit on every encounter row returned; ownership enforced via `patient_id == pid` filter.
- `routes_patient_appointments.py` — PHI audit present; ownership enforced in SQL with `patient_id = :pid`.
- `routes_pharmacy.py` — `SELECT FOR UPDATE` present on prescription line and medication stock; patient prescription endpoints call `write_phi_read_audit`.
- `routes_appointments.py` (booking, reschedule, cancel, status) — `SELECT FOR UPDATE` correctly used on slot and appointment rows.
- `routes_schedules.py` — branch-scoped via `healthcare_branch_session`; RBAC via `has_hc_permission`.
- `routes_lab.py` — PHI audit on patient lab result endpoints; ownership enforced.
- `routes_billing.py` — PHI audit present; branch-session used for staff endpoints.
- `schemas/*.py` — All schemas use `model_config = ConfigDict(from_attributes=True)`. No legacy `class Config: orm_mode = True` found.

---

## Test Suite

### Auth / RBAC

**TC-AUTH-001** — Patient token rejected on staff endpoint
```
POST /api/v1/modules/healthcare/patients/{patient_id}/consents
Authorization: Bearer <patient_jwt>
Expected: 201 Created (patient path)

GET /api/v1/modules/healthcare/branches/{branch_id}/schedules
Authorization: Bearer <patient_jwt>
Expected: 401 Unauthorized (staff dependency rejects patient token)
```

**TC-AUTH-002** — Staff token rejected on patient endpoint
```
GET /api/v1/patients/me/profile
Authorization: Bearer <staff_jwt>
Expected: 401 Unauthorized (get_current_patient rejects staff token)
```

**TC-AUTH-003** — Doctor can only list own schedules (not other providers')
```
GET /api/v1/modules/healthcare_scheduling/branches/{branch_id}/schedules
Authorization: Bearer <doctor_jwt>
Expected: 200, items filtered to doctor's own provider_id only
```

**TC-AUTH-004** — Nurse cannot access schedule CRUD (manager-only)
```
POST /api/v1/modules/healthcare_scheduling/branches/{branch_id}/schedules
Authorization: Bearer <nurse_jwt>
Expected: 403 Forbidden
```

**TC-AUTH-005** — `list_patient_consents` with patient JWT (regression for ISSUE-BE-002)
```
GET /api/v1/modules/healthcare/patients/{own_patient_id}/consents
Authorization: Bearer <patient_jwt>
Expected: 200 with own consents (currently fails — returns 403)
```

**TC-AUTH-006** — `list_patient_consents` cross-patient access denied
```
GET /api/v1/modules/healthcare/patients/{other_patient_id}/consents
Authorization: Bearer <patient_jwt>
Expected: 403 Forbidden
```

---

### PHI Audit Trail

**TC-AUDIT-001** — Profile GET writes PHI read audit
```
GET /api/v1/patients/me/profile
Authorization: Bearer <patient_jwt>
Post-condition: SELECT * FROM hc_audit_events WHERE entity_type='patient' AND event_type LIKE 'phi.read%' AND actor_id=<patient_id> LIMIT 1 → returns 1 row
```

**TC-AUDIT-002** — Appointment list GET writes PHI read audit (regression for ISSUE-BE-003)
```
GET /api/v1/patients/me/appointments
Authorization: Bearer <patient_jwt>
Post-condition: audit table has entry for entity_type='appointment_list' actor_id=<patient_id> (currently missing)
```

**TC-AUDIT-003** — Encounter detail GET writes PHI read audit
```
GET /api/v1/patients/me/encounters/{encounter_id}
Authorization: Bearer <patient_jwt>
Post-condition: audit row exists for entity_type='encounter', entity_id=<encounter_id>
```

**TC-AUDIT-004** — Consent list GET writes PHI read audit (regression for ISSUE-BE-005)
```
GET /api/v1/modules/healthcare/patients/{patient_id}/consents
Authorization: Bearer <clinic_owner_jwt>
Post-condition: audit table has phi.read entry for entity_type='patient_consent' (currently missing)
```

---

### Branch Isolation

**TC-BRANCH-001** — Missing X-Branch-ID returns 422
```
GET /api/v1/modules/healthcare_scheduling/branches/{branch_id}/schedules
Authorization: Bearer <staff_jwt>
Headers: (no X-Branch-ID)
Expected: 422 Unprocessable Entity (healthcare_branch_session dependency enforces header)
```

**TC-BRANCH-002** — Wrong branch ID in header returns 403/404
```
GET /api/v1/modules/healthcare_scheduling/branches/{branch_id}/schedules
Authorization: Bearer <staff_jwt>
Headers: X-Branch-ID: <different_branch_uuid>
Expected: 403 or 404 (branch scope mismatch)
```

**TC-BRANCH-003** — Cross-tenant data isolation
```
Staff from Tenant A cannot see appointments for Tenant B's branch
GET /api/v1/modules/healthcare_scheduling/branches/{tenant_b_branch_id}/schedules
Authorization: Bearer <tenant_a_staff_jwt>
Expected: 403 or empty result set (never Tenant B's data)
```

---

### Concurrency — Slot Double-Booking

**TC-CONCUR-001** — Simultaneous slot booking returns 409 for second caller
```
Precondition: slot S is 'available'
Thread 1: POST /api/v1/patients/me/appointments {slot_id: S}  →  201 Created
Thread 2 (concurrent): POST /api/v1/patients/me/appointments {slot_id: S}  →  409 Conflict
Post-condition: hcs_appointment_slots.status == 'booked', exactly 1 appointment row with status='confirmed'
```

**TC-CONCUR-002** — Dispense fails if stock drops to zero mid-transaction
```
Precondition: medication M has stock_quantity=1
Thread 1: POST /api/v1/modules/healthcare_pharmacy/branches/{bid}/prescriptions/{rx_id}/dispense  →  200
Thread 2 (concurrent): same request  →  409 (insufficient stock)
Post-condition: stock_quantity remains 0, not negative
```

---

### Patient Data Ownership

**TC-OWN-001** — Patient cannot read another patient's profile
```
GET /api/v1/patients/me/profile
Authorization: Bearer <patient_A_jwt>
Expected: profile of Patient A only (enforced by patient.patient_id filter)
```

**TC-OWN-002** — Patient cannot read another patient's encounter by ID
```
GET /api/v1/patients/me/encounters/{patient_B_encounter_id}
Authorization: Bearer <patient_A_jwt>
Expected: 404 Not Found (SQL filter includes patient_id == patient_A.id)
```

**TC-OWN-003** — Patient cannot read another patient's appointment by ID
```
GET /api/v1/patients/me/appointments/{patient_B_appointment_id}
Authorization: Bearer <patient_A_jwt>
Expected: 404 Not Found
```

**TC-OWN-004** — Patient cannot read another patient's prescription
```
GET /api/v1/patients/me/prescriptions/{patient_B_prescription_id}
Authorization: Bearer <patient_A_jwt>
Expected: 404 Not Found
```

---

### Public Endpoint PHI Safety

**TC-PUBLIC-001** — Clinic search returns zero PHI
```
GET /api/v1/clinics/search?specialty=cardiology
Expected response fields: clinic_name, slug, specialty_tags, city, average_rating, online_booking, branch_count
Prohibited fields: patient names, DOB, phone (patient), diagnosis, encounter_id
```

**TC-PUBLIC-002** — Clinic public profile contains no patient PHI
```
GET /api/v1/clinics/{slug}
Expected: clinic_name, branches (branch_name, address_city, address_street, contact_phone, providers[name, specialty])
Assert: no patient_id, no full_name (patient), no date_of_birth, no national_id fields in response
```

**TC-PUBLIC-003** — Provider list on public profile shows display_name + specialty only
```
GET /api/v1/clinics/{slug}/branches/{branch_id}
Assert: provider objects contain only {name, specialty} — no license_number, no user_id, no email
```

**TC-PUBLIC-004** — No auth token required for public endpoints
```
GET /api/v1/clinics/search (no Authorization header)
Expected: 200 OK (unauthenticated access allowed)
```
