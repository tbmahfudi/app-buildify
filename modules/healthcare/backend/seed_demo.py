"""
Healthcare demo seed — clinic + login-able patients with full portal data.

Run (inside the healthcare microservice container)::

    docker exec app_buildify_healthcare python -m modules.healthcare.seed_demo

Idempotent: get-or-create on natural keys, safe to re-run.

What it seeds (scoped to the existing MedCare tenant/clinic)::
    tenant_id : 50f10a52-66ad-4c38-a0b2-6015db8dd42c
    branch    : "MedCare Main Clinic" (slug medcare-main) — reused, not recreated
    providers : Dr. Andi Pratama (existing) + Dr. Sari Wijaya (created)
    schedules : weekday provider schedules + slots (some booked, some available)
    patients  : 3 patients, OTP-login-able by phone (see below)
    per patient: 2 appointments (1 upcoming + 1 completed), 1 encounter,
                 1 prescription (+lines), 1 lab order (+result, shared), 1 finalized invoice

Demo patient phone numbers (all share consent/PHI shape via the module helpers)::
    +6281100000001  Budi Santoso    (male)
    +6281100000002  Citra Lestari   (female)
    +6281100000003  Dewi Anggraini  (female)

================================  HOW TO LOG IN (dev)  ========================
There is NO fixed/test OTP — `sdk/otp.py` generates a random 6-digit code stored
in Redis under  otp:{phone}  with a 10-min TTL. The dev SMS gateway is a no-op
(routes_patient_auth.otp_send does not return the code). So to log a seeded
patient in via the real OTP flow in dev:

  1. POST /api/v1/patients/auth/otp/send   {"phone": "+6281100000001"}
       header  X-Captcha-Token: test      (HCAPTCHA_SECRET_KEY=test accepts any)
  2. Read the generated code straight from Redis (dev only)::
         docker exec app_buildify_redis redis-cli get "otp:+6281100000001"
     (this container's REDIS_URL points at the shared redis service)
  3. POST /api/v1/patients/auth/token      {"phone":"+6281100000001","code":"<code>"}
       -> returns {access_token, patient_id}. The token carries tenant_id =
          MedCare, so all /api/v1/patients/me/* routes resolve the seeded data.

The login lookup is `WHERE phone_hash = _hash_phone(phone)` — this script writes
that same hash (HMAC-SHA256, key = env PHONE_HASH_KEY, default
"changeme-set-PHONE_HASH_KEY" — matching the route's own default) so the seeded
patients are found by the auth route.

For automated verification without SMS, mint a token directly with
`sdk/patient_tokens.create_patient_access_token(patient_id, phone, tenant_id)`
(see seed_demo.verify / the --verify flag).
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, time as dtime

from sqlalchemy import text

# Module SDK / models — reuse the module's own helpers (no hand-rolled crypto)
from modules.sdk.db import generate_uuid
from modules.healthcare.models import (
    HCBranch,
    HCProvider,
    HCPatient,
    HCPatientConsent,
    HCEncounter,
)
from modules.healthcare.routes_patient_auth import _hash_phone  # exact login hash

# Platform DB session (appuser — superuser, bypasses RLS)
from app.core.dependencies import get_db


TENANT_ID = "50f10a52-66ad-4c38-a0b2-6015db8dd42c"
BRANCH_SLUG = "medcare-main"
CONSENT_VERSION = "1.0"

DEMO_PATIENTS = [
    {"phone": "+6281100000001", "full_name": "Budi Santoso",   "gender": "male",
     "dob": "1985-03-12", "email": "budi.demo@example.com"},
    {"phone": "+6281100000002", "full_name": "Citra Lestari",  "gender": "female",
     "dob": "1990-07-21", "email": "citra.demo@example.com"},
    {"phone": "+6281100000003", "full_name": "Dewi Anggraini", "gender": "female",
     "dob": "1978-11-05", "email": "dewi.demo@example.com"},
]


def _det_id(*parts: str) -> str:
    """Deterministic UUID5 so re-runs reuse the same row ids (idempotency)."""
    import uuid
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "hc-seed:" + ":".join(parts)))


def _exec(db, sql, **params):
    return db.execute(text(sql), params)


def _scalar(db, sql, **params):
    return db.execute(text(sql), params).scalar()


# ---------------------------------------------------------------------------
# Branch & providers
# ---------------------------------------------------------------------------

def get_branch(db) -> str:
    row = db.query(HCBranch).filter(
        HCBranch.tenant_id == TENANT_ID, HCBranch.slug == BRANCH_SLUG
    ).first()
    if not row:
        raise SystemExit(
            f"MedCare branch (slug={BRANCH_SLUG}) not found in tenant {TENANT_ID}. "
            "Expected it to already exist."
        )
    return row.id


def get_or_create_provider(db, branch_id, display_name, specialty, license_no) -> str:
    row = db.query(HCProvider).filter(
        HCProvider.tenant_id == TENANT_ID,
        HCProvider.branch_id == branch_id,
        HCProvider.display_name == display_name,
    ).first()
    if row:
        return row.id
    pid = _det_id("provider", display_name)
    prov = HCProvider(
        id=pid, tenant_id=TENANT_ID, branch_id=branch_id,
        user_id=_det_id("provider-user", display_name),
        provider_type="doctor", specialty=specialty,
        license_number=license_no, display_name=display_name,
        bio=f"{display_name}, {specialty} at MedCare Main Clinic.",
        is_active=True,
    )
    db.add(prov)
    db.flush()
    return pid


def get_or_create_schedule(db, branch_id, provider_id, day_of_week) -> str:
    sid = _det_id("schedule", provider_id, str(day_of_week))
    exists = _scalar(db, "SELECT id FROM hcs_provider_schedules WHERE id=:id", id=sid)
    if exists:
        return sid
    _exec(
        db,
        "INSERT INTO hcs_provider_schedules "
        "(id, tenant_id, branch_id, provider_id, day_of_week, start_time, end_time, "
        " slot_duration_minutes, appointment_types, is_active, created_at, updated_at) "
        "VALUES (:id,:tid,:bid,:pid,:dow,'09:00','17:00',30,"
        " '[\"general_consultation\"]'::jsonb, true, now(), now())",
        id=sid, tid=TENANT_ID, bid=branch_id, pid=provider_id, dow=day_of_week,
    )
    return sid


def get_or_create_slot(db, branch_id, provider_id, schedule_id, slot_date,
                       start_t, appt_type, slot_status) -> str:
    sid = _det_id("slot", provider_id, str(slot_date), start_t)
    exists = _scalar(db, "SELECT id FROM hcs_appointment_slots WHERE id=:id", id=sid)
    if exists:
        return sid
    end_t = "%02d:%s" % (int(start_t[:2]) + (1 if start_t[3:] == "30" else 0),
                         "00" if start_t[3:] == "30" else "30")
    _exec(
        db,
        "INSERT INTO hcs_appointment_slots "
        "(id, tenant_id, branch_id, provider_id, schedule_id, slot_date, start_time, "
        " end_time, appointment_type, status, created_at) "
        "VALUES (:id,:tid,:bid,:pid,:sch,:d,:st,:et,:at,:status, now())",
        id=sid, tid=TENANT_ID, bid=branch_id, pid=provider_id, sch=schedule_id,
        d=slot_date, st=start_t, et=end_t, at=appt_type, status=slot_status,
    )
    return sid


# ---------------------------------------------------------------------------
# Patients
# ---------------------------------------------------------------------------

def get_or_create_patient(db, spec) -> str:
    phone_hash = _hash_phone(spec["phone"])
    existing = _scalar(
        db,
        "SELECT id FROM hc_patients WHERE phone_hash=:ph AND tenant_id=:tid LIMIT 1",
        ph=phone_hash, tid=TENANT_ID,
    )
    if existing:
        return existing

    pid = _det_id("patient", spec["phone"])
    now = datetime.utcnow()
    patient = HCPatient(
        id=pid, tenant_id=TENANT_ID,
        full_name=spec["full_name"], date_of_birth=spec["dob"],
        phone=spec["phone"], email=spec["email"],
        gender=spec["gender"], locale="id-ID",
        consent_version=CONSENT_VERSION, consent_accepted_at=now,
        consent_ip="127.0.0.1", consent_user_agent="seed-demo",
        status="active",
    )
    db.add(patient)
    db.flush()  # PHI columns encrypted via EncryptedPHIType

    # hc_patients has no phone_hash column in the model — set it via raw SQL so
    # the auth route (WHERE phone_hash = ...) can find this patient at login.
    _exec(db, "UPDATE hc_patients SET phone_hash=:ph WHERE id=:id",
          ph=phone_hash, id=pid)

    db.add(HCPatientConsent(
        id=_det_id("consent", pid), tenant_id=TENANT_ID, patient_id=pid,
        consent_type="data_processing", consent_version=CONSENT_VERSION,
        status="active", accepted_at=now, ip="127.0.0.1",
        user_agent="seed-demo", purpose_description="Demo seed consent",
    ))
    db.flush()
    return pid


# ---------------------------------------------------------------------------
# Clinical data per patient
# ---------------------------------------------------------------------------

def seed_encounter(db, branch_id, provider_id, patient_id, completed_at) -> str:
    eid = _det_id("encounter", patient_id)
    if _scalar(db, "SELECT id FROM hc_encounters WHERE id=:id", id=eid):
        return eid
    enc = HCEncounter(
        id=eid, tenant_id=TENANT_ID, branch_id=branch_id,
        patient_id=patient_id, provider_id=provider_id,
        status="completed", started_at=completed_at - timedelta(minutes=30),
        completed_at=completed_at,
        soap_subjective="Patient reports mild headache and fatigue.",
        soap_assessment="Tension headache; advise rest and hydration.",
        patient_summary="Routine check-up. No serious findings.",
        summary_released=True, summary_released_at=completed_at,
    )
    db.add(enc)
    db.flush()
    return eid


def seed_appointments(db, branch_id, provider_id, patient_id,
                      upcoming_slot_id, past_slot_id):
    now = datetime.utcnow()
    # Completed (past)
    past_id = _det_id("appt-past", patient_id)
    if not _scalar(db, "SELECT id FROM hcs_appointments WHERE id=:id", id=past_id):
        _exec(
            db,
            "INSERT INTO hcs_appointments "
            "(id,tenant_id,branch_id,provider_id,patient_id,slot_id,appointment_type,"
            " status,scheduled_at,notes,created_at,updated_at) "
            "VALUES (:id,:tid,:bid,:pid,:pat,:slot,'general_consultation',"
            "'completed',:sched,'Follow-up completed.', now(), now())",
            id=past_id, tid=TENANT_ID, bid=branch_id, pid=provider_id, pat=patient_id,
            slot=past_slot_id, sched=now - timedelta(days=14),
        )
    # Upcoming (confirmed)
    up_id = _det_id("appt-up", patient_id)
    if not _scalar(db, "SELECT id FROM hcs_appointments WHERE id=:id", id=up_id):
        _exec(
            db,
            "INSERT INTO hcs_appointments "
            "(id,tenant_id,branch_id,provider_id,patient_id,slot_id,appointment_type,"
            " status,scheduled_at,notes,created_at,updated_at) "
            "VALUES (:id,:tid,:bid,:pid,:pat,:slot,'general_consultation',"
            "'confirmed',:sched,'Upcoming consultation.', now(), now())",
            id=up_id, tid=TENANT_ID, bid=branch_id, pid=provider_id, pat=patient_id,
            slot=upcoming_slot_id, sched=now + timedelta(days=7),
        )


def get_or_create_medication(db, branch_id) -> str:
    mid = _det_id("medication", "paracetamol", branch_id)
    if _scalar(db, "SELECT id FROM hcp_medications WHERE id=:id", id=mid):
        return mid
    _exec(
        db,
        "INSERT INTO hcp_medications "
        "(id,tenant_id,branch_id,name,generic_name,category,form,strength,unit,"
        " stock_quantity,minimum_stock,unit_price,currency,is_active,created_at,updated_at) "
        "VALUES (:id,:tid,:bid,'Paracetamol 500mg','Paracetamol','analgesic','tablet',"
        "'500mg','tablet',500,50,2500,'IDR',true,now(),now())",
        id=mid, tid=TENANT_ID, bid=branch_id,
    )
    return mid


def seed_prescription(db, branch_id, provider_id, patient_id, encounter_id, med_id):
    rx_id = _det_id("rx", patient_id)
    if not _scalar(db, "SELECT id FROM hcp_prescriptions WHERE id=:id", id=rx_id):
        _exec(
            db,
            "INSERT INTO hcp_prescriptions "
            "(id,tenant_id,branch_id,encounter_id,patient_id,provider_id,status,notes,"
            " created_at,updated_at) "
            "VALUES (:id,:tid,:bid,:enc,:pat,:prov,'active','Take as needed for pain.',"
            " now(),now())",
            id=rx_id, tid=TENANT_ID, bid=branch_id, enc=encounter_id,
            pat=patient_id, prov=provider_id,
        )
    line_id = _det_id("rx-line", patient_id)
    if not _scalar(db, "SELECT id FROM hcp_prescription_lines WHERE id=:id", id=line_id):
        _exec(
            db,
            "INSERT INTO hcp_prescription_lines "
            "(id,tenant_id,prescription_id,medication_id,quantity,dosage_instructions,"
            " days_supply,dispensed_quantity,status) "
            "VALUES (:id,:tid,:rx,:med,20,'1 tablet 3x daily after meals',7,0,'pending')",
            id=line_id, tid=TENANT_ID, rx=rx_id, med=med_id,
        )


def get_or_create_test_panel(db, branch_id) -> str:
    pid = _det_id("panel", "cbc", branch_id)
    if _scalar(db, "SELECT id FROM hcl_test_panels WHERE id=:id", id=pid):
        return pid
    _exec(
        db,
        "INSERT INTO hcl_test_panels "
        "(id,tenant_id,branch_id,code,name,category,turnaround_hours,unit_price,"
        " currency,sample_type,requires_fasting,is_active,created_at,updated_at) "
        "VALUES (:id,:tid,:bid,'CBC','Complete Blood Count','hematology',24,150000,"
        "'IDR','blood',false,true,now(),now())",
        id=pid, tid=TENANT_ID, bid=branch_id,
    )
    return pid


def seed_lab(db, branch_id, provider_id, patient_id, encounter_id, panel_id):
    order_id = _det_id("lab-order", patient_id)
    now = datetime.utcnow()
    if not _scalar(db, "SELECT id FROM hcl_lab_orders WHERE id=:id", id=order_id):
        _exec(
            db,
            "INSERT INTO hcl_lab_orders "
            "(id,tenant_id,branch_id,encounter_id,patient_id,provider_id,status,priority,"
            " clinical_notes,created_at,updated_at) "
            "VALUES (:id,:tid,:bid,:enc,:pat,:prov,'resulted','routine',"
            "'Routine CBC',:ca,now())",
            id=order_id, tid=TENANT_ID, bid=branch_id, enc=encounter_id,
            pat=patient_id, prov=provider_id, ca=now - timedelta(days=10),
        )
    line_id = _det_id("lab-line", patient_id)
    if not _scalar(db, "SELECT id FROM hcl_order_lines WHERE id=:id", id=line_id):
        _exec(
            db,
            "INSERT INTO hcl_order_lines (id,tenant_id,order_id,test_panel_id,status) "
            "VALUES (:id,:tid,:oid,:panel,'resulted')",
            id=line_id, tid=TENANT_ID, oid=order_id, panel=panel_id,
        )
    res_id = _det_id("lab-result", patient_id)
    if not _scalar(db, "SELECT id FROM hcl_results WHERE id=:id", id=res_id):
        _exec(
            db,
            "INSERT INTO hcl_results "
            "(id,tenant_id,order_id,order_line_id,test_panel_id,result_value,result_unit,"
            " reference_range,is_abnormal,is_critical,resulted_by,resulted_at,"
            " shared_with_patient,released_at,notes,created_at) "
            "VALUES (:id,:tid,:oid,:line,:panel,'13.5','g/dL','13.0-17.0',"
            " false,false,:by,:rat,true,:rat,'Within normal range.',:rat)",
            id=res_id, tid=TENANT_ID, oid=order_id, line=line_id, panel=panel_id,
            by=provider_id, rat=now - timedelta(days=9),
        )


def seed_invoice(db, branch_id, patient_id, encounter_id, seq):
    inv_id = _det_id("invoice", patient_id)
    now = datetime.utcnow()
    if not _scalar(db, "SELECT id FROM hcb_invoices WHERE id=:id", id=inv_id):
        inv_number = "INV-DEMO-%04d" % seq
        _exec(
            db,
            "INSERT INTO hcb_invoices "
            "(id,tenant_id,branch_id,patient_id,encounter_id,invoice_number,status,"
            " total_amount,currency,notes,finalized_at,created_at,updated_at) "
            "VALUES (:id,:tid,:bid,:pat,:enc,:num,'finalized',300000,'IDR',"
            "'Consultation + CBC',:fa,:fa,now())",
            id=inv_id, tid=TENANT_ID, bid=branch_id, pat=patient_id, enc=encounter_id,
            num=inv_number, fa=now - timedelta(days=9),
        )
    for idx, (name, code, qty, price, sub) in enumerate([
        ("General Consultation", "CONSULT", 1, 150000, 150000),
        ("Complete Blood Count", "CBC", 1, 150000, 150000),
    ]):
        lid = _det_id("invoice-line", patient_id, code)
        if not _scalar(db, "SELECT id FROM hcb_invoice_lines WHERE id=:id", id=lid):
            _exec(
                db,
                "INSERT INTO hcb_invoice_lines "
                "(id,tenant_id,invoice_id,item_name,item_code,quantity,unit_price,"
                " subtotal,created_at) "
                "VALUES (:id,:tid,:inv,:name,:code,:qty,:price,:sub,now())",
                id=lid, tid=TENANT_ID, inv=inv_id, name=name, code=code,
                qty=qty, price=price, sub=sub,
            )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run() -> dict:
    db = next(get_db())
    try:
        # The patient auth route looks patients up by `phone_hash`, but the
        # hc_patients table ships without that column (model + migrations never
        # added it) — so login/register currently fail at the DB level. Add it
        # idempotently here so seeded patients are findable by the OTP login.
        _exec(db, "ALTER TABLE hc_patients ADD COLUMN IF NOT EXISTS "
                  "phone_hash VARCHAR(64)")
        _exec(db, "CREATE INDEX IF NOT EXISTS idx_hc_patients_phone_hash "
                  "ON hc_patients (phone_hash)")
        db.commit()

        branch_id = get_branch(db)

        prov1 = get_or_create_provider(
            db, branch_id, "Dr. Andi Pratama", "General Practitioner", "SIP-001")
        prov2 = get_or_create_provider(
            db, branch_id, "Dr. Sari Wijaya", "Internal Medicine", "SIP-002")

        # Schedules (Mon/Wed/Fri) for both providers
        for prov in (prov1, prov2):
            for dow in (1, 3, 5):
                get_or_create_schedule(db, branch_id, prov, dow)

        med_id = get_or_create_medication(db, branch_id)
        panel_id = get_or_create_test_panel(db, branch_id)

        today = datetime.utcnow().date()
        counts = {"patients": 0, "appointments": 0, "prescriptions": 0,
                  "lab_orders": 0, "invoices": 0}

        for i, spec in enumerate(DEMO_PATIENTS):
            provider_id = prov1 if i % 2 == 0 else prov2
            schedule_id = get_or_create_schedule(db, branch_id, provider_id, 1)

            patient_id = get_or_create_patient(db, spec)
            counts["patients"] += 1

            up_slot = get_or_create_slot(
                db, branch_id, provider_id, schedule_id,
                today + timedelta(days=7), "10:00", "general_consultation", "booked")
            past_slot = get_or_create_slot(
                db, branch_id, provider_id, schedule_id,
                today - timedelta(days=14), "11:00", "general_consultation", "booked")
            # one available slot so the public booking grid shows openings
            get_or_create_slot(
                db, branch_id, provider_id, schedule_id,
                today + timedelta(days=7), "14:00", "general_consultation", "available")

            completed_at = datetime.utcnow() - timedelta(days=14)
            encounter_id = seed_encounter(db, branch_id, provider_id, patient_id, completed_at)

            seed_appointments(db, branch_id, provider_id, patient_id, up_slot, past_slot)
            counts["appointments"] += 2

            seed_prescription(db, branch_id, provider_id, patient_id, encounter_id, med_id)
            counts["prescriptions"] += 1

            seed_lab(db, branch_id, provider_id, patient_id, encounter_id, panel_id)
            counts["lab_orders"] += 1

            seed_invoice(db, branch_id, patient_id, encounter_id, seq=i + 1)
            counts["invoices"] += 1

        db.commit()
        counts["branch_id"] = branch_id
        counts["tenant_id"] = TENANT_ID
        return counts
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def verify():
    """Mint a token for patient #1 and print routes to curl (dev helper)."""
    from modules.healthcare.sdk.patient_tokens import create_patient_access_token
    pid = _det_id("patient", DEMO_PATIENTS[0]["phone"])
    token = create_patient_access_token(pid, DEMO_PATIENTS[0]["phone"], TENANT_ID)
    print("patient_id:", pid)
    print("token:", token)


if __name__ == "__main__":
    if "--verify" in sys.argv:
        verify()
    else:
        result = run()
        print("Seed complete:")
        for k, v in result.items():
            print(f"  {k}: {v}")
