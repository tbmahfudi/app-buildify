"""
Step definitions for features/query_builder.feature

As a backend developer I want DynamicQueryBuilder to translate filter/aggregate
dicts into correct SQL so that query logic is verified independently of the DB.
"""

import pytest
from sqlalchemy import Column, String, Numeric, Integer, create_engine
from sqlalchemy.orm import declarative_base, Session
from pytest_bdd import given, when, then, parsers, scenarios

from app.core.dynamic_query_builder import DynamicQueryBuilder

scenarios("../features/query_builder.feature")

pytestmark = pytest.mark.unit


# ── Test model (SQLite, no real DB needed) ───────────────────────────────────

_Base = declarative_base()


class _FakeProduct(_Base):
    __tablename__ = "fake_products_bdd"
    id       = Column(String, primary_key=True)
    name     = Column(String)
    status   = Column(String)
    price    = Column(Numeric(10, 2))
    quantity = Column(Integer)


@pytest.fixture(scope="module")
def qb():
    return DynamicQueryBuilder()


@pytest.fixture(scope="module")
def sqlite_session():
    engine = create_engine("sqlite:///:memory:")
    _Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


# ── Shared state ─────────────────────────────────────────────────────────────

@pytest.fixture
def clause_result():
    return {"clause": None, "error": None}


@pytest.fixture
def agg_result():
    return {"select_cols": None, "group_exprs": None, "output_keys": None, "error": None}


# ── When — filter clause ──────────────────────────────────────────────────────

@when(
    parsers.parse('I build a filter for field "{field}" with operator "{op}"'),
    target_fixture="clause_result",
)
def build_valid_filter(qb, field, op):
    value_map = {
        "eq": "active", "ne": "active", "gt": 5.0, "gte": 5.0,
        "lt": 100.0, "lte": 100.0, "contains": "Widget",
        "starts_with": "Widget", "ends_with": "A",
        "in": ["a", "b"], "not_in": ["x"],
        "is_null": None, "is_not_null": None,
        "like": "%Widget%", "ilike": "%widget%",
    }
    try:
        clause = qb._build_filter_clause(
            _FakeProduct, {"field": field, "operator": op, "value": value_map.get(op)}
        )
        return {"clause": clause, "error": None}
    except Exception as exc:
        return {"clause": None, "error": exc}


@when(
    parsers.parse('I build an AND compound filter for status "{status}" and price > {price:d}'),
    target_fixture="clause_result",
)
def build_and_filter(qb, status, price):
    clause = qb._build_filter_clause(_FakeProduct, {
        "operator": "AND",
        "conditions": [
            {"field": "status", "operator": "eq", "value": status},
            {"field": "price", "operator": "gt", "value": float(price)},
        ],
    })
    return {"clause": clause, "error": None}


@when(
    parsers.parse('I build an OR compound filter for status "{status}" and price < {price:d}'),
    target_fixture="clause_result",
)
def build_or_filter(qb, status, price):
    clause = qb._build_filter_clause(_FakeProduct, {
        "operator": "OR",
        "conditions": [
            {"field": "status", "operator": "eq", "value": status},
            {"field": "price", "operator": "lt", "value": float(price)},
        ],
    })
    return {"clause": clause, "error": None}


@when("I build a filter from an empty dict", target_fixture="clause_result")
def build_empty_filter(qb):
    clause = qb._build_filter_clause(_FakeProduct, {})
    return {"clause": clause, "error": None}


@when("I build an AND filter with an empty conditions list", target_fixture="clause_result")
def build_empty_conditions(qb):
    clause = qb._build_filter_clause(_FakeProduct, {"operator": "AND", "conditions": []})
    return {"clause": clause, "error": None}


@when("I build a filter with conditions but no operator key", target_fixture="clause_result")
def build_missing_operator(qb):
    try:
        clause = qb._build_filter_clause(_FakeProduct, {"conditions": [
            {"field": "status", "operator": "eq", "value": "x"}
        ]})
        return {"clause": clause, "error": None}
    except ValueError as exc:
        return {"clause": None, "error": exc}


@when(
    parsers.parse('I build a filter with unsupported operator "{op}"'),
    target_fixture="clause_result",
)
def build_unknown_operator(qb, op):
    try:
        clause = qb._build_filter_clause(
            _FakeProduct, {"field": "status", "operator": op, "value": ".*"}
        )
        return {"clause": clause, "error": None}
    except ValueError as exc:
        return {"clause": None, "error": exc}


@when(
    parsers.parse('I build a filter for field "{field}" with operator "eq"'),
    target_fixture="clause_result",
)
def build_filter_eq(qb, field):
    try:
        clause = qb._build_filter_clause(
            _FakeProduct, {"field": field, "operator": "eq", "value": "x"}
        )
        return {"clause": clause, "error": None}
    except ValueError as exc:
        return {"clause": None, "error": exc}


# ── When — aggregate select ───────────────────────────────────────────────────

@when(
    parsers.parse('I build an aggregate with function "{function}" on field "{field}" aliased "{alias}"'),
    target_fixture="agg_result",
)
def build_valid_aggregate(qb, function, field, alias):
    try:
        cols, grp, keys = qb.build_aggregate_select(
            _FakeProduct, group_by=None,
            metrics=[{"field": field, "function": function, "alias": alias}],
        )
        return {"select_cols": cols, "group_exprs": grp, "output_keys": keys, "error": None}
    except Exception as exc:
        return {"select_cols": None, "group_exprs": None, "output_keys": None, "error": exc}


@when("I build an aggregate with SUM(price) grouped by status", target_fixture="agg_result")
def build_agg_with_group(qb):
    cols, grp, keys = qb.build_aggregate_select(
        _FakeProduct, group_by=["status"],
        metrics=[{"field": "price", "function": "sum", "alias": "total_price"}],
    )
    return {"select_cols": cols, "group_exprs": grp, "output_keys": keys, "error": None}


@when(
    parsers.parse('I build an aggregate with function "sum" on field "price" with no alias'),
    target_fixture="agg_result",
)
def build_agg_auto_alias(qb):
    cols, grp, keys = qb.build_aggregate_select(
        _FakeProduct, group_by=None,
        metrics=[{"field": "price", "function": "sum"}],
    )
    return {"select_cols": cols, "group_exprs": grp, "output_keys": keys, "error": None}


@when(
    parsers.parse('I build an aggregate with function "{function}" on field "{field}"'),
    target_fixture="agg_result",
)
def build_agg_unknown(qb, function, field):
    try:
        cols, grp, keys = qb.build_aggregate_select(
            _FakeProduct, group_by=None,
            metrics=[{"field": field, "function": function}],
        )
        return {"select_cols": cols, "group_exprs": grp, "output_keys": keys, "error": None}
    except ValueError as exc:
        return {"select_cols": None, "group_exprs": None, "output_keys": None, "error": exc}


@when(
    parsers.parse('I build an aggregate with COUNT(*) grouped by "{field}"'),
    target_fixture="agg_result",
)
def build_agg_bad_group(qb, field):
    try:
        cols, grp, keys = qb.build_aggregate_select(
            _FakeProduct, group_by=[field],
            metrics=[{"field": "*", "function": "count"}],
        )
        return {"select_cols": cols, "group_exprs": grp, "output_keys": keys, "error": None}
    except ValueError as exc:
        return {"select_cols": None, "group_exprs": None, "output_keys": None, "error": exc}


# ── Then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse('the compiled SQL contains "{field}"'))
def check_sql_contains(clause_result, field):
    clause = clause_result["clause"]
    assert clause is not None, "Expected a clause, got None"
    sql = str(clause.compile(compile_kwargs={"literal_binds": True}))
    assert field in sql, f"Expected '{field}' in SQL: {sql}"


@then("the filter clause is None")
def check_clause_none(clause_result):
    assert clause_result["clause"] is None


@then("a ValueError is raised")
def check_value_error(clause_result, agg_result):
    err = clause_result.get("error") or agg_result.get("error")
    assert isinstance(err, ValueError), f"Expected ValueError, got: {err!r}"


@then(parsers.parse('the output keys contain "{key}"'))
def check_output_keys(agg_result, key):
    keys = agg_result["output_keys"]
    assert keys is not None, f"No output keys (error: {agg_result['error']})"
    assert key in keys, f"Expected '{key}' in {keys}"


@then(parsers.parse("the select column count is {n:d}"))
def check_select_count(agg_result, n):
    cols = agg_result["select_cols"]
    assert cols is not None
    assert len(cols) == n, f"Expected {n} columns, got {len(cols)}"
