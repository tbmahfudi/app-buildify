"""
E2E for the platform MFA endpoints (ADR-011 S4) — enroll / verify / disable.

Black-box against a running backend (uses the shared `user` client). The full
enroll->verify->active happy path needs to read the emailed code, which only
Redis has; that one assertion is skipped if Redis is unreachable from the test
host (mirrors the healthcare e2e's connectivity skips) so the rest of the suite
still runs in a DB/Redis-less CI.

Each test uses a *unique* email target so the OTP resend cooldown (per
purpose/channel/target) never collides across tests.
"""
import os
import uuid

import pytest

TARGET_PREFIX = "e2e-mfa-"


def _target() -> str:
    return f"{TARGET_PREFIX}{uuid.uuid4().hex[:8]}@example.com"


def _cleanup(client):
    """Remove any factors this suite created so reruns start clean."""
    for f in client.get("/mfa/factors").json():
        if str(f.get("target", "")).startswith(TARGET_PREFIX):
            client.delete(f"/mfa/factors/{f['id']}")


@pytest.fixture
def mfa_client(user):
    _cleanup(user)
    yield user
    _cleanup(user)


def test_list_requires_auth(anon):
    assert anon.get("/mfa/factors").status_code == 401


def test_enroll_rejects_unknown_factor_type(mfa_client):
    r = mfa_client.post("/mfa/factors", json={"factor_type": "totp", "target": _target()})
    assert r.status_code == 400


def test_enroll_rejects_bad_email(mfa_client):
    r = mfa_client.post("/mfa/factors", json={"factor_type": "email_otp", "target": "not-an-email"})
    assert r.status_code == 400


def test_enroll_creates_inactive_factor(mfa_client):
    r = mfa_client.post("/mfa/factors", json={"factor_type": "email_otp", "target": _target()})
    assert r.status_code == 200, r.text
    fid = r.json()["factor_id"]

    factors = {f["id"]: f for f in mfa_client.get("/mfa/factors").json()}
    assert factors[fid]["is_active"] is False  # R5 — not trusted until verified


def test_verify_wrong_code_rejected(mfa_client):
    fid = mfa_client.post(
        "/mfa/factors", json={"factor_type": "email_otp", "target": _target()}
    ).json()["factor_id"]
    r = mfa_client.post(f"/mfa/factors/{fid}/verify", json={"code": "000000"})
    assert r.status_code == 400


def test_disable_missing_factor_404(mfa_client):
    assert mfa_client.delete("/mfa/factors/00000000-0000-0000-0000-000000000000").status_code == 404


def test_full_enroll_verify_disable(mfa_client):
    """Happy path — needs the real code from Redis; skips if Redis is unreachable."""
    try:
        import redis
    except ImportError:  # pragma: no cover
        pytest.skip("redis client not installed on test host")

    r = redis.from_url(os.environ.get("E2E_REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    try:
        r.ping()
    except Exception:  # noqa: BLE001
        pytest.skip("Redis not reachable from test host; skipping happy-path verify")

    target = _target()
    fid = mfa_client.post(
        "/mfa/factors", json={"factor_type": "email_otp", "target": target}
    ).json()["factor_id"]

    keys = list(r.scan_iter(match=f"otp:code:mfa:email:*:{target}"))
    assert keys, "expected an OTP code in Redis after enroll"
    code = r.get(keys[0])

    r_verify = mfa_client.post(f"/mfa/factors/{fid}/verify", json={"code": code})
    assert r_verify.status_code == 200, r_verify.text
    assert r_verify.json()["is_active"] is True  # R5 — ownership proven, now active

    # Re-enrolling an already-active factor is a benign conflict (no new code sent).
    dup = mfa_client.post("/mfa/factors", json={"factor_type": "email_otp", "target": target})
    assert dup.status_code == 409

    assert mfa_client.delete(f"/mfa/factors/{fid}").status_code == 200
    remaining = [f["id"] for f in mfa_client.get("/mfa/factors").json()]
    assert fid not in remaining
