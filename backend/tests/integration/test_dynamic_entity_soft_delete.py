"""
Integration tests — Dynamic Entity Soft-Delete Lifecycle
=========================================================
Tests that soft-deleted records:
  - Disappear from list results
  - Return 404 on GET by ID
  - Are excluded from aggregate counts
  - Trigger 404 on double-delete
  - Disappear from search results

HOW TO ADJUST SCENARIOS
------------------------
Edit SOFT_DELETE_SCENARIOS below.  Each scenario names what to check
after a record is deleted.  Change "expect_*" values if your implementation
differs (e.g., hard-delete instead of soft-delete changes 204 to 204 but
double-delete may vary).
"""

import json
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.pg]


# ============================================================
# SCENARIOS — adjust these to modify test coverage
# ============================================================

SOFT_DELETE_SCENARIOS = [
    {
        "id": "hidden_from_list",
        "description": "After delete, record no longer appears in list",
        "check": "list",
        "expect_total": 0,
    },
    {
        "id": "get_returns_404",
        "description": "After delete, GET by ID returns 404",
        "check": "get",
        "expect_status": 404,
    },
    {
        "id": "excluded_from_aggregate",
        "description": "After delete, aggregate COUNT is decremented by 1",
        "check": "aggregate",
        "expect_count": 0,   # we create 1 record and delete it
    },
    {
        "id": "search_excludes_deleted",
        "description": "After delete, global search returns no match",
        "check": "search",
        "search_term": "UniqueSoftDeleteTarget",
        "expect_total": 0,
    },
    {
        "id": "double_delete_returns_404",
        "description": "Deleting an already-deleted record returns 404",
        "check": "double_delete",
        "expect_status": 404,
    },
]


# ============================================================
# Tests
# ============================================================

class TestSoftDeleteLifecycle:

    def _create_single_record(self, published_entity, name="Soft Delete Target"):
        client = published_entity["client"]
        headers = published_entity["headers"]
        entity_name = published_entity["entity_name"]

        resp = client.post(
            f"/api/v1/dynamic-data/{entity_name}/records",
            json={"data": {"name": name, "status": "active"}},
            headers=headers,
        )
        assert resp.status_code == 201, f"Seed failed: {resp.text}"
        return resp.json()["id"]

    def _delete_record(self, published_entity, record_id):
        client = published_entity["client"]
        headers = published_entity["headers"]
        entity_name = published_entity["entity_name"]

        resp = client.delete(
            f"/api/v1/dynamic-data/{entity_name}/records/{record_id}",
            headers=headers,
        )
        assert resp.status_code == 204, f"Delete returned {resp.status_code}: {resp.text}"

    @pytest.mark.parametrize(
        "scenario",
        SOFT_DELETE_SCENARIOS,
        ids=[s["id"] for s in SOFT_DELETE_SCENARIOS],
    )
    def test_soft_delete(self, published_entity, scenario):
        client = published_entity["client"]
        headers = published_entity["headers"]
        entity_name = published_entity["entity_name"]

        name = scenario.get("search_term", "Soft Delete Target")
        record_id = self._create_single_record(published_entity, name=name)
        self._delete_record(published_entity, record_id)

        check = scenario["check"]

        if check == "list":
            resp = client.get(
                f"/api/v1/dynamic-data/{entity_name}/records",
                headers=headers,
            )
            assert resp.status_code == 200
            assert resp.json()["total"] == scenario["expect_total"], (
                f"[{scenario['id']}] {scenario['description']}\n"
                f"Expected total={scenario['expect_total']}, got {resp.json()['total']}"
            )

        elif check == "get":
            resp = client.get(
                f"/api/v1/dynamic-data/{entity_name}/records/{record_id}",
                headers=headers,
            )
            assert resp.status_code == scenario["expect_status"], (
                f"[{scenario['id']}] Expected {scenario['expect_status']}, "
                f"got {resp.status_code}: {resp.text}"
            )

        elif check == "aggregate":
            resp = client.get(
                f"/api/v1/dynamic-data/{entity_name}/aggregate",
                params={"metrics": json.dumps([
                    {"field": "*", "function": "count", "alias": "n"}
                ])},
                headers=headers,
            )
            assert resp.status_code == 200
            n = resp.json()["groups"][0]["n"]
            assert n == scenario["expect_count"], (
                f"[{scenario['id']}] Expected COUNT(*)={scenario['expect_count']}, got {n}"
            )

        elif check == "search":
            resp = client.get(
                f"/api/v1/dynamic-data/{entity_name}/records",
                params={"search": scenario["search_term"]},
                headers=headers,
            )
            assert resp.status_code == 200
            assert resp.json()["total"] == scenario["expect_total"], (
                f"[{scenario['id']}] Search for '{scenario['search_term']}' after delete "
                f"should return {scenario['expect_total']} results, got {resp.json()['total']}"
            )

        elif check == "double_delete":
            resp = client.delete(
                f"/api/v1/dynamic-data/{entity_name}/records/{record_id}",
                headers=headers,
            )
            assert resp.status_code == scenario["expect_status"], (
                f"[{scenario['id']}] Expected {scenario['expect_status']} on double-delete, "
                f"got {resp.status_code}: {resp.text}"
            )


class TestSoftDeleteVsHardDelete:
    """
    Verifies that entities with supports_soft_delete=True use soft-delete
    (deleted_at set, row still in DB) rather than hard-delete (row removed).
    """

    def test_soft_deleted_row_still_in_db(self, published_entity, pg_session):
        """
        The physical row should remain in the database after soft-delete;
        only deleted_at gets set.
        """
        from sqlalchemy import text as sa_text

        client = published_entity["client"]
        headers = published_entity["headers"]
        entity_name = published_entity["entity_name"]
        table_name = published_entity["table_name"]

        # Create
        resp = client.post(
            f"/api/v1/dynamic-data/{entity_name}/records",
            json={"data": {"name": "Physical Row Check"}},
            headers=headers,
        )
        assert resp.status_code == 201
        record_id = resp.json()["id"]

        # Soft-delete via API
        del_resp = client.delete(
            f"/api/v1/dynamic-data/{entity_name}/records/{record_id}",
            headers=headers,
        )
        assert del_resp.status_code == 204

        # Raw SQL: confirm row still exists with deleted_at populated
        row = pg_session.execute(
            sa_text(f'SELECT deleted_at FROM "{table_name}" WHERE id = :id'),
            {"id": record_id},
        ).fetchone()

        assert row is not None, "Row should still exist physically after soft-delete"
        assert row[0] is not None, "deleted_at should be set after soft-delete"
