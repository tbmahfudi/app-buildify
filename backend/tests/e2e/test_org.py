"""
Deep coverage of the `org` router (21 operations): the Tenant → Company →
Branch → Department hierarchy plus org users.

Identity rules (from the live contract):
  * Tenant CRUD: superadmin (platform-level).
  * Company/Branch/Department CRUD: superadmin drives the full lifecycle via
    the is_superuser bypass when the parent ids are supplied in the body. A
    tenant user (`ceo@techstart.com`) can create companies but is denied
    branch/department creation and company deletion — exercised as authz cases.
"""
import uuid

import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)


# --------------------------------------------------------------------------- #
# Reads
# --------------------------------------------------------------------------- #
class TestReads:
    @pytest.mark.parametrize("path", ["/org/tenants", "/org/companies", "/org/branches", "/org/departments", "/org/users"])
    def test_list_ok(self, su, path):
        r = su.get(path)
        assert r.status_code == 200
        assert "items" in r.json()

    @pytest.mark.parametrize("path", ["/org/tenants", "/org/companies", "/org/branches", "/org/departments", "/org/users"])
    def test_list_requires_auth(self, anon, path):
        assert anon.get(path).status_code in UNAUTH

    @pytest.mark.parametrize("path", ["/org/tenants", "/org/companies", "/org/branches", "/org/departments"])
    def test_get_unknown_404(self, su, path):
        assert su.get(f"{path}/{uuid.uuid4()}").status_code == 404


# --------------------------------------------------------------------------- #
# Tenant lifecycle (superadmin)
# --------------------------------------------------------------------------- #
class TestTenantLifecycle:
    def test_create_get_update_delete(self, su, unique):
        code = unique("E2ET").replace("_", "")[:20]
        cr = su.post("/org/tenants", json={"name": f"E2E {code}", "code": code})
        assert cr.status_code == 201, cr.text
        tid = cr.json()["id"]
        try:
            assert su.get(f"/org/tenants/{tid}").json()["id"] == tid
            up = su.put(f"/org/tenants/{tid}", json={"description": "updated by e2e"})
            assert up.status_code in (200, 204)
        finally:
            assert su.delete(f"/org/tenants/{tid}").status_code in (200, 204)
        assert su.get(f"/org/tenants/{tid}").status_code == 404

    def test_create_missing_required_422(self, su):
        assert su.post("/org/tenants", json={"name": "no code"}).status_code == 422

    def test_create_requires_auth(self, anon):
        assert anon.post("/org/tenants", json={"name": "x", "code": "x"}).status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Company → Branch → Department hierarchy (superadmin)
# --------------------------------------------------------------------------- #
@pytest.fixture
def tenant_id(su):
    """An existing tenant to attach org entities to."""
    items = su.get("/org/tenants").json()["items"]
    assert items, "no tenants seeded"
    return items[0]["id"]


class TestOrgHierarchy:
    def test_company_branch_department_lifecycle(self, su, tenant_id, unique):
        sfx = uuid.uuid4().hex[:6]
        cid = bid = did = None
        try:
            # company
            co = su.post("/org/companies", json={"tenant_id": tenant_id, "code": f"C{sfx}", "name": f"Co {sfx}"})
            assert co.status_code == 201, co.text
            cid = co.json()["id"]
            assert co.json()["tenant_id"] == tenant_id
            # branch under company
            br = su.post("/org/branches", json={"company_id": cid, "code": f"B{sfx}", "name": f"Br {sfx}"})
            assert br.status_code == 201, br.text
            bid = br.json()["id"]
            # department under branch
            dp = su.post("/org/departments", json={"company_id": cid, "branch_id": bid, "code": f"D{sfx}", "name": f"Dept {sfx}"})
            assert dp.status_code == 201, dp.text
            did = dp.json()["id"]
            # read back + update
            assert su.get(f"/org/companies/{cid}").json()["id"] == cid
            assert su.put(f"/org/companies/{cid}", json={"description": "updated"}).status_code in (200, 204)
            assert su.get(f"/org/branches/{bid}").json()["id"] == bid
            assert su.get(f"/org/departments/{did}").json()["id"] == did
        finally:
            # tear down in dependency order
            if did:
                assert su.delete(f"/org/departments/{did}").status_code in (200, 204)
            if bid:
                assert su.delete(f"/org/branches/{bid}").status_code in (200, 204)
            if cid:
                assert su.delete(f"/org/companies/{cid}").status_code in (200, 204)

    def test_company_create_missing_tenant_422(self, su):
        assert su.post("/org/companies", json={"code": "X", "name": "X"}).status_code == 422

    def test_branch_requires_company_id_422(self, su):
        assert su.post("/org/branches", json={"code": "X", "name": "X"}).status_code == 422


# --------------------------------------------------------------------------- #
# Authorization — tenant user is scoped
# --------------------------------------------------------------------------- #
class TestTenantUserScoping:
    def test_tenant_user_can_create_company(self, user, su):
        """ceo has companies:create:tenant; superadmin cleans up (ceo lacks delete)."""
        me = user.get("/auth/me").json()
        sfx = uuid.uuid4().hex[:6]
        r = user.post("/org/companies", json={"tenant_id": me["tenant_id"], "code": f"UC{sfx}", "name": f"UCo {sfx}"})
        assert r.status_code == 201, r.text
        cid = r.json()["id"]
        try:
            # ceo is scoped: it cannot delete companies
            assert user.delete(f"/org/companies/{cid}").status_code == 403
        finally:
            # superadmin cleans up so we don't accumulate orphans
            su.delete(f"/org/companies/{cid}")

    def test_tenant_user_cannot_create_branch(self, user):
        # branches:create:company not granted to the tenant user
        items = user.get("/org/companies").json()["items"]
        if not items:
            pytest.skip("no company visible to tenant user")
        r = user.post("/org/branches", json={"company_id": items[0]["id"], "code": "X", "name": "X"})
        assert r.status_code == 403
