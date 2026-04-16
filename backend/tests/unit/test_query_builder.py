"""
Unit tests — DynamicQueryBuilder
==================================
Pure Python tests that run without any database connection.
A minimal SQLAlchemy declarative model is used as the test subject.

HOW TO ADJUST SCENARIOS
------------------------
Edit the FILTER_SCENARIOS and AGGREGATE_SCENARIOS lists below.  These are
plain dicts; the test logic stays unchanged.  Common adjustments:
  - Add a new filter operator to FILTER_SCENARIOS.
  - Add or change a metric function in AGGREGATE_SCENARIOS.
  - Edit MALFORMED_FILTER_SCENARIOS to add edge cases.
"""

import pytest
from sqlalchemy import Column, String, Numeric, Integer, create_engine
from sqlalchemy.orm import declarative_base, Session

from app.core.dynamic_query_builder import DynamicQueryBuilder

pytestmark = pytest.mark.unit


# ============================================================
# Minimal test model (no DB required — introspection only)
# ============================================================

Base = declarative_base()


class _FakeProduct(Base):
    """Minimal model used to exercise DynamicQueryBuilder."""
    __tablename__ = "fake_products"

    id       = Column(String, primary_key=True)
    name     = Column(String)
    status   = Column(String)
    price    = Column(Numeric(10, 2))
    quantity = Column(Integer)


@pytest.fixture(scope="module")
def builder():
    return DynamicQueryBuilder()


@pytest.fixture(scope="module")
def sqlite_session():
    """In-memory SQLite session for query execution tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


# ============================================================
# SCENARIOS
# ============================================================

FILTER_SCENARIOS = [
    # Single-condition filters
    {"id": "eq",          "filter": {"field": "status", "operator": "eq",          "value": "active"},     "expect_sql_fragment": "status"},
    {"id": "ne",          "filter": {"field": "status", "operator": "ne",          "value": "active"},     "expect_sql_fragment": "status"},
    {"id": "gt",          "filter": {"field": "price",  "operator": "gt",          "value": 5.00},         "expect_sql_fragment": "price"},
    {"id": "gte",         "filter": {"field": "price",  "operator": "gte",         "value": 5.00},         "expect_sql_fragment": "price"},
    {"id": "lt",          "filter": {"field": "price",  "operator": "lt",          "value": 100.0},        "expect_sql_fragment": "price"},
    {"id": "lte",         "filter": {"field": "price",  "operator": "lte",         "value": 100.0},        "expect_sql_fragment": "price"},
    {"id": "contains",    "filter": {"field": "name",   "operator": "contains",    "value": "Widget"},     "expect_sql_fragment": "name"},
    {"id": "starts_with", "filter": {"field": "name",   "operator": "starts_with", "value": "Widget"},     "expect_sql_fragment": "name"},
    {"id": "ends_with",   "filter": {"field": "name",   "operator": "ends_with",   "value": "A"},          "expect_sql_fragment": "name"},
    {"id": "in",          "filter": {"field": "status", "operator": "in",          "value": ["a", "b"]},   "expect_sql_fragment": "status"},
    {"id": "not_in",      "filter": {"field": "status", "operator": "not_in",      "value": ["x"]},        "expect_sql_fragment": "status"},
    {"id": "is_null",     "filter": {"field": "price",  "operator": "is_null",     "value": None},         "expect_sql_fragment": "price"},
    {"id": "is_not_null", "filter": {"field": "price",  "operator": "is_not_null", "value": None},         "expect_sql_fragment": "price"},
    {"id": "like",        "filter": {"field": "name",   "operator": "like",        "value": "%Widget%"},   "expect_sql_fragment": "name"},
    {"id": "ilike",       "filter": {"field": "name",   "operator": "ilike",       "value": "%widget%"},   "expect_sql_fragment": "name"},
    # Compound filters
    {
        "id": "and_compound",
        "filter": {"operator": "AND", "conditions": [
            {"field": "status", "operator": "eq", "value": "active"},
            {"field": "price",  "operator": "gt", "value": 5.00},
        ]},
        "expect_sql_fragment": "status",
    },
    {
        "id": "or_compound",
        "filter": {"operator": "OR", "conditions": [
            {"field": "status", "operator": "eq", "value": "inactive"},
            {"field": "price",  "operator": "lt", "value": 2.00},
        ]},
        "expect_sql_fragment": "status",
    },
]

MALFORMED_FILTER_SCENARIOS = [
    {
        "id": "missing_operator_key",
        "description": "Top-level dict with 'conditions' but no 'operator' — Gap 1.1 guard",
        "filter": {"conditions": [
            {"field": "status", "operator": "eq", "value": "active"}
        ]},
        "expect_error": ValueError,
    },
    {
        "id": "unknown_operator",
        "description": "Unsupported single-condition operator",
        "filter": {"field": "status", "operator": "regex", "value": ".*"},
        "expect_error": ValueError,
    },
    {
        "id": "unknown_field",
        "description": "Field not present on the model",
        "filter": {"field": "nonexistent_field", "operator": "eq", "value": "x"},
        "expect_error": ValueError,
    },
]

AGGREGATE_SCENARIOS = [
    {
        "id": "count_star",
        "description": "COUNT(*) with no group-by",
        "group_by": None,
        "metrics": [{"field": "*", "function": "count", "alias": "total"}],
        "expect_output_keys": ["total"],
        "expect_select_count": 1,
    },
    {
        "id": "sum_by_field",
        "description": "SUM grouped by status",
        "group_by": ["status"],
        "metrics": [{"field": "price", "function": "sum", "alias": "total_price"}],
        "expect_output_keys": ["status", "total_price"],
        "expect_select_count": 2,
    },
    {
        "id": "multi_metrics",
        "description": "Multiple metrics in one aggregate",
        "group_by": ["status"],
        "metrics": [
            {"field": "price",    "function": "sum",   "alias": "total"},
            {"field": "quantity", "function": "avg",   "alias": "avg_qty"},
            {"field": "id",       "function": "count", "alias": "n"},
        ],
        "expect_output_keys": ["status", "total", "avg_qty", "n"],
        "expect_select_count": 4,
    },
    {
        "id": "count_distinct",
        "description": "COUNT DISTINCT",
        "group_by": None,
        "metrics": [{"field": "status", "function": "count_distinct", "alias": "distinct_statuses"}],
        "expect_output_keys": ["distinct_statuses"],
        "expect_select_count": 1,
    },
    {
        "id": "auto_alias",
        "description": "When alias is omitted, auto-alias is '{function}_{field}'",
        "group_by": None,
        "metrics": [{"field": "price", "function": "sum"}],
        "expect_output_keys": ["sum_price"],
        "expect_select_count": 1,
    },
]

INVALID_AGGREGATE_SCENARIOS = [
    {
        "id": "unknown_function",
        "description": "Unsupported aggregation function raises ValueError",
        "group_by": None,
        "metrics": [{"field": "price", "function": "median"}],
        "expect_error": ValueError,
    },
    {
        "id": "unknown_group_by_field",
        "description": "Group-by on a field that doesn't exist raises ValueError",
        "group_by": ["nonexistent"],
        "metrics": [{"field": "*", "function": "count"}],
        "expect_error": ValueError,
    },
    {
        "id": "unknown_metric_field",
        "description": "Metric on a field that doesn't exist raises ValueError",
        "group_by": None,
        "metrics": [{"field": "ghost_field", "function": "sum"}],
        "expect_error": ValueError,
    },
]


# ============================================================
# Tests
# ============================================================

class TestFilterClauseBuilding:
    """_build_filter_clause produces SQLAlchemy expressions without DB access."""

    @pytest.mark.parametrize("scenario", FILTER_SCENARIOS, ids=[s["id"] for s in FILTER_SCENARIOS])
    def test_valid_filter(self, builder, scenario):
        clause = builder._build_filter_clause(_FakeProduct, scenario["filter"])
        assert clause is not None, (
            f"[{scenario['id']}] Expected a non-None clause for filter: {scenario['filter']}"
        )
        # Compile to string to verify the correct field appears in SQL
        sql_str = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert scenario["expect_sql_fragment"] in sql_str, (
            f"[{scenario['id']}] Expected '{scenario['expect_sql_fragment']}' in SQL: {sql_str}"
        )

    @pytest.mark.parametrize(
        "scenario",
        MALFORMED_FILTER_SCENARIOS,
        ids=[s["id"] for s in MALFORMED_FILTER_SCENARIOS],
    )
    def test_malformed_filter_raises(self, builder, scenario):
        with pytest.raises(scenario["expect_error"]):
            builder._build_filter_clause(_FakeProduct, scenario["filter"])

    def test_empty_filter_returns_none(self, builder):
        assert builder._build_filter_clause(_FakeProduct, {}) is None

    def test_empty_conditions_list_returns_none(self, builder):
        result = builder._build_filter_clause(
            _FakeProduct, {"operator": "AND", "conditions": []}
        )
        assert result is None

    def test_apply_filters_raises_on_bad_filter(self, builder, sqlite_session):
        """apply_filters() wraps _build_filter_clause errors as ValueError."""
        from sqlalchemy.orm import Query

        query = sqlite_session.query(_FakeProduct)
        bad_filter = {"conditions": [{"field": "status", "operator": "eq", "value": "x"}]}

        with pytest.raises(ValueError, match="Invalid filter"):
            builder.apply_filters(query, _FakeProduct, bad_filter)


class TestAggregateSelectBuilding:
    """build_aggregate_select generates correct SELECT / GROUP BY structures."""

    @pytest.mark.parametrize(
        "scenario",
        AGGREGATE_SCENARIOS,
        ids=[s["id"] for s in AGGREGATE_SCENARIOS],
    )
    def test_valid_aggregate(self, builder, scenario):
        select_cols, group_exprs, output_keys = builder.build_aggregate_select(
            _FakeProduct,
            group_by=scenario["group_by"],
            metrics=scenario["metrics"],
        )

        assert output_keys == scenario["expect_output_keys"], (
            f"[{scenario['id']}] Expected output_keys={scenario['expect_output_keys']}, "
            f"got {output_keys}"
        )
        assert len(select_cols) == scenario["expect_select_count"], (
            f"[{scenario['id']}] Expected {scenario['expect_select_count']} SELECT columns, "
            f"got {len(select_cols)}"
        )

        # When group_by is provided, group_exprs should match
        if scenario["group_by"]:
            assert len(group_exprs) == len(scenario["group_by"])
        else:
            assert group_exprs == []

    @pytest.mark.parametrize(
        "scenario",
        INVALID_AGGREGATE_SCENARIOS,
        ids=[s["id"] for s in INVALID_AGGREGATE_SCENARIOS],
    )
    def test_invalid_aggregate_raises(self, builder, scenario):
        with pytest.raises(scenario["expect_error"]):
            builder.build_aggregate_select(
                _FakeProduct,
                group_by=scenario.get("group_by"),
                metrics=scenario["metrics"],
            )


class TestSortBuilding:
    """apply_sort produces correct ORDER BY clauses."""

    def test_asc_sort(self, builder, sqlite_session):
        from sqlalchemy.orm import Query

        query = sqlite_session.query(_FakeProduct)
        sorted_q = builder.apply_sort(query, _FakeProduct, [("name", "asc")])
        sql = str(sorted_q.statement.compile(compile_kwargs={"literal_binds": True}))
        assert "name" in sql.lower()

    def test_desc_sort(self, builder, sqlite_session):
        from sqlalchemy.orm import Query

        query = sqlite_session.query(_FakeProduct)
        sorted_q = builder.apply_sort(query, _FakeProduct, [("price", "desc")])
        sql = str(sorted_q.statement.compile(compile_kwargs={"literal_binds": True}))
        assert "price" in sql.lower()
        assert "desc" in sql.lower()

    def test_unknown_sort_field_is_skipped(self, builder, sqlite_session):
        """Sorting on a non-existent field should be silently skipped, not crash."""
        query = sqlite_session.query(_FakeProduct)
        # Should not raise
        result_q = builder.apply_sort(query, _FakeProduct, [("nonexistent_field", "asc")])
        assert result_q is not None


class TestPagination:
    """apply_pagination applies correct LIMIT/OFFSET."""

    def test_first_page(self, builder, sqlite_session):
        query = sqlite_session.query(_FakeProduct)
        paged_q, total, pages = builder.apply_pagination(query, page=1, page_size=10)
        sql = str(paged_q.statement.compile(compile_kwargs={"literal_binds": True}))
        assert "LIMIT" in sql.upper()

    def test_page_count_calculation(self, builder, sqlite_session):
        """Pages = ceil(total / page_size)."""
        # We can't test total without rows, but we can test the math:
        query = sqlite_session.query(_FakeProduct)
        # With 0 rows, total=0, pages should be 0
        _, total, pages = builder.apply_pagination(query, page=1, page_size=3)
        assert total == 0
        assert pages == 0
