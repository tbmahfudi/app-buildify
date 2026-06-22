# Backend Fix Tasks (from D1 Audit)

Generated: 2026-06-22
Triage by: C1 Tech Lead
Assignee: C4

---

## Summary Table

| ID | Issue | Severity | File | Owner | Status |
|----|-------|----------|------|-------|--------|
| FIX-BE-001 | Broken patient auth on list_patient_consents | CRITICAL | routes_patients.py | C4 | OPEN |
| FIX-BE-002 | Sandbox violation in patient_auth.py | HIGH | sdk/patient_auth.py | C4 | OPEN |
| FIX-BE-003 | Missing write_phi_read_audit on list_patient_appointments | HIGH | routes_appointments.py | C4 | OPEN |
| FIX-BE-004 | Missing write_phi_read_audit on list_patient_consents | HIGH | routes_patients.py | C4 | OPEN |
| FIX-BE-005 | Rate limiting not implemented on public endpoints | MEDIUM | routes_public.py | C4 | OPEN |
| FIX-BE-006 | No audit on slot listing | LOW | routes_appointments.py | C4 | OPEN |

---

## FIX-BE-001 — Broken patient auth on list_patient_consents

**Issue**: ISSUE-BE-002
**File**: `modules/healthcare/routes_patients.py`
**Severity**: CRITICAL
**Regression test**: TC-AUTH-005, TC-AUTH-006

### Problem
`list_patient_consents` (~line 97) uses `get_current_user` (staff dependency) and then tries to detect a patient caller by checking `staff_roles == ["patient"]`. This can never work: `get_current_user` rejects patient JWTs at the dependency level, so a patient token never reaches the handler. Patients are permanently locked out of reading their own consents.

### Steps for C4

1. Open `modules/healthcare/routes_patients.py`, locate the `list_patient_consents` endpoint (~line 97).
2. Split the single endpoint into **two separate route handlers** on the same path:
   - **Patient path**: inject `current_patient = Depends(get_current_patient)`. Enforce `current_patient.patient_id == patient_id` (own data only — return 403 if mismatch). Return the consent records.
   - **Staff path**: inject `current_user = Depends(get_current_user)`. Enforce that `current_user` has `clinic_owner` role (or the appropriate `has_hc_permission` check). Return the consent records.
3. Remove the old heuristic `staff_roles == ["patient"]` check entirely — it must not appear in either new handler.
4. Register both handlers. FastAPI supports multiple routes on the same path with different dependencies; alternatively use a single handler with two optional dependency params and exactly one must be non-None (raise 401 if both are None).
5. Verify with TC-AUTH-005 (patient JWT → 200 own consents) and TC-AUTH-006 (patient JWT → 403 for another patient's ID).

---

## FIX-BE-002 — Sandbox violation in patient_auth.py

**Issue**: ISSUE-BE-001
**File**: `modules/healthcare/sdk/patient_auth.py`
**Severity**: HIGH

### Problem
`modules/healthcare/sdk/patient_auth.py` line 21 imports `decode_token` directly from `backend.app.core.auth`. Module SDK files must not cross the module sandbox boundary by importing from `backend.app` directly.

### Steps for C4

1. Open `modules/sdk/dependencies.py` (or the appropriate SDK wrapper file in the `modules/sdk/` layer).
2. Add a re-export:
   ```python
   from backend.app.core.auth import decode_token as _decode_token
   decode_token = _decode_token
   ```
3. Open `modules/healthcare/sdk/patient_auth.py`, line 21.
4. Replace:
   ```python
   from backend.app.core.auth import decode_token
   ```
   with:
   ```python
   from modules.sdk.dependencies import decode_token
   ```
5. Grep all files under `modules/healthcare/sdk/` for any remaining `from backend.app` imports and fix them the same way.
6. Run the existing auth unit tests to confirm nothing is broken.

---

## FIX-BE-003 — Missing write_phi_read_audit on list_patient_appointments

**Issue**: ISSUE-BE-003
**File**: `modules/healthcare/routes_appointments.py`
**Severity**: HIGH
**Regression test**: TC-AUDIT-002

### Problem
`GET /api/v1/patients/me/appointments` (~line 155) returns `AppointmentResponse` rows that include a `notes` field (Optional[str]) containing clinical notes — PHI. The function returns without calling `write_phi_read_audit()`. The cross-tenant counterpart in `routes_patient_appointments.py` does call the audit correctly; this route does not.

### Steps for C4

1. Open `modules/healthcare/routes_appointments.py`, locate the `list_patient_appointments` handler (~line 155).
2. Inspect the pattern used in `routes_patient_appointments.py` — mirror it exactly.
3. Before the `return` statement, add:
   ```python
   await write_phi_read_audit(
       db=db,
       actor_type="patient",
       actor_id=str(current_patient.patient_id),
       entity_type="appointment_list",
       entity_id=str(current_patient.patient_id),
   )
   ```
   (Adjust parameter names to match the actual `write_phi_read_audit` signature in the SDK.)
4. Ensure `write_phi_read_audit` is imported at the top of the file from the SDK wrapper (not directly from `backend.app`).
5. Verify with TC-AUDIT-002: after a GET, confirm a PHI audit row exists in `hc_audit_events` for `entity_type='appointment_list'` and the correct `actor_id`.

---

## FIX-BE-004 — Missing write_phi_read_audit on list_patient_consents

**Issue**: ISSUE-BE-005
**File**: `modules/healthcare/routes_patients.py`
**Severity**: HIGH
**Regression test**: TC-AUDIT-004

### Problem
`list_patient_consents` (~line 137) returns `HCPatientConsent` records (containing `consent_type`, `consent_version`, `ip`, `user_agent`, `accepted_at`) which are patient-linked PHI. Neither the patient path nor the clinic_owner path calls `write_phi_read_audit()`.

### Steps for C4

1. This fix should be applied **after** FIX-BE-001 (the endpoint split), since the two handlers will have separate return paths.
2. In the **patient path** handler (from FIX-BE-001), add before the return:
   ```python
   await write_phi_read_audit(
       db=db,
       actor_type="patient",
       actor_id=str(current_patient.patient_id),
       entity_type="patient_consent",
       entity_id=str(patient_id),
   )
   ```
3. In the **staff/clinic_owner path** handler (from FIX-BE-001), add before the return:
   ```python
   await write_phi_read_audit(
       db=db,
       actor_type="staff",
       actor_id=str(current_user.user_id),
       entity_type="patient_consent",
       entity_id=str(patient_id),
   )
   ```
4. Verify with TC-AUDIT-004: after a GET by clinic_owner JWT, confirm a `phi.read` audit row exists for `entity_type='patient_consent'`.

---

## FIX-BE-005 — Rate limiting not implemented on public endpoints

**Issue**: ISSUE-BE-004
**File**: `modules/healthcare/routes_public.py`, `modules/healthcare/schemas/public.py`
**Severity**: MEDIUM

### Problem
Clinic search and profile endpoints have slowapi rate limiting referenced in comments but not implemented. Additionally, `contact_phone` is a non-optional `str` in `PublicBranchDetail`, causing serialization failures for branches with no phone.

### Steps for C4

1. **Schema fix** — open `modules/healthcare/schemas/public.py`, find `PublicBranchDetail` (~line 49). Change:
   ```python
   contact_phone: str
   ```
   to:
   ```python
   contact_phone: Optional[str] = None
   ```
2. **Rate limiting** — in `modules/healthcare/routes_public.py`:
   - Ensure `from slowapi import Limiter` and `from slowapi.util import get_remote_address` are imported.
   - Ensure a `limiter` instance is available (check if one is already set up in the router/app factory; reuse it if so).
   - Add `@limiter.limit("60/minute")` decorator to each public endpoint handler (clinic search, clinic profile, branch detail). Pass `request: Request` as a parameter if not already present.
3. Verify TC-PUBLIC-001 through TC-PUBLIC-004 still pass after rate limiting is applied.
4. Confirm with legal/DPA that `contact_phone` is classified as public business data (not PHI) before shipping — note this in the PR description.

---

## FIX-BE-006 — No audit on slot listing

**Issue**: ISSUE-BE-006
**File**: `modules/healthcare/routes_appointments.py`
**Severity**: LOW

### Problem
`list_available_slots` (~line 35) joins `hc_providers` and returns `provider_name` (full_name) in the response. The endpoint is correctly patient-auth gated, but access is not audited.

### Steps for C4

1. Open `modules/healthcare/routes_appointments.py`, locate `list_available_slots` (~line 35).
2. Before the return statement, add a `write_event_audit()` call:
   ```python
   await write_event_audit(
       db=db,
       actor_type="patient",
       actor_id=str(current_patient.patient_id),
       event_type="slot.list",
       entity_type="appointment_slot",
       metadata={"branch_id": str(branch_id)},
   )
   ```
   (Adjust parameter names to match the actual `write_event_audit` signature.)
3. Confirm that `provider.full_name` is the display name column on `hc_providers` and is not a PHI column on patient records — add a comment to the code confirming this.
4. Import `write_event_audit` from the SDK wrapper (not from `backend.app` directly).

---

## Dependency Order

The fixes should be applied in this order to avoid merge conflicts:

1. **FIX-BE-002** — SDK re-export (no route changes, lowest risk, unblocks clean import pattern for all other fixes)
2. **FIX-BE-001** — Endpoint split (structural change; do first before audit injections)
3. **FIX-BE-003** — Audit on appointments list (independent of FIX-BE-001)
4. **FIX-BE-004** — Audit on consents (depends on FIX-BE-001 being done first)
5. **FIX-BE-005** — Rate limiting + schema fix (independent)
6. **FIX-BE-006** — Slot listing audit (independent, lowest priority)
