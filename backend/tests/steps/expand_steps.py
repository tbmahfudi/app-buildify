"""
Step definitions for features/expand.feature

As a NoCode developer I want to inline related records in responses
so that I can avoid extra round-trips in my frontend.
"""

import uuid
import pytest
from pytest_bdd import given, when, then, parsers, scenarios

scenarios("../features/expand.feature")

pytestmark = [pytest.mark.integration, pytest.mark.pg]


# ── Given ───────────────────────────────────────────────────────────────────

@given(
    "a category entity and a product entity with a category_id FK field",
    target_fixture="fk_setup",
)
def fk_setup_fixture(product_with_fk):
    return product_with_fk


@given(
    parsers.parse('a category "{label}" and a product linked to it'),
    target_fixture="linked_product",
)
def create_linked_product(fk_setup, label):
    client = fk_setup["client"]
    headers = fk_setup["headers"]
    cat_entity = fk_setup["category_entity"]

    cat_resp = client.post(
        f"/api/v1/dynamic-data/{cat_entity['entity_name']}/records",
        json={"data": {"label": label}},
        headers=headers,
    )
    assert cat_resp.status_code == 201
    cat_id = cat_resp.json()["id"]

    prod_resp = client.post(
        f"/api/v1/dynamic-data/{fk_setup['entity_name']}/records",
        json={"data": {"name": f"Product for {label}", "category_id": cat_id}},
        headers=headers,
    )
    assert prod_resp.status_code == 201

    return {"cat_id": cat_id, "prod_id": prod_resp.json()["id"]}


@given("a product with no category set", target_fixture="null_fk_product")
def create_null_fk_product(fk_setup):
    client = fk_setup["client"]
    headers = fk_setup["headers"]
    prod_resp = client.post(
        f"/api/v1/dynamic-data/{fk_setup['entity_name']}/records",
        json={"data": {"name": "No Category Product"}},
        headers=headers,
    )
    assert prod_resp.status_code == 201
    return prod_resp.json()["id"]


# ── When ────────────────────────────────────────────────────────────────────

@when(
    parsers.parse("I list products with expand={field}"),
    target_fixture="response",
)
def list_with_expand(fk_setup, field):
    client = fk_setup["client"]
    headers = fk_setup["headers"]
    return client.get(
        f"/api/v1/dynamic-data/{fk_setup['entity_name']}/records",
        params={"expand": field},
        headers=headers,
    )


@when(
    parsers.parse("I GET that product by ID with expand={field}"),
    target_fixture="response",
)
def get_product_by_id_with_expand(fk_setup, linked_product, field):
    client = fk_setup["client"]
    headers = fk_setup["headers"]
    return client.get(
        f"/api/v1/dynamic-data/{fk_setup['entity_name']}/records/{linked_product['prod_id']}",
        params={"expand": field},
        headers=headers,
    )


# ── Then ────────────────────────────────────────────────────────────────────

@then(parsers.parse("the response status is {code:d}"))
def check_status(response, code):
    assert response.status_code == code, (
        f"Expected {code}, got {response.status_code}: {response.text}"
    )


@then(parsers.parse('each product record has a "{key}" key'))
def check_inline_key_present(response, key):
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert len(items) > 0, "No items returned"
    for item in items:
        assert key in item, f"Expected '{key}' in item, got keys: {list(item.keys())}"


@then(parsers.parse('the inlined "{key}" has an "id" field'))
def check_inlined_has_id(response, key):
    items = response.json()["items"]
    for item in items:
        inlined = item.get(key)
        if inlined is not None:
            assert "id" in inlined, f"Inlined '{key}' missing 'id': {inlined}"


@then(parsers.parse('the product\'s "{key}" is null'))
def check_inlined_null(response, key):
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert len(items) > 0, "No items returned"
    assert items[0].get(key) is None, (
        f"Expected '{key}' to be null, got {items[0].get(key)!r}"
    )


@then(parsers.parse('the response data contains "{key}"'))
def check_response_data_key(response, key):
    assert response.status_code == 200, response.text
    body = response.json()
    data = body.get("data", body)
    assert key in data, f"Expected '{key}' in response data, got: {list(data.keys())}"


@then(parsers.parse('the "{key}" id matches the category id'))
def check_inlined_id(response, key, linked_product):
    body = response.json()
    data = body.get("data", body)
    assert data[key]["id"] == linked_product["cat_id"], (
        f"Expected id={linked_product['cat_id']}, got {data[key]['id']}"
    )
