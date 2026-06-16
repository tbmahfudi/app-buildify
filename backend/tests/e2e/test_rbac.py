"""
Deep coverage of the `rbac` router (23 operations).

Identity rules learned from the live contract:
  * cross-tenant *reads* (roles/permissions/groups/categories) work as `su`.
  * tenant-scoped *writes* (create role, assign permission) must run as a
    tenant-scoped admin — the superadmin has tenant_id=NULL and is rejected
    with 400 "User has no tenant; cannot create tenant-scoped role".
"""
import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)


# --------------------------------------------------------------------------- #
# Permissions (read-only catalogue)
# --------------------------------------------------------------------------- #
class TestPermissions:
    def test_list_permissions(self, su):
        r = su.get("/rbac/permissions")
        assert r.status_code == 200
        items = r.json()["items"]
        assert items, "no permissions seeded"
        p = items[0]
        for k in ("id", "code", "resource", "action"):
            assert k in p

    def test_list_permissions_requires_auth(self, anon):
        assert anon.get("/rbac/permissions").status_code in UNAUTH

    def test_permissions_grouped(self, su):
        r = su.get("/rbac/permissions/grouped")
        assert r.status_code == 200

    def test_permission_categories(self, su):
        r = su.get("/rbac/permission-categories")
        assert r.status_code == 200
        cats = r.json()["categories"]
        assert cats and {"name", "count"} <= set(cats[0])

    def test_get_permission_by_id(self, su):
        pid = su.get("/rbac/permissions").json()["items"][0]["id"]
        r = su.get(f"/rbac/permissions/{pid}")
        assert r.status_code == 200
        assert r.json()["id"] == pid

    def test_get_permission_unknown(self, su):
        import uuid
        r = su.get(f"/rbac/permissions/{uuid.uuid4()}")
        assert r.status_code == 404


# --------------------------------------------------------------------------- #
# Roles — read
# --------------------------------------------------------------------------- #
class TestRolesRead:
    def test_list_roles(self, su):
        r = su.get("/rbac/roles")
        assert r.status_code == 200
        items = r.json()["items"]
        assert items
        assert {"id", "code", "name", "is_system"} <= set(items[0])

    def test_get_role_by_id(self, su):
        rid = su.get("/rbac/roles").json()["items"][0]["id"]
        r = su.get(f"/rbac/roles/{rid}")
        assert r.status_code == 200
        assert r.json()["id"] == rid

    def test_get_role_unknown(self, su):
        import uuid
        assert su.get(f"/rbac/roles/{uuid.uuid4()}").status_code == 404

    def test_list_roles_requires_auth(self, anon):
        assert anon.get("/rbac/roles").status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Roles — full lifecycle (tenant-scoped, runs as tenant admin `user`)
# --------------------------------------------------------------------------- #
class TestRoleLifecycle:
    def test_create_role_requires_code(self, user):
        r = user.post("/rbac/roles", json={"name": "missing code"})
        assert r.status_code == 422

    def test_superadmin_cannot_create_tenant_role(self, su):
        # documents the tenant-scoping guard: superadmin has no tenant
        r = su.post("/rbac/roles", json={"code": "e2e_su_x", "name": "x", "description": "x"})
        assert r.status_code == 400

    def test_create_get_update_delete(self, user, unique):
        code = unique("e2e_role")
        # create
        cr = user.post("/rbac/roles", json={"code": code, "name": code, "description": "created by e2e"})
        assert cr.status_code == 201, cr.text
        role = cr.json()
        rid = role["id"]
        assert role["code"] == code
        assert role["is_system"] is False
        try:
            # read back
            got = user.get(f"/rbac/roles/{rid}")
            assert got.status_code == 200 and got.json()["id"] == rid
            # appears in list
            ids = [x["id"] for x in user.get("/rbac/roles").json()["items"]]
            assert rid in ids
            # update
            up = user.put(f"/rbac/roles/{rid}", json={"description": "updated by e2e"})
            assert up.status_code in (200, 204)
            if up.status_code == 200:
                assert up.json()["description"] == "updated by e2e"
        finally:
            d = user.delete(f"/rbac/roles/{rid}")
            assert d.status_code in (200, 204)
        # gone
        assert user.get(f"/rbac/roles/{rid}").status_code == 404

    def test_assign_and_remove_permission(self, user, unique):
        code = unique("e2e_role")
        rid = user.post("/rbac/roles", json={"code": code, "name": code}).json()["id"]
        pid = user.get("/rbac/permissions").json()["items"][0]["id"]
        try:
            # body is a bare JSON array of permission ids
            assign = user.post(f"/rbac/roles/{rid}/permissions", json=[pid])
            assert assign.status_code in (200, 201), assign.text
            remove = user.delete(f"/rbac/roles/{rid}/permissions/{pid}")
            assert remove.status_code in (200, 204)
        finally:
            user.delete(f"/rbac/roles/{rid}")

    def test_bulk_update_permissions(self, user, unique):
        code = unique("e2e_role")
        rid = user.post("/rbac/roles", json={"code": code, "name": code}).json()["id"]
        perms = user.get("/rbac/permissions").json()["items"]
        ids = [p["id"] for p in perms[:3]]
        try:
            # endpoint takes grant_ids + revoke_ids
            r = user.patch(
                f"/rbac/roles/{rid}/permissions/bulk",
                json={"grant_ids": ids, "revoke_ids": []},
            )
            assert r.status_code in (200, 204), r.text
        finally:
            user.delete(f"/rbac/roles/{rid}")

    def test_create_role_requires_auth(self, anon):
        r = anon.post("/rbac/roles", json={"code": "x", "name": "x"})
        assert r.status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Groups
# --------------------------------------------------------------------------- #
class TestGroups:
    def test_list_groups(self, su):
        r = su.get("/rbac/groups")
        assert r.status_code == 200
        assert "items" in r.json()

    def test_get_group_by_id(self, su):
        items = su.get("/rbac/groups").json()["items"]
        if not items:
            pytest.skip("no groups seeded")
        gid = items[0]["id"]
        r = su.get(f"/rbac/groups/{gid}")
        assert r.status_code == 200
        assert r.json()["id"] == gid

    def test_get_group_unknown(self, su):
        import uuid
        assert su.get(f"/rbac/groups/{uuid.uuid4()}").status_code == 404


# --------------------------------------------------------------------------- #
# User ↔ role/permission views
# --------------------------------------------------------------------------- #
class TestUserRoles:
    def test_get_user_roles(self, su):
        uid = su.get("/auth/me").json()["id"]
        r = su.get(f"/rbac/users/{uid}/roles")
        assert r.status_code == 200
        body = r.json()
        assert body["user_id"] == uid and "roles" in body

    def test_get_user_permissions(self, su):
        uid = su.get("/auth/me").json()["id"]
        r = su.get(f"/rbac/users/{uid}/permissions")
        assert r.status_code == 200
        body = r.json()
        assert "permission_codes" in body and body.get("is_superuser") is True

    def test_user_roles_requires_auth(self, anon):
        import uuid
        assert anon.get(f"/rbac/users/{uuid.uuid4()}/roles").status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Organization structure
# --------------------------------------------------------------------------- #
class TestOrgStructure:
    def test_organization_structure(self, su):
        r = su.get("/rbac/organization-structure")
        assert r.status_code == 200
