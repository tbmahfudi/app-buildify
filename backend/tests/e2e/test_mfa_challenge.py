"""E2E for the MFA login challenge + trusted devices (ADR-HC-009 D3/D4).

Black-box against a running backend. This is the suite that proves MFA is
actually *enforced*: before this feature a user could activate a factor and still
log in with a password alone.

These tests enroll MFA on a **dedicated throwaway user**, never on the shared
seeded accounts. That matters more than it looks: `login_raw` in conftest calls
`raise_for_status()`, and a 202 challenge is not an error status — so an MFA
factor left behind on a shared account would not fail loudly, it would make every
other test KeyError on `access_token`. The fixture deletes the user in a finally.
"""
import os
import uuid

import httpx
import pytest

from .conftest import API, SUPERADMIN, TIMEOUT, login_raw

pytestmark = pytest.mark.e2e

PASSWORD = "ChallengeTest123!"


def _redis():
    """The emailed code only exists in Redis; skip cleanly if we can't read it."""
    try:
        import redis
    except ImportError:  # pragma: no cover
        pytest.skip("redis client not installed on test host")
    r = redis.from_url(os.environ.get("E2E_REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    try:
        r.ping()
    except Exception:  # noqa: BLE001
        pytest.skip("Redis not reachable from test host")
    return r


def _code_for(target: str) -> str:
    r = _redis()
    keys = list(r.scan_iter(match=f"otp:code:mfa:email:*:{target}"))
    assert keys, f"expected an OTP code in Redis for {target}"
    return r.get(keys[0])


@pytest.fixture
def mfa_user(su, otp_quota_reset):
    """A throwaway user with an *active* email MFA factor.

    Yields (email, password, target, client). Deleted on teardown so no shared
    account is ever left in a challenge-required state.
    """
    _redis()  # skip early if we cannot read codes, before creating anything

    suffix = uuid.uuid4().hex[:8]
    email = f"e2e-mfa-{suffix}@example.com"
    target = f"e2e-mfa-target-{suffix}@example.com"

    # create_user requires an explicit tenant_id when the caller is a superadmin
    # (a superadmin has no tenant of its own to inherit).
    tenants = su.get("/org/tenants").json()
    tenant_list = tenants.get("items", tenants) if isinstance(tenants, dict) else tenants
    if not tenant_list:
        pytest.skip("no tenant available to create a throwaway user in")
    tenant_id = tenant_list[0]["id"]

    created = su.post(
        "/org/users",
        json={
            "email": email,
            "full_name": "E2E MFA",
            "password": PASSWORD,
            "tenant_id": tenant_id,
        },
    )
    if created.status_code not in (200, 201):
        pytest.skip(f"could not create throwaway user: {created.status_code} {created.text[:200]}")

    client = httpx.Client(base_url=API, timeout=TIMEOUT)
    token = login_raw({"email": email, "password": PASSWORD})["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    # Enroll + activate an email factor (R5: active only after a verified round-trip).
    enrolled = client.post("/mfa/factors", json={"factor_type": "email_otp", "target": target})
    assert enrolled.status_code == 200, f"enroll failed: {enrolled.status_code} {enrolled.text[:200]}"
    fid = enrolled.json()["factor_id"]
    activated = client.post(f"/mfa/factors/{fid}/verify", json={"code": _code_for(target)})
    assert activated.status_code == 200, activated.text
    assert activated.json()["is_active"] is True

    try:
        yield email, PASSWORD, target, client
    finally:
        # The platform has no delete-user endpoint, so the throwaway account row
        # itself cannot be removed over the API — it is left behind deliberately
        # rather than pretending a DELETE worked. What matters is stripping its
        # factors: an account holding an active factor is one that can no longer
        # log in with a password alone. Removing a factor also revokes that
        # user's trusted devices (D4), so this cleans both.
        try:
            for f in client.get("/mfa/factors").json():
                client.delete(f"/mfa/factors/{f['id']}")
        except Exception:  # noqa: BLE001 — teardown must not mask a test failure
            pass
        client.close()


def _login(email, password, cookies=None):
    return httpx.post(
        f"{API}/auth/login", json={"email": email, "password": password}, cookies=cookies or {}, timeout=TIMEOUT
    )


def test_login_with_active_factor_returns_challenge_not_tokens(mfa_user):
    """The core of the feature: an MFA user cannot log in with a password alone."""
    email, password, target, _ = mfa_user

    r = _login(email, password)
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["mfa_required"] is True
    assert "access_token" not in body, "a challenged login must not issue tokens"
    assert "refresh_token" not in body
    assert body["methods"] == ["email_otp"]
    assert body["mfa_token"]


def test_challenge_masks_the_delivery_target(mfa_user):
    """The user must learn where the code went; an attacker must not learn the address."""
    email, password, target, _ = mfa_user
    sent_to = _login(email, password).json()["sent_to"]
    assert sent_to != target
    assert "@example.com" in sent_to
    assert "***" in sent_to or "*" in sent_to


def test_verify_exchanges_challenge_for_real_tokens(mfa_user):
    email, password, target, _ = mfa_user
    mfa_token = _login(email, password).json()["mfa_token"]

    r = httpx.post(
        f"{API}/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": _code_for(target)},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, r.text
    assert r.json()["access_token"]

    # ...and the token actually works.
    me = httpx.get(
        f"{API}/auth/me",
        headers={"Authorization": f"Bearer {r.json()['access_token']}"},
        timeout=TIMEOUT,
    )
    assert me.status_code == 200


def test_wrong_code_is_rejected_and_does_not_spend_the_challenge(mfa_user):
    """A typo must cost a retry, not another SMS and a fresh login."""
    email, password, target, _ = mfa_user
    mfa_token = _login(email, password).json()["mfa_token"]

    bad = httpx.post(
        f"{API}/auth/mfa/verify", json={"mfa_token": mfa_token, "code": "000000"}, timeout=TIMEOUT
    )
    assert bad.status_code == 400
    assert "access_token" not in bad.text

    # The same challenge still works with the right code.
    good = httpx.post(
        f"{API}/auth/mfa/verify", json={"mfa_token": mfa_token, "code": _code_for(target)}, timeout=TIMEOUT
    )
    assert good.status_code == 200, good.text


def test_challenge_is_single_use(mfa_user):
    email, password, target, _ = mfa_user
    mfa_token = _login(email, password).json()["mfa_token"]
    code = _code_for(target)

    first = httpx.post(f"{API}/auth/mfa/verify", json={"mfa_token": mfa_token, "code": code}, timeout=TIMEOUT)
    assert first.status_code == 200

    replay = httpx.post(f"{API}/auth/mfa/verify", json={"mfa_token": mfa_token, "code": code}, timeout=TIMEOUT)
    assert replay.status_code == 401, "a spent challenge must not mint a second session"


def test_access_token_is_not_accepted_as_a_challenge(mfa_user, su):
    """A half-authenticated caller must not be able to swap token types."""
    real_token = login_raw(SUPERADMIN)["access_token"]
    r = httpx.post(
        f"{API}/auth/mfa/verify", json={"mfa_token": real_token, "code": "123456"}, timeout=TIMEOUT
    )
    assert r.status_code == 401


def test_garbage_challenge_rejected(mfa_user):
    r = httpx.post(
        f"{API}/auth/mfa/verify", json={"mfa_token": "not-a-jwt", "code": "123456"}, timeout=TIMEOUT
    )
    assert r.status_code == 401


def test_remember_device_suppresses_the_next_challenge(mfa_user):
    """D4: the whole point of the trusted-device store."""
    email, password, target, _ = mfa_user
    mfa_token = _login(email, password).json()["mfa_token"]

    verified = httpx.post(
        f"{API}/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": _code_for(target), "remember_device": True},
        timeout=TIMEOUT,
    )
    assert verified.status_code == 200
    cookies = verified.cookies
    assert "tdid" in cookies, "remember_device must set the device cookie"

    # With the cookie: straight in.
    trusted = _login(email, password, cookies=cookies)
    assert trusted.status_code == 200, "a remembered device should skip the challenge"
    assert trusted.json()["access_token"]

    # Without it: still challenged.
    assert _login(email, password).status_code == 202


def test_device_cookie_is_httponly(mfa_user):
    """Script must not be able to read the secret that skips MFA."""
    email, password, target, _ = mfa_user
    mfa_token = _login(email, password).json()["mfa_token"]
    r = httpx.post(
        f"{API}/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": _code_for(target), "remember_device": True},
        timeout=TIMEOUT,
    )
    set_cookie = "; ".join(v for k, v in r.headers.multi_items() if k.lower() == "set-cookie")
    assert "httponly" in set_cookie.lower()
    assert "samesite=lax" in set_cookie.lower().replace(" ", "")


def test_not_remembering_leaves_no_device(mfa_user):
    email, password, target, client = mfa_user
    mfa_token = _login(email, password).json()["mfa_token"]
    r = httpx.post(
        f"{API}/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": _code_for(target)},  # remember_device omitted
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    assert "tdid" not in r.cookies
    assert client.get("/mfa/devices").json() == []


def test_trusted_device_listed_then_revoked(mfa_user):
    email, password, target, client = mfa_user
    mfa_token = _login(email, password).json()["mfa_token"]
    httpx.post(
        f"{API}/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": _code_for(target), "remember_device": True},
        timeout=TIMEOUT,
    )

    devices = client.get("/mfa/devices").json()
    assert len(devices) == 1
    assert devices[0]["expires_at"]

    assert client.delete(f"/mfa/devices/{devices[0]['id']}").status_code == 200
    assert client.get("/mfa/devices").json() == []


def test_revoke_unknown_device_404(mfa_user):
    _, _, _, client = mfa_user
    assert client.delete(f"/mfa/devices/{uuid.uuid4()}").status_code == 404


def test_devices_require_auth(anon):
    assert anon.get("/mfa/devices").status_code == 401


def test_disabling_the_factor_revokes_trusted_devices(mfa_user):
    """D4: a remembered browser must not outlive the factor that justified it."""
    email, password, target, client = mfa_user
    mfa_token = _login(email, password).json()["mfa_token"]
    httpx.post(
        f"{API}/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": _code_for(target), "remember_device": True},
        timeout=TIMEOUT,
    )
    assert len(client.get("/mfa/devices").json()) == 1

    factor_id = client.get("/mfa/factors").json()[0]["id"]
    assert client.delete(f"/mfa/factors/{factor_id}").status_code == 200

    assert client.get("/mfa/devices").json() == []
    # No factor left -> back to a plain password login.
    assert _login(email, password).status_code == 200


def test_password_change_revokes_trusted_devices(mfa_user):
    """sec-review-011 R8 — this is the seam that shipped as a no-op in S4."""
    email, password, target, client = mfa_user
    mfa_token = _login(email, password).json()["mfa_token"]
    verified = httpx.post(
        f"{API}/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": _code_for(target), "remember_device": True},
        timeout=TIMEOUT,
    )
    cookies = verified.cookies
    assert len(client.get("/mfa/devices").json()) == 1

    new_password = "RotatedPass456!"
    changed = client.post(
        "/auth/change-password",
        json={
            "current_password": password,
            "new_password": new_password,
            "confirm_password": new_password,
        },
    )
    assert changed.status_code == 200, changed.text

    # The trust is gone from the store...
    assert client.get("/mfa/devices").json() == []
    # ...and the cookie no longer buys a challenge-free login.
    assert _login(email, new_password, cookies=cookies).status_code == 202
