"""
Step definitions for features/soft_delete.feature

As a NoCode developer I want deleted records hidden from all read paths
so that data is consistent and recoverable.
"""

import json
import pytest
from pytest_bdd import given, when, then, parsers, scenarios
from sqlalchemy import text as sa_text

scenarios("../features/soft_delete.feature")

pytestmark = [pytest.mark.integration, pytest.mark.pg]


# ── Given ───────────────────────────────────────────────────────────────────

@given("a published entity with soft-delete enabled", target_fixture="sd_entity")
def sd_entity_fixture(published_entity):
    return published_entity


@given(
    parsers.parse('a record exists with name "{name}"'),
    target_fixture="sd_record_id",
)
def create_sd_record(sd_entity, name):
    resp = sd_entity["client"].post(
        f"/api/v1/dynamic-data/{sd_entity['entity_name']}/records",
        json={"data": {"name": name}},
        headers=sd_entity["headers"],
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ── When ────────────────────────────────────────────────────────────────────

@when("I delete that record", target_fixture="delete_response")
def soft_delete(sd_entity, sd_record_id):
    resp = sd_entity["client"].delete(
        f"/api/v1/dynamic-data/{sd_entity['entity_name']}/records/{sd_record_id}",
        headers=sd_entity["headers"],
    )
    assert resp.status_code == 204, f"First delete returned {resp.status_code}: {resp.text}"
    return resp


@when("I delete that record again", target_fixture="second_delete_response")
def soft_delete_again(sd_entity, sd_record_id):
    return sd_entity["client"].delete(
        f"/api/v1/dynamic-data/{sd_entity['entity_name']}/records/{sd_record_id}",
        headers=sd_entity["headers"],
    )


# ── Then ────────────────────────────────────────────────────────────────────

@then(parsers.parse("the response status is {code:d}"))
def check_status(delete_response, code):
    assert delete_response.status_code == code, (
        f"Expected {code}, got {delete_response.status_code}: {delete_response.text}"
    )


@then("listing records returns 0 results")
def list_returns_zero(sd_entity, delete_response):
    resp = sd_entity["client"].get(
        f"/api/v1/dynamic-data/{sd_entity['entity_name']}/records",
        headers=sd_entity["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0, f"Expected 0, got {resp.json()['total']}"


@then("fetching that record by ID returns 404")
def get_returns_404(sd_entity, sd_record_id, delete_response):
    resp = sd_entity["client"].get(
        f"/api/v1/dynamic-data/{sd_entity['entity_name']}/records/{sd_record_id}",
        headers=sd_entity["headers"],
    )
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"


@then("COUNT(*) aggregate returns 0")
def agg_count_zero(sd_entity, delete_response):
    resp = sd_entity["client"].get(
        f"/api/v1/dynamic-data/{sd_entity['entity_name']}/aggregate",
        params={"metrics": json.dumps([{"field": "*", "function": "count", "alias": "n"}])},
        headers=sd_entity["headers"],
    )
    assert resp.status_code == 200
    n = resp.json()["groups"][0]["n"]
    assert n == 0, f"Expected COUNT(*)=0 after delete, got {n}"


@then(parsers.parse('searching for "{term}" returns 0 results'))
def search_returns_zero(sd_entity, delete_response, term):
    resp = sd_entity["client"].get(
        f"/api/v1/dynamic-data/{sd_entity['entity_name']}/records",
        params={"search": term},
        headers=sd_entity["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0, (
        f"Expected 0 search results for '{term}', got {resp.json()['total']}"
    )


@then(parsers.parse("the second delete response status is {code:d}"))
def check_second_delete_status(second_delete_response, code):
    assert second_delete_response.status_code == code, (
        f"Expected {code} on double-delete, "
        f"got {second_delete_response.status_code}: {second_delete_response.text}"
    )


@then("the row still exists in the database with deleted_at populated")
def row_exists_with_deleted_at(sd_entity, sd_record_id, pg_session, delete_response):
    table_name = sd_entity["table_name"]
    row = pg_session.execute(
        sa_text(f'SELECT deleted_at FROM "{table_name}" WHERE id = :id'),
        {"id": sd_record_id},
    ).fetchone()
    assert row is not None, "Row should still exist physically after soft-delete"
    assert row[0] is not None, "deleted_at should be set after soft-delete"
