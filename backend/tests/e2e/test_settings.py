"""
Deep coverage of the `settings` router (4 ops):
  - GET /settings/user             — get (or auto-create) user settings
  - PUT /settings/user             — update user settings (upsert)
  - GET /settings/tenant           — get (or auto-create) tenant settings
  - PUT /settings/tenant           — update tenant settings (upsert)

Regression coverage for:
- DEF-025 (Medium): PUT /settings/tenant 500'd for tenant users.
  Root cause: target_tenant resolved to current_user.tenant_id (UUID object)
  and was compared against TenantSettings.tenant_id (Column(String(36)) — VARCHAR),
  causing Postgres "operator does not exist: character varying = uuid". Fixed by
  casting str(current_user.tenant_id) when tenant_id param is absent.
- DEF-026 (Medium): PUT /settings/tenant?tenant_id=<own-tenant-id> returned 403
  instead of 200. Root cause: ownership check was `tenant_id != current_user.tenant_id`
  where str("37ba...") != UUID("37ba...") is always True — so even own-tenant access
  was blocked. Fixed by using str() on both sides, matching the GET handler.
"""
import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)
OK = (200, 201)

_SETTINGS_PERMS = [
    "settings:read:own",
    "settings:update:own",
    "settings:read:tenant",
    "settings:update:tenant",
]


@pytest.fixture(scope="session", autouse=True)
def _grant_settings_permissions(user, su):
    me = user.get("/auth/me").json()
    tenant_id = me["tenant_id"]
    roles = su.get("/rbac/roles", params={"limit": 1000}).json()["items"]
    role = next(r for r in roles if r["code"] == "tenant_admin" and r.get("tenant_id") == tenant_id)
    perms = su.get("/rbac/permissions", params={"limit": 1000}).json()["items"]
    perm_ids = [p["id"] for p in perms if p["code"] in _SETTINGS_PERMS]
    r = su.post(f"/rbac/roles/{role['id']}/permissions", json=perm_ids)
    assert r.status_code in OK, r.text


# ─── user settings ──────────────────────────────────────────────────────────

class TestUserSettings:
    def test_get_returns_settings(self, user):
        r = user.get("/settings/user")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "id" in body
        assert "user_id" in body
        assert "theme" in body
        assert body["theme"] in ("light", "dark")

    def test_get_auto_creates_if_absent(self, user):
        """Endpoint is idempotent — second call returns same id."""
        r1 = user.get("/settings/user")
        r2 = user.get("/settings/user")
        assert r1.status_code == 200 and r2.status_code == 200
        assert r1.json()["id"] == r2.json()["id"]

    def test_update_theme(self, user):
        r = user.put("/settings/user", json={"theme": "dark"})
        assert r.status_code == 200, r.text
        assert r.json()["theme"] == "dark"
        # restore
        user.put("/settings/user", json={"theme": "light"})

    def test_update_language(self, user):
        r = user.put("/settings/user", json={"language": "fr"})
        assert r.status_code == 200, r.text
        assert r.json()["language"] == "fr"
        user.put("/settings/user", json={"language": "en"})

    def test_update_timezone(self, user):
        r = user.put("/settings/user", json={"timezone": "America/New_York"})
        assert r.status_code == 200, r.text
        assert r.json()["timezone"] == "America/New_York"
        user.put("/settings/user", json={"timezone": "UTC"})

    def test_update_density(self, user):
        r = user.put("/settings/user", json={"density": "compact"})
        assert r.status_code == 200, r.text
        assert r.json()["density"] == "compact"
        user.put("/settings/user", json={"density": "normal"})

    def test_update_preferences_dict(self, user):
        prefs = {"sidebar_collapsed": True, "items_per_page": 25}
        r = user.put("/settings/user", json={"preferences": prefs})
        assert r.status_code == 200, r.text
        assert r.json()["preferences"] == prefs
        user.put("/settings/user", json={"preferences": None})

    def test_get_after_update_reflects_change(self, user):
        user.put("/settings/user", json={"theme": "dark"})
        r = user.get("/settings/user")
        assert r.status_code == 200
        assert r.json()["theme"] == "dark"
        user.put("/settings/user", json={"theme": "light"})

    def test_superuser_has_own_settings(self, su):
        r = su.get("/settings/user")
        assert r.status_code == 200
        body = r.json()
        assert "theme" in body

    def test_get_requires_auth(self, anon):
        assert anon.get("/settings/user").status_code in UNAUTH

    def test_put_requires_auth(self, anon):
        assert anon.put("/settings/user", json={"theme": "dark"}).status_code in UNAUTH


# ─── tenant settings ─────────────────────────────────────────────────────────

class TestTenantSettings:
    def test_get_returns_tenant_settings(self, user):
        r = user.get("/settings/tenant")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "id" in body
        assert "tenant_id" in body
        assert "primary_color" in body

    def test_get_auto_creates_if_absent(self, user):
        """Endpoint is idempotent — second call returns same id."""
        r1 = user.get("/settings/tenant")
        r2 = user.get("/settings/tenant")
        assert r1.status_code == 200 and r2.status_code == 200
        assert r1.json()["id"] == r2.json()["id"]

    def test_update_primary_color(self, user):
        """DEF-025 regression: was 500 for tenant users (UUID vs VARCHAR mismatch)."""
        r = user.put("/settings/tenant", json={"primary_color": "#1976d2"})
        assert r.status_code == 200, r.text
        assert r.json()["primary_color"] == "#1976d2"

    def test_update_tenant_name(self, user):
        r = user.put("/settings/tenant", json={"tenant_name": "E2E Test Tenant"})
        assert r.status_code == 200, r.text
        assert r.json()["tenant_name"] == "E2E Test Tenant"

    def test_update_secondary_color(self, user):
        r = user.put("/settings/tenant", json={"secondary_color": "#424242"})
        assert r.status_code == 200, r.text
        assert r.json()["secondary_color"] == "#424242"

    def test_update_with_explicit_own_tenant_id(self, user):
        """DEF-026 regression: explicit own tenant_id was 403 (str != UUID comparison)."""
        me = user.get("/auth/me").json()
        tenant_id = me["tenant_id"]
        r = user.put("/settings/tenant", json={"primary_color": "#1976d2"}, params={"tenant_id": tenant_id})
        assert r.status_code == 200, r.text

    def test_update_foreign_tenant_id_403(self, user):
        """Cross-tenant update must be blocked."""
        foreign = "00000000-0000-0000-0000-000000000001"
        r = user.put("/settings/tenant", json={}, params={"tenant_id": foreign})
        assert r.status_code == 403, r.text

    def test_get_with_explicit_own_tenant_id(self, user):
        me = user.get("/auth/me").json()
        r = user.get("/settings/tenant", params={"tenant_id": me["tenant_id"]})
        assert r.status_code == 200, r.text
        assert r.json()["tenant_id"] == me["tenant_id"]

    def test_superuser_get_returns_defaults_for_no_tenant(self, su):
        """Superadmin has no tenant — should get default settings response."""
        r = su.get("/settings/tenant")
        assert r.status_code == 200, r.text

    def test_superuser_can_update_any_tenant(self, su, user):
        me = user.get("/auth/me").json()
        tenant_id = me["tenant_id"]
        r = su.put("/settings/tenant", json={"secondary_color": "#000000"}, params={"tenant_id": tenant_id})
        assert r.status_code in (200, 400), r.text

    def test_get_requires_auth(self, anon):
        assert anon.get("/settings/tenant").status_code in UNAUTH

    def test_put_requires_auth(self, anon):
        assert anon.put("/settings/tenant", json={}).status_code in UNAUTH
