"""
Step definitions for features/aggregate.feature

As a NoCode developer I want to run aggregate queries on my entity data
so that I can generate reports without writing SQL.
"""

import json
import pytest
from pytest_bdd import given, when, then, parsers, scenarios

scenarios("../features/aggregate.feature")

pytestmark = [pytest.mark.integration, pytest.mark.pg]


# ── Given ───────────────────────────────────────────────────────────────────

@given("the 5 standard seed records are loaded", target_fixture="entity")
def seed_fixture(sample_records):
    return sample_records["entity"]


@given("1 record is deleted", target_fixture="entity")
def entity_with_one_deleted(sample_records):
    entity = sample_records["entity"]
    record_id = sample_records["record_ids"][0]
    resp = entity["client"].delete(
        f"/api/v1/dynamic-data/{entity['entity_name']}/records/{record_id}",
        headers=entity["headers"],
    )
    assert resp.status_code == 204
    return entity


# ── When ────────────────────────────────────────────────────────────────────

def _agg_get(entity, params):
    return entity["client"].get(
        f"/api/v1/dynamic-data/{entity['entity_name']}/aggregate",
        params=params,
        headers=entity["headers"],
    )


@when("I aggregate COUNT(*) with no group-by", target_fixture="response")
def agg_count_all(entity):
    return _agg_get(entity, {
        "metrics": json.dumps([{"field": "*", "function": "count", "alias": "total_records"}])
    })


@when("I aggregate COUNT(id) grouped by status", target_fixture="response")
def agg_count_by_status(entity):
    return _agg_get(entity, {
        "group_by": "status",
        "metrics": json.dumps([{"field": "id", "function": "count", "alias": "count_id"}]),
    })


@when("I aggregate SUM(price) grouped by status", target_fixture="response")
def agg_sum_by_status(entity):
    return _agg_get(entity, {
        "group_by": "status",
        "metrics": json.dumps([{"field": "price", "function": "sum", "alias": "total_price"}]),
    })


@when(
    parsers.parse('I aggregate SUM(price) grouped by status filtered to status "{status}"'),
    target_fixture="response",
)
def agg_sum_filtered(entity, status):
    return _agg_get(entity, {
        "group_by": "status",
        "metrics": json.dumps([{"field": "price", "function": "sum", "alias": "total_price"}]),
        "filters": json.dumps({"operator": "AND", "conditions": [
            {"field": "status", "operator": "eq", "value": status}
        ]}),
    })


@when("I aggregate MIN(quantity) and MAX(quantity) with no group-by", target_fixture="response")
def agg_min_max(entity):
    return _agg_get(entity, {
        "metrics": json.dumps([
            {"field": "quantity", "function": "min", "alias": "min_qty"},
            {"field": "quantity", "function": "max", "alias": "max_qty"},
        ])
    })


@when("I aggregate COUNT DISTINCT on status", target_fixture="response")
def agg_count_distinct(entity):
    return _agg_get(entity, {
        "metrics": json.dumps([
            {"field": "status", "function": "count_distinct", "alias": "distinct_statuses"}
        ])
    })


@when("I aggregate SUM(price) and COUNT(id) grouped by status", target_fixture="response")
def agg_multi_metrics(entity):
    return _agg_get(entity, {
        "group_by": "status",
        "metrics": json.dumps([
            {"field": "price", "function": "sum", "alias": "total_price"},
            {"field": "id", "function": "count", "alias": "count_records"},
        ]),
    })


@when("I aggregate COUNT(id) grouped by created_at truncated to month", target_fixture="response")
def agg_date_trunc(entity):
    return _agg_get(entity, {
        "group_by": "created_at",
        "metrics": json.dumps([{"field": "id", "function": "count", "alias": "count_per_month"}]),
        "date_trunc": "month",
        "date_field": "created_at",
    })


@when(
    parsers.parse('I aggregate with an unsupported function "{function}" on field "{field}"'),
    target_fixture="response",
)
def agg_bad_function(entity, function, field):
    return _agg_get(entity, {
        "metrics": json.dumps([{"field": field, "function": function}])
    })


@when("I aggregate with an empty metrics list", target_fixture="response")
def agg_empty_metrics(entity):
    return _agg_get(entity, {
        "group_by": "status",
        "metrics": json.dumps([]),
    })


# ── Then ────────────────────────────────────────────────────────────────────

@then(parsers.parse("the response status is {code:d}"))
def check_status(response, code):
    assert response.status_code == code, (
        f"Expected {code}, got {response.status_code}: {response.text}"
    )


@then(parsers.parse("the result has {n:d} group"))
@then(parsers.parse("the result has {n:d} groups"))
def check_group_count(response, n):
    assert response.status_code == 200, response.text
    actual = response.json()["total_groups"]
    assert actual == n, f"Expected {n} groups, got {actual}. Groups: {response.json()['groups']}"


@then(parsers.parse('the group value "{key}" is {value:d}'))
def check_group_value_int(response, key, value):
    assert response.status_code == 200, response.text
    groups = response.json()["groups"]
    assert len(groups) >= 1
    actual = groups[0][key]
    assert actual == value, f"Expected {key}={value}, got {actual}"


@then(parsers.parse('the group value "{key}" is approximately {value:f}'))
def check_group_value_approx(response, key, value):
    assert response.status_code == 200, response.text
    groups = response.json()["groups"]
    assert len(groups) >= 1
    actual = float(groups[0][key])
    assert abs(actual - value) < 0.05, f"Expected {key}≈{value}, got {actual}"
