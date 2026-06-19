"""
Deep coverage of the `metadata` router (6 ops):
  - GET  /metadata/entities              — list published entities with UI config
  - GET  /metadata/entities/{name}       — get entity metadata by name
  - POST /metadata/entities              — seed UI config for existing entity
  - PUT  /metadata/entities/{name}       — update entity UI config (version++)
  - DELETE /metadata/entities/{name}     — deactivate entity (is_active=False, 204)
  - POST /metadata/entities/{name}/regenerate — force-rebuild config from entity def

Known stable entities in DB: SLAPolicy, SupportTicket, TicketCategory
(TicketComment was deactivated during exploratory probing).
"""
import uuid

import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)
OK = (200, 201)

_METADATA_PERMS = [
    "metadata:read:tenant",
    "metadata:create:tenant",
    "metadata:update:tenant",
    "metadata:delete:tenant",
]
# Use these two stable entities across multiple read/update/regenerate tests
STABLE_ENTITY = "SLAPolicy"
STABLE_ENTITY2 = "TicketCategory"


@pytest.fixture(scope="session", autouse=True)
def _grant_metadata_permissions(user, su):
    me = user.get("/auth/me").json()
    tenant_id = me["tenant_id"]
    roles = su.get("/rbac/roles", params={"limit": 1000}).json()["items"]
    role = next(r for r in roles if r["code"] == "tenant_admin" and r.get("tenant_id") == tenant_id)
    perms = su.get("/rbac/permissions", params={"limit": 1000}).json()["items"]
    perm_ids = [p["id"] for p in perms if p["code"] in _METADATA_PERMS]
    r = su.post(f"/rbac/roles/{role['id']}/permissions", json=perm_ids)
    assert r.status_code in OK, r.text


@pytest.fixture(scope="session")
def _dm_entity(user):
    """
    Create a throwaway entity in data-model for lifecycle tests.
    Returns (entity_id, entity_name). Tears down at session end.
    """
    me = user.get("/auth/me").json()
    tenant_id = me["tenant_id"]
    name = f"e2emeta{uuid.uuid4().hex[:8]}"
    r = user.post("/data-model/entities", json={
        "name": name,
        "label": "E2E Metadata Test",
        "table_name": f"e2e_{name}",
        "entity_type": "custom",
        "tenant_id": tenant_id,
    })
    assert r.status_code in OK, f"data-model create failed: {r.text}"
    eid = r.json().get("id") or r.json().get("entity_id")
    yield eid, name
    # Teardown: permanently delete the entity from data-model
    user.delete(f"/data-model/entities/{eid}/permanent")
    user.delete(f"/data-model/entities/{eid}")


@pytest.fixture(scope="session")
def _meta_entity(user, _dm_entity):
    """
    Ensure UI metadata config exists on the throwaway entity. Returns entity_name.
    Idempotent: if config already exists (400) treats it as success.
    """
    eid, name = _dm_entity
    r = user.post("/metadata/entities", json={
        "entity_name": name,
        "display_name": "E2E Metadata Test",
        "description": "created by e2e test suite",
        "table_config": {"columns": [], "page_size": 25},
        "form_config": {"fields": [], "layout": "vertical"},
        "permissions": {},
    })
    # 400 means config already exists (created earlier in same session) — that's fine
    assert r.status_code in (200, 201, 400), f"metadata create failed: {r.text}"
    yield name


# ─── list ────────────────────────────────────────────────────────────────────

class TestMetadataList:
    def test_list_returns_dict_with_entities_and_total(self, user):
        r = user.get("/metadata/entities")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "entities" in body
        assert "total" in body
        assert isinstance(body["entities"], list)
        assert body["total"] >= 0

    def test_list_contains_stable_entities(self, user):
        body = user.get("/metadata/entities").json()
        # At least one known entity should be present
        entities = body["entities"]
        assert any(e in entities for e in (STABLE_ENTITY, STABLE_ENTITY2, "SupportTicket"))

    def test_list_requires_auth(self, anon):
        assert anon.get("/metadata/entities").status_code in UNAUTH


# ─── get ─────────────────────────────────────────────────────────────────────

class TestMetadataGet:
    def test_get_known_entity_returns_200(self, user):
        r = user.get(f"/metadata/entities/{STABLE_ENTITY}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["entity_name"] == STABLE_ENTITY
        assert "table" in body
        assert "form" in body
        assert "version" in body
        assert "is_active" in body

    def test_get_returns_expected_schema_fields(self, user):
        r = user.get(f"/metadata/entities/{STABLE_ENTITY}")
        assert r.status_code == 200
        body = r.json()
        for key in ("id", "entity_name", "display_name", "table", "form", "is_system", "created_at"):
            assert key in body, f"missing key: {key}"

    def test_get_unknown_entity_404(self, user):
        r = user.get(f"/metadata/entities/nonexistent_xyz_{uuid.uuid4().hex[:6]}")
        assert r.status_code == 404, r.text

    def test_get_requires_auth(self, anon):
        assert anon.get(f"/metadata/entities/{STABLE_ENTITY}").status_code in UNAUTH


# ─── create (POST /metadata/entities) ────────────────────────────────────────

class TestMetadataCreate:
    def test_create_seeds_config_on_existing_entity(self, user, _dm_entity):
        eid, name = _dm_entity
        # Create fresh config (teardown will clean the entity)
        r = user.post("/metadata/entities", json={
            "entity_name": name,
            "display_name": "Create Test",
            "table_config": {"columns": [], "page_size": 10},
            "form_config": {"fields": []},
        })
        # If _meta_entity fixture already created it → 400; otherwise 201
        assert r.status_code in (200, 201, 400), r.text
        if r.status_code in (200, 201):
            body = r.json()
            assert body["entity_name"] == name

    def test_create_duplicate_400(self, user, _meta_entity):
        """Seeding config on an entity that already has table_config → 400."""
        r = user.post("/metadata/entities", json={
            "entity_name": _meta_entity,
            "display_name": "Dup",
            "table_config": {"columns": []},
            "form_config": {"fields": []},
        })
        assert r.status_code == 400, r.text

    def test_create_unknown_entity_404(self, user):
        r = user.post("/metadata/entities", json={
            "entity_name": f"nonexistent_{uuid.uuid4().hex[:8]}",
            "display_name": "Nonexistent",
            "table_config": {"columns": []},
            "form_config": {"fields": []},
        })
        assert r.status_code == 404, r.text

    def test_create_missing_required_fields_422(self, user):
        # Missing entity_name
        r = user.post("/metadata/entities", json={
            "display_name": "Missing name",
            "table_config": {"columns": []},
            "form_config": {"fields": []},
        })
        assert r.status_code == 422, r.text

    def test_create_requires_auth(self, anon):
        r = anon.post("/metadata/entities", json={
            "entity_name": "x",
            "display_name": "x",
            "table_config": {"columns": []},
            "form_config": {"fields": []},
        })
        assert r.status_code in UNAUTH


# ─── update ──────────────────────────────────────────────────────────────────

class TestMetadataUpdate:
    def test_update_description(self, user, _meta_entity):
        r = user.put(f"/metadata/entities/{_meta_entity}", json={"description": "Updated by E2E"})
        assert r.status_code == 200, r.text
        assert r.json()["description"] == "Updated by E2E"

    def test_update_increments_version(self, user, _meta_entity):
        r1 = user.get(f"/metadata/entities/{_meta_entity}")
        v_before = r1.json()["version"]
        user.put(f"/metadata/entities/{_meta_entity}", json={"description": "bump"})
        r2 = user.get(f"/metadata/entities/{_meta_entity}")
        assert r2.json()["version"] == v_before + 1

    def test_update_display_name(self, user):
        r = user.put(f"/metadata/entities/{STABLE_ENTITY2}", json={"display_name": "Ticket Category E2E"})
        assert r.status_code == 200, r.text
        assert r.json()["display_name"] == "Ticket Category E2E"

    def test_update_unknown_entity_404(self, user):
        r = user.put(f"/metadata/entities/nonexistent_xyz", json={"description": "x"})
        assert r.status_code == 404, r.text

    def test_update_requires_auth(self, anon, _meta_entity):
        assert anon.put(f"/metadata/entities/{_meta_entity}", json={"description": "x"}).status_code in UNAUTH


# ─── delete ──────────────────────────────────────────────────────────────────

class TestMetadataDelete:
    def test_delete_deactivates_entity_204(self, user, unique):
        """Create a fresh entity+config, delete it, verify 204 and absent from list."""
        me = user.get("/auth/me").json()
        tenant_id = me["tenant_id"]
        name = f"e2edel{uuid.uuid4().hex[:8]}"

        # Create in data-model
        dm_r = user.post("/data-model/entities", json={
            "name": name,
            "label": "E2E Delete Test",
            "table_name": f"e2e_del_{name}",
            "entity_type": "custom",
            "tenant_id": tenant_id,
        })
        assert dm_r.status_code in OK, dm_r.text
        eid = dm_r.json().get("id") or dm_r.json().get("entity_id")

        try:
            # Seed metadata
            meta_r = user.post("/metadata/entities", json={
                "entity_name": name,
                "display_name": "E2E Delete Test",
                "table_config": {"columns": []},
                "form_config": {"fields": []},
            })
            assert meta_r.status_code in OK, meta_r.text

            # Delete (deactivate)
            del_r = user.delete(f"/metadata/entities/{name}")
            assert del_r.status_code == 204, del_r.text
            assert del_r.text == ""

            # Verify: entity no longer in list
            entities = user.get("/metadata/entities").json()["entities"]
            assert name not in entities

            # Verify: can re-activate via PUT
            ra = user.put(f"/metadata/entities/{name}", json={"is_active": True})
            assert ra.status_code == 200, ra.text
            assert ra.json()["is_active"] is True
        finally:
            user.delete(f"/data-model/entities/{eid}/permanent")
            user.delete(f"/data-model/entities/{eid}")

    def test_delete_unknown_entity_404(self, user):
        r = user.delete(f"/metadata/entities/nonexistent_xyz")
        assert r.status_code == 404, r.text

    def test_delete_requires_auth(self, anon):
        assert anon.delete(f"/metadata/entities/{STABLE_ENTITY}").status_code in UNAUTH


# ─── regenerate ──────────────────────────────────────────────────────────────

class TestMetadataRegenerate:
    def test_regenerate_returns_200_with_entity(self, user):
        r = user.post(f"/metadata/entities/{STABLE_ENTITY}/regenerate")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["entity_name"] == STABLE_ENTITY
        assert "table" in body
        assert "form" in body

    def test_regenerate_rebuilds_config(self, user):
        """After regenerate, entity still has valid table/form config."""
        r = user.post(f"/metadata/entities/{STABLE_ENTITY}/regenerate")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["table"] is not None
        assert body["form"] is not None

    def test_regenerate_unknown_entity_404(self, user):
        r = user.post(f"/metadata/entities/nonexistent_xyz/regenerate")
        assert r.status_code == 404, r.text

    def test_regenerate_requires_auth(self, anon):
        assert anon.post(f"/metadata/entities/{STABLE_ENTITY}/regenerate").status_code in UNAUTH
