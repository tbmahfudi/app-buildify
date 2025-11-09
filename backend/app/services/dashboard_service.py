"""
Dashboard service - business logic for dashboards.

Reuses ReportService for data fetching and execution.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import json

from app.models.dashboard import (
    Dashboard,
    DashboardPage,
    DashboardWidget,
    DashboardShare,
    DashboardSnapshot,
    WidgetDataCache,
    WidgetType
)
from app.schemas.dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardPageCreate,
    DashboardPageUpdate,
    DashboardWidgetCreate,
    DashboardWidgetUpdate,
    DashboardShareCreate,
    DashboardSnapshotCreate
)
from app.services.report_service import ReportService
from app.schemas.report import ReportExecutionRequest


class DashboardService:
    """Service for dashboard operations."""

    # ==================== Dashboard CRUD ====================

    @staticmethod
    def create_dashboard(
        db: Session,
        tenant_id: int,
        user_id: int,
        dashboard_data: DashboardCreate
    ) -> Dashboard:
        """Create a new dashboard."""
        dashboard_dict = dashboard_data.model_dump()

        # Convert Pydantic models to dict for JSON columns
        json_fields = ['global_parameters', 'global_filters', 'tags', 'allowed_roles', 'allowed_users']
        for field in json_fields:
            if field in dashboard_dict and dashboard_dict[field] is not None:
                if isinstance(dashboard_dict[field], list):
                    dashboard_dict[field] = [
                        item.model_dump() if hasattr(item, 'model_dump') else item
                        for item in dashboard_dict[field]
                    ]

        db_dashboard = Dashboard(
            tenant_id=tenant_id,
            created_by=user_id,
            **dashboard_dict
        )
        db.add(db_dashboard)
        db.commit()
        db.refresh(db_dashboard)
        return db_dashboard

    @staticmethod
    def get_dashboard(
        db: Session,
        tenant_id: int,
        dashboard_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Dashboard]:
        """Get dashboard by ID with permission check."""
        dashboard = db.query(Dashboard).filter(
            Dashboard.id == dashboard_id,
            Dashboard.tenant_id == tenant_id,
            Dashboard.is_active == True
        ).first()

        if not dashboard:
            return None

        # Check permissions
        if not dashboard.is_public and user_id:
            if dashboard.allowed_users and user_id not in dashboard.allowed_users:
                # Check if user has access via share
                share = db.query(DashboardShare).filter(
                    DashboardShare.dashboard_id == dashboard_id,
                    DashboardShare.shared_with_user_id == user_id,
                    DashboardShare.can_view == True
                ).first()
                if not share:
                    return None

        return dashboard

    @staticmethod
    def list_dashboards(
        db: Session,
        tenant_id: int,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        favorites_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dashboard]:
        """List dashboards with filtering."""
        query = db.query(Dashboard).filter(
            Dashboard.tenant_id == tenant_id,
            Dashboard.is_active == True
        )

        if category:
            query = query.filter(Dashboard.category == category)

        if favorites_only:
            query = query.filter(Dashboard.is_favorite == True)

        # Filter by permissions
        if user_id:
            query = query.filter(
                or_(
                    Dashboard.is_public == True,
                    Dashboard.created_by == user_id,
                    Dashboard.allowed_users.contains([user_id])
                )
            )

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_dashboard(
        db: Session,
        tenant_id: int,
        dashboard_id: int,
        dashboard_data: DashboardUpdate
    ) -> Optional[Dashboard]:
        """Update dashboard."""
        db_dashboard = db.query(Dashboard).filter(
            Dashboard.id == dashboard_id,
            Dashboard.tenant_id == tenant_id
        ).first()

        if not db_dashboard:
            return None

        update_data = dashboard_data.model_dump(exclude_unset=True)

        # Convert Pydantic models to dict for JSON columns
        json_fields = ['global_parameters', 'global_filters', 'tags', 'allowed_roles', 'allowed_users']
        for field in json_fields:
            if field in update_data and update_data[field] is not None:
                if isinstance(update_data[field], list):
                    update_data[field] = [
                        item.model_dump() if hasattr(item, 'model_dump') else item
                        for item in update_data[field]
                    ]

        for field, value in update_data.items():
            setattr(db_dashboard, field, value)

        db_dashboard.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_dashboard)
        return db_dashboard

    @staticmethod
    def delete_dashboard(
        db: Session,
        tenant_id: int,
        dashboard_id: int
    ) -> bool:
        """Soft delete dashboard."""
        db_dashboard = db.query(Dashboard).filter(
            Dashboard.id == dashboard_id,
            Dashboard.tenant_id == tenant_id
        ).first()

        if not db_dashboard:
            return False

        db_dashboard.is_active = False
        db.commit()
        return True

    @staticmethod
    def clone_dashboard(
        db: Session,
        tenant_id: int,
        user_id: int,
        dashboard_id: int,
        new_name: str
    ) -> Optional[Dashboard]:
        """Clone an existing dashboard."""
        source_dashboard = DashboardService.get_dashboard(db, tenant_id, dashboard_id, user_id)
        if not source_dashboard:
            return None

        # Create new dashboard
        new_dashboard = Dashboard(
            tenant_id=tenant_id,
            created_by=user_id,
            name=new_name,
            description=source_dashboard.description,
            category=source_dashboard.category,
            tags=source_dashboard.tags,
            layout_type=source_dashboard.layout_type,
            theme=source_dashboard.theme,
            global_parameters=source_dashboard.global_parameters,
            global_filters=source_dashboard.global_filters,
            refresh_interval=source_dashboard.refresh_interval,
            show_header=source_dashboard.show_header,
            show_filters=source_dashboard.show_filters
        )
        db.add(new_dashboard)
        db.flush()

        # Clone pages and widgets
        for page in source_dashboard.pages:
            new_page = DashboardPage(
                dashboard_id=new_dashboard.id,
                tenant_id=tenant_id,
                name=page.name,
                slug=page.slug,
                description=page.description,
                icon=page.icon,
                layout_config=page.layout_config,
                order=page.order,
                is_default=page.is_default
            )
            db.add(new_page)
            db.flush()

            # Clone widgets
            for widget in page.widgets:
                new_widget = DashboardWidget(
                    page_id=new_page.id,
                    tenant_id=tenant_id,
                    title=widget.title,
                    description=widget.description,
                    widget_type=widget.widget_type,
                    report_definition_id=widget.report_definition_id,
                    data_source_config=widget.data_source_config,
                    widget_config=widget.widget_config,
                    chart_config=widget.chart_config,
                    filter_mapping=widget.filter_mapping,
                    position=widget.position,
                    order=widget.order,
                    show_title=widget.show_title,
                    show_border=widget.show_border,
                    background_color=widget.background_color,
                    auto_refresh=widget.auto_refresh,
                    refresh_interval=widget.refresh_interval
                )
                db.add(new_widget)

        db.commit()
        db.refresh(new_dashboard)
        return new_dashboard

    # ==================== Dashboard Page CRUD ====================

    @staticmethod
    def create_page(
        db: Session,
        tenant_id: int,
        page_data: DashboardPageCreate
    ) -> DashboardPage:
        """Create a new dashboard page."""
        page_dict = page_data.model_dump()

        # Convert layout_config if it's a Pydantic model
        if 'layout_config' in page_dict and page_dict['layout_config'] is not None:
            if hasattr(page_dict['layout_config'], 'model_dump'):
                page_dict['layout_config'] = page_dict['layout_config'].model_dump()

        db_page = DashboardPage(
            tenant_id=tenant_id,
            **page_dict
        )
        db.add(db_page)
        db.commit()
        db.refresh(db_page)
        return db_page

    @staticmethod
    def update_page(
        db: Session,
        tenant_id: int,
        page_id: int,
        page_data: DashboardPageUpdate
    ) -> Optional[DashboardPage]:
        """Update dashboard page."""
        db_page = db.query(DashboardPage).filter(
            DashboardPage.id == page_id,
            DashboardPage.tenant_id == tenant_id
        ).first()

        if not db_page:
            return None

        update_data = page_data.model_dump(exclude_unset=True)

        # Convert layout_config if it's a Pydantic model
        if 'layout_config' in update_data and update_data['layout_config'] is not None:
            if hasattr(update_data['layout_config'], 'model_dump'):
                update_data['layout_config'] = update_data['layout_config'].model_dump()

        for field, value in update_data.items():
            setattr(db_page, field, value)

        db_page.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_page)
        return db_page

    @staticmethod
    def delete_page(
        db: Session,
        tenant_id: int,
        page_id: int
    ) -> bool:
        """Delete dashboard page."""
        db_page = db.query(DashboardPage).filter(
            DashboardPage.id == page_id,
            DashboardPage.tenant_id == tenant_id
        ).first()

        if not db_page:
            return False

        db.delete(db_page)
        db.commit()
        return True

    # ==================== Dashboard Widget CRUD ====================

    @staticmethod
    def create_widget(
        db: Session,
        tenant_id: int,
        widget_data: DashboardWidgetCreate
    ) -> DashboardWidget:
        """Create a new dashboard widget."""
        widget_dict = widget_data.model_dump()

        # Convert Pydantic models to dict for JSON columns
        json_fields = ['data_source_config', 'widget_config', 'chart_config',
                      'filter_mapping', 'position']
        for field in json_fields:
            if field in widget_dict and widget_dict[field] is not None:
                if hasattr(widget_dict[field], 'model_dump'):
                    widget_dict[field] = widget_dict[field].model_dump()

        db_widget = DashboardWidget(
            tenant_id=tenant_id,
            **widget_dict
        )
        db.add(db_widget)
        db.commit()
        db.refresh(db_widget)
        return db_widget

    @staticmethod
    def update_widget(
        db: Session,
        tenant_id: int,
        widget_id: int,
        widget_data: DashboardWidgetUpdate
    ) -> Optional[DashboardWidget]:
        """Update dashboard widget."""
        db_widget = db.query(DashboardWidget).filter(
            DashboardWidget.id == widget_id,
            DashboardWidget.tenant_id == tenant_id
        ).first()

        if not db_widget:
            return None

        update_data = widget_data.model_dump(exclude_unset=True)

        # Convert Pydantic models to dict for JSON columns
        json_fields = ['data_source_config', 'widget_config', 'chart_config',
                      'filter_mapping', 'position']
        for field in json_fields:
            if field in update_data and update_data[field] is not None:
                if hasattr(update_data[field], 'model_dump'):
                    update_data[field] = update_data[field].model_dump()

        for field, value in update_data.items():
            setattr(db_widget, field, value)

        db_widget.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_widget)
        return db_widget

    @staticmethod
    def delete_widget(
        db: Session,
        tenant_id: int,
        widget_id: int
    ) -> bool:
        """Delete dashboard widget."""
        db_widget = db.query(DashboardWidget).filter(
            DashboardWidget.id == widget_id,
            DashboardWidget.tenant_id == tenant_id
        ).first()

        if not db_widget:
            return False

        db.delete(db_widget)
        db.commit()
        return True

    @staticmethod
    def bulk_update_widgets(
        db: Session,
        tenant_id: int,
        updates: List[Dict[str, Any]]
    ) -> bool:
        """Bulk update widget positions and order."""
        for update in updates:
            widget_id = update.get('widget_id')
            position = update.get('position')
            order = update.get('order')

            db_widget = db.query(DashboardWidget).filter(
                DashboardWidget.id == widget_id,
                DashboardWidget.tenant_id == tenant_id
            ).first()

            if db_widget:
                if position:
                    db_widget.position = position
                if order is not None:
                    db_widget.order = order
                db_widget.updated_at = datetime.utcnow()

        db.commit()
        return True

    # ==================== Widget Data Retrieval (Reuses ReportService) ====================

    @staticmethod
    def get_widget_data(
        db: Session,
        tenant_id: int,
        user_id: int,
        widget_id: int,
        parameters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get data for a widget - REUSES ReportService for report-based widgets.
        """
        widget = db.query(DashboardWidget).filter(
            DashboardWidget.id == widget_id,
            DashboardWidget.tenant_id == tenant_id
        ).first()

        if not widget:
            raise ValueError("Widget not found")

        # Check cache first
        if use_cache:
            cached_data = DashboardService._get_cached_widget_data(
                db, tenant_id, widget_id, parameters
            )
            if cached_data:
                return {
                    'data': cached_data,
                    'cached': True,
                    'widget_type': widget.widget_type
                }

        # Get data based on widget type
        data = None
        execution_time_ms = 0
        start_time = datetime.utcnow()

        if widget.widget_type == WidgetType.REPORT_TABLE and widget.report_definition_id:
            # REUSE ReportService for report-based widgets
            execution_request = ReportExecutionRequest(
                report_definition_id=widget.report_definition_id,
                parameters=parameters or {},
                use_cache=use_cache
            )
            execution = ReportService.execute_report(
                db, tenant_id, user_id, execution_request
            )

            if execution.status == 'completed':
                # Fetch the actual data from the execution
                query_result = ReportService._build_and_execute_query(
                    db,
                    tenant_id,
                    ReportService.get_report_definition(
                        db, tenant_id, widget.report_definition_id, user_id
                    ),
                    parameters or {}
                )
                data = query_result['data']
                execution_time_ms = execution.execution_time_ms or 0

        elif widget.widget_type == WidgetType.CHART and widget.report_definition_id:
            # REUSE ReportService for chart data
            report_def = ReportService.get_report_definition(
                db, tenant_id, widget.report_definition_id, user_id
            )
            if report_def:
                query_result = ReportService._build_and_execute_query(
                    db, tenant_id, report_def, parameters or {}
                )
                data = DashboardService._transform_data_for_chart(
                    query_result['data'],
                    widget.chart_config
                )

        elif widget.widget_type == WidgetType.KPI_CARD:
            # For KPI cards, fetch single metric from report
            if widget.report_definition_id:
                report_def = ReportService.get_report_definition(
                    db, tenant_id, widget.report_definition_id, user_id
                )
                if report_def:
                    query_result = ReportService._build_and_execute_query(
                        db, tenant_id, report_def, parameters or {}
                    )
                    data = DashboardService._transform_data_for_kpi(
                        query_result['data'],
                        widget.widget_config
                    )

        elif widget.widget_type == WidgetType.TEXT:
            # Static text widget
            data = widget.widget_config

        elif widget.widget_type == WidgetType.IFRAME:
            # Iframe widget
            data = widget.widget_config

        end_time = datetime.utcnow()
        if execution_time_ms == 0:
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

        # Cache the result
        if use_cache and data:
            DashboardService._cache_widget_data(
                db, tenant_id, widget_id, parameters, data
            )

        return {
            'data': data,
            'cached': False,
            'execution_time_ms': execution_time_ms,
            'widget_type': widget.widget_type
        }

    @staticmethod
    def _transform_data_for_chart(data: List[Dict], chart_config: Optional[Dict]) -> Dict:
        """Transform report data for chart visualization."""
        if not chart_config:
            return {'data': data}

        # Extract chart configuration
        x_axis = chart_config.get('x_axis')
        y_axis = chart_config.get('y_axis', [])

        # Build chart-friendly format
        chart_data = {
            'labels': [row.get(x_axis) for row in data],
            'datasets': []
        }

        for y_field in y_axis:
            chart_data['datasets'].append({
                'label': y_field,
                'data': [row.get(y_field) for row in data]
            })

        return chart_data

    @staticmethod
    def _transform_data_for_kpi(data: List[Dict], widget_config: Optional[Dict]) -> Dict:
        """Transform report data for KPI card."""
        if not widget_config or not data:
            return {'value': 0}

        value_field = widget_config.get('value_field')

        # Aggregate if multiple rows
        if len(data) > 0:
            if len(data) == 1:
                value = data[0].get(value_field, 0)
            else:
                # Sum all values
                value = sum(row.get(value_field, 0) for row in data)
        else:
            value = 0

        return {
            'value': value,
            'label': widget_config.get('label', ''),
            'format': widget_config.get('format', 'number')
        }

    @staticmethod
    def _get_cached_widget_data(
        db: Session,
        tenant_id: int,
        widget_id: int,
        parameters: Optional[Dict[str, Any]]
    ) -> Optional[Any]:
        """Get cached widget data."""
        cache_key = DashboardService._generate_widget_cache_key(widget_id, parameters)

        cache_entry = db.query(WidgetDataCache).filter(
            WidgetDataCache.tenant_id == tenant_id,
            WidgetDataCache.widget_id == widget_id,
            WidgetDataCache.cache_key == cache_key,
            WidgetDataCache.expires_at > datetime.utcnow()
        ).first()

        if cache_entry:
            cache_entry.hit_count += 1
            db.commit()
            return cache_entry.cached_data

        return None

    @staticmethod
    def _cache_widget_data(
        db: Session,
        tenant_id: int,
        widget_id: int,
        parameters: Optional[Dict[str, Any]],
        data: Any,
        ttl_minutes: int = 15
    ):
        """Cache widget data."""
        cache_key = DashboardService._generate_widget_cache_key(widget_id, parameters)
        params_hash = hashlib.sha256(
            json.dumps(parameters or {}, sort_keys=True).encode()
        ).hexdigest()

        # Check if cache entry exists
        cache_entry = db.query(WidgetDataCache).filter(
            WidgetDataCache.cache_key == cache_key
        ).first()

        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)

        if cache_entry:
            cache_entry.cached_data = data
            cache_entry.expires_at = expires_at
        else:
            cache_entry = WidgetDataCache(
                widget_id=widget_id,
                tenant_id=tenant_id,
                cache_key=cache_key,
                parameters_hash=params_hash,
                cached_data=data,
                expires_at=expires_at
            )
            db.add(cache_entry)

        db.commit()

    @staticmethod
    def _generate_widget_cache_key(widget_id: int, parameters: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for widget data."""
        params_str = json.dumps(parameters or {}, sort_keys=True)
        return f"widget_{widget_id}_{hashlib.sha256(params_str.encode()).hexdigest()}"

    # ==================== Dashboard Sharing ====================

    @staticmethod
    def create_share(
        db: Session,
        tenant_id: int,
        user_id: int,
        share_data: DashboardShareCreate
    ) -> DashboardShare:
        """Create dashboard share."""
        import secrets

        db_share = DashboardShare(
            tenant_id=tenant_id,
            created_by=user_id,
            share_token=secrets.token_urlsafe(32) if not share_data.shared_with_user_id else None,
            **share_data.model_dump()
        )
        db.add(db_share)
        db.commit()
        db.refresh(db_share)
        return db_share

    # ==================== Dashboard Snapshots ====================

    @staticmethod
    def create_snapshot(
        db: Session,
        tenant_id: int,
        user_id: int,
        snapshot_data: DashboardSnapshotCreate
    ) -> DashboardSnapshot:
        """Create dashboard snapshot."""
        # Get full dashboard data
        dashboard = DashboardService.get_dashboard(
            db, tenant_id, snapshot_data.dashboard_id, user_id
        )

        if not dashboard:
            raise ValueError("Dashboard not found")

        # Serialize dashboard state
        snapshot_dict = {
            'dashboard': {
                'id': dashboard.id,
                'name': dashboard.name,
                'description': dashboard.description,
                'layout_type': dashboard.layout_type,
                'theme': dashboard.theme
            },
            'pages': [],
            'created_at': datetime.utcnow().isoformat()
        }

        for page in dashboard.pages:
            page_dict = {
                'id': page.id,
                'name': page.name,
                'widgets': []
            }
            for widget in page.widgets:
                widget_dict = {
                    'id': widget.id,
                    'title': widget.title,
                    'widget_type': widget.widget_type,
                    'position': widget.position
                }
                page_dict['widgets'].append(widget_dict)
            snapshot_dict['pages'].append(page_dict)

        db_snapshot = DashboardSnapshot(
            tenant_id=tenant_id,
            created_by=user_id,
            dashboard_id=snapshot_data.dashboard_id,
            name=snapshot_data.name,
            description=snapshot_data.description,
            snapshot_data=snapshot_dict,
            parameters_used=snapshot_data.parameters_used
        )
        db.add(db_snapshot)
        db.commit()
        db.refresh(db_snapshot)
        return db_snapshot
