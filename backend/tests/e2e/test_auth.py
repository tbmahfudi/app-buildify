"""
Exhaustive coverage of the `auth` router (9 operations).

Calibrated to the live contract:
  * missing/!invalid credentials on a protected route -> 403 (FastAPI HTTPBearer)
  * a syntactically valid but unknown account -> 401
  * the platform enforces max_concurrent_sessions; one-off logins use the
    `ephemeral` fixture so they release their slot and never evict `su`.
"""
import pytest

from .conftest import SUPERADMIN, TENANT_USER

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)  # this API returns 403 for a missing bearer token


# --------------------------------------------------------------------------- #
# POST /auth/login
# --------------------------------------------------------------------------- #
class TestLogin:
    def test_login_success_shape(self, ephemeral):
        with ephemeral(SUPERADMIN) as c:
            r = c.get("/auth/me")
            assert r.status_code == 200
        # re-login through anon just to assert the token envelope shape
        import httpx
        from .conftest import API, TIMEOUT
        r = httpx.post(f"{API}/auth/login", json=SUPERADMIN, timeout=TIMEOUT)
        assert r.status_code == 200
        body = r.json()
        for field in ("access_token", "refresh_token", "token_type", "expires_in"):
            assert field in body, f"missing {field} in login response"
        assert body["token_type"].lower() == "bearer"
        assert isinstance(body["expires_in"], int) and body["expires_in"] > 0
        from .conftest import logout_token
        logout_token(body["access_token"])

    def test_login_wrong_password(self, anon):
        r = anon.post("/auth/login", json={**SUPERADMIN, "password": "wrong-pw-123"})
        assert r.status_code == 401

    def test_login_unknown_user(self, anon):
        # valid email *format* but no such account -> reaches auth logic -> 401
        r = anon.post("/auth/login", json={"email": "ghost@example.com", "password": "whatever123"})
        assert r.status_code == 401

    def test_login_missing_password(self, anon):
        r = anon.post("/auth/login", json={"email": SUPERADMIN["email"]})
        assert r.status_code == 422

    def test_login_malformed_email(self, anon):
        r = anon.post("/auth/login", json={"email": "not-an-email", "password": "x"})
        assert r.status_code == 422  # caught by email-format validation


# --------------------------------------------------------------------------- #
# GET /auth/me  &  PUT /auth/me
# --------------------------------------------------------------------------- #
class TestMe:
    def test_me_requires_auth(self, anon):
        assert anon.get("/auth/me").status_code in UNAUTH

    def test_me_with_token(self, su):
        r = su.get("/auth/me")
        assert r.status_code == 200
        assert r.json().get("email") == SUPERADMIN["email"]

    def test_me_rejects_garbage_token(self, anon):
        r = anon.get("/auth/me", headers={"Authorization": "Bearer garbage.token.value"})
        assert r.status_code in UNAUTH

    def test_update_me_echoes_change(self, su):
        original = su.get("/auth/me").json()
        new_name = "E2E Display" if original.get("display_name") != "E2E Display" else "E2E Display 2"
        r = su.put("/auth/me", json={"display_name": new_name})
        assert r.status_code in (200, 204)
        if r.status_code == 200:
            assert r.json().get("display_name") == new_name
        # restore
        su.put("/auth/me", json={"display_name": original.get("display_name")})


# --------------------------------------------------------------------------- #
# POST /auth/refresh
# --------------------------------------------------------------------------- #
class TestRefresh:
    def test_refresh_success(self, ephemeral):
        with ephemeral(SUPERADMIN) as c:
            # mint a refresh token via a fresh login, then exchange it
            import httpx
            from .conftest import API, TIMEOUT
            login = httpx.post(f"{API}/auth/login", json=SUPERADMIN, timeout=TIMEOUT).json()
            r = c.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})
            assert r.status_code == 200
            assert "access_token" in r.json()
            from .conftest import logout_token
            logout_token(login["access_token"])

    def test_refresh_with_invalid_token(self, anon):
        r = anon.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
        assert r.status_code in (401, 422)

    def test_refresh_rejects_access_token(self, ephemeral):
        import httpx
        from .conftest import API, TIMEOUT, logout_token
        login = httpx.post(f"{API}/auth/login", json=SUPERADMIN, timeout=TIMEOUT).json()
        r = httpx.post(f"{API}/auth/refresh", json={"refresh_token": login["access_token"]}, timeout=TIMEOUT)
        assert r.status_code in (401, 422)
        logout_token(login["access_token"])


# --------------------------------------------------------------------------- #
# GET /auth/password-policy
# --------------------------------------------------------------------------- #
class TestPasswordPolicy:
    def test_password_policy(self, anon, su):
        r = anon.get("/auth/password-policy")
        if r.status_code in UNAUTH:
            r = su.get("/auth/password-policy")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)


# --------------------------------------------------------------------------- #
# POST /auth/change-password
# --------------------------------------------------------------------------- #
class TestChangePassword:
    def test_change_password_wrong_current(self, ephemeral):
        with ephemeral(SUPERADMIN) as c:
            r = c.post(
                "/auth/change-password",
                json={"current_password": "definitely-wrong", "new_password": "Whatever123!"},
            )
            assert r.status_code in (400, 401, 422)

    def test_change_password_requires_auth(self, anon):
        r = anon.post(
            "/auth/change-password",
            json={"current_password": "x", "new_password": "Whatever123!"},
        )
        assert r.status_code in UNAUTH


# --------------------------------------------------------------------------- #
# POST /auth/reset-password-request  &  -confirm
# --------------------------------------------------------------------------- #
class TestResetPassword:
    def test_reset_request_does_not_leak_existence(self, anon):
        # valid format, unknown account -> must not 404/enumerate; expect 2xx
        r = anon.post("/auth/reset-password-request", json={"email": "ghost@example.com"})
        assert r.status_code in (200, 202, 204)

    def test_reset_confirm_with_bad_token(self, anon):
        r = anon.post(
            "/auth/reset-password-confirm",
            json={"token": "invalid-token", "new_password": "Whatever123!"},
        )
        assert r.status_code in (400, 401, 404, 422)


# --------------------------------------------------------------------------- #
# POST /auth/logout
# --------------------------------------------------------------------------- #
class TestLogout:
    def test_logout_then_token_rejected(self, ephemeral):
        with ephemeral(SUPERADMIN) as c:
            assert c.get("/auth/me").status_code == 200
            assert c.post("/auth/logout").status_code in (200, 204)
            # token must be blacklisted immediately after logout
            assert c.get("/auth/me").status_code in UNAUTH

    def test_logout_requires_auth(self, anon):
        assert anon.post("/auth/logout").status_code in UNAUTH
