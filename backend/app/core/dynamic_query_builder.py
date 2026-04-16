"""
Dynamic Query Builder - Builds SQLAlchemy queries with filters, sorting, and search

This module provides utilities to construct dynamic queries based on runtime criteria
for nocode entities.
"""

from typing import Type, List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Query
from sqlalchemy import and_, or_, not_, desc, asc, func
import logging

logger = logging.getLogger(__name__)


class DynamicQueryBuilder:
    """
    Builds SQLAlchemy queries dynamically based on filters, sorting, and search criteria

    Supports:
    - Complex filters with AND/OR operators
    - Multiple field sorting
    - Global text search across multiple fields
    - Pagination
    """

    # Operator mapping
    OPERATORS = {
        'eq': lambda field, value: field == value,
        'ne': lambda field, value: field != value,
        'gt': lambda field, value: field > value,
        'gte': lambda field, value: field >= value,
        'lt': lambda field, value: field < value,
        'lte': lambda field, value: field <= value,
        'contains': lambda field, value: field.contains(value),
        'starts_with': lambda field, value: field.startswith(value),
        'ends_with': lambda field, value: field.endswith(value),
        'in': lambda field, value: field.in_(value),
        'not_in': lambda field, value: field.notin_(value),
        'is_null': lambda field, value: field.is_(None),
        'is_not_null': lambda field, value: field.isnot(None),
        'like': lambda field, value: field.like(value),
        'ilike': lambda field, value: field.ilike(value),  # Case-insensitive LIKE
    }

    def apply_filters(
        self,
        query: Query,
        model: Type,
        filters: Dict[str, Any]
    ) -> Query:
        """
        Apply filters to query

        Filter format:
        {
            "operator": "AND",  # or "OR"
            "conditions": [
                {"field": "email", "operator": "contains", "value": "@example.com"},
                {"field": "created_at", "operator": "gte", "value": "2026-01-01"},
                {
                    "operator": "OR",
                    "conditions": [
                        {"field": "status", "operator": "eq", "value": "active"},
                        {"field": "status", "operator": "eq", "value": "pending"}
                    ]
                }
            ]
        }

        Args:
            query: SQLAlchemy Query object
            model: SQLAlchemy model class
            filters: Filter specification dict

        Returns:
            Modified Query object
        """
        if not filters:
            return query

        try:
            filter_clause = self._build_filter_clause(model, filters)
            if filter_clause is not None:
                query = query.filter(filter_clause)
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            raise ValueError(f"Invalid filter specification: {str(e)}")

        return query

    def _build_filter_clause(self, model: Type, filters: Dict[str, Any]):
        """
        Recursively build filter clause from filter specification

        Args:
            model: SQLAlchemy model class
            filters: Filter specification dict

        Returns:
            SQLAlchemy filter expression
        """
        # Check if this is a condition group (AND/OR)
        if 'operator' in filters and filters['operator'] in ('AND', 'OR'):
            conditions = filters.get('conditions', [])
            if not conditions:
                return None

            # Build clauses for each condition
            clauses = []
            for condition in conditions:
                clause = self._build_filter_clause(model, condition)
                if clause is not None:
                    clauses.append(clause)

            if not clauses:
                return None

            # Combine with AND or OR
            if filters['operator'] == 'AND':
                return and_(*clauses)
            else:
                return or_(*clauses)

        # This is a single condition
        if 'field' in filters and 'operator' in filters:
            field_name = filters['field']
            operator = filters['operator']
            value = filters.get('value')

            # Get field from model
            if not hasattr(model, field_name):
                raise ValueError(f"Field '{field_name}' not found in model")

            field = getattr(model, field_name)

            # Get operator function
            if operator not in self.OPERATORS:
                raise ValueError(f"Operator '{operator}' not supported")

            operator_func = self.OPERATORS[operator]

            # Apply operator
            # Special handling for is_null and is_not_null (they don't need value)
            if operator in ('is_null', 'is_not_null'):
                return operator_func(field, None)
            else:
                return operator_func(field, value)

        # Neither a condition group (operator + conditions) nor a single condition
        # (field + operator).  A non-empty dict that reaches here is malformed —
        # raise instead of silently dropping all filters.
        #
        # Common mistake: callers send {"conditions": [...]} without the required
        # top-level "operator" key ("AND" or "OR").  That causes this branch and
        # every filter to be silently ignored.
        if filters:
            keys = list(filters.keys())
            raise ValueError(
                f"Malformed filter object: expected either "
                f"{{'operator': 'AND'|'OR', 'conditions': [...]}} "
                f"or {{'field': '...', 'operator': '...', 'value': ...}}, "
                f"but received keys {keys}. "
                f"If you intended an AND group, add \"operator\": \"AND\" to the top-level dict."
            )
        return None

    def apply_sort(
        self,
        query: Query,
        model: Type,
        sort: List[Tuple[str, str]]
    ) -> Query:
        """
        Apply sorting to query

        Args:
            query: SQLAlchemy Query object
            model: SQLAlchemy model class
            sort: List of (field_name, direction) tuples
                  Example: [('name', 'asc'), ('created_at', 'desc')]

        Returns:
            Modified Query object
        """
        if not sort:
            return query

        for field_name, direction in sort:
            if not hasattr(model, field_name):
                logger.warning(f"Sort field '{field_name}' not found in model, skipping")
                continue

            field = getattr(model, field_name)

            if direction.lower() == 'desc':
                query = query.order_by(desc(field))
            else:
                query = query.order_by(asc(field))

        return query

    def apply_search(
        self,
        query: Query,
        model: Type,
        search_term: str,
        search_fields: Optional[List[str]] = None
    ) -> Query:
        """
        Apply global text search across specified fields

        Args:
            query: SQLAlchemy Query object
            model: SQLAlchemy model class
            search_term: Search term
            search_fields: List of field names to search (if None, searches all string fields)

        Returns:
            Modified Query object
        """
        if not search_term:
            return query

        # If no search fields specified, auto-detect string/text fields
        if not search_fields:
            search_fields = self._get_searchable_fields(model)

        if not search_fields:
            logger.warning("No searchable fields found for model")
            return query

        # Build OR conditions for each field
        search_conditions = []
        search_pattern = f"%{search_term}%"

        for field_name in search_fields:
            if not hasattr(model, field_name):
                continue

            field = getattr(model, field_name)

            # Use case-insensitive ILIKE for text search
            search_conditions.append(field.ilike(search_pattern))

        if search_conditions:
            query = query.filter(or_(*search_conditions))

        return query

    def _get_searchable_fields(self, model: Type) -> List[str]:
        """
        Get list of searchable (string/text) fields from model

        Args:
            model: SQLAlchemy model class

        Returns:
            List of field names
        """
        searchable_fields = []

        for column in model.__table__.columns:
            # Check if column is string type
            col_type = str(column.type).lower()
            if any(t in col_type for t in ['string', 'text', 'varchar', 'char']):
                searchable_fields.append(column.name)

        return searchable_fields

    def apply_pagination(
        self,
        query: Query,
        page: int = 1,
        page_size: int = 25
    ) -> Tuple[Query, int, int]:
        """
        Apply pagination to query

        Args:
            query: SQLAlchemy Query object
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (paginated_query, total_count, total_pages)
        """
        # Get total count before pagination
        total_count = query.count()

        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size

        # Apply pagination
        offset = (page - 1) * page_size
        paginated_query = query.offset(offset).limit(page_size)

        return paginated_query, total_count, total_pages

    def build_list_query(
        self,
        model: Type,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Tuple[str, str]]] = None,
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 25
    ) -> Tuple[Query, Dict[str, Any]]:
        """
        Build complete query with filters, sort, search, and pagination

        This is a convenience method that combines all query building steps.

        Args:
            model: SQLAlchemy model class
            filters: Filter specification
            sort: Sort specification
            search: Search term
            search_fields: Fields to search
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (query, metadata)
            metadata includes: {total, page, page_size, pages}
        """
        from sqlalchemy.orm import Session

        # This method needs a session - it will be called from service layer
        # For now, just build the filter/sort criteria
        raise NotImplementedError(
            "build_list_query requires a session. "
            "Use individual apply_* methods from service layer."
        )

    def parse_filter_string(self, filter_json: str) -> Dict[str, Any]:
        """
        Parse filter JSON string to dict

        Args:
            filter_json: JSON string with filter specification

        Returns:
            Filter dict

        Raises:
            ValueError: If JSON is invalid
        """
        import json

        try:
            return json.loads(filter_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid filter JSON: {str(e)}")

    # ------------------------------------------------------------------
    # Aggregation helpers
    # ------------------------------------------------------------------

    # Supported aggregation functions mapped to their SQLAlchemy equivalents.
    AGGREGATE_FUNCTIONS = {
        'count':          lambda col: func.count(col),
        'sum':            lambda col: func.sum(col),
        'avg':            lambda col: func.avg(col),
        'min':            lambda col: func.min(col),
        'max':            lambda col: func.max(col),
        'count_distinct': lambda col: func.count(col.distinct()),
    }

    def build_aggregate_select(
        self,
        model: Type,
        group_by: Optional[List[str]],
        metrics: List[dict],
        date_trunc: Optional[str] = None,
        date_field: Optional[str] = None
    ):
        """
        Build the SELECT column list and GROUP BY clause for an aggregate query.

        Args:
            model:      SQLAlchemy model class.
            group_by:   Field names to group by (may be None / empty).
            metrics:    List of dicts with keys 'field', 'function', and optional 'alias'.
            date_trunc: Truncation unit ('hour', 'day', 'week', 'month', 'quarter', 'year').
            date_field: Which group_by field to apply date_trunc to.

        Returns:
            Tuple of (select_columns, group_by_expressions, output_keys)
            - select_columns: list of SQLAlchemy column/label objects to pass to select()
            - group_by_expressions: list of expressions to pass to .group_by()
            - output_keys: list of string keys matching the select_columns order
        """
        select_columns = []
        group_by_expressions = []
        output_keys = []

        # ---- group-by columns ----
        for field_name in (group_by or []):
            if not hasattr(model, field_name):
                raise ValueError(f"Group-by field '{field_name}' not found in entity")

            col = getattr(model, field_name)

            if date_trunc and field_name == date_field:
                expr = func.date_trunc(date_trunc, col)
                select_columns.append(expr.label(field_name))
                group_by_expressions.append(expr)
            else:
                select_columns.append(col.label(field_name))
                group_by_expressions.append(col)

            output_keys.append(field_name)

        # ---- metric columns ----
        for m in metrics:
            field_name = m['field']
            fn_name = m['function']
            alias = m.get('alias') or f"{fn_name}_{field_name}"

            if fn_name not in self.AGGREGATE_FUNCTIONS:
                raise ValueError(
                    f"Unknown aggregation function '{fn_name}'. "
                    f"Supported: {', '.join(self.AGGREGATE_FUNCTIONS)}"
                )

            if field_name == '*':
                # COUNT(*) — field name is irrelevant
                agg_col = func.count().label(alias)
            else:
                if not hasattr(model, field_name):
                    raise ValueError(f"Metric field '{field_name}' not found in entity")
                agg_col = self.AGGREGATE_FUNCTIONS[fn_name](
                    getattr(model, field_name)
                ).label(alias)

            select_columns.append(agg_col)
            output_keys.append(alias)

        return select_columns, group_by_expressions, output_keys

    def parse_sort_string(self, sort_str: str) -> List[Tuple[str, str]]:
        """
        Parse sort string to list of tuples

        Format: "field1:asc,field2:desc,field3"

        Args:
            sort_str: Sort specification string

        Returns:
            List of (field_name, direction) tuples
        """
        if not sort_str:
            return []

        sort_list = []
        for item in sort_str.split(','):
            item = item.strip()
            if ':' in item:
                field, direction = item.split(':', 1)
                sort_list.append((field.strip(), direction.strip()))
            else:
                # Default to ascending
                sort_list.append((item, 'asc'))

        return sort_list
