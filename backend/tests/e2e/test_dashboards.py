"""
Deep coverage of the `dashboards` router (16 ops): dashboard CRUD + clone,
page create/update/delete, widget create/update/delete + bulk-update,
widget data fetch, sharing, snapshot.

Regression coverage for:
- DEF-019 (Critical): Dashboard/DashboardPage/DashboardWidget/DashboardShare/
  DashboardSnapshot/WidgetDataCache models declared GUID PKs without
  default=generate_uuid, and all schemas/router path params typed IDs as int
  instead of UUID — every create 500'd, every by-id read/update/delete 422'd.
  Same pattern as DEF-015 (scheduler). Fixed by adding default=generate_uuid to
  all 6 model PK columns and correcting every int annotation to UUID.
"""
import uuid

import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)
OK = (200, 201)

_DASHBOARD_PERMISSION_CODES = [
    "dashboards:create:tenant", "dashboards:read:tenant", "dashboards:read:own",
    "dashboards:update:own", "dashboards:delete:own", "dashboards:clone:tenant",
    "dashboards:create_page:tenant", "dashboards:update_page:own", "dashboards:delete_page:own",
    "dashboards:create_widget:tenant", "dashboards:update_widget:own", "dashboards:delete_widget:own",
    "dashboards:share:tenant", "dashboards:snapshot:tenant",
]


@pytest.fixture(scope="session", autouse=True)
def _grant_dashboard_permissions(user):
    me = user.get("/auth/me").json()
    tenant_id = me["tenant_id"]
    roles = user.get("/rbac/roles", params={"limit": 1000}).json()["items"]
    role = next(r for r in roles if r["code"] == "tenant_admin" and r["tenant_id"] == tenant_id)
    perms = user.get("/rbac/permissions", params={"limit": 1000}).json()["items"]
    perm_ids = [p["id"] for p in perms if p["code"] in _DASHBOARD_PERMISSION_CODES]
    r = user.post(f"/rbac/roles/{role['id']}/permissions", json=perm_ids)
    assert r.status_code in OK, r.text


@pytest.fixture
def dashboard(user, unique):
    r = user.post("/dashboards", json={"name": unique("dash")})
    assert r.status_code in OK, r.text
    did = r.json()["id"]
    yield did
    user.delete(f"/dashboards/{did}")


@pytest.fixture
def page(user, dashboard, unique):
    r = user.post("/dashboards/pages", json={"dashboard_id": dashboard, "name": unique("pg")})
    assert r.status_code in OK, r.text
    pid = r.json()["id"]
    yield pid
    user.delete(f"/dashboards/pages/{pid}")


@pytest.fixture
def widget(user, page, unique):
    r = user.post("/dashboards/widgets", json={
        "page_id": page,
        "title": unique("wgt"),
        "widget_type": "text",
        "position": {"x": 0, "y": 0, "w": 4, "h": 3},
    })
    assert r.status_code in OK, r.text
    wid = r.json()["id"]
    yield wid
    user.delete(f"/dashboards/widgets/{wid}")


# --------------------------------------------------------------------------- #
# Dashboard CRUD
# --------------------------------------------------------------------------- #
class TestDashboards:
    def test_create_get_update_delete(self, user, unique):
        cr = user.post("/dashboards", json={"name": unique("dash"), "category": "analytics"})
        assert cr.status_code in OK, cr.text
        did = cr.json()["id"]
        uuid.UUID(did)  # DEF-019 regression: must be a real UUID
        try:
            got = user.get(f"/dashboards/{did}")
            assert got.status_code == 200 and got.json()["id"] == did

            listed = [d["id"] for d in user.get("/dashboards").json()]
            assert did in listed

            up = user.put(f"/dashboards/{did}", json={"name": "renamed", "is_favorite": True})
            assert up.status_code == 200
            assert up.json()["name"] == "renamed" and up.json()["is_favorite"] is True
        finally:
            dele = user.delete(f"/dashboards/{did}")
            assert dele.status_code == 204

        assert user.get(f"/dashboards/{did}").status_code == 404

    def test_list_filter_by_category(self, user, unique):
        r = user.post("/dashboards", json={"name": unique("dash"), "category": "finance"})
        did = r.json()["id"]
        try:
            results = [d["id"] for d in user.get("/dashboards", params={"category": "finance"}).json()]
            assert did in results
        finally:
            user.delete(f"/dashboards/{did}")

    def test_list_favorites_only(self, user, unique):
        r = user.post("/dashboards", json={"name": unique("dash")})
        did = r.json()["id"]
        try:
            user.put(f"/dashboards/{did}", json={"is_favorite": True})
            favs = [d["id"] for d in user.get("/dashboards", params={"favorites_only": True}).json()]
            assert did in favs
        finally:
            user.delete(f"/dashboards/{did}")

    def test_create_missing_name_422(self, user):
        assert user.post("/dashboards", json={}).status_code == 422

    def test_get_unknown_404(self, user):
        assert user.get(f"/dashboards/{uuid.uuid4()}").status_code == 404

    def test_update_unknown_404(self, user):
        assert user.put(f"/dashboards/{uuid.uuid4()}", json={"name": "x"}).status_code == 404

    def test_delete_unknown_404(self, user):
        assert user.delete(f"/dashboards/{uuid.uuid4()}").status_code == 404

    def test_clone(self, user, dashboard, unique):
        r = user.post(f"/dashboards/{dashboard}/clone", json={"name": unique("clone")})
        assert r.status_code in OK, r.text
        clone_id = r.json()["id"]
        assert clone_id != dashboard
        user.delete(f"/dashboards/{clone_id}")

    def test_clone_unknown_404(self, user, unique):
        r = user.post(f"/dashboards/{uuid.uuid4()}/clone", json={"name": unique("clone")})
        assert r.status_code == 404

    def test_requires_auth(self, anon):
        assert anon.get("/dashboards").status_code in UNAUTH
        assert anon.post("/dashboards", json={"name": "x"}).status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
class TestPages:
    def test_create_update_delete(self, user, dashboard, unique):
        cr = user.post("/dashboards/pages", json={"dashboard_id": dashboard, "name": unique("pg")})
        assert cr.status_code in OK, cr.text
        pid = cr.json()["id"]
        uuid.UUID(pid)  # DEF-019 regression

        up = user.put(f"/dashboards/pages/{pid}", json={"name": "renamed-page"})
        assert up.status_code == 200 and up.json()["name"] == "renamed-page"

        # page appears in dashboard detail
        got = user.get(f"/dashboards/{dashboard}")
        assert pid in [p["id"] for p in got.json()["pages"]]

        dele = user.delete(f"/dashboards/pages/{pid}")
        assert dele.status_code == 204

    def test_create_missing_fields_422(self, user, dashboard):
        assert user.post("/dashboards/pages", json={"dashboard_id": dashboard}).status_code == 422

    def test_update_unknown_404(self, user):
        assert user.put(f"/dashboards/pages/{uuid.uuid4()}", json={"name": "x"}).status_code == 404

    def test_delete_unknown_404(self, user):
        assert user.delete(f"/dashboards/pages/{uuid.uuid4()}").status_code == 404

    def test_requires_auth(self, anon, dashboard):
        r = anon.post("/dashboards/pages", json={"dashboard_id": dashboard, "name": "x"})
        assert r.status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Widgets
# --------------------------------------------------------------------------- #
class TestWidgets:
    def test_create_update_delete(self, user, page, unique):
        cr = user.post("/dashboards/widgets", json={
            "page_id": page,
            "title": unique("wgt"),
            "widget_type": "kpi_card",
            "position": {"x": 0, "y": 0, "w": 3, "h": 2},
        })
        assert cr.status_code in OK, cr.text
        wid = cr.json()["id"]
        uuid.UUID(wid)  # DEF-019 regression

        up = user.put(f"/dashboards/widgets/{wid}", json={"title": "renamed-widget"})
        assert up.status_code == 200 and up.json()["title"] == "renamed-widget"

        dele = user.delete(f"/dashboards/widgets/{wid}")
        assert dele.status_code == 204

    def test_create_missing_position_422(self, user, page, unique):
        r = user.post("/dashboards/widgets", json={
            "page_id": page, "title": unique("wgt"), "widget_type": "text",
        })
        assert r.status_code == 422

    def test_update_unknown_404(self, user):
        assert user.put(f"/dashboards/widgets/{uuid.uuid4()}", json={"title": "x"}).status_code == 404

    def test_delete_unknown_404(self, user):
        assert user.delete(f"/dashboards/widgets/{uuid.uuid4()}").status_code == 404

    def test_bulk_update(self, user, widget):
        r = user.post("/dashboards/widgets/bulk-update", json={
            "updates": [{"widget_id": widget, "position": {"x": 1, "y": 1, "w": 4, "h": 3}, "order": 0}]
        })
        assert r.status_code == 200 and r.json()["success"] is True

    def test_requires_auth(self, anon, page, unique):
        r = anon.post("/dashboards/widgets", json={
            "page_id": page, "title": "x", "widget_type": "text",
            "position": {"x": 0, "y": 0, "w": 1, "h": 1},
        })
        assert r.status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Widget data
# --------------------------------------------------------------------------- #
class TestWidgetData:
    def test_get_widget_data_not_found_404(self, user):
        r = user.post("/dashboards/widgets/data", json={"widget_id": str(uuid.uuid4())})
        assert r.status_code == 404

    def test_requires_auth(self, anon):
        r = anon.post("/dashboards/widgets/data", json={"widget_id": str(uuid.uuid4())})
        assert r.status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Sharing
# --------------------------------------------------------------------------- #
class TestSharing:
    def test_create_share(self, user, dashboard):
        me = user.get("/auth/me").json()
        r = user.post("/dashboards/shares", json={
            "dashboard_id": dashboard,
            "shared_with_user_id": me["id"],
            "can_view": True,
        })
        assert r.status_code in OK, r.text
        share_id = r.json()["id"]
        uuid.UUID(share_id)  # DEF-019 regression

    def test_share_unknown_dashboard_400(self, user):
        r = user.post("/dashboards/shares", json={
            "dashboard_id": str(uuid.uuid4()), "can_view": True,
        })
        assert r.status_code in (400, 404)

    def test_requires_auth(self, anon, dashboard):
        r = anon.post("/dashboards/shares", json={"dashboard_id": dashboard, "can_view": True})
        assert r.status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Snapshots
# --------------------------------------------------------------------------- #
class TestSnapshots:
    def test_create_snapshot(self, user, dashboard, unique):
        r = user.post("/dashboards/snapshots", json={
            "dashboard_id": dashboard,
            "name": unique("snap"),
        })
        assert r.status_code in OK, r.text
        snap_id = r.json()["id"]
        uuid.UUID(snap_id)  # DEF-019 regression

    def test_snapshot_unknown_dashboard_404(self, user, unique):
        r = user.post("/dashboards/snapshots", json={
            "dashboard_id": str(uuid.uuid4()),
            "name": unique("snap"),
        })
        assert r.status_code in (400, 404)

    def test_requires_auth(self, anon, dashboard, unique):
        r = anon.post("/dashboards/snapshots", json={"dashboard_id": dashboard, "name": "x"})
        assert r.status_code in UNAUTH
