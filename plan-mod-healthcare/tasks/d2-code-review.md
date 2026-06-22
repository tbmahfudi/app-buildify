# D2 Code Review — Healthcare Module Backend

**Reviewer:** D2 Code Reviewer
**Date:** 2026-06-22
**Scope:** routes_appointments.py, routes_pharmacy.py, routes_lab.py, routes_billing.py, routes_patients.py, sdk/notification_service.py, sdk/branch_scope.py, migrations/hcs_001_scheduling_tables.py

---

## Findings

### CR-001: Double db.commit() splits audit from business write
- **Severity**: MAJOR
- **File**: routes_pharmacy.py (lines 264-272, 359-368, 403-411, 891-898)
- **Problem**: create_medication, update_medication, adjust_stock, and cancel_prescription each call db.commit() after the business INSERT/UPDATE, then call write_event_audit(), then call db.commit() a second time. The audit is in a separate transaction from the write it describes. If the second commit fails, the record is committed but the audit is silently dropped.
- **Fix**: Move the single db.commit() to after write_event_audit() so both the business row and the audit row commit atomically.

### CR-002: Stock adjust race condition — no SELECT FOR UPDATE
- **Severity**: BLOCKER
- **File**: routes_pharmacy.py (lines 386-413)
- **Problem**: adjust_stock reads stock_quantity via _get_medication_or_404 (plain SELECT, no FOR UPDATE). Two concurrent requests can read the same value, both pass the negative-stock guard, and both commit — leaving stock lower than permitted. dispense_prescription correctly uses SELECT FOR UPDATE on the same table; adjust_stock must too.
- **Fix**: Add FOR UPDATE to the medication SELECT in adjust_stock, or perform the adjustment atomically: UPDATE hcp_medications SET stock_quantity = stock_quantity + :adj WHERE id = :mid AND stock_quantity + :adj >= 0 RETURNING stock_quantity and raise 422 if no row is returned.

### CR-003: enter_results marks order resulted on partial submission
- **Severity**: MAJOR
- **File**: routes_lab.py (lines 799-805)
- **Problem**: After inserting whichever result lines are in the payload, the code unconditionally sets order status = resulted. A 3-panel order with only 1 result submitted is marked resulted; release_results then exposes incomplete data to the patient.
- **Fix**: After inserting results, query whether all order lines have status resulted. Only transition to resulted when every line is filled; otherwise leave status at processing.

### CR-004: Hardcoded string literal "staff" as actor_id in audit calls
- **Severity**: MAJOR
- **File**: routes_lab.py (lines 617, 706, 810, 924, 967)
- **Problem**: Five write_event_audit and write_phi_read_audit calls pass actor_id="staff" as a string literal. The authenticated user object (_auth) is in scope. This renders the audit trail non-attributable — a compliance failure for a PHI system.
- **Fix**: Extract the user id from _auth: actor_id=str(_auth.id). Apply to all five call sites.

### CR-005: SET LOCAL uses f-string interpolation — SQL injection risk
- **Severity**: MAJOR
- **File**: sdk/branch_scope.py (lines ~150-151)
- **Problem**: Session vars are set with f-string interpolation: db.execute(text(f"SET LOCAL app.tenant_id = '{tenant_id}'")). While tenant_id is a UUID from the token, f-string interpolation into raw SQL is incorrect practice and unsafe if the source ever changes.
- **Fix**: Use bound parameters: db.execute(text("SET LOCAL app.tenant_id TO :val"), {"val": tenant_id}). Same for app.branch_id.

### CR-006: Critical alert dispatched to patient, not ordering provider
- **Severity**: BLOCKER
- **File**: routes_lab.py (lines 831-864)
- **Problem**: _dispatch_critical_alert fetches the provider contact record (user_id, tenant_id, branch_id) but then calls svc._dispatch(patient_id=str(order["patient_id"]), ...). The patient's phone receives the message "Critical results are available for your patient. Please check the system." — clinician-facing copy sent to the wrong recipient. The ordering provider is never notified.
- **Fix**: Dispatch the alert to the provider's contact point, not the patient. If the notification service only supports patient phone dispatch, route critical alerts through a staff notification channel or internal inbox.

### CR-007: _get_patient_db() double-wraps Depends — db is never a Session at runtime
- **Severity**: BLOCKER
- **File**: routes_lab.py (lines 1098-1100), routes_pharmacy.py (lines 906-909)
- **Problem**: Both files define a helper that returns Depends(tenant_scoped_session) and use it as db: Session = Depends(_get_patient_db). FastAPI calls _get_patient_db() which returns another Depends object — not a session. Every patient-facing endpoint in these two files will raise AttributeError on the first db.execute() call at runtime.
- **Fix**: Remove the wrapper functions. Reference tenant_scoped_session directly: db: Session = Depends(tenant_scoped_session).

### CR-008: N+1 query in patient_list_prescriptions
- **Severity**: MAJOR
- **File**: routes_pharmacy.py (lines 935-952)
- **Problem**: For each prescription row a separate SELECT fires to fetch medication names. 50 prescriptions = 51 queries.
- **Fix**: Batch-fetch all lines for the prescription IDs in one query (WHERE prescription_id = ANY(:ids)), group in Python, then build the response.

### CR-009: N+1 query in staff list_prescriptions
- **Severity**: MAJOR
- **File**: routes_pharmacy.py (line 648)
- **Problem**: items = [_row_to_prescription(r, _get_prescription_lines(db, r[0])) for r in rows] fires one SELECT per page row. page_size=100 means 101 queries.
- **Fix**: Same batch approach as CR-008.

### CR-010: finalize_invoice and void_invoice UPDATE missing tenant_id / branch_id guard
- **Severity**: MAJOR
- **File**: routes_billing.py (lines 491-496, 532)
- **Problem**: UPDATE hcb_invoices SET status = 'finalized' ... WHERE id = :id has no AND tenant_id = :tid AND branch_id = :bid filter. _fetch_invoice confirms ownership before the update but takes no row-level lock, leaving a window for a race or logic error to mutate a different tenant's invoice.
- **Fix**: Add AND tenant_id = :tid AND branch_id = :bid to both UPDATE statements.

### CR-011: Naive vs aware datetime in cancel_appointment cancellation policy
- **Severity**: MINOR
- **File**: routes_appointments.py (lines ~278-285)
- **Problem**: (scheduled_at - datetime.utcnow()).total_seconds() raises TypeError if scheduled_at is timezone-aware (PostgreSQL TIMESTAMPTZ returns tz-aware datetimes via SQLAlchemy) and utcnow() is tz-naive.
- **Fix**: Use datetime.now(timezone.utc) consistently (matching the billing module convention).

### CR-013: healthcare_branch_session double-wraps Depends
- **Severity**: BLOCKER
- **File**: sdk/branch_scope.py (lines ~130-135, ~175-180)
- **Problem**: _get_tenant_scoped_session() and _get_current_user() return Depends(...) objects. The healthcare_branch_session signature uses Depends(_get_tenant_scoped_session) — FastAPI calls the wrapper, gets back another Depends, and injects a Depends object instead of a Session. Every branch-scoped endpoint crashes at runtime.
- **Fix**: Import tenant_scoped_session and get_current_user at module level and reference them directly in the healthcare_branch_session signature.

### CR-014: Migration missing unique constraint on slot (provider, date, start_time)
- **Severity**: MAJOR
- **File**: migrations/hcs_001_scheduling_tables.py
- **Problem**: hcs_appointment_slots has no unique constraint preventing two slots for the same provider at the same date+time. A slot generation bug or concurrent job could create duplicates, allowing two patients to book the same appointment time.
- **Fix**: Add op.create_unique_constraint("uq_hcs_slots_prov_time", "hcs_appointment_slots", ["provider_id", "slot_date", "start_time"]).

### CR-015: list_available_slots slot query missing tenant_id filter
- **Severity**: MAJOR
- **File**: routes_appointments.py (lines 59-75)
- **Problem**: The slot query filters on branch_id and slot_date but not tenant_id. The branch is validated to exist but no tenant boundary is enforced in the slot query itself, inconsistent with every other query in the module.
- **Fix**: Add AND s.tenant_id = :tid using branch_row[0] (already fetched).

### CR-016: get_lab_order PHI audit actor_id always hardcoded to "staff"
- **Severity**: MINOR
- **File**: routes_lab.py (lines 565-574)
- **Problem**: actor_id=str(_auth) if isinstance(_auth, str) else "staff" — _auth is a user object, never a string, so actor_id is always "staff". Same root cause as CR-004.
- **Fix**: actor_id=str(_auth.id).

### CR-018: collect_specimen hardcodes collected_by=None despite authenticated user being available
- **Severity**: MINOR
- **File**: routes_lab.py (line 685)
- **Problem**: cby=None with comment "lab_tech user_id not directly available here" — _auth is in scope and holds the user.
- **Fix**: cby=str(_auth.id).

### CR-019: Staff consent endpoint does not verify patient belongs to the requested branch
- **Severity**: MINOR
- **File**: routes_patients.py (lines ~155-175)
- **Problem**: list_patient_consents_staff verifies the caller is a clinic_owner or branch_manager but does not verify the patient has any relationship to branch_id. A branch_manager from Branch A can read consents for any patient in the tenant.
- **Fix**: Verify the patient has an encounter or registration in branch_id before returning consents.

### CR-020: notification_service clinic_name equals branch_name in all templates
- **Severity**: MINOR
- **File**: sdk/notification_service.py (lines ~180-190)
- **Problem**: _build_appt_context sets both clinic_name and branch_name to branch["branch_name"]. Templates render "{clinic_name} - {branch_name}" producing e.g. "Klinik Utama - Klinik Utama".
- **Fix**: Fetch the tenant/clinic name separately and use it for clinic_name.

---

## Summary Table

| ID     | Severity   | File                                    | Title                                                              |
|--------|------------|-----------------------------------------|--------------------------------------------------------------------|
| CR-001 | MAJOR      | routes_pharmacy.py                      | Double commit splits business + audit into separate transactions   |
| CR-002 | BLOCKER    | routes_pharmacy.py                      | Stock adjust lacks SELECT FOR UPDATE — race condition              |
| CR-003 | MAJOR      | routes_lab.py                           | enter_results marks order resulted on partial submission           |
| CR-004 | MAJOR      | routes_lab.py                           | Hardcoded "staff" as actor_id in 5 audit calls                    |
| CR-005 | MAJOR      | sdk/branch_scope.py                     | SET LOCAL uses f-string interpolation                              |
| CR-006 | BLOCKER    | routes_lab.py                           | Critical alert dispatched to patient, not ordering provider        |
| CR-007 | BLOCKER    | routes_lab.py, routes_pharmacy.py       | _get_patient_db() double-wraps Depends — db never a Session        |
| CR-008 | MAJOR      | routes_pharmacy.py                      | N+1 in patient_list_prescriptions                                  |
| CR-009 | MAJOR      | routes_pharmacy.py                      | N+1 in staff list_prescriptions                                    |
| CR-010 | MAJOR      | routes_billing.py                       | finalize/void UPDATE missing tenant_id + branch_id guard           |
| CR-011 | MINOR      | routes_appointments.py                  | Naive vs aware datetime in cancel policy                           |
| CR-013 | BLOCKER    | sdk/branch_scope.py                     | healthcare_branch_session double-wraps Depends                     |
| CR-014 | MAJOR      | migrations/hcs_001_scheduling_tables.py | Missing unique constraint on slot (provider, date, start_time)     |
| CR-015 | MAJOR      | routes_appointments.py                  | list_available_slots slot query missing tenant_id filter           |
| CR-016 | MINOR      | routes_lab.py                           | get_lab_order PHI audit actor_id always "staff"                    |
| CR-018 | MINOR      | routes_lab.py                           | collect_specimen hardcodes collected_by=None                       |
| CR-019 | MINOR      | routes_patients.py                      | Staff consent endpoint lacks patient-branch membership check       |
| CR-020 | MINOR      | sdk/notification_service.py             | clinic_name == branch_name in notification context                 |

**BLOCKER: 4** (CR-002, CR-006, CR-007, CR-013)
**MAJOR: 9** (CR-001, CR-003, CR-004, CR-005, CR-008, CR-009, CR-010, CR-014, CR-015)
**MINOR: 5** (CR-011, CR-016, CR-018, CR-019, CR-020)

### Must-fix before merge (BLOCKERs)

1. **CR-007 + CR-013** — Depends double-wrapping in _get_patient_db() and healthcare_branch_session: every patient-facing pharmacy/lab endpoint AND every branch-scoped staff endpoint crashes at runtime with AttributeError on the first db.execute() call. The entire healthcare API is non-functional until this is resolved.
2. **CR-002** — Stock adjust race: concurrent requests can drive stock negative despite the guard.
3. **CR-006** — Critical alert sent to the patient's phone with clinician-facing copy; the ordering provider is never notified of a critical lab result.
