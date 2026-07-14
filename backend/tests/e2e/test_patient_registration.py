"""
E2E — ADR-011 patient email+password self-registration (verify-email flow).

Covers the S2/S2b endpoints on the healthcare module service:
  POST /api/v1/patients/register   (verify-email, enumeration-safe 202)
  POST /api/v1/patients/activate   (single-use token)

Targets the healthcare service directly (default http://localhost:9002) because
the module runs as its own app; override with HC_BASE_URL. Skips when that
service isn't reachable (mirrors the healthcare probes in the suite).

Run (healthcare service up):
    HC_BASE_URL=http://localhost:9002 python -m pytest tests/e2e/test_patient_registration.py -v
"""
import os
import uuid

import httpx
import pytest

pytestmark = pytest.mark.e2e

HC_BASE = os.environ.get("HC_BASE_URL", "http://localhost:9002").rstrip("/")
HC_API = f"{HC_BASE}/api/v1"
# Dev captcha secret is "test"; require_captcha accepts this token in dev.
CAPTCHA_HEADERS = {"X-Captcha-Token": "test", "Content-Type": "application/json"}


def _hc_register_available() -> bool:
    try:
        # An empty body hits validation (422) only if the route is mounted.
        r = httpx.post(f"{HC_API}/patients/register", json={}, timeout=5)
        return r.status_code in (422, 400, 403)
    except Exception:
        return False


skip_if_no_hc = pytest.mark.skipif(
    not _hc_register_available(),
    reason=f"healthcare patient-register route not reachable at {HC_API}",
)


def _payload(**over):
    body = {
        "email": f"e2e.{uuid.uuid4().hex[:10]}@example.com",
        "password": "Xy9$kLmn2Pqr",
        "phone": "+628123456789",
        "full_name": "E2E Patient",
        "date_of_birth": "1990-01-01",
        "gender": "male",
        "consent_accepted": True,
        "consent_version": "v1",
    }
    body.update(over)
    return body


# --------------------------------------------------------------------------
# Runnable without portal context
# --------------------------------------------------------------------------

@skip_if_no_hc
def test_register_empty_body_422():
    r = httpx.post(f"{HC_API}/patients/register", json={}, headers=CAPTCHA_HEADERS, timeout=10)
    assert r.status_code == 422, r.text  # missing required fields


@skip_if_no_hc
def test_register_missing_consent_422():
    # Consent gate runs before the self-service gate, so this is deterministic.
    r = httpx.post(
        f"{HC_API}/patients/register",
        json=_payload(consent_accepted=False),
        headers=CAPTCHA_HEADERS,
        timeout=10,
    )
    assert r.status_code == 422, r.text
    assert "consent" in r.text.lower()


@skip_if_no_hc
def test_register_self_service_off_returns_403():
    # sec-review-011 R4: self-registration is OFF unless the tenant enables it.
    r = httpx.post(f"{HC_API}/patients/register", json=_payload(), headers=CAPTCHA_HEADERS, timeout=10)
    assert r.status_code == 403, r.text
    assert "not enabled" in r.text.lower()


@skip_if_no_hc
def test_activate_invalid_token_returns_400():
    # sec-review-011 R1: generic error, no signal about token existence.
    r = httpx.post(
        f"{HC_API}/patients/activate",
        json={"token": "definitely-not-a-real-token"},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert r.status_code == 400, r.text
    assert "invalid or expired" in r.text.lower()


# --------------------------------------------------------------------------
# Happy path — needs a portal Company context (app.company_id GUC) that public
# self-registration does not yet establish (registration-scope resolution is
# Phase 5 / epic-20). Kept here as executable spec, skipped until wired.
# --------------------------------------------------------------------------

@pytest.mark.skip(
    reason="register 202 needs a resolved Company context (app.company_id); public "
    "self-registration scope resolution is Phase 5/epic-20. See routes_patient_auth."
)
def test_register_then_activate_then_login_happy_path():
    # 1. register -> 202 generic (same message for new + duplicate email, R1)
    body = _payload()
    r1 = httpx.post(f"{HC_API}/patients/register", json=body, headers=CAPTCHA_HEADERS, timeout=10)
    assert r1.status_code == 202
    first_msg = r1.json()["message"]

    r2 = httpx.post(f"{HC_API}/patients/register", json=body, headers=CAPTCHA_HEADERS, timeout=10)
    assert r2.status_code == 202
    assert r2.json()["message"] == first_msg  # duplicate is indistinguishable

    # 2. activation consumes a single-use token -> is_verified=true
    # 3. from-platform seam rejects the patient with 403 until activated
    # (token capture requires the activation-email/redis hook; wired with S4/S5).
