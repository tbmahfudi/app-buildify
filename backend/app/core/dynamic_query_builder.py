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
