"""
Step definitions for features/crud.feature

As a NoCode developer I want to create, read, update, and delete records
in a custom entity so that I can manage business data without writing code.
"""

import uuid
import pytest
from pytest_bdd import given, when, then, parsers, scenarios

scenarios("../features/crud.feature")

pytestmark = [pytest.mark.integration, pytest.mark.pg]


# ── shared state ────────────────────────────────────────────────────────────

@pytest.fixture
def ctx():
    """Mutable dict shared between steps within one scenario."""
    return {}


# ── Given ───────────────────────────────────────────────────────────────────

@given("a published entity with standard fields", target_fixture="entity")
def entity_fixture(published_entity):
    return published_entity


@given(parsers.parse('a record exists with name "{name}"'), target_fixture="existing_record_id")
def create_existing_record(published_entity, name):
    client = published_entity["client"]
    headers = published_entity["headers"]
    entity_name = published_entity["entity_name"]
    resp = client.post(
        f"/api/v1/dynamic-data/{entity_name}/records",
        json={"data": {"name": name}},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ── When ────────────────────────────────────────────────────────────────────

@when(
    parsers.parse('I create a record with name "{name}" price "{price}" status "{status}"'),
    target_fixture="response",
)
def create_all_fields(published_entity, name, price, status):
    client = published_entity["client"]
    headers = published_entity["headers"]
    entity_name = published_entity["entity_name"]
    return client.post(
        f"/api/v1/dynamic-data/{entity_name}/records",
        json={"data": {"name": name, "price": price, "status": status}},
        headers=headers,
    )


@when(
    parsers.parse('I create a record with name "{name}"'),
    target_fixture="response",
)
def create_min_fields(published_entity, name):
    client = published_entity["client"]
    headers = published_entity["headers"]
    entity_name = published_entity["entity_name"]
    return client.post(
        f"/api/v1/dynamic-data/{entity_name}/records",
        json={"data": {"name": name}},
        headers=headers,
    )


@when("I create a record with price \"5.00\" and no name", target_fixture="response")
def create_missing_required(published_entity):
    client = published_entity["client"]
    headers = published_entity["headers"]
    entity_name = published_entity["entity_name"]
    return client.post(
        f"/api/v1/dynamic-data/{entity_name}/records",
        json={"data": {"price": "5.00"}},
        headers=headers,
    )


@when(
    parsers.parse('I create a record with name "{name}" and an extra field "nonexistent"'),
    target_fixture="response",
)
def create_with_extra_field(published_entity, name):
    client = published_entity["client"]
    headers = published_entity["headers"]
    entity_name = published_entity["entity_name"]
    return client.post(
        f"/api/v1/dynamic-data/{entity_name}/records",
        json={"data": {"name": name, "nonexistent": "value"}},
        headers=headers,
    )


@when("I fetch that record by its ID", target_fixture="response")
def fetch_by_id(published_entity, existing_record_id):
    client = published_entity["client"]
    headers = published_entity["headers"]
    entity_name = published_entity["entity_name"]
    return client.get(
        f"/api/v1/dynamic-data/{entity_name}/records/{existing_record_id}",
        headers=headers,
    )


@when("I fetch a record with a random unknown ID", target_fixture="response")
def fetch_unknown_id(published_entity):
    client = published_entity["client"]
    headers = published_entity["headers"]
    entity_name = published_entity["entity_name"]
    return client.get(
        f"/api/v1/dynamic-data/{entity_name}/records/{uuid.uuid4()}",
        headers=headers,
    )


@when(
    parsers.parse('I update that record with name "{name}"'),
    target_fixture="response",
)
def update_record(published_entity, existing_record_id, name):
    client = published_entity["client"]
    headers = published_entity["headers"]
    entity_name = published_entity["entity_name"]
    return client.put(
        f"/api/v1/dynamic-data/{entity_name}/records/{existing_record_id}",
        json={"data": {"name": name}},
        headers=headers,
    )


@when("I delete that record", target_fixture="response")
def delete_record(published_entity, existing_record_id):
    client = published_entity["client"]
    headers = published_entity["headers"]
    entity_name = published_entity["entity_name"]
    return client.delete(
        f"/api/v1/dynamic-data/{entity_name}/records/{existing_record_id}",
        headers=headers,
    )


# ── Then ────────────────────────────────────────────────────────────────────

@then(parsers.parse("the response status is {code:d}"))
def check_status(response, code):
    assert response.status_code == code, (
        f"Expected {code}, got {response.status_code}: {response.text}"
    )


@then('the response body contains an "id" field')
def check_id_field(response):
    assert "id" in response.json(), f"Missing 'id' in response: {response.json()}"


@then(parsers.parse('the record data name is "{name}"'))
def check_record_name(response, name):
    body = response.json()
    data = body.get("data", body)
    assert data.get("name") == name, f"Expected name={name!r}, got: {data}"
