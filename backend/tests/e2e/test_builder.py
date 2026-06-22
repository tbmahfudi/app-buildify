"""
Deep coverage of the `builder` router (10 ops, prefix /builder):
  - GET  /           — list pages (with filters: module_name, published_only, skip/limit)
  - GET  /{page_id}  — get page by id
  - POST /           — create page (201)
  - PUT  /{page_id}  — update page
  - DELETE /{page_id}— delete page + all versions
  - POST /{page_id}/publish               — publish (creates a version snapshot)
  - POST /{page_id}/unpublish             — unpublish (keeps versions)
  - GET  /{page_id}/versions              — list versions (ordered by version_number desc)
  - GET  /{page_id}/versions/{version_number} — get specific version
  - POST /{page_id}/restore/{version_number}  — restore page to a previous version

No RBAC gates — any authenticated user may CRUD their own tenant's pages.
Tenant isolation: each page is scoped to the creating user's tenant.
"""
import uuid

import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)
OK = (200, 201)


def _page_body(unique, suffix=""):
    u = unique(f"bp{suffix}")
    return {
        "name": f"E2E {u}",
        "slug": u,
        "route_path": f"/e2e/{u}",
        "grapejs_data": {"components": [], "styles": []},
        "description": "e2e test page",
    }


@pytest.fixture
def page(user, unique):
    """Create a builder page, yield its id, delete on teardown."""
    body = _page_body(unique)
    r = user.post("/builder/", json=body)
    assert r.status_code in OK, r.text
    pid = r.json()["id"]
    yield pid
    user.delete(f"/builder/{pid}")


@pytest.fixture
def published_page(user, unique):
    """Create a page and publish it. Yields (page_id, page dict)."""
    body = _page_body(unique, "pub")
    r = user.post("/builder/", json=body)
    assert r.status_code in OK, r.text
    pid = r.json()["id"]
    pub = user.post(f"/builder/{pid}/publish", json={"commit_message": "initial"})
    assert pub.status_code == 200, pub.text
    yield pid, pub.json()
    user.delete(f"/builder/{pid}")


# ─── auth required ────────────────────────────────────────────────────────────

class TestBuilderAuth:
    def test_list_requires_auth(self, anon):
        assert anon.get("/builder/").status_code in UNAUTH

    def test_get_requires_auth(self, anon):
        assert anon.get(f"/builder/{uuid.uuid4()}").status_code in UNAUTH

    def test_create_requires_auth(self, anon):
        r = anon.post("/builder/", json={
            "name": "x", "slug": "x", "route_path": "/x", "grapejs_data": {},
        })
        assert r.status_code in UNAUTH

    def test_update_requires_auth(self, anon, page):
        assert anon.put(f"/builder/{page}", json={"name": "x"}).status_code in UNAUTH

    def test_delete_requires_auth(self, anon, page):
        assert anon.delete(f"/builder/{page}").status_code in UNAUTH

    def test_publish_requires_auth(self, anon, page):
        assert anon.post(f"/builder/{page}/publish", json={}).status_code in UNAUTH

    def test_list_versions_requires_auth(self, anon, page):
        assert anon.get(f"/builder/{page}/versions").status_code in UNAUTH


# ─── list ─────────────────────────────────────────────────────────────────────

class TestBuilderList:
    def test_list_returns_list(self, user):
        r = user.get("/builder/")
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_list_contains_created_page(self, user, page):
        pages = user.get("/builder/").json()
        assert any(p["id"] == page for p in pages)

    def test_list_published_only_filters(self, user, page, published_page):
        pid, _ = published_page
        pages = user.get("/builder/", params={"published_only": "true"}).json()
        assert any(p["id"] == pid for p in pages), "published page should appear"
        assert all(p.get("published") is True for p in pages), "only published pages"

    def test_list_module_name_filter(self, user):
        r = user.get("/builder/", params={"module_name": "nonexistent_module_xyz"})
        assert r.status_code == 200
        assert r.json() == []

    def test_list_skip_limit(self, user):
        r = user.get("/builder/", params={"skip": 0, "limit": 2})
        assert r.status_code == 200
        assert len(r.json()) <= 2

    def test_list_excludes_other_tenant_pages(self, user, su, unique):
        """Pages created by superadmin (tenant_id=None) don't appear in tenant list."""
        pages = user.get("/builder/").json()
        # All listed pages must belong to the user's tenant
        me = user.get("/auth/me").json()
        tid = me["tenant_id"]
        for p in pages:
            assert p.get("tenant_id") == tid, f"page {p['id']} belongs to wrong tenant"


# ─── create ───────────────────────────────────────────────────────────────────

class TestBuilderCreate:
    def test_create_returns_201_with_page(self, user, unique):
        body = _page_body(unique, "cr")
        r = user.post("/builder/", json=body)
        assert r.status_code in OK, r.text
        page = r.json()
        assert "id" in page
        assert page["name"] == body["name"]
        assert page["slug"] == body["slug"]
        assert page["published"] is False
        user.delete(f"/builder/{page['id']}")

    def test_create_duplicate_slug_409(self, user, page, unique):
        existing = user.get(f"/builder/{page}").json()
        r = user.post("/builder/", json={
            "name": "Dup", "slug": existing["slug"],
            "route_path": "/unique-route-" + unique("dup"),
            "grapejs_data": {},
        })
        assert r.status_code == 409, r.text

    def test_create_duplicate_route_path_409(self, user, page, unique):
        existing = user.get(f"/builder/{page}").json()
        r = user.post("/builder/", json={
            "name": "Dup2", "slug": unique("dup2"),
            "route_path": existing["route_path"],
            "grapejs_data": {},
        })
        assert r.status_code == 409, r.text

    def test_create_missing_name_422(self, user):
        r = user.post("/builder/", json={"slug": "x", "route_path": "/x", "grapejs_data": {}})
        assert r.status_code == 422

    def test_create_missing_slug_422(self, user):
        r = user.post("/builder/", json={"name": "x", "route_path": "/x", "grapejs_data": {}})
        assert r.status_code == 422

    def test_create_missing_route_path_422(self, user):
        r = user.post("/builder/", json={"name": "x", "slug": "x", "grapejs_data": {}})
        assert r.status_code == 422

    def test_create_missing_grapejs_data_422(self, user):
        r = user.post("/builder/", json={"name": "x", "slug": "x", "route_path": "/x"})
        assert r.status_code == 422


# ─── get ──────────────────────────────────────────────────────────────────────

class TestBuilderGet:
    def test_get_returns_page_shape(self, user, page):
        r = user.get(f"/builder/{page}")
        assert r.status_code == 200, r.text
        body = r.json()
        for key in ("id", "name", "slug", "route_path", "published", "tenant_id", "created_by"):
            assert key in body, f"missing key: {key}"

    def test_get_id_matches(self, user, page):
        assert user.get(f"/builder/{page}").json()["id"] == page

    def test_get_unknown_404(self, user):
        assert user.get(f"/builder/{uuid.uuid4()}").status_code == 404

    def test_get_requires_auth(self, anon, page):
        assert anon.get(f"/builder/{page}").status_code in UNAUTH


# ─── update ───────────────────────────────────────────────────────────────────

class TestBuilderUpdate:
    def test_update_name(self, user, page, unique):
        new_name = unique("upd")
        r = user.put(f"/builder/{page}", json={"name": new_name})
        assert r.status_code == 200, r.text
        assert r.json()["name"] == new_name

    def test_update_persisted(self, user, page, unique):
        new_name = unique("pers")
        user.put(f"/builder/{page}", json={"name": new_name})
        assert user.get(f"/builder/{page}").json()["name"] == new_name

    def test_update_slug_to_duplicate_409(self, user, unique):
        a = _page_body(unique, "a"); b = _page_body(unique, "b")
        pid_a = user.post("/builder/", json=a).json()["id"]
        pid_b = user.post("/builder/", json=b).json()["id"]
        try:
            r = user.put(f"/builder/{pid_b}", json={"slug": a["slug"]})
            assert r.status_code == 409, r.text
        finally:
            user.delete(f"/builder/{pid_a}")
            user.delete(f"/builder/{pid_b}")

    def test_update_unknown_404(self, user):
        assert user.put(f"/builder/{uuid.uuid4()}", json={"name": "x"}).status_code == 404

    def test_update_requires_auth(self, anon, page):
        assert anon.put(f"/builder/{page}", json={"name": "x"}).status_code in UNAUTH


# ─── delete ───────────────────────────────────────────────────────────────────

class TestBuilderDelete:
    def test_delete_returns_204(self, user, unique):
        pid = user.post("/builder/", json=_page_body(unique, "del")).json()["id"]
        r = user.delete(f"/builder/{pid}")
        assert r.status_code == 204
        assert r.text == ""

    def test_delete_removes_page(self, user, unique):
        pid = user.post("/builder/", json=_page_body(unique, "del2")).json()["id"]
        user.delete(f"/builder/{pid}")
        assert user.get(f"/builder/{pid}").status_code == 404

    def test_delete_unknown_404(self, user):
        assert user.delete(f"/builder/{uuid.uuid4()}").status_code == 404

    def test_delete_requires_auth(self, anon, page):
        assert anon.delete(f"/builder/{page}").status_code in UNAUTH


# ─── publish / unpublish ──────────────────────────────────────────────────────

class TestBuilderPublish:
    def test_publish_sets_published_true(self, user, page):
        r = user.post(f"/builder/{page}/publish", json={"commit_message": "v1"})
        assert r.status_code == 200, r.text
        assert r.json()["published"] is True
        assert r.json()["published_at"] is not None

    def test_publish_creates_version(self, user, page):
        user.post(f"/builder/{page}/publish", json={})
        versions = user.get(f"/builder/{page}/versions").json()
        assert len(versions) >= 1

    def test_publish_increments_version_number(self, user, page):
        user.post(f"/builder/{page}/publish", json={})
        user.post(f"/builder/{page}/publish", json={})
        versions = user.get(f"/builder/{page}/versions").json()
        nums = sorted(v["version_number"] for v in versions)
        assert nums == [1, 2]

    def test_publish_stores_commit_message(self, user, page):
        user.post(f"/builder/{page}/publish", json={"commit_message": "test commit"})
        v = user.get(f"/builder/{page}/versions/1").json()
        assert v["commit_message"] == "test commit"

    def test_publish_unknown_page_404(self, user):
        r = user.post(f"/builder/{uuid.uuid4()}/publish", json={})
        assert r.status_code == 404

    def test_unpublish_sets_published_false(self, user, published_page):
        pid, _ = published_page
        r = user.post(f"/builder/{pid}/unpublish")
        assert r.status_code == 200
        assert r.json()["published"] is False

    def test_unpublish_keeps_versions(self, user, published_page):
        pid, _ = published_page
        user.post(f"/builder/{pid}/unpublish")
        assert len(user.get(f"/builder/{pid}/versions").json()) >= 1

    def test_unpublish_unknown_page_404(self, user):
        assert user.post(f"/builder/{uuid.uuid4()}/unpublish").status_code == 404


# ─── versions ─────────────────────────────────────────────────────────────────

class TestBuilderVersions:
    def test_list_versions_returns_list(self, user, published_page):
        pid, _ = published_page
        r = user.get(f"/builder/{pid}/versions")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_versions_has_correct_fields(self, user, published_page):
        pid, _ = published_page
        v = user.get(f"/builder/{pid}/versions").json()[0]
        for key in ("id", "page_id", "version_number", "grapejs_data", "commit_message"):
            assert key in v, f"missing key: {key}"

    def test_list_versions_unknown_page_404(self, user):
        assert user.get(f"/builder/{uuid.uuid4()}/versions").status_code == 404

    def test_get_version_by_number(self, user, published_page):
        pid, _ = published_page
        r = user.get(f"/builder/{pid}/versions/1")
        assert r.status_code == 200
        assert r.json()["version_number"] == 1

    def test_get_version_unknown_page_404(self, user):
        assert user.get(f"/builder/{uuid.uuid4()}/versions/1").status_code == 404

    def test_get_version_unknown_number_404(self, user, published_page):
        pid, _ = published_page
        assert user.get(f"/builder/{pid}/versions/999").status_code == 404


# ─── restore ──────────────────────────────────────────────────────────────────

class TestBuilderRestore:
    def test_restore_returns_page(self, user, page):
        user.post(f"/builder/{page}/publish", json={"commit_message": "v1"})
        user.put(f"/builder/{page}", json={"name": "After v1"})
        user.post(f"/builder/{page}/publish", json={"commit_message": "v2"})
        r = user.post(f"/builder/{page}/restore/1")
        assert r.status_code == 200, r.text
        assert "id" in r.json()

    def test_restore_unknown_version_404(self, user, published_page):
        pid, _ = published_page
        assert user.post(f"/builder/{pid}/restore/999").status_code == 404

    def test_restore_unknown_page_404(self, user):
        assert user.post(f"/builder/{uuid.uuid4()}/restore/1").status_code == 404
