"""
Integration tests — Dynamic Entity Expand (inline related records)
===================================================================
Tests the ?expand= query parameter on GET /{entity}/records and
GET /{entity}/records/{id}.

HOW TO ADJUST SCENARIOS
------------------------
Edit EXPAND_SCENARIOS below.  Each scenario specifies:
  - "expand":             comma-separated field names to expand
  - "expect_inline_keys": list of keys that should appear on each record
  - "null_fk":            if True, the FK field is left NULL on the record
  - "expect_no_crash":    if True, skip key-assertion (just check no 500)
"""

import uuid
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.pg]


# ============================================================
# SCENARIOS — adjust these to modify test coverage
# ============================================================

EXPAND_SCENARIOS = [
    {
        "id": "expand_single_fk",
        "description": "Expand a single FK lookup field — related record inlined as {field}_data",
        "expand": "category_id",
        "null_fk": False,
        "expect_inline_keys": ["category_id_data"],
    },
    {
        "id": "expand_null_fk",
        "description": "When the FK value is NULL, {field}_data should be None (not a crash)",
        "expand": "category_id",
        "null_fk": True,
        "expect_inline_keys": ["category_id_data"],
        "expect_data_value": None,
    },
    {
        "id": "expand_unknown_field",
        "description": "Expanding a field that does not exist should not crash — just skip it",
        "expand": "not_a_real_field",
        "null_fk": False,
        "expect_no_crash": True,
    },
]


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="function")
def category_entity(pg_client, pg_session, pg_admin_headers):
    """
    Creates and publishes a simple 'category' entity used as the FK target.

    Yields the entity dict: {entity_id, entity_name, table_name}.
    """
    from tests.conftest import _create_entity_via_api, _drop_entity

    unique = uuid.uuid4().hex[:8]
    entity_name = f"test_category_{unique}"
    table_name = f"test_category_{unique}"

    entity_payload = {
        "name": entity_name,
        "label": "Test Category",
        "table_name": table_name,
        "data_scope": "tenant",
        "supports_soft_delete": False,
        "is_audited": False,
    }
    fields_payload = [
        {"name": "label", "label": "Label", "field_type": "string",
         "data_type": "VARCHAR", "is_required": True, "max_length": 100, "display_order": 1},
    ]
    entity_id, entity_name, table_name = _create_entity_via_api(
        pg_client, pg_admin_headers, entity_payload, fields_payload
    )
    yield {"entity_id": entity_id, "entity_name": entity_name, "table_name": table_name}
    _drop_entity(pg_session, entity_id, table_name)


@pytest.fixture(scope="function")
def product_with_fk(pg_client, pg_session, pg_admin_headers, category_entity):
    """
    Creates and publishes a 'product' entity with a category_id FK field
    pointing at category_entity.

    Yields the entity dict plus the category_entity dict.
    """
    from tests.conftest import _create_entity_via_api, _drop_entity

    unique = uuid.uuid4().hex[:8]
    entity_name = f"test_product_fk_{unique}"
    table_name = f"test_product_fk_{unique}"

    entity_payload = {
        "name": entity_name,
        "label": "Test Product FK",
        "table_name": table_name,
        "data_scope": "tenant",
        "supports_soft_delete": False,
        "is_audited": False,
    }
    fields_payload = [
        {"name": "name", "label": "Name", "field_type": "string",
         "data_type": "VARCHAR", "is_required": True, "max_length": 255, "display_order": 1},
        {
            "name": "category_id",
            "label": "Category",
            "field_type": "lookup",
            "data_type": "UUID",
            "is_required": False,
            "display_order": 2,
            "reference_entity_id": category_entity["entity_id"],
            "reference_field": "id",
            "display_field": "label",
            "relationship_type": "many-to-one",
        },
    ]
    entity_id, entity_name, table_name = _create_entity_via_api(
        pg_client, pg_admin_headers, entity_payload, fields_payload
    )
    yield {
        "entity_id": entity_id,
        "entity_name": entity_name,
        "table_name": table_name,
        "category_entity": category_entity,
        "client": pg_client,
        "headers": pg_admin_headers,
    }
    _drop_entity(pg_session, entity_id, table_name)


# ============================================================
# Tests
# ============================================================

class TestExpand:

    @pytest.mark.parametrize(
        "scenario",
        EXPAND_SCENARIOS,
        ids=[s["id"] for s in EXPAND_SCENARIOS],
    )
    def test_expand_list(self, product_with_fk, scenario):
        client = product_with_fk["client"]
        headers = product_with_fk["headers"]
        entity_name = product_with_fk["entity_name"]
        category_entity = product_with_fk["category_entity"]

        # Create a category record to use as FK target
        cat_resp = client.post(
            f"/api/v1/dynamic-data/{category_entity['entity_name']}/records",
            json={"data": {"label": "Electronics"}},
            headers=headers,
        )
        assert cat_resp.status_code == 201
        cat_id = cat_resp.json()["id"]

        # Create a product record
        fk_value = None if scenario.get("null_fk") else cat_id
        product_data = {"name": "Test Product"}
        if fk_value:
            product_data["category_id"] = fk_value

        prod_resp = client.post(
            f"/api/v1/dynamic-data/{entity_name}/records",
            json={"data": product_data},
            headers=headers,
        )
        assert prod_resp.status_code == 201

        # List with expand
        resp = client.get(
            f"/api/v1/dynamic-data/{entity_name}/records",
            params={"expand": scenario["expand"]},
            headers=headers,
        )
        assert resp.status_code == 200, (
            f"[{scenario['id']}] Expected 200, got {resp.status_code}: {resp.text}"
        )

        if scenario.get("expect_no_crash"):
            return  # just verifying no 500

        items = resp.json()["items"]
        assert len(items) > 0, f"[{scenario['id']}] No items returned"
        item = items[0]

        for key in scenario.get("expect_inline_keys", []):
            assert key in item, (
                f"[{scenario['id']}] Expected key '{key}' in item, got keys: {list(item.keys())}"
            )

        if "expect_data_value" in scenario:
            for key in scenario.get("expect_inline_keys", []):
                assert item[key] == scenario["expect_data_value"], (
                    f"[{scenario['id']}] Expected '{key}'={scenario['expect_data_value']!r}, "
                    f"got {item[key]!r}"
                )
        elif not scenario.get("null_fk") and scenario.get("expect_inline_keys"):
            # With a valid FK, the inlined record should have an 'id' field
            for key in scenario.get("expect_inline_keys", []):
                inlined = item.get(key)
                if inlined is not None:
                    assert "id" in inlined, (
                        f"[{scenario['id']}] Inlined record under '{key}' missing 'id'"
                    )

    def test_expand_single_record(self, product_with_fk):
        """GET /records/{id}?expand= also inlines related records."""
        client = product_with_fk["client"]
        headers = product_with_fk["headers"]
        entity_name = product_with_fk["entity_name"]
        category_entity = product_with_fk["category_entity"]

        # Create category
        cat_resp = client.post(
            f"/api/v1/dynamic-data/{category_entity['entity_name']}/records",
            json={"data": {"label": "Books"}},
            headers=headers,
        )
        assert cat_resp.status_code == 201
        cat_id = cat_resp.json()["id"]

        # Create product
        prod_resp = client.post(
            f"/api/v1/dynamic-data/{entity_name}/records",
            json={"data": {"name": "Python Book", "category_id": cat_id}},
            headers=headers,
        )
        assert prod_resp.status_code == 201
        record_id = prod_resp.json()["id"]

        # Fetch single record with expand
        resp = client.get(
            f"/api/v1/dynamic-data/{entity_name}/records/{record_id}",
            params={"expand": "category_id"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "category_id_data" in body["data"], (
            "Single-record expand must include category_id_data in the response data"
        )
        assert body["data"]["category_id_data"]["id"] == cat_id
