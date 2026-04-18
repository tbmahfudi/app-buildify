"""
Step definitions for features/filters.feature

As a NoCode developer I want to filter, sort, and paginate records
so that I can retrieve only data relevant to my use case.
"""

import json
import pytest
from pytest_bdd import given, when, then, parsers, scenarios

scenarios("../features/filters.feature")

pytestmark = [pytest.mark.integration, pytest.mark.pg]


# ── Given ───────────────────────────────────────────────────────────────────

@given("the 5 standard seed records are loaded", target_fixture="entity")
def seed_fixture(sample_records):
    return sample_records["entity"]


# ── When ────────────────────────────────────────────────────────────────────

@when(
    parsers.parse('I list records with filter field "{field}" operator "{op}" value "{value}"'),
    target_fixture="response",
)
def list_with_filter(entity, field, op, value):
    client = entity["client"]
    headers = entity["headers"]
    entity_name = entity["entity_name"]

    # Handle list values for "in" / "not_in"
    if op in ("in", "not_in"):
        filter_value = [value]
    elif op in ("is_null", "is_not_null"):
        filter_value = None
    else:
        # Try to coerce to float for numeric comparisons
        try:
            filter_value = float(value)
        except (ValueError, TypeError):
            filter_value = value

    return client.get(
        f"/api/v1/dynamic-data/{entity_name}/records",
        params={"filters": json.dumps({"operator": "AND", "conditions": [
            {"field": field, "operator": op, "value": filter_value}
        ]})},
        headers=headers,
    )


@when("I list records with status \"active\" AND price greater than 5.00", target_fixture="response")
def list_and_filter(entity):
    client = entity["client"]
    headers = entity["headers"]
    entity_name = entity["entity_name"]
    return client.get(
        f"/api/v1/dynamic-data/{entity_name}/records",
        params={"filters": json.dumps({
            "operator": "AND",
            "conditions": [
                {"field": "status", "operator": "eq", "value": "active"},
                {"field": "price", "operator": "gt", "value": 5.00},
            ],
        })},
        headers=headers,
    )


@when("I list records with status \"inactive\" OR price less than 2.00", target_fixture="response")
def list_or_filter(entity):
    client = entity["client"]
    headers = entity["headers"]
    entity_name = entity["entity_name"]
    return client.get(
        f"/api/v1/dynamic-data/{entity_name}/records",
        params={"filters": json.dumps({
            "operator": "OR",
            "conditions": [
                {"field": "status", "operator": "eq", "value": "inactive"},
                {"field": "price", "operator": "lt", "value": 2.00},
            ],
        })},
        headers=headers,
    )


@when("I list records with a filter that has no operator key", target_fixture="response")
def list_bad_filter(entity):
    client = entity["client"]
    headers = entity["headers"]
    entity_name = entity["entity_name"]
    return client.get(
        f"/api/v1/dynamic-data/{entity_name}/records",
        params={"filters": json.dumps({"conditions": [
            {"field": "status", "operator": "eq", "value": "active"}
        ]})},
        headers=headers,
    )


@when(
    parsers.parse('I list records sorted by "{field}" "{direction}"'),
    target_fixture="response",
)
def list_sorted(entity, field, direction):
    client = entity["client"]
    headers = entity["headers"]
    entity_name = entity["entity_name"]
    return client.get(
        f"/api/v1/dynamic-data/{entity_name}/records",
        params={"sort_by": field, "sort_order": direction},
        headers=headers,
    )


@when(
    parsers.parse("I list records with page {page:d} and page_size {size:d}"),
    target_fixture="response",
)
def list_paginated(entity, page, size):
    client = entity["client"]
    headers = entity["headers"]
    entity_name = entity["entity_name"]
    return client.get(
        f"/api/v1/dynamic-data/{entity_name}/records",
        params={"page": page, "page_size": size},
        headers=headers,
    )


@when(parsers.parse('I search records for "{term}"'), target_fixture="response")
def list_search(entity, term):
    client = entity["client"]
    headers = entity["headers"]
    entity_name = entity["entity_name"]
    return client.get(
        f"/api/v1/dynamic-data/{entity_name}/records",
        params={"search": term},
        headers=headers,
    )


# ── Then ────────────────────────────────────────────────────────────────────

@then(parsers.parse("the response status is {code:d}"))
def check_status(response, code):
    assert response.status_code == code, (
        f"Expected {code}, got {response.status_code}: {response.text}"
    )


@then(parsers.parse("the response total is {count:d}"))
def check_total(response, count):
    assert response.status_code == 200, response.text
    assert response.json()["total"] == count, (
        f"Expected total={count}, got {response.json()['total']}"
    )


@then(parsers.parse("the response total is at least {count:d}"))
def check_total_at_least(response, count):
    assert response.status_code == 200, response.text
    assert response.json()["total"] >= count, (
        f"Expected total >= {count}, got {response.json()['total']}"
    )


@then(parsers.parse('the first result price is "{expected}"'))
def check_first_price(response, expected):
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert len(items) > 0, "No items returned"
    actual = str(items[0].get("price", ""))
    assert actual == expected, f"Expected first price={expected!r}, got {actual!r}"


@then(parsers.parse("the response contains {items:d} items and total is {total:d}"))
def check_pagination(response, items, total):
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["items"]) == items, (
        f"Expected {items} items, got {len(body['items'])}"
    )
    assert body["total"] == total, f"Expected total={total}, got {body['total']}"
