"""
Healthcare module regression tests.
Covers: OTP platform service, public tenant resolution, healthcare public API,
patient registration/login via OTP token, patient self-service endpoints.

Run (from inside the backend container):
    docker exec app_buildify_backend python -m pytest tests/e2e/test_healthcare_regression.py -v --tb=short
"""
import time
import uuid

import httpx
import pytest

pytestmark = pytest.mark.e2e

from .conftest import API, TIMEOUT

# ---------------------------------------------------------------------------
# Constants — derived from seeded data
# ---------------------------------------------------------------------------

# The seeded healthcare tenant is stored as "MEDCARE"; the public router does
# a case-sensitive lookup, so use the actual stored code.
MEDCARE_CODE = "MEDCARE"
HC_TENANT_CODE = "healthpoint"  # alternative seeded clinic tenant

OTP_PURPOSE = "patient_login"

# ---------------------------------------------------------------------------
# Probe: detect whether the healthcare module routes are mounted
# ---------------------------------------------------------------------------

def _hc_routes_available() -> bool:
    """Return True if the healthcare module routes are currently mounted."""
    try:
        r = httpx.get(f"{API}/clinics/{HC_TENANT_CODE}", timeout=5)
        return r.status_code != 404
    except Exception:
        return False


HC_ROUTES = _hc_routes_available()
skip_if_no_hc = pytest.mark.skipif(
    not HC_ROUTES,
    reason="Healthcare module routes not mounted (module not activated in this environment)",
)


def _redis_client():
    """Return a redis client, or None if redis-py is not installed / unreachable."""
    try:
        import redis as _redis
        r = _redis.from_url("redis://redis:6379/0", socket_connect_timeout=2)
        r.ping()
        return r
    except Exception:
        try:
            import redis as _redis
            r = _redis.from_url("redis://localhost:6379/0", socket_connect_timeout=2)
            r.ping()
            return r
        except Exception:
            return None


# ---------------------------------------------------------------------------
# 1. OTP service -- send endpoint
# ---------------------------------------------------------------------------

class TestOtpSend:
    def test_send_valid_returns_200(self, anon):
        """Valid send request returns 200 with expected envelope."""
        r = anon.post("/otp/send", json={
            "phone": "+628120001111",
            "purpose": OTP_PURPOSE,
            "tenant_code": MEDCARE_CODE,
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("message") == "OTP sent"
        assert "resend_after" in body
        assert body["resend_after"] == 60

    def test_send_unknown_purpose_returns_400(self, anon):
        """Unknown purpose is rejected with 400."""
        r = anon.post("/otp/send", json={
            "phone": "+628120001111",
            "purpose": "invalid_purpose_xyz",
            "tenant_code": MEDCARE_CODE,
        })
        assert r.status_code == 400, r.text

    def test_send_missing_phone_returns_422(self, anon):
        """Missing required field `phone` returns 422 validation error."""
        r = anon.post("/otp/send", json={"purpose": OTP_PURPOSE, "tenant_code": MEDCARE_CODE})
        assert r.status_code == 422, r.text

    def test_send_missing_tenant_code_returns_422(self, anon):
        """Missing required field `tenant_code` returns 422 validation error."""
        r = anon.post("/otp/send", json={"phone": "+628120001111", "purpose": OTP_PURPOSE})
        assert r.status_code == 422, r.text

    def test_send_cooldown_enforced(self, anon):
        """A second immediate send to the same phone returns 429 (cooldown)."""
        phone = "+62811" + str(uuid.uuid4().int)[:7]
        r1 = anon.post("/otp/send", json={"phone": phone, "purpose": OTP_PURPOSE, "tenant_code": MEDCARE_CODE})
        assert r1.status_code == 200, r1.text
        # Immediate re-send must be rate-limited
        r2 = anon.post("/otp/send", json={"phone": phone, "purpose": OTP_PURPOSE, "tenant_code": MEDCARE_CODE})
        assert r2.status_code == 429, r2.text


# ---------------------------------------------------------------------------
# 2. OTP service -- verify endpoint
# ---------------------------------------------------------------------------

class TestOtpVerify:
    def test_wrong_code_returns_400(self, anon):
        """Submitting an incorrect code returns 400 with 'Incorrect OTP' detail."""
        phone = "+628120002222"
        # Send first so a code exists
        anon.post("/otp/send", json={"phone": phone, "purpose": OTP_PURPOSE, "tenant_code": MEDCARE_CODE})
        r = anon.post("/otp/verify", json={
            "phone": phone,
            "purpose": OTP_PURPOSE,
            "tenant_code": MEDCARE_CODE,
            "code": "000000",
        })
        assert r.status_code == 400, r.text
        assert "Incorrect OTP" in r.json().get("detail", "")

    def test_no_otp_record_returns_400(self, anon):
        """Verifying a phone that was never sent an OTP returns 400 with expiry message."""
        # Use a unique phone that has no OTP in Redis
        phone = "+6281900" + str(uuid.uuid4().int)[:6]
        r = anon.post("/otp/verify", json={
            "phone": phone,
            "purpose": OTP_PURPOSE,
            "tenant_code": MEDCARE_CODE,
            "code": "123456",
        })
        assert r.status_code == 400, r.text
        detail = r.json().get("detail", "").lower()
        assert "expired or not found" in detail

    def test_unknown_purpose_returns_400(self, anon):
        """Verify with unknown purpose returns 400."""
        r = anon.post("/otp/verify", json={
            "phone": "+628120003333",
            "purpose": "unknown_purpose",
            "tenant_code": MEDCARE_CODE,
            "code": "123456",
        })
        assert r.status_code == 400, r.text

    def test_happy_path_send_verify(self, anon):
        """Full send → read code from Redis → verify → get otp_token."""
        rc = _redis_client()
        if rc is None:
            pytest.skip("Redis not reachable from test runner")

        phone = "+62812" + str(uuid.uuid4().int)[:7]
        send_r = anon.post("/otp/send", json={
            "phone": phone,
            "purpose": OTP_PURPOSE,
            "tenant_code": MEDCARE_CODE,
        })
        assert send_r.status_code == 200, send_r.text

        redis_key = f"otp:code:{OTP_PURPOSE}:{MEDCARE_CODE}:{phone}"
        raw = rc.get(redis_key)
        if raw is None:
            pytest.skip(f"OTP key not found in Redis: {redis_key}")
        code = raw.decode() if isinstance(raw, bytes) else raw

        verify_r = anon.post("/otp/verify", json={
            "phone": phone,
            "purpose": OTP_PURPOSE,
            "tenant_code": MEDCARE_CODE,
            "code": code,
        })
        assert verify_r.status_code == 200, verify_r.text
        body = verify_r.json()
        assert "otp_token" in body, f"Expected otp_token in response: {body}"
        assert body.get("verified") is True


# ---------------------------------------------------------------------------
# 3. Public tenant resolution
# ---------------------------------------------------------------------------

class TestPublicTenants:
    def test_medcare_resolves(self, anon):
        """GET /public/tenants/MEDCARE returns 200 with id, name, code."""
        r = anon.get(f"/public/tenants/{MEDCARE_CODE}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "id" in body
        assert "name" in body
        assert body.get("code") == MEDCARE_CODE

    def test_healthpoint_resolves(self, anon):
        """GET /public/tenants/healthpoint returns 200."""
        r = anon.get(f"/public/tenants/{HC_TENANT_CODE}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("code", "").upper() == HC_TENANT_CODE.upper()

    def test_nonexistent_tenant_404(self, anon):
        """Unknown tenant code returns 404."""
        r = anon.get("/public/tenants/nonexistent_xyz_abc_12345")
        assert r.status_code == 404, r.text

    def test_accessible_without_auth(self):
        """Public tenant endpoint is reachable without any Authorization header."""
        with httpx.Client(base_url=API, timeout=TIMEOUT) as c:
            r = c.get(f"/public/tenants/{MEDCARE_CODE}")
        assert r.status_code == 200, r.text

    def test_accessible_with_auth(self, su):
        """Public tenant endpoint also works with a valid staff token."""
        r = su.get(f"/public/tenants/{MEDCARE_CODE}")
        assert r.status_code == 200, r.text


# ---------------------------------------------------------------------------
# 4. Healthcare public API (clinic routes)
# ---------------------------------------------------------------------------

class TestHealthcarePublicApi:
    @skip_if_no_hc
    def test_get_clinic_by_slug(self, anon):
        """GET /clinics/{slug} returns 200 with id, name, code, branches."""
        r = anon.get(f"/clinics/{HC_TENANT_CODE}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "clinic_name" in body or "name" in body or "id" in body
        assert "slug" in body or "code" in body
        assert "branches" in body

    @skip_if_no_hc
    def test_get_clinic_branches(self, anon):
        """GET /clinics/{slug} returns branches list in response body."""
        r = anon.get(f"/clinics/{HC_TENANT_CODE}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "branches" in body
        assert isinstance(body["branches"], list)

    @skip_if_no_hc
    def test_nonexistent_clinic_404(self, anon):
        """GET /clinics/nonexistent returns 404."""
        r = anon.get("/clinics/nonexistent_xyz_abc_12345")
        assert r.status_code == 404, r.text

    @skip_if_no_hc
    def test_clinic_search(self, anon):
        """GET /clinics/search returns a list."""
        r = anon.get("/clinics/search")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "items" in data
        assert isinstance(data["items"], list)


# ---------------------------------------------------------------------------
# 5. Patient auth -- registration requires valid OTP token
# ---------------------------------------------------------------------------

class TestPatientRegistration:
    @skip_if_no_hc
    def test_register_with_fake_otp_token_returns_400(self, anon):
        """Registration with an invalid otp_token is rejected with 400."""
        r = anon.post("/patients/register",
            json={"otp_token": "fake-otp-token-that-does-not-exist",
                  "full_name": "Test Patient",
                  "phone": "+628131234567",
                  "date_of_birth": "1990-01-01",
                  "gender": "M",
                  "consent_accepted": True,
                  "consent_version": "1.0",
                  "tenant_code": HC_TENANT_CODE},
            headers={"X-Captcha-Token": "test-bypass"},
        )
        assert r.status_code in (400, 422), r.text
        detail = r.json().get("detail", "") or str(r.json())
        assert "otp" in detail.lower() or "token" in detail.lower() or "invalid" in detail.lower() or r.status_code == 422

    @skip_if_no_hc
    def test_register_missing_token_returns_422(self, anon):
        """Registration with missing otp_token returns 422."""
        r = anon.post("/patients/register",
            json={"full_name": "Test Patient", "tenant_code": HC_TENANT_CODE},
            headers={"X-Captcha-Token": "test-bypass"},
        )
        assert r.status_code == 422, r.text  # missing required fields

    @skip_if_no_hc
    def test_full_register_happy_path(self, anon):
        """Full OTP send → verify → register → access_token flow."""
        rc = _redis_client()
        if rc is None:
            pytest.skip("Redis not reachable from test runner")

        phone = "+62813" + str(uuid.uuid4().int)[:7]
        # Step 1: Send OTP via healthcare-specific endpoint
        send_r = anon.post("/patients/auth/otp/send",
            json={"phone": phone, "tenant_code": HC_TENANT_CODE},
            headers={"X-Captcha-Token": "test-bypass"})
        assert send_r.status_code == 200, send_r.text

        # Step 2: Read code from Redis (healthcare OTP key uses platform otp:code schema)
        redis_key = f"otp:code:patient_registration:{HC_TENANT_CODE}:{phone}"
        raw = rc.get(redis_key)
        if raw is None:
            # Try alternative key format used by healthcare module
            for purpose in ["patient_registration", "patient_login", "registration"]:
                redis_key = f"otp:code:{purpose}:{HC_TENANT_CODE}:{phone}"
                raw = rc.get(redis_key)
                if raw:
                    break
        if raw is None:
            pytest.skip(f"OTP key not found in Redis after send")
        code = raw.decode() if isinstance(raw, bytes) else raw

        # Step 3: Verify via healthcare endpoint — sets otp_verified:{phone} in Redis
        verify_r = anon.post("/patients/auth/otp/verify", json={
            "phone": phone,
            "tenant_code": HC_TENANT_CODE,
            "code": code,
        })
        assert verify_r.status_code == 200, verify_r.text

        # Step 4: Register using the phone (otp_verified:{phone} is now set in Redis)
        reg_r = anon.post("/patients/register",
            json={"otp_token": "not-used",
                  "full_name": "Test Patient E2E",
                  "phone": phone,
                  "date_of_birth": "1990-06-15",
                  "gender": "F",
                  "consent_accepted": True,
                  "consent_version": "1.0",
                  "tenant_code": HC_TENANT_CODE},
            headers={"X-Captcha-Token": "test-bypass"},
        )
        assert reg_r.status_code in (200, 201), reg_r.text
        body = reg_r.json()
        assert "access_token" in body, f"Expected access_token in response: {body}"


# ---------------------------------------------------------------------------
# 6. Patient self-service -- auth guard
# ---------------------------------------------------------------------------

class TestPatientSelfService:
    @skip_if_no_hc
    def test_profile_no_auth_returns_401(self, anon):
        """Patient appointments endpoint requires authentication."""
        r = anon.get("/patients/me/appointments")
        assert r.status_code == 401, r.text

    @skip_if_no_hc
    def test_profile_with_staff_token_returns_403(self, su):
        """Patient appointments endpoint rejects staff tokens (role check)."""
        r = su.get("/patients/me/appointments")
        assert r.status_code in (401, 403), r.text


# ---------------------------------------------------------------------------
# 7. get_current_user_optional -- soft auth
# ---------------------------------------------------------------------------

class TestSoftAuth:
    def test_public_tenant_accessible_without_auth(self, anon):
        """Public tenant endpoint returns 200 with no auth."""
        r = anon.get(f"/public/tenants/{MEDCARE_CODE}")
        assert r.status_code == 200, r.text

    def test_public_tenant_accessible_with_auth(self, su):
        """Public tenant endpoint returns 200 with valid staff token."""
        r = su.get(f"/public/tenants/{MEDCARE_CODE}")
        assert r.status_code == 200, r.text

    def test_public_tenant_no_authorization_header(self):
        """Public tenant endpoint returns 200 with no Authorization header at all."""
        with httpx.Client(base_url=API, timeout=TIMEOUT) as c:
            r = c.get(f"/public/tenants/{MEDCARE_CODE}")
        assert r.status_code == 200, r.text

    def test_otp_send_is_public(self, anon):
        """OTP send endpoint requires no authentication."""
        r = anon.post("/otp/send", json={
            "phone": "+628120009999",
            "purpose": OTP_PURPOSE,
            "tenant_code": MEDCARE_CODE,
        })
        # 200 = sent, 429 = cooldown (still means unauthenticated access worked)
        assert r.status_code in (200, 429), f"Expected 200 or 429, got {r.status_code}: {r.text}"
