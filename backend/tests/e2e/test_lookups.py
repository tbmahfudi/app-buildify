"""
Deep coverage of the `lookups` router (8 ops):
  - POST /lookups/configurations          — create
  - GET  /lookups/configurations          — list (array, optional filters)
  - GET  /lookups/configurations/{id}     — get by id
  - PUT  /lookups/configurations/{id}     — update
  - DELETE /lookups/configurations/{id}  — soft-delete → {"message": "..."}
  - GET  /lookups/configurations/{id}/data — lookup data (paginated items)
  - POST /lookups/cascading-rules         — create rule
  - GET  /lookups/cascading-rules         — list rules (optional parent/child filter)

No RBAC permission gates on this router (get_current_user only).
"""
import uuid

import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)
OK = (200, 201)


# ─── helpers ────────────────────────────────────────────────────────────────

def _cfg_body(unique, source_type="static_list", **overrides):
    body = {
        "name": unique("lkp"),
        "label": "E2E Lookup",
        "source_type": source_type,
        "static_options": [{"value": "a", "label": "Alpha"}, {"value": "b", "label": "Beta"}],
    }
    body.update(overrides)
    return body


# ─── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def config(user, unique):
    """Create a static_list lookup config and delete it on teardown."""
    r = user.post("/lookups/configurations", json=_cfg_body(unique))
    assert r.status_code in OK, r.text
    cid = r.json()["id"]
    yield cid
    user.delete(f"/lookups/configurations/{cid}")


@pytest.fixture
def config2(user, unique):
    """Second config used for cascading rules."""
    r = user.post("/lookups/configurations", json=_cfg_body(unique, label="E2E Lookup 2"))
    assert r.status_code in OK, r.text
    cid = r.json()["id"]
    yield cid
    user.delete(f"/lookups/configurations/{cid}")


# ─── configuration CRUD ──────────────────────────────────────────────────────

class TestLookupConfigCreate:
    def test_create_returns_200_with_id(self, user, unique):
        body = _cfg_body(unique)
        r = user.post("/lookups/configurations", json=body)
        assert r.status_code in OK, r.text
        data = r.json()
        assert "id" in data
        assert data["name"] == body["name"]
        assert data["source_type"] == "static_list"
        # cleanup
        user.delete(f"/lookups/configurations/{data['id']}")

    def test_create_missing_name_422(self, user):
        r = user.post("/lookups/configurations", json={"label": "X", "source_type": "static_list"})
        assert r.status_code == 422

    def test_create_missing_label_422(self, user, unique):
        r = user.post("/lookups/configurations", json={"name": unique("lkp"), "source_type": "static_list"})
        assert r.status_code == 422

    def test_create_missing_source_type_422(self, user, unique):
        r = user.post("/lookups/configurations", json={"name": unique("lkp"), "label": "X"})
        assert r.status_code == 422

    def test_create_duplicate_name_400(self, user, config, unique):
        """Duplicate name within same tenant → 400."""
        existing_name = user.get(f"/lookups/configurations/{config}").json()["name"]
        r = user.post("/lookups/configurations", json={
            "name": existing_name,
            "label": "Dup",
            "source_type": "static_list",
        })
        assert r.status_code == 400, r.text

    def test_create_requires_auth(self, anon, unique):
        assert anon.post("/lookups/configurations", json=_cfg_body(unique)).status_code in UNAUTH


class TestLookupConfigList:
    def test_list_returns_array(self, user, config):
        r = user.get("/lookups/configurations")
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_list_contains_created_config(self, user, config):
        ids = [c["id"] for c in user.get("/lookups/configurations").json()]
        assert config in ids

    def test_list_filter_by_source_type(self, user, config):
        r = user.get("/lookups/configurations", params={"source_type": "static_list"})
        assert r.status_code == 200, r.text
        for c in r.json():
            assert c["source_type"] == "static_list"

    def test_list_filter_unknown_source_type_returns_empty_or_list(self, user):
        r = user.get("/lookups/configurations", params={"source_type": "nonexistent_xyz"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_requires_auth(self, anon):
        assert anon.get("/lookups/configurations").status_code in UNAUTH


class TestLookupConfigGet:
    def test_get_by_id_returns_config(self, user, config):
        r = user.get(f"/lookups/configurations/{config}")
        assert r.status_code == 200, r.text
        assert r.json()["id"] == config

    def test_get_unknown_id_404(self, user):
        assert user.get(f"/lookups/configurations/{uuid.uuid4()}").status_code == 404

    def test_get_requires_auth(self, anon, config):
        assert anon.get(f"/lookups/configurations/{config}").status_code in UNAUTH


class TestLookupConfigUpdate:
    def test_update_label(self, user, config):
        r = user.put(f"/lookups/configurations/{config}", json={"label": "Updated Label"})
        assert r.status_code == 200, r.text
        assert r.json()["label"] == "Updated Label"

    def test_update_static_options(self, user, config):
        new_opts = [{"value": "z", "label": "Zeta"}]
        r = user.put(f"/lookups/configurations/{config}", json={"static_options": new_opts})
        assert r.status_code == 200, r.text
        assert r.json()["static_options"] == new_opts

    def test_update_unknown_id_404(self, user):
        r = user.put(f"/lookups/configurations/{uuid.uuid4()}", json={"label": "x"})
        assert r.status_code == 404, r.text

    def test_update_requires_auth(self, anon, config):
        assert anon.put(f"/lookups/configurations/{config}", json={"label": "x"}).status_code in UNAUTH


class TestLookupConfigDelete:
    def test_delete_returns_message(self, user, unique):
        r = user.post("/lookups/configurations", json=_cfg_body(unique))
        cid = r.json()["id"]
        dr = user.delete(f"/lookups/configurations/{cid}")
        assert dr.status_code == 200, dr.text
        assert "message" in dr.json()

    def test_deleted_config_not_in_list(self, user, unique):
        r = user.post("/lookups/configurations", json=_cfg_body(unique))
        cid = r.json()["id"]
        user.delete(f"/lookups/configurations/{cid}")
        ids = [c["id"] for c in user.get("/lookups/configurations").json()]
        assert cid not in ids

    def test_deleted_config_404_on_get(self, user, unique):
        r = user.post("/lookups/configurations", json=_cfg_body(unique))
        cid = r.json()["id"]
        user.delete(f"/lookups/configurations/{cid}")
        assert user.get(f"/lookups/configurations/{cid}").status_code == 404

    def test_delete_unknown_id_404(self, user):
        assert user.delete(f"/lookups/configurations/{uuid.uuid4()}").status_code == 404

    def test_delete_requires_auth(self, anon, config):
        assert anon.delete(f"/lookups/configurations/{config}").status_code in UNAUTH


# ─── lookup data ─────────────────────────────────────────────────────────────

class TestLookupData:
    def test_data_static_list_returns_items(self, user, config):
        r = user.get(f"/lookups/configurations/{config}/data")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "items" in body
        assert "total_count" in body
        assert body["total_count"] == 2
        labels = [i["label"] for i in body["items"]]
        assert "Alpha" in labels and "Beta" in labels

    def test_data_search_filters_items(self, user, config):
        r = user.get(f"/lookups/configurations/{config}/data", params={"search": "Alpha"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["total_count"] == 1
        assert body["items"][0]["label"] == "Alpha"

    def test_data_pagination(self, user, config):
        r = user.get(f"/lookups/configurations/{config}/data", params={"page": 1, "page_size": 1})
        assert r.status_code == 200, r.text
        body = r.json()
        assert len(body["items"]) == 1
        assert body["has_more"] is True

    def test_data_unknown_id_404(self, user):
        assert user.get(f"/lookups/configurations/{uuid.uuid4()}/data").status_code == 404

    def test_data_requires_auth(self, anon, config):
        assert anon.get(f"/lookups/configurations/{config}/data").status_code in UNAUTH


# ─── cascading rules ─────────────────────────────────────────────────────────

class TestCascadingRules:
    def _rule_body(self, unique, parent_id, child_id):
        return {
            "name": unique("rule"),
            "parent_lookup_id": parent_id,
            "child_lookup_id": child_id,
            "filter_type": "field_match",
            "parent_field": "value",
            "child_filter_field": "value",
        }

    def test_create_rule_returns_200_with_id(self, user, unique, config, config2):
        r = user.post("/lookups/cascading-rules", json=self._rule_body(unique, config, config2))
        assert r.status_code in OK, r.text
        data = r.json()
        assert "id" in data
        assert data["parent_lookup_id"] == config
        assert data["child_lookup_id"] == config2

    def test_create_rule_missing_name_422(self, user, config, config2):
        r = user.post("/lookups/cascading-rules", json={
            "parent_lookup_id": config,
            "child_lookup_id": config2,
        })
        assert r.status_code == 422

    def test_create_rule_missing_parent_422(self, user, unique, config2):
        r = user.post("/lookups/cascading-rules", json={
            "name": unique("rule"),
            "child_lookup_id": config2,
        })
        assert r.status_code == 422

    def test_list_rules_returns_array(self, user, unique, config, config2):
        r_create = user.post("/lookups/cascading-rules", json=self._rule_body(unique, config, config2))
        assert r_create.status_code in OK, r_create.text

        r = user.get("/lookups/cascading-rules")
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)
        rule_ids = [rule["id"] for rule in r.json()]
        assert r_create.json()["id"] in rule_ids

    def test_list_filter_by_parent(self, user, unique, config, config2):
        r_create = user.post("/lookups/cascading-rules", json=self._rule_body(unique, config, config2))
        assert r_create.status_code in OK

        r = user.get("/lookups/cascading-rules", params={"parent_lookup_id": config})
        assert r.status_code == 200, r.text
        for rule in r.json():
            assert rule["parent_lookup_id"] == config

    def test_list_filter_by_child(self, user, unique, config, config2):
        r_create = user.post("/lookups/cascading-rules", json=self._rule_body(unique, config, config2))
        assert r_create.status_code in OK

        r = user.get("/lookups/cascading-rules", params={"child_lookup_id": config2})
        assert r.status_code == 200, r.text
        for rule in r.json():
            assert rule["child_lookup_id"] == config2

    def test_create_rule_requires_auth(self, anon, unique, config, config2):
        assert anon.post(
            "/lookups/cascading-rules",
            json=self._rule_body(unique, config, config2)
        ).status_code in UNAUTH

    def test_list_rules_requires_auth(self, anon):
        assert anon.get("/lookups/cascading-rules").status_code in UNAUTH
