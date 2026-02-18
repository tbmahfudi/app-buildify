"""
Dashboard models for the dashboard visualization system.

Dashboards can contain multiple pages, and each page contains multiple widgets.
Widgets can display reports, charts, KPIs, and other visualizations.
"""
import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models import Base
from app.models.base import GUID


class DashboardLayout(str, enum.Enum):
    """Dashboard layout types."""
    GRID = "grid"  # Grid-based layout
    FREEFORM = "freeform"  # Absolute positioning
    RESPONSIVE = "responsive"  # Responsive grid


class WidgetType(str, enum.Enum):
    """Dashboard widget types."""
    REPORT_TABLE = "report_table"  # Tabular report display
    CHART = "chart"  # Chart visualization
    KPI_CARD = "kpi_card"  # KPI/metric card
    METRIC = "metric"  # Single metric display
    TEXT = "text"  # Rich text/HTML content
    IFRAME = "iframe"  # Embedded iframe
    IMAGE = "image"  # Image display
    FILTER_PANEL = "filter_panel"  # Global filter panel


class ChartType(str, enum.Enum):
    """Chart types for chart widgets."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    SCATTER = "scatter"
    GAUGE = "gauge"
    FUNNEL = "funnel"
    HEATMAP = "heatmap"


class RefreshInterval(str, enum.Enum):
    """Auto-refresh intervals."""
    NONE = "none"
    THIRTY_SECONDS = "30s"
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"


class Dashboard(Base):
    """Dashboard model - container for multiple pages."""
    __tablename__ = "dashboards"

    id = Column(GUID, primary_key=True, index=True)
    tenant_id = Column(GUID, nullable=False, index=True)
    # module_id: Associates dashboard with a specific module (optional)
    module_id = Column(GUID, ForeignKey("modules.id"), nullable=True, index=True)

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)  # List of tags for categorization

    # Layout
    layout_type = Column(String(50), default="grid")
    theme = Column(String(50), default="light")  # light, dark, custom

    # Global settings
    global_parameters = Column(JSON, nullable=True)  # Shared parameters across widgets
    global_filters = Column(JSON, nullable=True)  # Global filter configuration
    refresh_interval = Column(String(20), default="none")

    # Permissions
    is_public = Column(Boolean, default=False)
    allowed_roles = Column(JSON, nullable=True)
    allowed_users = Column(JSON, nullable=True)

    # Display settings
    show_header = Column(Boolean, default=True)
    show_filters = Column(Boolean, default=True)
    full_screen_mode = Column(Boolean, default=False)

    # Metadata
    created_by = Column(GUID, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_favorite = Column(Boolean, default=False)

    # Relationships
    pages = relationship("DashboardPage", back_populates="dashboard", cascade="all, delete-orphan", order_by="DashboardPage.order")
    shares = relationship("DashboardShare", back_populates="dashboard", cascade="all, delete-orphan")


class DashboardPage(Base):
    """Dashboard page - a single page within a dashboard."""
    __tablename__ = "dashboard_pages"

    id = Column(GUID, primary_key=True, index=True)
    dashboard_id = Column(GUID, ForeignKey("dashboards.id"), nullable=False)
    tenant_id = Column(GUID, nullable=False, index=True)

    # Page info
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=True)  # URL-friendly identifier
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Icon identifier

    # Layout
    layout_config = Column(JSON, nullable=True)  # Grid columns, row height, etc.

    # Display order
    order = Column(Integer, default=0)
    is_default = Column(Boolean, default=False)  # Default landing page

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dashboard = relationship("Dashboard", back_populates="pages")
    widgets = relationship("DashboardWidget", back_populates="page", cascade="all, delete-orphan", order_by="DashboardWidget.order")


class DashboardWidget(Base):
    """Dashboard widget - individual visualization component."""
    __tablename__ = "dashboard_widgets"

    id = Column(GUID, primary_key=True, index=True)
    page_id = Column(GUID, ForeignKey("dashboard_pages.id"), nullable=False)
    tenant_id = Column(GUID, nullable=False, index=True)

    # Widget info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    widget_type = Column(String(50), nullable=False)

    # Data source
    report_definition_id = Column(GUID, nullable=True)  # Link to report if applicable
    data_source_config = Column(JSON, nullable=True)  # Custom data source configuration

    # Widget configuration
    widget_config = Column(JSON, nullable=True)  # Widget-specific settings
    chart_config = Column(JSON, nullable=True)  # Chart configuration if chart widget
    filter_mapping = Column(JSON, nullable=True)  # Map global filters to widget parameters

    # Layout and positioning
    position = Column(JSON, nullable=False)  # {x, y, w, h} for grid layout
    order = Column(Integer, default=0)

    # Display settings
    show_title = Column(Boolean, default=True)
    show_border = Column(Boolean, default=True)
    background_color = Column(String(20), nullable=True)

    # Refresh settings
    auto_refresh = Column(Boolean, default=False)
    refresh_interval = Column(String(20), default="none")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    page = relationship("DashboardPage", back_populates="widgets")


class DashboardShare(Base):
    """Dashboard sharing and collaboration."""
    __tablename__ = "dashboard_shares"

    id = Column(GUID, primary_key=True, index=True)
    dashboard_id = Column(GUID, ForeignKey("dashboards.id"), nullable=False)
    tenant_id = Column(GUID, nullable=False, index=True)

    # Share info
    shared_with_user_id = Column(GUID, nullable=True)  # Specific user
    shared_with_role_id = Column(GUID, nullable=True)  # Specific role
    share_token = Column(String(255), nullable=True, unique=True)  # Public share token

    # Permissions
    can_view = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    # Metadata
    created_by = Column(GUID, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    dashboard = relationship("Dashboard", back_populates="shares")


class DashboardSnapshot(Base):
    """Dashboard snapshot - saved state at a point in time."""
    __tablename__ = "dashboard_snapshots"

    id = Column(GUID, primary_key=True, index=True)
    dashboard_id = Column(GUID, ForeignKey("dashboards.id"), nullable=False)
    tenant_id = Column(GUID, nullable=False, index=True)

    # Snapshot info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Snapshot data
    snapshot_data = Column(JSON, nullable=False)  # Complete dashboard state
    parameters_used = Column(JSON, nullable=True)  # Parameter values at snapshot time

    # Metadata
    created_by = Column(GUID, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class WidgetDataCache(Base):
    """Cache for widget data."""
    __tablename__ = "widget_data_cache"

    id = Column(GUID, primary_key=True, index=True)
    widget_id = Column(GUID, ForeignKey("dashboard_widgets.id"), nullable=False)
    tenant_id = Column(GUID, nullable=False, index=True)

    # Cache key
    cache_key = Column(String(255), nullable=False, unique=True, index=True)
    parameters_hash = Column(String(255), nullable=False)

    # Cached data
    cached_data = Column(JSON, nullable=True)
    row_count = Column(Integer, nullable=True)

    # Cache metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    hit_count = Column(Integer, default=0)
