"""
E2E — patient phone/OTP login is RETIRED (ADR-011 S6b).

S6b removed the healthcare module's phone+OTP patient auth once the D7 backfill left
no OTP-only patients: the `/api/v1/patients/auth/otp/send`, `.../otp/verify`,
`.../token` (OTP login) and the OTP-gated `.../claim-account` endpoints are gone, along
with the HC_PATIENT_OTP_ENABLED flag. Patient auth is now password-primary (email +
password + platform MFA), with the platform-login → `/auth/from-platform` bridge minting
the portal session; a straggler backfilled account is onboarded via staff-link + reset.

This suite replaces the old S6a OTP-contract suite. It pins the retirement: the removed
routes must return 404 (route absent), not 403 (route present but flag off) or any 2xx.
It also confirms the endpoints that REMAIN are still mounted, so a 404 here means "this
specific route was removed", not "the patient-auth router failed to load".

Targets the healthcare service directly (it runs as its own app); override with
HC_BASE_URL. Skips when that service isn't reachable.
"""
import os
import uuid

import httpx
import pytest

pytestmark = pytest.mark.e2e

HC_BASE = os.environ.get("HC_BASE_URL", "http://localhost:9002").rstrip("/")
HC_API = f"{HC_BASE}/api/v1"
JSON_HEADERS = {"X-Captcha-Token": "test", "Content-Type": "application/json"}

# Removed with S6b — every one must be 404 (route absent).
_REMOVED_ROUTES = [
    ("post", "/patients/auth/otp/send", {"phone": "+62899000000001"}),
    ("post", "/patients/auth/otp/verify", {"phone": "+62899000000001", "code": "000000"}),
    ("post", "/patients/auth/token", {"phone": "+62899000000001", "code": "000000"}),
    ("post", "/patients/auth/claim-account", {"password": "Sup3rSecret!x"}),
]

# Still present after S6b — used to prove the router loaded (so a 404 above is a real
# removal, not a dead service). We only assert these are NOT 404; their own contracts
# are covered by their own suites.
_KEPT_ROUTES = [
    ("post", "/patients/auth/refresh", {}),
    ("post", "/patients/auth/logout", {}),
    ("post", "/patients/auth/from-platform", {}),
]


def _reachable() -> bool:
    try:
        # A kept route answering (any status) means the service + router are up.
        r = httpx.post(f"{HC_API}/patients/auth/logout", json={}, timeout=5)
        return r.status_code != 404 or True  # logout returns 204; reachable if it answered
    except Exception:
        return False


skip_if_unreachable = pytest.mark.skipif(
    not _reachable(), reason=f"healthcare patient-auth not reachable at {HC_API}")


@skip_if_unreachable
def test_kept_patient_auth_routes_still_mounted():
    """Guard: the surviving patient-auth routes are present, so a 404 on a removed
    route below is a genuine removal rather than a router that failed to load."""
    for method, path, body in _KEPT_ROUTES:
        r = httpx.request(method, f"{HC_API}{path}", json=body, timeout=10)
        assert r.status_code != 404, f"{path} unexpectedly 404 — router may not be loaded ({r.text})"


@skip_if_unreachable
@pytest.mark.parametrize("method,path,body", _REMOVED_ROUTES)
def test_otp_and_claim_routes_removed(method, path, body):
    """Each S6b-removed route must be 404 (absent). A 403 would mean the flag gate is
    still there (route not removed); a 2xx would mean it still works."""
    r = httpx.request(method, f"{HC_API}{path}", json=body, headers=JSON_HEADERS, timeout=10)
    assert r.status_code == 404, (
        f"{path} returned {r.status_code}, expected 404 (route should be removed by S6b): {r.text}"
    )
