"""
Dashboard schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DashboardLayout(str, Enum):
    """Dashboard layout types."""
    GRID = "grid"
    FREEFORM = "freeform"
    RESPONSIVE = "responsive"


class WidgetType(str, Enum):
    """Widget types."""
    REPORT_TABLE = "report_table"
    CHART = "chart"
    KPI_CARD = "kpi_card"
    METRIC = "metric"
    TEXT = "text"
    IFRAME = "iframe"
    IMAGE = "image"
    FILTER_PANEL = "filter_panel"


class ChartType(str, Enum):
    """Chart types."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    SCATTER = "scatter"
    GAUGE = "gauge"
    FUNNEL = "funnel"
    HEATMAP = "heatmap"


class RefreshInterval(str, Enum):
    """Refresh intervals."""
    NONE = "none"
    THIRTY_SECONDS = "30s"
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"


# Widget Schemas

class WidgetPosition(BaseModel):
    """Widget position in grid layout."""
    x: int = Field(..., description="X position in grid")
    y: int = Field(..., description="Y position in grid")
    w: int = Field(..., description="Width in grid units")
    h: int = Field(..., description="Height in grid units")


class ChartConfig(BaseModel):
    """Chart configuration for chart widgets."""
    chart_type: ChartType
    x_axis: str = Field(..., description="X-axis field")
    y_axis: List[str] = Field(..., description="Y-axis fields")
    title: Optional[str] = None
    show_legend: bool = True
    show_grid: bool = True
    colors: Optional[List[str]] = None
    options: Optional[Dict[str, Any]] = None


class KpiCardConfig(BaseModel):
    """KPI card configuration."""
    value_field: str = Field(..., description="Field to display as main value")
    label: str = Field(..., description="KPI label")
    format: Optional[str] = Field(None, description="Number format (e.g., currency, percentage)")
    icon: Optional[str] = None
    color: Optional[str] = None
    show_trend: bool = False
    trend_field: Optional[str] = None
    comparison_type: Optional[str] = None  # previous_period, target, etc.


class TextWidgetConfig(BaseModel):
    """Text widget configuration."""
    content: str = Field(..., description="HTML or markdown content")
    content_type: str = Field("html", description="html or markdown")


class IframeWidgetConfig(BaseModel):
    """Iframe widget configuration."""
    url: str = Field(..., description="URL to embed")
    allow_fullscreen: bool = True


class WidgetDataSource(BaseModel):
    """Widget data source configuration."""
    type: str = Field(..., description="report, query, or api")
    report_id: Optional[int] = None
    query: Optional[str] = None
    api_endpoint: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class DashboardWidgetBase(BaseModel):
    """Base dashboard widget schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    widget_type: WidgetType
    report_definition_id: Optional[int] = None
    data_source_config: Optional[WidgetDataSource] = None
    widget_config: Optional[Dict[str, Any]] = None
    chart_config: Optional[ChartConfig] = None
    filter_mapping: Optional[Dict[str, str]] = None
    position: WidgetPosition
    order: int = 0
    show_title: bool = True
    show_border: bool = True
    background_color: Optional[str] = None
    auto_refresh: bool = False
    refresh_interval: RefreshInterval = RefreshInterval.NONE


class DashboardWidgetCreate(DashboardWidgetBase):
    """Create dashboard widget schema."""
    page_id: int


class DashboardWidgetUpdate(BaseModel):
    """Update dashboard widget schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    widget_type: Optional[WidgetType] = None
    report_definition_id: Optional[int] = None
    data_source_config: Optional[WidgetDataSource] = None
    widget_config: Optional[Dict[str, Any]] = None
    chart_config: Optional[ChartConfig] = None
    filter_mapping: Optional[Dict[str, str]] = None
    position: Optional[WidgetPosition] = None
    order: Optional[int] = None
    show_title: Optional[bool] = None
    show_border: Optional[bool] = None
    background_color: Optional[str] = None
    auto_refresh: Optional[bool] = None
    refresh_interval: Optional[RefreshInterval] = None


class DashboardWidgetResponse(DashboardWidgetBase):
    """Dashboard widget response schema."""
    id: int
    page_id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Page Schemas

class LayoutConfig(BaseModel):
    """Page layout configuration."""
    columns: int = Field(12, description="Number of grid columns")
    row_height: int = Field(50, description="Height of each row in pixels")
    margin: List[int] = Field([10, 10], description="Margin between widgets [x, y]")
    container_padding: List[int] = Field([10, 10], description="Container padding [x, y]")


class DashboardPageBase(BaseModel):
    """Base dashboard page schema."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    layout_config: Optional[LayoutConfig] = None
    order: int = 0
    is_default: bool = False


class DashboardPageCreate(DashboardPageBase):
    """Create dashboard page schema."""
    dashboard_id: int


class DashboardPageUpdate(BaseModel):
    """Update dashboard page schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    layout_config: Optional[LayoutConfig] = None
    order: Optional[int] = None
    is_default: Optional[bool] = None


class DashboardPageResponse(DashboardPageBase):
    """Dashboard page response schema."""
    id: int
    dashboard_id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime
    widgets: List[DashboardWidgetResponse] = []

    class Config:
        from_attributes = True


# Dashboard Schemas

class GlobalParameter(BaseModel):
    """Global dashboard parameter."""
    name: str
    label: str
    parameter_type: str
    default_value: Optional[Any] = None
    required: bool = False


class DashboardBase(BaseModel):
    """Base dashboard schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    layout_type: DashboardLayout = DashboardLayout.GRID
    theme: str = "light"
    global_parameters: Optional[List[GlobalParameter]] = None
    global_filters: Optional[Dict[str, Any]] = None
    refresh_interval: RefreshInterval = RefreshInterval.NONE
    is_public: bool = False
    allowed_roles: Optional[List[int]] = None
    allowed_users: Optional[List[int]] = None
    show_header: bool = True
    show_filters: bool = True
    full_screen_mode: bool = False


class DashboardCreate(DashboardBase):
    """Create dashboard schema."""
    pass


class DashboardUpdate(BaseModel):
    """Update dashboard schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    layout_type: Optional[DashboardLayout] = None
    theme: Optional[str] = None
    global_parameters: Optional[List[GlobalParameter]] = None
    global_filters: Optional[Dict[str, Any]] = None
    refresh_interval: Optional[RefreshInterval] = None
    is_public: Optional[bool] = None
    allowed_roles: Optional[List[int]] = None
    allowed_users: Optional[List[int]] = None
    show_header: Optional[bool] = None
    show_filters: Optional[bool] = None
    full_screen_mode: Optional[bool] = None
    is_favorite: Optional[bool] = None


class DashboardResponse(DashboardBase):
    """Dashboard response schema."""
    id: int
    tenant_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    is_favorite: bool
    pages: List[DashboardPageResponse] = []

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    """Dashboard summary (without pages/widgets for listing)."""
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    is_public: bool
    is_favorite: bool
    created_by: int
    created_at: datetime
    updated_at: datetime
    page_count: int = 0

    class Config:
        from_attributes = True


# Widget Data Schemas

class WidgetDataRequest(BaseModel):
    """Request to get widget data."""
    widget_id: int
    parameters: Optional[Dict[str, Any]] = None
    use_cache: bool = True


class WidgetDataResponse(BaseModel):
    """Widget data response."""
    widget_id: int
    data: Any
    metadata: Optional[Dict[str, Any]] = None
    cached: bool = False
    execution_time_ms: Optional[int] = None


# Dashboard Share Schemas

class DashboardShareCreate(BaseModel):
    """Create dashboard share."""
    dashboard_id: int
    shared_with_user_id: Optional[int] = None
    shared_with_role_id: Optional[int] = None
    can_view: bool = True
    can_edit: bool = False
    can_share: bool = False
    expires_at: Optional[datetime] = None


class DashboardShareResponse(BaseModel):
    """Dashboard share response."""
    id: int
    dashboard_id: int
    shared_with_user_id: Optional[int]
    shared_with_role_id: Optional[int]
    share_token: Optional[str]
    can_view: bool
    can_edit: bool
    can_share: bool
    expires_at: Optional[datetime]
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


# Dashboard Snapshot Schemas

class DashboardSnapshotCreate(BaseModel):
    """Create dashboard snapshot."""
    dashboard_id: int
    name: str
    description: Optional[str] = None
    parameters_used: Optional[Dict[str, Any]] = None


class DashboardSnapshotResponse(BaseModel):
    """Dashboard snapshot response."""
    id: int
    dashboard_id: int
    name: str
    description: Optional[str]
    snapshot_data: Dict[str, Any]
    parameters_used: Optional[Dict[str, Any]]
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


# Bulk Operations

class BulkWidgetUpdateRequest(BaseModel):
    """Bulk update widgets (for repositioning)."""
    updates: List[Dict[str, Any]] = Field(..., description="List of {widget_id, position, order}")


class DashboardCloneRequest(BaseModel):
    """Clone dashboard request."""
    name: str
    include_data: bool = False
