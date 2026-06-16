"""
Deep coverage of the `data-model` router (NoCode entity designer).

Scope: the **design-time** surface — entity + field + relationship CRUD,
clone, soft-delete/restore, migration preview, introspection. We deliberately
do NOT call `/publish` or `/generate-migration` + `/execute`, which run real
DDL and create physical tables in the shared dev database. Publish/rollback is
covered separately and gated behind an opt-in marker.

Entities are created in `draft` status (invisible to the runtime data API),
so this whole module is safe and self-cleaning.
"""
import uuid

import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)


@pytest.fixture
def draft_entity(su):
    """Create a draft entity; yield (id, name); clean up it and any clone."""
    sfx = uuid.uuid4().hex[:8]
    name = f"e2e_{sfx}"
    body = {
        "name": name,
        "label": f"E2E {sfx}",
        "plural_label": f"E2E {sfx}s",
        "table_name": f"e2e_tbl_{sfx}",
        "data_scope": "tenant",
    }
    r = su.post("/data-model/entities", json=body)
    assert r.status_code in (200, 201), r.text
    eid = r.json()["id"]
    yield eid, name
    # cleanup: the entity + any clone created from it
    su.delete(f"/data-model/entities/{eid}")
    for e in su.get("/data-model/entities").json():
        if e.get("name", "").startswith(name):
            su.delete(f"/data-model/entities/{e['id']}")


def _add_field(su, eid, **over):
    body = {"name": "title", "label": "Title", "field_type": "text", "data_type": "VARCHAR"}
    body.update(over)
    return su.post(f"/data-model/entities/{eid}/fields", json=body)


# --------------------------------------------------------------------------- #
# Reads
# --------------------------------------------------------------------------- #
class TestReads:
    def test_list_entities(self, su):
        r = su.get("/data-model/entities")
        assert r.status_code == 200 and isinstance(r.json(), list)

    def test_introspect_objects(self, su):
        r = su.get("/data-model/introspect/objects")
        assert r.status_code == 200 and "tables" in r.json()

    def test_list_relationships(self, su):
        r = su.get("/data-model/relationships")
        assert r.status_code == 200 and isinstance(r.json(), list)

    @pytest.mark.parametrize("path", ["/data-model/entities", "/data-model/relationships", "/data-model/introspect/objects"])
    def test_requires_auth(self, anon, path):
        assert anon.get(path).status_code in UNAUTH

    def test_get_entity_unknown_404(self, su):
        assert su.get(f"/data-model/entities/{uuid.uuid4()}").status_code == 404


# --------------------------------------------------------------------------- #
# Entity lifecycle
# --------------------------------------------------------------------------- #
class TestEntityLifecycle:
    def test_create_get_update_delete(self, su):
        sfx = uuid.uuid4().hex[:8]
        name = f"e2e_{sfx}"
        cr = su.post("/data-model/entities", json={
            "name": name, "label": "L", "table_name": f"e2e_tbl_{sfx}", "data_scope": "tenant",
        })
        assert cr.status_code in (200, 201), cr.text
        body = cr.json()
        eid = body["id"]
        assert body["status"] == "draft"
        try:
            assert su.get(f"/data-model/entities/{eid}").json()["id"] == eid
            names = [e["name"] for e in su.get("/data-model/entities").json()]
            assert name in names
            up = su.put(f"/data-model/entities/{eid}", json={"description": "updated"})
            assert up.status_code == 200 and up.json()["description"] == "updated"
        finally:
            assert su.delete(f"/data-model/entities/{eid}").status_code in (200, 204)
        assert su.get(f"/data-model/entities/{eid}").status_code == 404

    def test_create_missing_required_422(self, su):
        # missing table_name + data_scope
        assert su.post("/data-model/entities", json={"name": "x", "label": "x"}).status_code == 422

    def test_create_requires_auth(self, anon):
        r = anon.post("/data-model/entities", json={"name": "x", "label": "x", "table_name": "x", "data_scope": "tenant"})
        assert r.status_code in UNAUTH

    def test_clone(self, su, draft_entity):
        eid, name = draft_entity
        r = su.post(f"/data-model/entities/{eid}/clone", json={"name": f"{name}_c", "label": "Clone", "table_name": f"{name}_c"})
        assert r.status_code in (200, 201), r.text
        clone_name = r.json()["name"]
        names = [e["name"] for e in su.get("/data-model/entities").json()]
        assert clone_name in names  # cleanup handled by the fixture (prefix match)

    def test_preview_migration(self, su, draft_entity):
        eid, _ = draft_entity
        r = su.get(f"/data-model/entities/{eid}/preview-migration")
        assert r.status_code == 200
        assert r.json()["operation"] == "CREATE"
        assert "CREATE" in r.json()["up_script"].upper()


# --------------------------------------------------------------------------- #
# Field lifecycle
# --------------------------------------------------------------------------- #
class TestFieldLifecycle:
    def test_add_list_update(self, su, draft_entity):
        eid, _ = draft_entity
        add = _add_field(su, eid)
        assert add.status_code in (200, 201), add.text
        fid = add.json()["id"]
        fields = su.get(f"/data-model/entities/{eid}/fields").json()
        names = [f["name"] for f in fields]
        assert "title" in names and "id" in names  # entity auto-gets an id field
        up = su.put(f"/data-model/entities/{eid}/fields/{fid}", json={"label": "Title 2"})
        assert up.status_code == 200 and up.json()["label"] == "Title 2"

    def test_soft_delete_then_restore(self, su, draft_entity):
        eid, _ = draft_entity
        fid = _add_field(su, eid, name="temp", label="Temp").json()["id"]
        assert su.delete(f"/data-model/entities/{eid}/fields/{fid}").status_code in (200, 204)
        deleted = su.get(f"/data-model/entities/{eid}/fields/deleted").json()
        assert any(f["id"] == fid for f in deleted)
        assert su.post(f"/data-model/entities/{eid}/fields/{fid}/restore").status_code == 200
        deleted2 = su.get(f"/data-model/entities/{eid}/fields/deleted").json()
        assert not any(f["id"] == fid for f in deleted2)

    def test_soft_delete_then_permanent(self, su, draft_entity):
        eid, _ = draft_entity
        fid = _add_field(su, eid, name="temp2", label="Temp2").json()["id"]
        assert su.delete(f"/data-model/entities/{eid}/fields/{fid}").status_code in (200, 204)
        assert su.delete(f"/data-model/entities/{eid}/fields/{fid}/permanent").status_code in (200, 204)

    def test_add_field_unknown_entity_404(self, su):
        r = _add_field(su, uuid.uuid4())
        assert r.status_code == 404
