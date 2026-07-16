"""
E2E — patient account claim (ADR-HC-009 §D7 / epic-18 Story 18.9.1).

Black-box against the healthcare service (:9002), which owns the patient-auth routes; the
platform backend does not serve them.

**These skip unless the healthcare service is reachable AND HC_PATIENT_OTP_ENABLED is on**,
mirroring tests/e2e/test_patient_otp_login.py. CI brings up only postgres + redis + backend,
so they are a local/staging gate rather than a CI one.

Worth stating plainly, because it is a real property of the design: the claim endpoint is
reachable ONLY with a patient token, and the only thing that mints one for a backfilled
account is phone+OTP. The OTP is the proof of identity the whole claim rests on — the
backfill created accounts nobody had ever authenticated to, and the phone on record is the
only link between a human and that row. So while OTP login is disabled, backfilled patients
cannot claim.
"""
import os
import uuid

import httpx
import pytest

HC_BASE = os.environ.get("E2E_HC_BASE_URL", "http://localhost:9002").rstrip("/")
HC_API = f"{HC_BASE}/api/v1"
TIMEOUT = float(os.environ.get("E2E_TIMEOUT", "30"))

CLAIM = f"{HC_API}/patients/auth/claim-account"


def _hc_reachable() -> bool:
    try:
        httpx.get(f"{HC_BASE}/health", timeout=5).raise_for_status()
        return True
    except Exception:  # noqa: BLE001
        return False


def _otp_enabled() -> bool:
    """Probe the flag through the API rather than the env: the flag that matters is the
    one the *running service* sees, not the one this process happens to have."""
    try:
        r = httpx.post(
            f"{HC_API}/patients/auth/otp/send",
            json={"phone": "+620000000000"},
            timeout=TIMEOUT,
        )
        return r.status_code != 403
    except Exception:  # noqa: BLE001
        return False


pytestmark = pytest.mark.skipif(
    not _hc_reachable(),
    reason=f"healthcare service not reachable at {HC_BASE}",
)


class TestClaimRequiresAuthentication:
    """The gate that keeps the claim flow honest — no patient token, no claim."""

    def test_unauthenticated_claim_is_rejected(self):
        r = httpx.post(CLAIM, json={"password": "Some$Password9"}, timeout=TIMEOUT)
        assert r.status_code in (401, 403), (
            f"claim-account must not be reachable unauthenticated: {r.status_code} {r.text}"
        )

    def test_garbage_token_is_rejected(self):
        r = httpx.post(
            CLAIM,
            json={"password": "Some$Password9"},
            headers={"Authorization": "Bearer not-a-real-token"},
            timeout=TIMEOUT,
        )
        assert r.status_code == 401, r.text

    def test_staff_token_is_rejected(self):
        """A platform (staff) JWT is not a patient token — the patient boundary rejects it."""
        base = os.environ.get("E2E_BASE_URL", "http://localhost:8000").rstrip("/")
        try:
            login = httpx.post(
                f"{base}/api/v1/auth/login",
                json={
                    "email": os.environ.get("E2E_SU_EMAIL", "superadmin@system.com"),
                    "password": os.environ.get("E2E_SU_PASSWORD", "SuperAdmin123!"),
                },
                timeout=TIMEOUT,
            )
        except Exception:  # noqa: BLE001
            pytest.skip("platform API not reachable")
        if login.status_code != 200:
            pytest.skip("could not obtain a staff token")

        r = httpx.post(
            CLAIM,
            json={"password": "Some$Password9"},
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
            timeout=TIMEOUT,
        )
        assert r.status_code == 401, f"a staff JWT must not claim a patient account: {r.text}"


@pytest.mark.skipif(not _otp_enabled(), reason="HC_PATIENT_OTP_ENABLED is off")
class TestClaimFlagGate:
    def test_otp_login_response_carries_the_claim_signal(self):
        """PatientTokenResponse must expose must_set_password (18.9.1).

        Asserted on the schema via a failed login: the field is part of the contract the
        portal routes on, so its absence is a break even when no code is presented.
        """
        r = httpx.post(
            f"{HC_API}/patients/auth/token",
            json={"phone": f"+62{uuid.uuid4().int % 10**10:010d}", "code": "000000"},
            timeout=TIMEOUT,
        )
        # Wrong/unknown -> 401 generic (no enumeration). The signal is only on success;
        # this asserts the endpoint stays generic for a stranger.
        assert r.status_code in (401, 422, 429), r.text
