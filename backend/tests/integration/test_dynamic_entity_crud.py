"""
Integration tests — Dynamic Entity CRUD
========================================
Tests the full create / read / update / delete lifecycle for dynamic entities.

All tests require a running PostgreSQL database.
Set the TEST_DATABASE_URL env var before running:

    TEST_DATABASE_URL=postgresql://testuser:testpass@localhost:5433/appbuildify_test \
        pytest tests/integration/test_dynamic_entity_crud.py -v

HOW TO ADJUST SCENARIOS
------------------------
Edit the SCENARIOS lists below.  Each entry is a plain dict; the test method
stays unchanged.  Common adjustments:
  - Change "data" values to test different field combinations.
  - Change "expect" to the HTTP status code you expect.
  - Add new dicts to cover additional edge cases.
"""

import json
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.pg]


# ============================================================
# SCENARIOS — adjust these to modify test coverage
# ============================================================

CREATE_SCENARIOS = [
    {
        "id": "all_fields",
        "description": "All fields provided",
        "data": {"name": "Widget A", "price": "9.99", "status": "active", "quantity": 5},
        "expect": 201,
    },
    {
        "id": "min_fields",
        "description": "Only required field (name)",
        "data": {"name": "Widget B"},
        "expect": 201,
    },
    {
        "id": "missing_required",
        "description": "Missing required 'name' field",
        "data": {"price": "5.00", "status": "active"},
        "expect": 400,
    },
    {
        "id": "extra_unknown_key",
        "description": "Extra unknown keys are stripped, not rejected",
        "data": {"name": "Widget C", "nonexistent_field": "ignored"},
        "expect": 201,
    },
]

UPDATE_SCENARIOS = [
    {
        "id": "update_name",
        "description": "Update the name field",
        "initial": {"name": "Original Name"},
        "patch": {"name": "Updated Name"},
        "expect": 200,
        "assert_value": ("name", "Updated Name"),
    },
    {
        "id": "update_price",
        "description": "Set price on a record that had none",
        "initial": {"name": "No Price"},
        "patch": {"price": "42.50"},
        "expect": 200,
        "assert_value": ("price", 42.5),
    },
]

GET_SCENARIOS = [
    {
        "id": "get_existing",
        "description": "Retrieve a record that exists",
        "data": {"name": "Findable Widget"},
        "expect": 200,
    },
    {
        "id": "get_nonexistent",
        "description": "Retrieve a record with an unknown ID returns 404",
        "record_id": "00000000-0000-0000-0000-000000000000",
        "expect": 404,
    },
]

VIRTUAL_ENTITY_WRITE_SCENARIOS = [
    {
        "id": "post_to_virtual_is_405",
        "description": "POST to a virtual (view-backed) entity returns 405",
        "method": "POST",
        "expect": 405,
    },
    {
        "id": "put_to_virtual_is_405",
        "description": "PUT to a virtual (view-backed) entity returns 405",
        "method": "PUT",
        "expect": 405,
    },
    {
        "id": "delete_to_virtual_is_405",
        "description": "DELETE to a virtual (view-backed) entity returns 405",
        "method": "DELETE",
        "expect": 405,
    },
]


# ============================================================
# Tests
# ============================================================

class TestCreateRecord:
    """POST /{entity}/records"""

    @pytest.mark.parametrize("scenario", CREATE_SCENARIOS, ids=[s["id"] for s in CREATE_SCENARIOS])
    def test_create(self, published_entity, scenario):
        client = published_entity["client"]
        headers = published_entity["headers"]
        entity_name = published_entity["entity_name"]

        resp = client.post(
            f"/api/v1/dynamic-data/{entity_name}/records",
            json={"data": scenario["data"]},
            headers=headers,
        )

        assert resp.status_code == scenario["expect"], (
            f"[{scenario['id']}] {scenario['description']}\n"
            f"Expected HTTP {scenario['expect']}, got {resp.status_code}: {resp.text}"
        )

        if scenario["expect"] == 201:
            body = resp.json()
            assert "id" in body, "Response must include an 'id' field"
            assert "data" in body, "Response must include a 'data' field"
            # Name should round-trip
            if "name" in scenario["data"]:
                assert body["data"]["name"] == scenario["data"]["name"]


class TestGetRecord:
    """GET /{entity}/records/{id}"""

    @pytest.mark.parametrize("scenario", GET_SCENARIOS, ids=[s["id"] for s in GET_SCENARIOS])
    def test_get(self, published_entity, scenario):
        client = published_entity["client"]
        headers = published_entity["headers"]
        entity_name = published_entity["entity_name"]

        record_id = scenario.get("record_id")

        if record_id is None:
            # Create the record first
            create_resp = client.post(
                f"/api/v1/dynamic-data/{entity_name}/records",
                json={"data": scenario["data"]},
                headers=headers,
            )
            assert create_resp.status_code == 201
            record_id = create_resp.json()["id"]

        resp = client.get(
            f"/api/v1/dynamic-data/{entity_name}/records/{record_id}",
            headers=headers,
        )

        assert resp.status_code == scenario["expect"], (
            f"[{scenario['id']}] Expected HTTP {scenario['expect']}, got {resp.status_code}: {resp.text}"
        )

        if scenario["expect"] == 200:
            body = resp.json()
            assert body["id"] == record_id


class TestUpdateRecord:
    """PUT /{entity}/records/{id}"""

    @pytest.mark.parametrize("scenario", UPDATE_SCENARIOS, ids=[s["id"] for s in UPDATE_SCENARIOS])
    def test_update(self, published_entity, scenario):
        client = published_entity["client"]
        headers = published_entity["headers"]
        entity_name = published_entity["entity_name"]

        # Create initial record
        create_resp = client.post(
            f"/api/v1/dynamic-data/{entity_name}/records",
            json={"data": scenario["initial"]},
            headers=headers,
        )
        assert create_resp.status_code == 201
        record_id = create_resp.json()["id"]

        # Update it
        resp = client.put(
            f"/api/v1/dynamic-data/{entity_name}/records/{record_id}",
            json={"data": scenario["patch"]},
            headers=headers,
        )

        assert resp.status_code == scenario["expect"], (
            f"[{scenario['id']}] Expected HTTP {scenario['expect']}, got {resp.status_code}: {resp.text}"
        )

        if "assert_value" in scenario and scenario["expect"] == 200:
            field, expected = scenario["assert_value"]
            assert resp.json()["data"][field] == expected, (
                f"[{scenario['id']}] Field '{field}' expected {expected!r}, "
                f"got {resp.json()['data'].get(field)!r}"
            )


class TestDeleteRecord:
    """DELETE /{entity}/records/{id}"""

    def test_delete_returns_no_content(self, published_entity):
        client = published_entity["client"]
        headers = published_entity["headers"]
        entity_name = published_entity["entity_name"]

        # Create then delete
        create_resp = client.post(
            f"/api/v1/dynamic-data/{entity_name}/records",
            json={"data": {"name": "To Be Deleted"}},
            headers=headers,
        )
        assert create_resp.status_code == 201
        record_id = create_resp.json()["id"]

        resp = client.delete(
            f"/api/v1/dynamic-data/{entity_name}/records/{record_id}",
            headers=headers,
        )
        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}: {resp.text}"

    def test_delete_nonexistent_returns_404(self, published_entity):
        client = published_entity["client"]
        headers = published_entity["headers"]
        entity_name = published_entity["entity_name"]

        resp = client.delete(
            f"/api/v1/dynamic-data/{entity_name}/records/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"


class TestListRecords:
    """GET /{entity}/records"""

    def test_list_empty_entity(self, published_entity):
        client = published_entity["client"]
        headers = published_entity["headers"]
        entity_name = published_entity["entity_name"]

        resp = client.get(f"/api/v1/dynamic-data/{entity_name}/records", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_list_returns_created_records(self, sample_records):
        entity = sample_records["entity"]
        client = entity["client"]
        headers = entity["headers"]
        entity_name = entity["entity_name"]

        resp = client.get(f"/api/v1/dynamic-data/{entity_name}/records", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == len(sample_records["records"])
        assert len(body["items"]) == len(sample_records["records"])

    def test_list_unauthenticated_returns_403(self, published_entity):
        client = published_entity["client"]
        entity_name = published_entity["entity_name"]

        resp = client.get(f"/api/v1/dynamic-data/{entity_name}/records")
        assert resp.status_code in (401, 403)


class TestVirtualEntityWriteBlock:
    """Virtual (view-backed) entities must reject write operations with 405."""

    @pytest.mark.parametrize(
        "scenario",
        VIRTUAL_ENTITY_WRITE_SCENARIOS,
        ids=[s["id"] for s in VIRTUAL_ENTITY_WRITE_SCENARIOS],
    )
    def test_virtual_entity_write_rejected(self, pg_client, pg_session, pg_admin_headers, pg_engine, scenario):
        """
        Creates a real PostgreSQL view, registers it as a virtual entity,
        then verifies that write operations return 405.
        """
        import uuid as _uuid
        from sqlalchemy import text as sa_text

        unique = _uuid.uuid4().hex[:8]
        view_name = f"v_test_virtual_{unique}"
        entity_name = f"test_virtual_{unique}"

        # Create a real view in PostgreSQL
        pg_session.execute(sa_text(
            f"CREATE OR REPLACE VIEW {view_name} AS SELECT 1::integer AS id, 'hello'::text AS label"
        ))
        pg_session.commit()

        try:
            # Register as virtual entity (no publish/DDL needed)
            entity_payload = {
                "name": entity_name,
                "label": "Test Virtual",
                "table_name": view_name,
                "entity_type": "virtual",
                "data_scope": "tenant",
                "is_audited": False,
                "supports_soft_delete": False,
            }
            resp = pg_client.post(
                "/api/v1/data-model/entities",
                json=entity_payload,
                headers=pg_admin_headers,
            )
            assert resp.status_code == 201, f"Entity create failed: {resp.text}"
            entity_id = resp.json()["id"]

            # Manually mark as published so the dynamic-data router can find it
            pg_session.execute(
                sa_text("UPDATE entity_definitions SET status='published' WHERE id=:id"),
                {"id": entity_id},
            )
            pg_session.commit()

            # Exercise the scenario
            method = scenario["method"].lower()
            url = f"/api/v1/dynamic-data/{entity_name}/records"
            if method == "put":
                url += "/00000000-0000-0000-0000-000000000000"
            elif method == "delete":
                url += "/00000000-0000-0000-0000-000000000000"

            call = getattr(pg_client, method)
            kwargs = {"headers": pg_admin_headers}
            if method in ("post", "put"):
                kwargs["json"] = {"data": {"label": "x"}}

            resp = call(url, **kwargs)
            assert resp.status_code == scenario["expect"], (
                f"[{scenario['id']}] Expected {scenario['expect']}, got {resp.status_code}: {resp.text}"
            )
        finally:
            # Cleanup
            try:
                pg_session.execute(sa_text(
                    "DELETE FROM entity_definitions WHERE name = :name",
                    {"name": entity_name},
                ))
                pg_session.execute(sa_text(f"DROP VIEW IF EXISTS {view_name}"))
                pg_session.commit()
            except Exception:
                pg_session.rollback()
