"""
Deep coverage of the `dynamic-data` router (runtime CRUD on published entities).

The runtime data API is tenant-scoped, so these run as the tenant user (`user`
= ceo@techstart.com), not the superadmin (which has no tenant and gets 404).

A module-scoped `published_entity` fixture creates a throwaway entity, adds a
field, and publishes it (real DDL → a physical table), then tears it down. This
keeps the suite self-contained rather than depending on seeded published
entities (several of which are marked published but have no backing table).
"""
import uuid

import pytest

from .conftest import drop_table_best_effort

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)


@pytest.fixture(scope="module")
def published_entity(user):
    """Create + publish a tenant entity with a `title` text field; yield its name."""
    sfx = uuid.uuid4().hex[:8]
    name = f"e2e_dd_{sfx}"
    cr = user.post("/data-model/entities", json={
        "name": name, "label": f"E2E {sfx}", "plural_label": f"E2E {sfx}s",
        "table_name": name, "data_scope": "tenant",
    })
    assert cr.status_code in (200, 201), cr.text
    eid = cr.json()["id"]
    fr = user.post(f"/data-model/entities/{eid}/fields",
                   json={"name": "title", "label": "Title", "field_type": "text", "data_type": "VARCHAR"})
    assert fr.status_code in (200, 201), fr.text
    pub = user.post(f"/data-model/entities/{eid}/publish", json={"commit_message": "e2e publish"})
    assert pub.status_code == 200, f"publish failed: {pub.text}"
    yield name
    user.delete(f"/data-model/entities/{eid}")
    # deleting a published entity does not drop its table — clean it up
    drop_table_best_effort(name)


@pytest.fixture
def record(user, published_entity):
    """Create a record, yield (entity, id, body); delete it afterward."""
    r = user.post(f"/dynamic-data/{published_entity}/records", json={"data": {"title": "fixture"}})
    assert r.status_code == 201, r.text
    rid = r.json()["id"]
    yield published_entity, rid
    user.delete(f"/dynamic-data/{published_entity}/records/{rid}")


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #
class TestMetadata:
    def test_metadata(self, user, published_entity):
        r = user.get(f"/dynamic-data/{published_entity}/metadata")
        assert r.status_code == 200
        names = [f["name"] for f in r.json()["fields"]]
        assert "title" in names and "id" in names

    def test_metadata_unknown_entity_404(self, user):
        assert user.get(f"/dynamic-data/does_not_exist_{uuid.uuid4().hex[:6]}/metadata").status_code == 404


# --------------------------------------------------------------------------- #
# Record CRUD
# --------------------------------------------------------------------------- #
class TestRecordCrud:
    def test_create_returns_201_with_id(self, user, published_entity):
        r = user.post(f"/dynamic-data/{published_entity}/records", json={"data": {"title": "hello"}})
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["id"] and body["data"]["title"] == "hello"
        user.delete(f"/dynamic-data/{published_entity}/records/{body['id']}")

    def test_get_record(self, user, record):
        entity, rid = record
        r = user.get(f"/dynamic-data/{entity}/records/{rid}")
        assert r.status_code == 200 and r.json()["id"] == rid

    def test_update_record(self, user, record):
        entity, rid = record
        r = user.put(f"/dynamic-data/{entity}/records/{rid}", json={"data": {"title": "updated"}})
        assert r.status_code == 200
        assert user.get(f"/dynamic-data/{entity}/records/{rid}").json()["data"]["title"] == "updated"

    def test_delete_record(self, user, published_entity):
        rid = user.post(f"/dynamic-data/{published_entity}/records", json={"data": {"title": "to-delete"}}).json()["id"]
        assert user.delete(f"/dynamic-data/{published_entity}/records/{rid}").status_code == 204
        assert user.get(f"/dynamic-data/{published_entity}/records/{rid}").status_code == 404

    def test_create_missing_data_422(self, user, published_entity):
        assert user.post(f"/dynamic-data/{published_entity}/records", json={"title": "no wrapper"}).status_code == 422

    def test_get_unknown_record_404(self, user, published_entity):
        assert user.get(f"/dynamic-data/{published_entity}/records/{uuid.uuid4()}").status_code == 404


# --------------------------------------------------------------------------- #
# List / filter / paginate
# --------------------------------------------------------------------------- #
class TestList:
    def test_list_envelope(self, user, record):
        entity, _ = record
        r = user.get(f"/dynamic-data/{entity}/records?page=1&page_size=10")
        assert r.status_code == 200
        body = r.json()
        assert "items" in body and "total" in body
        assert body["total"] >= 1

    def test_list_search(self, user, record):
        entity, rid = record
        r = user.get(f"/dynamic-data/{entity}/records", params={"search": "fixture"})
        assert r.status_code == 200


# --------------------------------------------------------------------------- #
# Aggregate
# --------------------------------------------------------------------------- #
class TestAggregate:
    def test_count(self, user, published_entity):
        r = user.get(f"/dynamic-data/{published_entity}/aggregate",
                     params={"metrics": '[{"field":"*","function":"count"}]'})
        assert r.status_code == 200
        assert "groups" in r.json()


# --------------------------------------------------------------------------- #
# Bulk
# --------------------------------------------------------------------------- #
class TestBulk:
    def test_bulk_create(self, user, published_entity):
        r = user.post(f"/dynamic-data/{published_entity}/records/bulk",
                      json={"records": [{"title": "b1"}, {"title": "b2"}]})
        assert r.status_code in (200, 201), r.text


# --------------------------------------------------------------------------- #
# AuthN / tenant scoping
# --------------------------------------------------------------------------- #
class TestAuthScoping:
    def test_requires_auth(self, anon, published_entity):
        assert anon.get(f"/dynamic-data/{published_entity}/records").status_code in UNAUTH

    def test_superadmin_has_no_tenant_scope(self, su, published_entity):
        # superadmin has tenant_id=NULL; runtime data is tenant-scoped → not visible
        r = su.get(f"/dynamic-data/{published_entity}/records")
        assert r.status_code in (400, 404)
