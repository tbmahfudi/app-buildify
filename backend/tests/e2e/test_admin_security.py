"""
Deep coverage of the `admin/security` router (14 operations):
security policies (CRUD), locked accounts, active sessions, login attempts,
notification config + queue. All require RBAC `*:all` permissions, which the
superuser (`su`) bypasses entirely — so this suite runs as `su`.
"""
import uuid

import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)


@pytest.fixture
def tenant(su, unique):
    code = unique("SECPOL").replace("_", "")[:20]
    cr = su.post("/org/tenants", json={"name": f"SecPol {code}", "code": code})
    assert cr.status_code == 201, cr.text
    tid = cr.json()["id"]
    yield tid
    su.delete(f"/org/tenants/{tid}")


# --------------------------------------------------------------------------- #
# Security policies
# --------------------------------------------------------------------------- #
class TestPolicies:
    def test_list_includes_system_default(self, su):
        r = su.get("/admin/security/policies")
        assert r.status_code == 200
        policies = r.json()
        assert any(p["tenant_id"] is None for p in policies)

    def test_list_requires_auth(self, anon):
        assert anon.get("/admin/security/policies").status_code in UNAUTH

    def test_get_system_default_by_id(self, su):
        default = next(p for p in su.get("/admin/security/policies").json() if p["tenant_id"] is None)
        r = su.get(f"/admin/security/policies/{default['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == default["id"]

    def test_get_unknown_404(self, su):
        assert su.get(f"/admin/security/policies/{uuid.uuid4()}").status_code == 404

    def test_create_update_delete_tenant_policy(self, su, tenant):
        cr = su.post(
            "/admin/security/policies",
            json={"tenant_id": tenant, "policy_name": "Test Policy", "policy_type": "combined"},
        )
        assert cr.status_code == 201, cr.text
        assert cr.json()["tenant_id"] == tenant
        policy_id = cr.json()["id"]
        try:
            up = su.put(f"/admin/security/policies/{policy_id}", json={"password_min_length": 16})
            assert up.status_code == 200
            assert up.json()["password_min_length"] == 16
        finally:
            d = su.delete(f"/admin/security/policies/{policy_id}")
            assert d.status_code == 204
        # delete is a soft-deactivate: excluded from the list, but still
        # fetchable by id (audit trail) — `is_active` flips to False.
        assert su.get(f"/admin/security/policies/{policy_id}").json()["is_active"] is False
        assert policy_id not in [p["id"] for p in su.get("/admin/security/policies").json()]

    def test_create_duplicate_tenant_policy_400(self, su, tenant):
        cr = su.post(
            "/admin/security/policies",
            json={"tenant_id": tenant, "policy_name": "P1", "policy_type": "combined"},
        )
        assert cr.status_code == 201
        policy_id = cr.json()["id"]
        try:
            dup = su.post(
                "/admin/security/policies",
                json={"tenant_id": tenant, "policy_name": "P2", "policy_type": "combined"},
            )
            assert dup.status_code == 400
        finally:
            su.delete(f"/admin/security/policies/{policy_id}")

    def test_create_missing_name_422(self, su, tenant):
        r = su.post("/admin/security/policies", json={"tenant_id": tenant})
        assert r.status_code == 422

    def test_cannot_delete_system_default(self, su):
        default = next(p for p in su.get("/admin/security/policies").json() if p["tenant_id"] is None)
        r = su.delete(f"/admin/security/policies/{default['id']}")
        assert r.status_code == 400

    def test_update_unknown_404(self, su):
        r = su.put(f"/admin/security/policies/{uuid.uuid4()}", json={"password_min_length": 10})
        assert r.status_code == 404

    def test_create_requires_auth(self, anon, unique):
        r = anon.post(
            "/admin/security/policies",
            json={"tenant_id": unique("tenant"), "policy_name": "x", "policy_type": "combined"},
        )
        assert r.status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Locked accounts
# --------------------------------------------------------------------------- #
class TestLockedAccounts:
    def test_list_ok(self, su):
        r = su.get("/admin/security/locked-accounts")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_requires_auth(self, anon):
        assert anon.get("/admin/security/locked-accounts").status_code in UNAUTH

    def test_unlock_unknown_user_404(self, su):
        r = su.post("/admin/security/unlock-account", json={"user_id": str(uuid.uuid4())})
        assert r.status_code == 404

    def test_unlock_not_locked_user_400(self, su):
        me = su.get("/auth/me").json()
        r = su.post("/admin/security/unlock-account", json={"user_id": me["id"]})
        assert r.status_code == 400

    def test_unlock_requires_auth(self, anon):
        r = anon.post("/admin/security/unlock-account", json={"user_id": str(uuid.uuid4())})
        assert r.status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Active sessions
# --------------------------------------------------------------------------- #
class TestSessions:
    def test_list_ok(self, su):
        r = su.get("/admin/security/sessions")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_with_limit(self, su):
        r = su.get("/admin/security/sessions", params={"limit": 1})
        assert r.status_code == 200
        assert len(r.json()) <= 1

    def test_list_requires_auth(self, anon):
        assert anon.get("/admin/security/sessions").status_code in UNAUTH

    def test_revoke_unknown_session_404(self, su):
        r = su.post("/admin/security/sessions/revoke", json={"session_id": str(uuid.uuid4())})
        assert r.status_code == 404

    def test_revoke_all_unknown_user_404(self, su):
        r = su.post(f"/admin/security/sessions/revoke-all/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_revoke_requires_auth(self, anon):
        r = anon.post("/admin/security/sessions/revoke", json={"session_id": str(uuid.uuid4())})
        assert r.status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Login attempts
# --------------------------------------------------------------------------- #
class TestLoginAttempts:
    def test_list_ok(self, su):
        r = su.get("/admin/security/login-attempts")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) > 0  # the su login itself is recorded

    def test_filter_by_email(self, su):
        r = su.get("/admin/security/login-attempts", params={"email": "superadmin@system.com"})
        assert r.status_code == 200
        assert all(a["email"] == "superadmin@system.com" for a in r.json())

    def test_filter_by_success(self, su):
        r = su.get("/admin/security/login-attempts", params={"success": True})
        assert r.status_code == 200
        assert all(a["success"] is True for a in r.json())

    def test_list_requires_auth(self, anon):
        assert anon.get("/admin/security/login-attempts").status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Notification configuration
# --------------------------------------------------------------------------- #
class TestNotificationConfig:
    def test_list_ok(self, su):
        r = su.get("/admin/security/notification-config")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_requires_auth(self, anon):
        assert anon.get("/admin/security/notification-config").status_code in UNAUTH

    def test_update_unknown_404(self, su):
        r = su.put(f"/admin/security/notification-config/{uuid.uuid4()}", json={"email_enabled": False})
        assert r.status_code == 404

    def test_update_requires_auth(self, anon):
        r = anon.put(f"/admin/security/notification-config/{uuid.uuid4()}", json={"email_enabled": False})
        assert r.status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Notification queue
# --------------------------------------------------------------------------- #
class TestNotificationQueue:
    def test_list_ok(self, su):
        r = su.get("/admin/security/notification-queue")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_with_status_filter(self, su):
        r = su.get("/admin/security/notification-queue", params={"status": "pending"})
        assert r.status_code == 200

    def test_list_requires_auth(self, anon):
        assert anon.get("/admin/security/notification-queue").status_code in UNAUTH
