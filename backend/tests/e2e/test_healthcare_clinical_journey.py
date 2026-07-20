"""
E2E: the core clinical staff journey — registration → queue → encounter → coding,
then orders → billing (prescription → lab order → invoice).

This is the first end-to-end *clinical-workflow* scenario in the suite. Everything else
under `tests/e2e` that touches healthcare exercises auth, the public portal, or patient
self-service; nothing drove a patient through the staff-side clinical spine. It walks one
real journey and asserts the linkage at every hop:

    patient  ─► walk-in visit  ─► queue ticket  ─► call  ─► encounter (EMR hand-off)
             ─► ICD-10 diagnosis  ─► coding summary
             ─► prescription (pharmacy)  ─► lab order (lab)  ─► invoice + finalize (billing)

Why it is skip-guarded rather than hard-wired: the staff healthcare endpoints live on the
healthcare service (`/api/v1/modules/healthcare*`), which the platform backend does NOT
proxy — so the default e2e base (`:8000`, the backend) returns 404 for them. This module
therefore resolves a reachable healthcare base of its own (env first, then a short probe
list) and skips cleanly when the healthcare service or the demo clinic seed is absent, so
it never fails red in an environment that simply isn't wired for it. Where the stack + seed
ARE present (the docker dev stack), it runs the full journey green.

The orders/billing leg needs the catalog seed (medications, test panels, service items) and
the clinic DPA consent from `modules/healthcare/migrations/saas_seed_catalog.sql`; the
per-step discovery helpers skip (never fail) if a prerequisite is missing.

Configuration (all optional):
    E2E_HC_BASE_URL     healthcare service / nginx base (e.g. http://localhost:8080)
    E2E_HC_STAFF_EMAIL  a clinic staff/owner login          default admin@healthpoint.com
    E2E_HC_STAFF_PASS   their password                       default password123
    E2E_HC_BRANCH_ID    the clinic branch (hc_branches.id)   default the seeded HealthPoint Main
"""
import os
import uuid

import httpx
import pytest

pytestmark = pytest.mark.e2e

# Platform base (:8000) — for the login call. Mirrors conftest's env defaults rather than
# importing them, so this module never triggers a second conftest import.
BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = float(os.environ.get("E2E_TIMEOUT", "30"))

STAFF_EMAIL = os.environ.get("E2E_HC_STAFF_EMAIL", "admin@healthpoint.com")
STAFF_PASS = os.environ.get("E2E_HC_STAFF_PASS", "password123")
DEFAULT_BRANCH = os.environ.get("E2E_HC_BRANCH_ID", "1beba417-b2d4-5dda-8c24-3aae164a1f88")

# Where the staff /modules/healthcare API lives. The backend does not proxy it, so try the
# usual suspects in order: explicit env, host-published nginx / healthcare ports, then the
# in-docker-network service aliases (when the suite runs inside the backend container).
_HC_CANDIDATES = [
    os.environ.get("E2E_HC_BASE_URL"),
    "http://localhost:8080",            # frontend nginx (host)
    "http://localhost:9002",            # healthcare service (host)
    "http://healthcare-module:9002",    # compose network alias
    "http://app_buildify_healthcare:9002",
    "http://frontend:80",               # compose nginx
]

HC_PREFIX = "/api/v1/modules/healthcare"
PHARMACY_PREFIX = "/api/v1/modules/healthcare_pharmacy"
LAB_PREFIX = "/api/v1/modules/healthcare_lab"
BILLING_PREFIX = "/api/v1/modules/healthcare_billing"


def _reachable(base: str) -> bool:
    """A base is usable if the staff API answers at all (401 without a token is fine —
    it means the route exists; a connection error or 404 means it does not)."""
    try:
        r = httpx.get(f"{base}{HC_PREFIX}/icd10/search", params={"q": ""}, timeout=5)
        return r.status_code != 404
    except Exception:
        return False


def _resolve_hc_base() -> str:
    for cand in _HC_CANDIDATES:
        if cand and _reachable(cand):
            return cand.rstrip("/")
    pytest.skip("healthcare staff API not reachable from this environment")


def _login_token() -> str:
    try:
        r = httpx.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": STAFF_EMAIL, "password": STAFF_PASS},
            timeout=TIMEOUT,
        )
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"platform login unreachable: {e}")
    if r.status_code != 200 or "access_token" not in r.json():
        pytest.skip(f"clinic staff {STAFF_EMAIL} not seeded / cannot log in (HTTP {r.status_code})")
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def hc():
    """A ready-to-use healthcare-staff client bound to a branch the caller can access.

    Yields an object whose helpers prefix the various healthcare module APIs and carry the
    staff token + X-Branch-ID. Skips (never fails) when the stack/seed is not present.
    """
    base = _resolve_hc_base()
    token = _login_token()
    branch = DEFAULT_BRANCH
    headers = {"Authorization": f"Bearer {token}", "X-Branch-ID": branch}
    client = httpx.Client(base_url=base, headers=headers, timeout=TIMEOUT)

    # Confirm this staff user actually has access to this branch, else the journey is moot.
    probe = client.get(f"{HC_PREFIX}/branches/{branch}/encounters")
    if probe.status_code == 422:
        client.close()
        pytest.skip(f"staff {STAFF_EMAIL} has no access to branch {branch} (X-Branch-ID rejected)")
    if probe.status_code != 200:
        client.close()
        pytest.skip(f"branch {branch} encounters not listable (HTTP {probe.status_code})")

    class _HC:
        branch_id = branch

        # healthcare (registration/queue/encounter/coding) prefix
        def get(self, path, **kw):
            return client.get(f"{HC_PREFIX}{path}", **kw)

        def post(self, path, **kw):
            return client.post(f"{HC_PREFIX}{path}", **kw)

        # sibling module prefixes (pharmacy / lab / billing)
        def mget(self, prefix, path, **kw):
            return client.get(f"{prefix}{path}", **kw)

        def mpost(self, prefix, path, **kw):
            return client.post(f"{prefix}{path}", **kw)

    try:
        yield _HC()
    finally:
        client.close()


# --------------------------------------------------------------------------- #
# discovery helpers — each skips (not fails) if the seed can't supply a prereq
# --------------------------------------------------------------------------- #

def _pick_patient(hc) -> str:
    r = hc.get("/patients", params={"q": "", "page_size": 5})
    assert r.status_code == 200, r.text
    rows = r.json()
    if not rows:
        pytest.skip("no patients seeded at this clinic")
    return rows[0]["id"]


def _pick_medical_department(hc) -> str:
    r = hc.get(f"/branches/{hc.branch_id}/departments")
    assert r.status_code == 200, r.text
    depts = r.json()
    med = next((d for d in depts if d.get("kind") == "medical"), None) or (depts[0] if depts else None)
    if med is None:
        pytest.skip("no departments seeded at this clinic")
    return med["id"]


def _pick_provider(hc) -> str:
    r = hc.get(f"/branches/{hc.branch_id}/providers")
    assert r.status_code == 200, r.text
    provs = r.json()
    if not provs:
        pytest.skip("no providers seeded at this clinic")
    return provs[0]["id"]


def _pick_icd10(hc) -> str:
    r = hc.get("/icd10/search", params={"q": "", "page": 1})
    assert r.status_code == 200, r.text
    codes = r.json()
    if not codes:
        pytest.skip("ICD-10 catalog is empty at this clinic")
    return codes[0]["code"]


def _pick_medication(hc) -> str:
    r = hc.mget(PHARMACY_PREFIX, f"/branches/{hc.branch_id}/medications", params={"page_size": 5})
    assert r.status_code == 200, r.text
    items = r.json().get("items") or []
    if not items:
        pytest.skip("no medications seeded at this clinic (run saas_seed_catalog.sql)")
    return items[0]["id"]


def _pick_test_panel(hc) -> str:
    r = hc.mget(LAB_PREFIX, f"/branches/{hc.branch_id}/test-panels", params={"page_size": 5})
    assert r.status_code == 200, r.text
    items = r.json().get("items") or []
    if not items:
        pytest.skip("no test panels seeded at this clinic (run saas_seed_catalog.sql)")
    return items[0]["id"]


def _pick_service_item(hc) -> dict:
    r = hc.mget(BILLING_PREFIX, f"/branches/{hc.branch_id}/service-items", params={"page_size": 10})
    assert r.status_code == 200, r.text
    items = r.json().get("items") or []
    if not items:
        pytest.skip("no billing service items seeded at this clinic (run saas_seed_catalog.sql)")
    return items[0]


# --------------------------------------------------------------------------- #
# shared journey step — walk-in through to an open encounter
# --------------------------------------------------------------------------- #

def _walk_in_to_encounter(hc) -> dict:
    """Register a walk-in and drive it to an open encounter, asserting linkage at each hop.

    Returns {patient_id, department_id, provider_id, visit_id, encounter_id}.
    """
    b = hc.branch_id
    patient_id = _pick_patient(hc)
    department_id = _pick_medical_department(hc)
    provider_id = _pick_provider(hc)

    # 1. Walk-in registration -> a visit in status 'registered', tied to patient + dept.
    r = hc.post(
        f"/branches/{b}/visits/walk-in",
        json={
            "patient_id": patient_id,
            "department_id": department_id,
            "payment_category": "self_pay",
            "referral_source": "self",
        },
    )
    assert r.status_code == 201, r.text
    visit = r.json()
    visit_id = visit["id"]
    assert visit["patient_id"] == patient_id
    assert visit["department_id"] == department_id
    assert visit["visit_type"] == "walk_in"
    assert visit["status"] == "registered"
    assert visit["encounter_id"] is None

    # 2. Queue ticket -> issued for THIS visit, in the visit's department, status 'waiting'.
    r = hc.post(f"/branches/{b}/visits/{visit_id}/queue-ticket", json={})
    assert r.status_code == 201, r.text
    ticket = r.json()
    assert ticket["visit_id"] == visit_id
    assert ticket["department_id"] == department_id
    assert ticket["status"] == "waiting"
    assert ticket["ticket_number"]

    # 3. Call the ticket -> moves waiting -> called, stamps called_at.
    r = hc.post(f"/branches/{b}/queue-tickets/{ticket['id']}/call")
    assert r.status_code == 200, r.text
    called = r.json()
    assert called["status"] == "called"
    assert called["called_at"]

    # 4. EMR hand-off -> opens an encounter for the visit; visit now has that encounter.
    r = hc.post(f"/branches/{b}/visits/{visit_id}/encounter", json={"provider_id": provider_id})
    assert r.status_code == 201, r.text
    handoff = r.json()
    encounter_id = handoff["encounter_id"]
    assert handoff["visit_id"] == visit_id
    assert encounter_id

    return {
        "patient_id": patient_id,
        "department_id": department_id,
        "provider_id": provider_id,
        "visit_id": visit_id,
        "encounter_id": encounter_id,
    }


# --------------------------------------------------------------------------- #
# the journeys
# --------------------------------------------------------------------------- #

def test_clinical_journey_registration_to_coding(hc):
    """One patient, walked end-to-end through the staff clinical spine, asserting that
    each artifact is created AND correctly linked to the previous one."""
    b = hc.branch_id
    ctx = _walk_in_to_encounter(hc)
    encounter_id = ctx["encounter_id"]

    # 5. Code the encounter -> attach a primary ICD-10 diagnosis.
    icd10 = _pick_icd10(hc)
    r = hc.post(
        f"/branches/{b}/encounters/{encounter_id}/diagnoses",
        json={"icd10_code": icd10, "is_primary": True, "sequence": 1},
    )
    assert r.status_code == 201, r.text
    dx = r.json()
    assert dx["encounter_id"] == encounter_id
    assert dx["icd10_code"] == icd10
    assert dx["is_primary"] is True

    # 6. Coding summary -> the encounter reflects the diagnosis we just filed.
    r = hc.get(f"/branches/{b}/encounters/{encounter_id}/coding-summary")
    assert r.status_code == 200, r.text
    summary = r.json()
    codes = [d.get("icd10_code") for d in (summary.get("diagnoses") or [])]
    assert icd10 in codes, f"filed diagnosis {icd10} not in coding summary: {summary}"


def test_clinical_journey_orders_and_billing(hc):
    """Continue the spine into orders + billing: from an open encounter, file a prescription
    (pharmacy), a lab order (lab), then an invoice that is created draft and finalized
    (billing) — asserting each artifact links back to the encounter/patient."""
    b = hc.branch_id
    ctx = _walk_in_to_encounter(hc)
    encounter_id = ctx["encounter_id"]
    patient_id = ctx["patient_id"]

    # 7. Prescription -> pending, linked to the encounter, carrying the ordered line.
    med_id = _pick_medication(hc)
    r = hc.mpost(
        PHARMACY_PREFIX,
        f"/branches/{b}/prescriptions",
        json={
            "encounter_id": encounter_id,
            "lines": [
                {
                    "medication_id": med_id,
                    "quantity": 10,
                    "dosage_instructions": "1 tablet 3x daily after meals",
                    "days_supply": 3,
                }
            ],
        },
    )
    assert r.status_code == 201, r.text
    rx = r.json()
    assert rx["encounter_id"] == encounter_id
    assert rx["status"] == "pending"
    assert any(ln["medication_id"] == med_id for ln in rx["lines"])

    # 8. Lab order -> ordered, linked to the encounter, carrying the requested panel.
    panel_id = _pick_test_panel(hc)
    r = hc.mpost(
        LAB_PREFIX,
        f"/branches/{b}/orders",
        json={
            "encounter_id": encounter_id,
            "test_panel_ids": [panel_id],
            "priority": "routine",
            "clinical_notes": "Baseline labs for this encounter.",
        },
    )
    assert r.status_code == 201, r.text
    order = r.json()
    assert order["encounter_id"] == encounter_id
    assert order["status"] == "ordered"

    # 9. Invoice -> created as a draft with an auto-calculated total from the service item.
    item = _pick_service_item(hc)
    r = hc.mpost(
        BILLING_PREFIX,
        f"/branches/{b}/invoices",
        json={
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "lines": [{"service_item_id": item["id"], "quantity": 1}],
            "notes": "Clinical journey e2e invoice.",
        },
    )
    assert r.status_code == 201, r.text
    invoice = r.json()
    invoice_id = invoice["id"]
    assert invoice["patient_id"] == patient_id
    assert invoice["encounter_id"] == encounter_id
    assert invoice["status"] == "draft"
    assert float(invoice["total_amount"]) == float(item["unit_price"])
    assert any(ln["service_item_id"] == item["id"] for ln in invoice["lines"])

    # 10. Finalize -> the invoice becomes immutable/finalized.
    r = hc.mpost(BILLING_PREFIX, f"/branches/{b}/invoices/{invoice_id}/finalize")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "finalized"


def test_walk_in_rejects_unknown_department(hc):
    """A guard case on the same path — a bogus department is refused, so the journey's
    green result above is real validation, not an anything-goes endpoint."""
    patient_id = _pick_patient(hc)
    r = hc.post(
        f"/branches/{hc.branch_id}/visits/walk-in",
        json={
            "patient_id": patient_id,
            "department_id": str(uuid.uuid4()),
            "payment_category": "self_pay",
            "referral_source": "self",
        },
    )
    assert r.status_code in (400, 404, 422), r.text
