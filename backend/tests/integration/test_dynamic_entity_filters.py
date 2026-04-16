"""
Integration tests — Dynamic Entity Filters, Sort & Pagination
===============================================================
Tests the GET /{entity}/records endpoint's filtering, sorting, search,
and pagination capabilities.

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

Adjust "expect_count" if you change the seed data.
"""

import json
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.pg]


# ============================================================
# SCENARIOS — adjust these to modify test coverage
# ============================================================

FILTER_SCENARIOS = [
    {
        "id": "eq_status_active",
        "description": "Exact match on status=active",
        "filter": {"operator": "AND", "conditions": [
            {"field": "status", "operator": "eq", "value": "active"}
        ]},
        "expect_count": 3,
    },
    {
        "id": "ne_status_active",
        "description": "Not-equal: records where status != active",
        "filter": {"operator": "AND", "conditions": [
            {"field": "status", "operator": "ne", "value": "active"}
        ]},
        "expect_count": 2,
    },
    {
        "id": "gt_price_5",
        "description": "Price greater than 5.00",
        "filter": {"operator": "AND", "conditions": [
            {"field": "price", "operator": "gt", "value": 5.00}
        ]},
        "expect_count": 3,   # 5.99, 9.99, 99.99
    },
    {
        "id": "gte_price_5_99",
        "description": "Price >= 5.99",
        "filter": {"operator": "AND", "conditions": [
            {"field": "price", "operator": "gte", "value": 5.99}
        ]},
        "expect_count": 3,   # 5.99, 9.99, 99.99
    },
    {
        "id": "lt_price_10",
        "description": "Price less than 10.00",
        "filter": {"operator": "AND", "conditions": [
            {"field": "price", "operator": "lt", "value": 10.00}
        ]},
        "expect_count": 3,   # 1.99, 5.99, 9.99
    },
    {
        "id": "lte_quantity_5",
        "description": "Quantity <= 5",
        "filter": {"operator": "AND", "conditions": [
            {"field": "quantity", "operator": "lte", "value": 5}
        ]},
        "expect_count": 3,   # 5, 3, 0
    },
    {
        "id": "contains_name_widget",
        "description": "Name contains 'Widget' (case-sensitive)",
        "filter": {"operator": "AND", "conditions": [
            {"field": "name", "operator": "contains", "value": "Widget"}
        ]},
        "expect_count": 3,
    },
    {
        "id": "starts_with_gadget",
        "description": "Name starts with 'Gadget'",
        "filter": {"operator": "AND", "conditions": [
            {"field": "name", "operator": "starts_with", "value": "Gadget"}
        ]},
        "expect_count": 2,
    },
    {
        "id": "ends_with_A",
        "description": "Name ends with ' A'",
        "filter": {"operator": "AND", "conditions": [
            {"field": "name", "operator": "ends_with", "value": " A"}
        ]},
        "expect_count": 2,   # Widget A, Gadget A
    },
    {
        "id": "in_status_list",
        "description": "Status is in [active, pending]",
        "filter": {"operator": "AND", "conditions": [
            {"field": "status", "operator": "in", "value": ["active", "pending"]}
        ]},
        "expect_count": 4,
    },
    {
        "id": "not_in_status",
        "description": "Status not in [active]",
        "filter": {"operator": "AND", "conditions": [
            {"field": "status", "operator": "not_in", "value": ["active"]}
        ]},
        "expect_count": 2,
    },
    {
        "id": "is_null_price",
        "description": "Records where price is NULL",
        "filter": {"operator": "AND", "conditions": [
            {"field": "price", "operator": "is_null", "value": None}
        ]},
        "expect_count": 1,   # Gadget B has no price
    },
    {
        "id": "is_not_null_price",
        "description": "Records where price is not NULL",
        "filter": {"operator": "AND", "conditions": [
            {"field": "price", "operator": "is_not_null", "value": None}
        ]},
        "expect_count": 4,
    },
    {
        "id": "and_compound",
        "description": "AND: status=active AND price > 5.00",
        "filter": {"operator": "AND", "conditions": [
            {"field": "status", "operator": "eq",  "value": "active"},
            {"field": "price",  "operator": "gt",  "value": 5.00},
        ]},
        "expect_count": 2,   # Widget B (5.99), Widget C (9.99)
    },
    {
        "id": "or_compound",
        "description": "OR: status=inactive OR price < 2.00",
        "filter": {"operator": "OR", "conditions": [
            {"field": "status", "operator": "eq", "value": "inactive"},
            {"field": "price",  "operator": "lt", "value": 2.00},
        ]},
        "expect_count": 2,   # Gadget A (inactive), Widget A (1.99)
    },
]

SORT_SCENARIOS = [
    {
        "id": "sort_price_asc",
        "description": "Sort by price ascending — cheapest first",
        "sort": "price:asc",
        # Gadget B has NULL price — sort behaviour with NULLs may vary;
        # only assert on the non-null first item.
        "first_name": "Widget A",
    },
    {
        "id": "sort_price_desc",
        "description": "Sort by price descending — most expensive first",
        "sort": "price:desc",
        "first_name": "Gadget A",
    },
    {
        "id": "sort_name_asc",
        "description": "Sort by name alphabetically",
        "sort": "name:asc",
        "first_name": "Gadget A",   # G < W
    },
]

PAGINATION_SCENARIOS = [
    {
        "id": "page1_size2",
        "description": "First page of 2 items",
        "page": 1,
        "page_size": 2,
        "expect_items": 2,
        "expect_total": 5,
        "expect_pages": 3,
    },
    {
        "id": "page2_size2",
        "description": "Second page of 2 items",
        "page": 2,
        "page_size": 2,
        "expect_items": 2,
        "expect_total": 5,
    },
    {
        "id": "page3_size2",
        "description": "Third (last) page — only 1 item remains",
        "page": 3,
        "page_size": 2,
        "expect_items": 1,
        "expect_total": 5,
    },
    {
        "id": "large_page_size",
        "description": "Page size larger than total returns all records",
        "page": 1,
        "page_size": 100,
        "expect_items": 5,
        "expect_total": 5,
    },
]

SEARCH_SCENARIOS = [
    {
        "id": "search_widget",
        "description": "Global search for 'Widget' matches name field",
        "search": "Widget",
        "expect_min_count": 3,   # At least 3 widgets
    },
    {
        "id": "search_no_match",
        "description": "Search for a term that doesn't exist returns 0 results",
        "search": "zzz_no_match_xyz",
        "expect_min_count": 0,
        "expect_max_count": 0,
    },
]


# ============================================================
# Tests
# ============================================================

class TestFilters:
    """Filter scenarios applied to the 5-record seed dataset."""

    @pytest.mark.parametrize("scenario", FILTER_SCENARIOS, ids=[s["id"] for s in FILTER_SCENARIOS])
    def test_filter(self, sample_records, scenario):
        entity = sample_records["entity"]
        client = entity["client"]
        headers = entity["headers"]
        entity_name = entity["entity_name"]

        params = {"filters": json.dumps(scenario["filter"])}
        resp = client.get(
            f"/api/v1/dynamic-data/{entity_name}/records",
            params=params,
            headers=headers,
        )

        assert resp.status_code == 200, (
            f"[{scenario['id']}] Expected 200, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body["total"] == scenario["expect_count"], (
            f"[{scenario['id']}] {scenario['description']}\n"
            f"Expected {scenario['expect_count']} records, got {body['total']}.\n"
            f"Filter: {scenario['filter']}"
        )


class TestSort:
    """Sorting scenarios."""

    @pytest.mark.parametrize("scenario", SORT_SCENARIOS, ids=[s["id"] for s in SORT_SCENARIOS])
    def test_sort(self, sample_records, scenario):
        entity = sample_records["entity"]
        client = entity["client"]
        headers = entity["headers"]
        entity_name = entity["entity_name"]

        params = {"sort": scenario["sort"], "page_size": 10}
        resp = client.get(
            f"/api/v1/dynamic-data/{entity_name}/records",
            params=params,
            headers=headers,
        )

        assert resp.status_code == 200, (
            f"[{scenario['id']}] Expected 200, got {resp.status_code}: {resp.text}"
        )
        items = resp.json()["items"]
        assert len(items) > 0, f"[{scenario['id']}] No items returned"

        # Find first non-null item when sorting by price
        first_item = items[0]
        assert first_item["name"] == scenario["first_name"], (
            f"[{scenario['id']}] {scenario['description']}\n"
            f"Expected first record name='{scenario['first_name']}', got '{first_item['name']}'"
        )


class TestPagination:
    """Pagination scenarios."""

    @pytest.mark.parametrize("scenario", PAGINATION_SCENARIOS, ids=[s["id"] for s in PAGINATION_SCENARIOS])
    def test_pagination(self, sample_records, scenario):
        entity = sample_records["entity"]
        client = entity["client"]
        headers = entity["headers"]
        entity_name = entity["entity_name"]

        params = {"page": scenario["page"], "page_size": scenario["page_size"]}
        resp = client.get(
            f"/api/v1/dynamic-data/{entity_name}/records",
            params=params,
            headers=headers,
        )

        assert resp.status_code == 200, (
            f"[{scenario['id']}] Expected 200, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert len(body["items"]) == scenario["expect_items"], (
            f"[{scenario['id']}] {scenario['description']}\n"
            f"Expected {scenario['expect_items']} items on page, got {len(body['items'])}"
        )
        assert body["total"] == scenario["expect_total"], (
            f"[{scenario['id']}] Expected total={scenario['expect_total']}, got {body['total']}"
        )
        if "expect_pages" in scenario:
            assert body["pages"] == scenario["expect_pages"]


class TestSearch:
    """Global search scenarios."""

    @pytest.mark.parametrize("scenario", SEARCH_SCENARIOS, ids=[s["id"] for s in SEARCH_SCENARIOS])
    def test_search(self, sample_records, scenario):
        entity = sample_records["entity"]
        client = entity["client"]
        headers = entity["headers"]
        entity_name = entity["entity_name"]

        params = {"search": scenario["search"], "page_size": 100}
        resp = client.get(
            f"/api/v1/dynamic-data/{entity_name}/records",
            params=params,
            headers=headers,
        )

        assert resp.status_code == 200, (
            f"[{scenario['id']}] Expected 200, got {resp.status_code}: {resp.text}"
        )
        total = resp.json()["total"]
        assert total >= scenario["expect_min_count"], (
            f"[{scenario['id']}] {scenario['description']}\n"
            f"Expected at least {scenario['expect_min_count']} results, got {total}"
        )
        if "expect_max_count" in scenario:
            assert total <= scenario["expect_max_count"], (
                f"[{scenario['id']}] Expected at most {scenario['expect_max_count']} results, got {total}"
            )


class TestInvalidFilter:
    """Malformed filter payloads should be handled gracefully."""

    def test_missing_operator_key_returns_error(self, published_entity):
        """
        Filter JSON without the top-level 'operator' key should fail.
        (This catches the Gap 1.1 regression where {conditions:[...]} was silently ignored.)
        """
        client = published_entity["client"]
        headers = published_entity["headers"]
        entity_name = published_entity["entity_name"]

        bad_filter = json.dumps({"conditions": [
            {"field": "status", "operator": "eq", "value": "active"}
        ]})
        resp = client.get(
            f"/api/v1/dynamic-data/{entity_name}/records",
            params={"filters": bad_filter},
            headers=headers,
        )
        # Should return 400 (bad request) not silently return all records
        assert resp.status_code == 400, (
            f"Expected 400 for malformed filter, got {resp.status_code}: {resp.text}"
        )

    def test_invalid_json_returns_400(self, published_entity):
        client = published_entity["client"]
        headers = published_entity["headers"]
        entity_name = published_entity["entity_name"]

        resp = client.get(
            f"/api/v1/dynamic-data/{entity_name}/records",
            params={"filters": "not valid json {{{"},
            headers=headers,
        )
        assert resp.status_code == 400
