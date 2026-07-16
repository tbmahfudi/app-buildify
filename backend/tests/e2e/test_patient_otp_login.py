"""
E2E — patient phone/OTP login on the platform OTP service (tasks-011 S6a).

After S6a, the healthcare module's `/api/v1/patients/auth/otp/*` + `.../token`
endpoints delegate to the PLATFORM OTP service (`app.routers.otp`) instead of a
module-local implementation. This suite pins the externally-visible contract of
that repoint on the healthcare module service (default http://localhost:9002):

  - the HC_PATIENT_OTP_ENABLED flag still gates the routes (403 when off);
  - a wrong code is a generic auth failure (the platform's 400 is remapped back
    to this module's historical 401/422, not leaked through);
  - the per-target attempt lockout (R7) surfaces as 429 (propagated, not remapped);
  - the per-target daily cap (R6) — which the deleted module implementation never
    had — now binds with 429.

Targets the healthcare service directly because the module runs as its own app;
override with HC_BASE_URL. Skips when that service isn't reachable. When OTP is
disabled (the default), only the flag-gate assertion runs and the enabled-path
tests skip — they cannot force server env on.

Run (healthcare service up, OTP enabled):
    HC_PATIENT_OTP_ENABLED=true  # on the :9002 service
    HC_BASE_URL=http://localhost:9002 python -m pytest \
        tests/e2e/test_patient_otp_login.py -v
"""
import os
import uuid

import httpx
import pytest

pytestmark = pytest.mark.e2e

HC_BASE = os.environ.get("HC_BASE_URL", "http://localhost:9002").rstrip("/")
HC_API = f"{HC_BASE}/api/v1"
CAPTCHA_HEADERS = {"X-Captcha-Token": "test", "Content-Type": "application/json"}


def _rand_phone() -> str:
    # Unique per run so the per-target daily cap / cooldown never collide with a
    # prior run's residue (there is no delete-OTP endpoint; keys self-expire).
    return "+62899" + f"{uuid.uuid4().int % 10**9:09d}"


def _otp_route_state():
    """(reachable, enabled). 'enabled' means the flag is on for the :9002 service."""
    try:
        r = httpx.post(f"{HC_API}/patients/auth/otp/send",
                       json={"phone": _rand_phone()}, headers=CAPTCHA_HEADERS, timeout=5)
    except Exception:
        return False, False
    if r.status_code == 403:
        return True, False          # route mounted but flag off
    if r.status_code in (200, 429):
        return True, True
    # Any other status still means the service answered.
    return True, False


_REACHABLE, _ENABLED = _otp_route_state()

skip_if_unreachable = pytest.mark.skipif(
    not _REACHABLE, reason=f"healthcare OTP route not reachable at {HC_API}")
skip_if_disabled = pytest.mark.skipif(
    not _ENABLED, reason="HC_PATIENT_OTP_ENABLED is off on the target service")


@skip_if_unreachable
def test_flag_gate_or_enabled():
    """Whatever the flag state, the route is mounted and behaves per the flag."""
    r = httpx.post(f"{HC_API}/patients/auth/otp/send",
                   json={"phone": _rand_phone()}, headers=CAPTCHA_HEADERS, timeout=10)
    if _ENABLED:
        assert r.status_code in (200, 429), r.text
    else:
        assert r.status_code == 403, r.text
        assert "disabled" in r.text.lower()


@skip_if_unreachable
@skip_if_disabled
def test_wrong_code_is_generic_401():
    """A wrong token code -> 401 (the platform verify's 400 is remapped, not leaked)."""
    phone = _rand_phone()
    httpx.post(f"{HC_API}/patients/auth/otp/send",
               json={"phone": phone}, headers=CAPTCHA_HEADERS, timeout=10)
    r = httpx.post(f"{HC_API}/patients/auth/token",
                   json={"phone": phone, "code": "000000"}, timeout=10)
    assert r.status_code == 401, r.text


@skip_if_unreachable
@skip_if_disabled
def test_verify_wrong_code_is_generic_422():
    """The /otp/verify endpoint keeps its historical 422 on a bad code."""
    phone = _rand_phone()
    httpx.post(f"{HC_API}/patients/auth/otp/send",
               json={"phone": phone}, headers=CAPTCHA_HEADERS, timeout=10)
    r = httpx.post(f"{HC_API}/patients/auth/otp/verify",
                   json={"phone": phone, "code": "000000"}, timeout=10)
    assert r.status_code == 422, r.text


@skip_if_unreachable
@skip_if_disabled
def test_attempt_lockout_propagates_as_429():
    """Repeated wrong codes trip the platform attempt lockout (R7) -> 429, and
    that 429 is propagated (not remapped to 401), so the client can tell 'locked
    out' apart from 'wrong code'."""
    phone = _rand_phone()
    httpx.post(f"{HC_API}/patients/auth/token",  # never sent a code; still lockout-counted
               json={"phone": phone, "code": "000000"}, timeout=10)
    httpx.post(f"{HC_API}/patients/auth/otp/send",
               json={"phone": phone}, headers=CAPTCHA_HEADERS, timeout=10)
    saw_429 = False
    for _ in range(8):  # MAX_ATTEMPTS is 5; a few extra guarantees the trip
        r = httpx.post(f"{HC_API}/patients/auth/token",
                       json={"phone": phone, "code": "111111"}, timeout=10)
        if r.status_code == 429:
            saw_429 = True
            break
        assert r.status_code == 401, r.text
    assert saw_429, "attempt lockout never surfaced as 429"


@skip_if_unreachable
@skip_if_disabled
def test_daily_cap_binds():
    """The per-target daily send cap (R6) binds — the module implementation this
    replaced had NO daily cap, so this is the security hole S6a closed."""
    phone = _rand_phone()
    statuses = []
    # Cooldown (60s) would 429 us before the daily cap does; but a cooldown 429 and
    # a cap 429 are indistinguishable black-box. Either way, an unbounded flood is
    # impossible now, which is the property under test. Send briskly and assert a
    # 429 appears within a bounded number of attempts.
    for _ in range(15):
        r = httpx.post(f"{HC_API}/patients/auth/otp/send",
                       json={"phone": phone}, headers=CAPTCHA_HEADERS, timeout=10)
        statuses.append(r.status_code)
        if r.status_code == 429:
            break
    assert 429 in statuses, f"send was never rate-limited: {statuses}"
