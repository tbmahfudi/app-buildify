"""
Report service for business logic.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import json

from app.models.report import (
    ReportDefinition,
    ReportExecution,
    ReportSchedule,
    ReportCache,
    ExportFormat
)
from app.schemas.report import (
    ReportDefinitionCreate,
    ReportDefinitionUpdate,
    ReportExecutionRequest,
    LookupDataRequest,
    FilterGroup
)


class ReportService:
    """Service for report operations."""

    @staticmethod
    def create_report_definition(
        db: Session,
        tenant_id: int,
        user_id: int,
        report_data: ReportDefinitionCreate
    ) -> ReportDefinition:
        """Create a new report definition."""
        # Convert Pydantic models to dict for JSON columns
        report_dict = report_data.model_dump()

        # Extract JSON fields
        json_fields = ['query_config', 'columns_config', 'parameters',
                      'visualization_config', 'formatting_rules',
                      'allowed_roles', 'allowed_users']

        for field in json_fields:
            if field in report_dict and report_dict[field] is not None:
                if isinstance(report_dict[field], list):
                    report_dict[field] = [
                        item.model_dump() if hasattr(item, 'model_dump') else item
                        for item in report_dict[field]
                    ]
                elif hasattr(report_dict[field], 'model_dump'):
                    report_dict[field] = report_dict[field].model_dump()

        db_report = ReportDefinition(
            tenant_id=tenant_id,
            created_by=user_id,
            **report_dict
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        return db_report

    @staticmethod
    def get_report_definition(
        db: Session,
        tenant_id: int,
        report_id: int,
        user_id: Optional[int] = None
    ) -> Optional[ReportDefinition]:
        """Get a report definition by ID."""
        query = db.query(ReportDefinition).filter(
            ReportDefinition.id == report_id,
            ReportDefinition.tenant_id == tenant_id,
            ReportDefinition.is_active == True
        )

        report = query.first()

        # Check permissions
        if report and not report.is_public and user_id:
            if report.allowed_users and user_id not in report.allowed_users:
                # TODO: Check role permissions
                return None

        return report

    @staticmethod
    def list_report_definitions(
        db: Session,
        tenant_id: int,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReportDefinition]:
        """List report definitions."""
        query = db.query(ReportDefinition).filter(
            ReportDefinition.tenant_id == tenant_id,
            ReportDefinition.is_active == True
        )

        if category:
            query = query.filter(ReportDefinition.category == category)

        # Filter by permissions (show public or user's accessible reports)
        if user_id:
            query = query.filter(
                or_(
                    ReportDefinition.is_public == True,
                    ReportDefinition.created_by == user_id,
                    ReportDefinition.allowed_users.contains([user_id])
                )
            )

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_report_definition(
        db: Session,
        tenant_id: int,
        report_id: int,
        report_data: ReportDefinitionUpdate
    ) -> Optional[ReportDefinition]:
        """Update a report definition."""
        db_report = db.query(ReportDefinition).filter(
            ReportDefinition.id == report_id,
            ReportDefinition.tenant_id == tenant_id
        ).first()

        if not db_report:
            return None

        update_data = report_data.model_dump(exclude_unset=True)

        # Convert Pydantic models to dict for JSON columns
        json_fields = ['query_config', 'columns_config', 'parameters',
                      'visualization_config', 'formatting_rules',
                      'allowed_roles', 'allowed_users']

        for field in json_fields:
            if field in update_data and update_data[field] is not None:
                if isinstance(update_data[field], list):
                    update_data[field] = [
                        item.model_dump() if hasattr(item, 'model_dump') else item
                        for item in update_data[field]
                    ]
                elif hasattr(update_data[field], 'model_dump'):
                    update_data[field] = update_data[field].model_dump()

        for field, value in update_data.items():
            setattr(db_report, field, value)

        db_report.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_report)
        return db_report

    @staticmethod
    def delete_report_definition(
        db: Session,
        tenant_id: int,
        report_id: int
    ) -> bool:
        """Soft delete a report definition."""
        db_report = db.query(ReportDefinition).filter(
            ReportDefinition.id == report_id,
            ReportDefinition.tenant_id == tenant_id
        ).first()

        if not db_report:
            return False

        db_report.is_active = False
        db.commit()
        return True

    @staticmethod
    def execute_report(
        db: Session,
        tenant_id: int,
        user_id: int,
        request: ReportExecutionRequest
    ) -> ReportExecution:
        """Execute a report and return results."""
        start_time = datetime.utcnow()

        # Get report definition
        report_def = ReportService.get_report_definition(
            db, tenant_id, request.report_definition_id, user_id
        )

        if not report_def:
            raise ValueError("Report definition not found or access denied")

        # Create execution record
        execution = ReportExecution(
            tenant_id=tenant_id,
            report_definition_id=request.report_definition_id,
            executed_by=user_id,
            parameters_used=request.parameters,
            export_format=request.export_format,
            status="running"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        try:
            # Check cache if requested
            cached_data = None
            if request.use_cache:
                cached_data = ReportService._get_cached_data(
                    db, tenant_id, request.report_definition_id, request.parameters
                )

            if cached_data:
                # Use cached data
                execution.status = "completed"
                execution.row_count = cached_data.get('row_count', 0)
                execution.execution_time_ms = 0
            else:
                # Build and execute query
                query_result = ReportService._build_and_execute_query(
                    db, tenant_id, report_def, request.parameters
                )

                execution.status = "completed"
                execution.row_count = len(query_result.get('data', []))

                # Cache the results
                if request.use_cache:
                    ReportService._cache_results(
                        db, tenant_id, request.report_definition_id,
                        request.parameters, query_result
                    )

            # Calculate execution time
            end_time = datetime.utcnow()
            execution.execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)

        db.commit()
        db.refresh(execution)
        return execution

    @staticmethod
    def _build_and_execute_query(
        db: Session,
        tenant_id: int,
        report_def: ReportDefinition,
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build and execute the report query."""
        # This is a simplified version - in production, you'd want a more robust query builder
        base_entity = report_def.base_entity
        columns_config = report_def.columns_config or []
        query_config = report_def.query_config or {}

        # Build SELECT clause
        select_fields = []
        for col in columns_config:
            col_name = col.get('name')
            col_label = col.get('label', col_name)
            aggregation = col.get('aggregation', 'none')

            if aggregation and aggregation != 'none':
                select_fields.append(f"{aggregation.upper()}({col_name}) as {col_label}")
            else:
                select_fields.append(f"{col_name} as {col_label}")

        if not select_fields:
            select_fields = ['*']

        # Build FROM clause
        from_clause = f"{base_entity}"

        # Build WHERE clause
        where_conditions = [f"tenant_id = {tenant_id}"]

        # Add filter conditions from query config
        if query_config.get('filters'):
            filter_sql = ReportService._build_filter_sql(
                query_config['filters'], parameters
            )
            if filter_sql:
                where_conditions.append(filter_sql)

        # Build GROUP BY clause
        group_by_clause = ""
        if query_config.get('group_by'):
            group_by_fields = query_config['group_by']
            group_by_clause = f"GROUP BY {', '.join(group_by_fields)}"

        # Build ORDER BY clause
        order_by_clause = ""
        if query_config.get('order_by'):
            order_by_parts = []
            for order in query_config['order_by']:
                field = order.get('field')
                direction = order.get('direction', 'ASC')
                order_by_parts.append(f"{field} {direction}")
            order_by_clause = f"ORDER BY {', '.join(order_by_parts)}"

        # Build LIMIT clause
        limit_clause = ""
        if query_config.get('limit'):
            limit_clause = f"LIMIT {query_config['limit']}"

        # Construct full query
        sql = f"""
            SELECT {', '.join(select_fields)}
            FROM {from_clause}
            WHERE {' AND '.join(where_conditions)}
            {group_by_clause}
            {order_by_clause}
            {limit_clause}
        """

        # Execute query
        result = db.execute(text(sql))
        rows = result.fetchall()

        # Convert to list of dicts
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in rows]

        return {
            'data': data,
            'row_count': len(data),
            'columns': list(columns)
        }

    @staticmethod
    def _build_filter_sql(
        filter_group: Dict[str, Any],
        parameters: Optional[Dict[str, Any]]
    ) -> str:
        """Build SQL WHERE clause from filter group."""
        conditions = []

        for condition in filter_group.get('conditions', []):
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value')
            param_name = condition.get('parameter')

            # Use parameter value if specified
            if param_name and parameters:
                value = parameters.get(param_name, value)

            # Build condition based on operator
            if operator == 'eq':
                conditions.append(f"{field} = '{value}'")
            elif operator == 'ne':
                conditions.append(f"{field} != '{value}'")
            elif operator == 'gt':
                conditions.append(f"{field} > '{value}'")
            elif operator == 'lt':
                conditions.append(f"{field} < '{value}'")
            elif operator == 'gte':
                conditions.append(f"{field} >= '{value}'")
            elif operator == 'lte':
                conditions.append(f"{field} <= '{value}'")
            elif operator == 'like':
                conditions.append(f"{field} LIKE '%{value}%'")
            elif operator == 'in':
                if isinstance(value, list):
                    values_str = ', '.join([f"'{v}'" for v in value])
                    conditions.append(f"{field} IN ({values_str})")

        # Handle nested groups recursively
        for nested_group in filter_group.get('groups', []):
            nested_sql = ReportService._build_filter_sql(nested_group, parameters)
            if nested_sql:
                conditions.append(f"({nested_sql})")

        logic = filter_group.get('logic', 'AND')
        return f" {logic} ".join(conditions)

    @staticmethod
    def _get_cached_data(
        db: Session,
        tenant_id: int,
        report_id: int,
        parameters: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get cached report data if available and not expired."""
        cache_key = ReportService._generate_cache_key(report_id, parameters)

        cache_entry = db.query(ReportCache).filter(
            ReportCache.tenant_id == tenant_id,
            ReportCache.report_definition_id == report_id,
            ReportCache.cache_key == cache_key,
            ReportCache.expires_at > datetime.utcnow()
        ).first()

        if cache_entry:
            cache_entry.hit_count += 1
            db.commit()
            return cache_entry.cached_data

        return None

    @staticmethod
    def _cache_results(
        db: Session,
        tenant_id: int,
        report_id: int,
        parameters: Optional[Dict[str, Any]],
        data: Dict[str, Any],
        ttl_minutes: int = 60
    ):
        """Cache report results."""
        cache_key = ReportService._generate_cache_key(report_id, parameters)
        params_hash = hashlib.sha256(
            json.dumps(parameters or {}, sort_keys=True).encode()
        ).hexdigest()

        # Check if cache entry exists
        cache_entry = db.query(ReportCache).filter(
            ReportCache.cache_key == cache_key
        ).first()

        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)

        if cache_entry:
            # Update existing cache
            cache_entry.cached_data = data
            cache_entry.row_count = data.get('row_count', 0)
            cache_entry.expires_at = expires_at
        else:
            # Create new cache entry
            cache_entry = ReportCache(
                tenant_id=tenant_id,
                report_definition_id=report_id,
                cache_key=cache_key,
                parameters_hash=params_hash,
                cached_data=data,
                row_count=data.get('row_count', 0),
                expires_at=expires_at
            )
            db.add(cache_entry)

        db.commit()

    @staticmethod
    def _generate_cache_key(report_id: int, parameters: Optional[Dict[str, Any]]) -> str:
        """Generate a cache key from report ID and parameters."""
        params_str = json.dumps(parameters or {}, sort_keys=True)
        return f"report_{report_id}_{hashlib.sha256(params_str.encode()).hexdigest()}"

    @staticmethod
    def get_lookup_data(
        db: Session,
        tenant_id: int,
        request: LookupDataRequest
    ) -> Dict[str, Any]:
        """Get lookup data for a parameter."""
        entity = request.entity
        display_field = request.display_field
        value_field = request.value_field

        # Build query
        sql = f"""
            SELECT DISTINCT {value_field} as value, {display_field} as label
            FROM {entity}
            WHERE tenant_id = {tenant_id}
        """

        # Add search filter
        if request.search:
            sql += f" AND {display_field} LIKE '%{request.search}%'"

        # Add custom filter conditions
        if request.filter_conditions:
            for field, value in request.filter_conditions.items():
                sql += f" AND {field} = '{value}'"

        # Add parent value filter for cascading
        if request.parent_value:
            # Assuming parent field naming convention
            sql += f" AND parent_id = '{request.parent_value}'"

        sql += f" ORDER BY {display_field} LIMIT {request.limit}"

        # Execute query
        result = db.execute(text(sql))
        rows = result.fetchall()

        items = [{'value': row[0], 'label': row[1]} for row in rows]

        return {
            'items': items,
            'total_count': len(items)
        }
