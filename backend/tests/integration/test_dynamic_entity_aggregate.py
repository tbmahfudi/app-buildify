"""
Integration tests — Dynamic Entity Aggregation
===============================================
Tests the GET /{entity}/aggregate endpoint.

HOW TO ADJUST SCENARIOS
------------------------
Edit the SCENARIOS lists below.  The seed data (SAMPLE_RECORDS in conftest.py)
contains 5 records:

  | name      | price | status   | quantity |
  |-----------|-------|----------|----------|
  | Widget A  | 1.99  | active   | 10       |
  | Widget B  | 5.99  | active   | 20       |
  | Widget C  | 9.99  | active   | 5        |
  | Gadget A  | 99.99 | inactive | 3        |
  | Gadget B  | None  | pending  | 0        |

Important fields:
  - "group_by":   list of field names (or None for grand total)
  - "metrics":    list of {field, function, alias?} dicts
  - "filters":    optional filter dict (same format as list_records)
  - "date_trunc": "hour" | "day" | "week" | "month" | "quarter" | "year"
  - "date_field": which group_by field to truncate
  - "expect_groups": number of rows in the aggregate result
  - "assert_group":  optional {group_key: value, metric_key: expected_value}
"""

import json
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.pg]


# ============================================================
# SCENARIOS — adjust these to modify test coverage
# ============================================================

AGGREGATE_SCENARIOS = [
    {
        "id": "count_all",
        "description": "Grand-total COUNT(*) with no group-by",
        "group_by": None,
        "metrics": [{"field": "*", "function": "count", "alias": "total_records"}],
        "expect_groups": 1,
        "assert_group": {"total_records": 5},
    },
    {
        "id": "count_by_status",
        "description": "COUNT per status group",
        "group_by": ["status"],
        "metrics": [{"field": "id", "function": "count", "alias": "count_id"}],
        "expect_groups": 3,  # active, inactive, pending
    },
    {
        "id": "sum_price_by_status",
        "description": "SUM of price grouped by status",
        "group_by": ["status"],
        "metrics": [{"field": "price", "function": "sum", "alias": "total_price"}],
        "expect_groups": 3,
        "assert_group": {
            "_check": "status",
            "_check_value": "active",
            "total_price": pytest.approx(17.97, rel=1e-2),  # 1.99 + 5.99 + 9.99
        },
    },
    {
        "id": "avg_price_by_status",
        "description": "AVG of price grouped by status",
        "group_by": ["status"],
        "metrics": [{"field": "price", "function": "avg", "alias": "avg_price"}],
        "expect_groups": 3,
    },
    {
        "id": "min_max_quantity",
        "description": "MIN and MAX quantity (no group-by)",
        "group_by": None,
        "metrics": [
            {"field": "quantity", "function": "min", "alias": "min_qty"},
            {"field": "quantity", "function": "max", "alias": "max_qty"},
        ],
        "expect_groups": 1,
        "assert_group": {"min_qty": 0, "max_qty": 20},
    },
    {
        "id": "count_distinct_status",
        "description": "COUNT DISTINCT on status values",
        "group_by": None,
        "metrics": [{"field": "status", "function": "count_distinct", "alias": "distinct_statuses"}],
        "expect_groups": 1,
        "assert_group": {"distinct_statuses": 3},
    },
    {
        "id": "multi_metrics",
        "description": "Multiple metrics in one query",
        "group_by": ["status"],
        "metrics": [
            {"field": "price", "function": "sum",   "alias": "total_price"},
            {"field": "id",    "function": "count",  "alias": "count_records"},
        ],
        "expect_groups": 3,
    },
    {
        "id": "filtered_aggregate",
        "description": "Aggregate only active records",
        "group_by": ["status"],
        "metrics": [{"field": "price", "function": "sum", "alias": "total_price"}],
        "filters": {"operator": "AND", "conditions": [
            {"field": "status", "operator": "eq", "value": "active"}
        ]},
        "expect_groups": 1,
        "assert_group": {
            "status": "active",
            "total_price": pytest.approx(17.97, rel=1e-2),
        },
    },
    {
        "id": "date_trunc_month",
        "description": "Group by month of created_at",
        "group_by": ["created_at"],
        "metrics": [{"field": "id", "function": "count", "alias": "count_per_month"}],
        "date_trunc": "month",
        "date_field": "created_at",
        # All 5 records created in the same test run → 1 group
        "expect_groups": 1,
    },
]

INVALID_AGGREGATE_SCENARIOS = [
    {
        "id": "unknown_metric_function",
        "description": "Unsupported metric function name returns 400 or 422",
        "group_by": ["status"],
        "metrics": [{"field": "price", "function": "median"}],  # not supported
        "expect_status": 400,
    },
    {
        "id": "missing_metrics",
        "description": "No metrics at all — should return 400 or 422",
        "group_by": ["status"],
        "metrics": [],
        "expect_status": 400,
    },
]


# ============================================================
# Tests
# ============================================================

def _build_params(scenario):
    params = {}
    if scenario.get("group_by") is not None:
        params["group_by"] = ",".join(scenario["group_by"])
    params["metrics"] = json.dumps(scenario["metrics"])
    if scenario.get("filters"):
        params["filters"] = json.dumps(scenario["filters"])
    if scenario.get("date_trunc"):
        params["date_trunc"] = scenario["date_trunc"]
        params["date_field"] = scenario.get("date_field", "created_at")
    return params


class TestAggregation:
    """Aggregation scenarios applied to the 5-record seed dataset."""

    @pytest.mark.parametrize(
        "scenario",
        AGGREGATE_SCENARIOS,
        ids=[s["id"] for s in AGGREGATE_SCENARIOS],
    )
    def test_aggregate(self, sample_records, scenario):
        entity = sample_records["entity"]
        client = entity["client"]
        headers = entity["headers"]
        entity_name = entity["entity_name"]

        resp = client.get(
            f"/api/v1/dynamic-data/{entity_name}/aggregate",
            params=_build_params(scenario),
            headers=headers,
        )

        assert resp.status_code == 200, (
            f"[{scenario['id']}] Expected 200, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()

        assert body["total_groups"] == scenario["expect_groups"], (
            f"[{scenario['id']}] {scenario['description']}\n"
            f"Expected {scenario['expect_groups']} groups, got {body['total_groups']}.\n"
            f"Groups returned: {body['groups']}"
        )

        # Optional: assert a specific group's metric value
        if "assert_group" in scenario:
            ag = scenario["assert_group"]
            check_field = ag.get("_check")

            if check_field:
                # Find the specific group by a field value
                check_value = ag["_check_value"]
                matched = [g for g in body["groups"] if g.get(check_field) == check_value]
                assert matched, (
                    f"[{scenario['id']}] No group with {check_field}={check_value!r}. "
                    f"Groups: {body['groups']}"
                )
                group = matched[0]
            else:
                assert len(body["groups"]) == 1, "assert_group without _check requires exactly 1 group"
                group = body["groups"][0]

            for key, expected in ag.items():
                if key.startswith("_"):
                    continue
                actual = group.get(key)
                assert actual == expected, (
                    f"[{scenario['id']}] Metric '{key}': expected {expected!r}, got {actual!r}\n"
                    f"Full group: {group}"
                )


class TestInvalidAggregation:
    """Malformed aggregation requests should return 4xx."""

    @pytest.mark.parametrize(
        "scenario",
        INVALID_AGGREGATE_SCENARIOS,
        ids=[s["id"] for s in INVALID_AGGREGATE_SCENARIOS],
    )
    def test_invalid(self, published_entity, scenario):
        client = published_entity["client"]
        headers = published_entity["headers"]
        entity_name = published_entity["entity_name"]

        resp = client.get(
            f"/api/v1/dynamic-data/{entity_name}/aggregate",
            params=_build_params(scenario),
            headers=headers,
        )
        assert resp.status_code == scenario["expect_status"], (
            f"[{scenario['id']}] Expected {scenario['expect_status']}, "
            f"got {resp.status_code}: {resp.text}"
        )


class TestAggregateExcludesSoftDeleted:
    """Soft-deleted records must not appear in aggregate results."""

    def test_deleted_record_excluded_from_count(self, sample_records):
        entity = sample_records["entity"]
        client = entity["client"]
        headers = entity["headers"]
        entity_name = entity["entity_name"]
        record_ids = sample_records["record_ids"]

        # Delete the first record (soft delete)
        del_resp = client.delete(
            f"/api/v1/dynamic-data/{entity_name}/records/{record_ids[0]}",
            headers=headers,
        )
        assert del_resp.status_code == 204

        # Grand-total count should now be 4
        resp = client.get(
            f"/api/v1/dynamic-data/{entity_name}/aggregate",
            params={"metrics": json.dumps([{"field": "*", "function": "count", "alias": "n"}])},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["groups"][0]["n"] == 4, (
            "Soft-deleted record should be excluded from aggregate COUNT(*)"
        )
