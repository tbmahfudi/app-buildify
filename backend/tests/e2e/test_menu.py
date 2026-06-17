"""
Deep coverage of the `menu` router (11 ops): user menu (RBAC-filtered),
admin item list, CRUD lifecycle, reorder, sync status/history/preview.

Regression coverage for:
- DEF-022 (Critical): GET /menu 500'd for every authenticated user.
  Root cause: _get_builder_page_menu_items queried BuilderPage.tenant_id
  (Column(String(36)) — VARCHAR in DB) against user.tenant_id (uuid.UUID object),
  which Postgres rejected with "operator does not exist: character varying = uuid".
  Fixed by casting str(user.tenant_id) before the filter.
- DEF-023 (Medium): POST /menu with a duplicate code 500'd instead of 400.
  Root cause: psycopg2 UniqueViolation (IntegrityError) was not caught before
  the generic except Exception handler. Fixed by adding except IntegrityError
  → 400 "A menu item with this code already exists" in routers/menu.py.
"""
import uuid

import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)
OK = (200, 201)

_MENU_PERMISSION_CODES = [
    "menu:create:tenant",
    "menu:read:tenant",
    "menu:update:tenant",
    "menu:delete:tenant",
    "menu:manage:tenant",
]


@pytest.fixture(scope="session", autouse=True)
def _grant_menu_permissions(user, su):
    me = user.get("/auth/me").json()
    tenant_id = me["tenant_id"]
    roles = su.get("/rbac/roles", params={"limit": 1000}).json()["items"]
    role = next(r for r in roles if r["code"] == "tenant_admin" and r.get("tenant_id") == tenant_id)
    perms = su.get("/rbac/permissions", params={"limit": 1000}).json()["items"]
    perm_ids = [p["id"] for p in perms if p["code"] in _MENU_PERMISSION_CODES]
    r = su.post(f"/rbac/roles/{role['id']}/permissions", json=perm_ids)
    assert r.status_code in OK, r.text


@pytest.fixture
def menu_item(user, unique):
    r = user.post("/menu", json={
        "code": unique("menu"),
        "title": "E2E Test Item",
        "route": "e2e-test-route",
        "is_system": False,
    })
    assert r.status_code in OK, r.text
    mid = r.json()["id"]
    yield mid
    user.delete(f"/menu/{mid}")


# --------------------------------------------------------------------------- #
# User menu (RBAC-filtered)
# --------------------------------------------------------------------------- #
class TestUserMenu:
    def test_returns_list(self, user):
        """DEF-022 regression: was 500 for all users (builder_pages VARCHAR vs UUID mismatch)."""
        r = user.get("/menu")
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_superuser_gets_list(self, su):
        r = su.get("/menu")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_requires_auth(self, anon):
        assert anon.get("/menu").status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Admin item list
# --------------------------------------------------------------------------- #
class TestAdminList:
    def test_admin_list_returns_items(self, user):
        r = user.get("/menu/admin")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "items" in body and "total" in body
        assert body["total"] >= 0

    def test_admin_list_superuser(self, su):
        r = su.get("/menu/admin")
        assert r.status_code == 200
        assert r.json()["total"] > 0

    def test_requires_auth(self, anon):
        assert anon.get("/menu/admin").status_code in UNAUTH


# --------------------------------------------------------------------------- #
# CRUD lifecycle
# --------------------------------------------------------------------------- #
class TestMenuItemCRUD:
    def test_create_get_update_delete(self, user, unique):
        code = unique("menu")
        cr = user.post("/menu", json={
            "code": code,
            "title": "Lifecycle Test",
            "route": "lifecycle-test",
            "is_system": False,
        })
        assert cr.status_code in OK, cr.text
        mid = cr.json()["id"]
        assert cr.json()["code"] == code
        assert cr.json()["title"] == "Lifecycle Test"

        try:
            # GET by id
            got = user.get(f"/menu/{mid}")
            assert got.status_code == 200 and got.json()["id"] == mid

            # UPDATE
            up = user.put(f"/menu/{mid}", json={"title": "Renamed"})
            assert up.status_code == 200 and up.json()["title"] == "Renamed"
        finally:
            # DELETE (soft-delete — returns 200 with {success: True})
            dele = user.delete(f"/menu/{mid}")
            assert dele.status_code == 200 and dele.json()["success"] is True

    def test_create_missing_required_fields_422(self, user):
        assert user.post("/menu", json={"title": "No Code"}).status_code == 422
        assert user.post("/menu", json={"code": "no_title_" + uuid.uuid4().hex[:6]}).status_code == 422

    def test_create_duplicate_code_400(self, user, menu_item, unique):
        """DEF-023 regression: duplicate code was 500, now clean 400."""
        # Get the code of the existing item
        existing_code = user.get(f"/menu/{menu_item}").json()["code"]
        r = user.post("/menu", json={
            "code": existing_code,
            "title": "Duplicate",
            "route": "dup-route",
            "is_system": False,
        })
        assert r.status_code == 400, r.text

    def test_get_unknown_404(self, user):
        assert user.get(f"/menu/{uuid.uuid4()}").status_code == 404

    def test_update_unknown_404(self, user):
        assert user.put(f"/menu/{uuid.uuid4()}", json={"title": "x"}).status_code == 404

    def test_delete_unknown_404(self, user):
        assert user.delete(f"/menu/{uuid.uuid4()}").status_code == 404

    def test_delete_system_item_as_non_superuser_404(self, user, su):
        # Find a system menu item (tenant_id=None, is_system=True)
        items = su.get("/menu/admin").json()["items"]
        sys_item = next(
            (i for i in items if i.get("is_system") is True and i.get("tenant_id") is None),
            None,
        )
        if sys_item is None:
            pytest.skip("No system menu items in DB")
        r = user.delete(f"/menu/{sys_item['id']}")
        assert r.status_code == 404

    def test_requires_auth(self, anon, menu_item, unique):
        code = unique("menu")
        assert anon.post("/menu", json={"code": code, "title": "x", "route": "x"}).status_code in UNAUTH
        assert anon.get(f"/menu/{menu_item}").status_code in UNAUTH
        assert anon.put(f"/menu/{menu_item}", json={"title": "x"}).status_code in UNAUTH
        assert anon.delete(f"/menu/{menu_item}").status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Reorder
# --------------------------------------------------------------------------- #
class TestReorder:
    def test_reorder_items(self, user, menu_item):
        r = user.post("/menu/reorder", json={
            "items": [{"id": menu_item, "order": 42}]
        })
        assert r.status_code == 200 and r.json()["success"] is True

    def test_reorder_empty_list_succeeds(self, user):
        r = user.post("/menu/reorder", json={"items": []})
        assert r.status_code == 200 and r.json()["success"] is True

    def test_requires_auth(self, anon, menu_item):
        r = anon.post("/menu/reorder", json={"items": [{"id": menu_item, "order": 1}]})
        assert r.status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Sync endpoints
# --------------------------------------------------------------------------- #
class TestSync:
    def test_sync_status(self, user):
        r = user.get("/menu/sync/status")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "menu_items_count" in body
        assert isinstance(body["menu_items_count"], int)
        assert "is_synced" in body

    def test_sync_history(self, user):
        r = user.get("/menu/sync/history")
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_sync_preview(self, user):
        r = user.get("/menu/sync/preview")
        # 200 if menu.json found; 404 if the file is not present in this env
        assert r.status_code in (200, 404), r.text
        if r.status_code == 200:
            body = r.json()
            assert "total_items" in body

    def test_sync_requires_auth(self, anon):
        assert anon.get("/menu/sync/status").status_code in UNAUTH
        assert anon.get("/menu/sync/history").status_code in UNAUTH
        assert anon.get("/menu/sync/preview").status_code in UNAUTH
        assert anon.post("/menu/sync").status_code in UNAUTH
