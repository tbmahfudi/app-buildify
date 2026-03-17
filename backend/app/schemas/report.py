"""
Report schemas for request/response validation.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


class ParameterType(str, Enum):
    """Parameter types."""
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    LOOKUP = "lookup"
    MULTI_SELECT = "multi_select"


class ExportFormat(str, Enum):
    """Export formats."""
    PDF = "pdf"
    EXCEL_FORMATTED = "excel_formatted"
    EXCEL_RAW = "excel_raw"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


class ReportType(str, Enum):
    """
    Report output types.

    - tabular  : plain rows-and-columns table (default)
    - summary  : grouped/aggregated totals (like a GROUP BY view)
    - crosstab : pivot/matrix — rows × columns with aggregate cells
    - metric   : single KPI card(s) — one or a few key numbers
    - chart    : chart is the primary output (bar, line, pie, …)
    """
    TABULAR  = "tabular"
    SUMMARY  = "summary"
    CROSSTAB = "crosstab"
    METRIC   = "metric"
    CHART    = "chart"


class AggregationType(str, Enum):
    """Aggregation types."""
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    NONE = "none"


# Parameter Schemas

class LookupConfig(BaseModel):
    """Configuration for lookup parameters."""
    entity: str = Field(..., description="Entity/table to lookup from")
    display_field: str = Field(..., description="Field to display to users")
    value_field: str = Field(..., description="Field value to use")
    filter_conditions: Optional[Dict[str, Any]] = Field(None, description="Filter conditions")
    depends_on: Optional[str] = Field(None, description="Parent parameter for cascading")
    allow_multiple: bool = Field(False, description="Allow multiple selections")


class ValidationRule(BaseModel):
    """Validation rule for parameters."""
    rule_type: str = Field(..., description="Type of validation (min, max, regex, etc.)")
    value: Any = Field(..., description="Validation value")
    error_message: Optional[str] = Field(None, description="Custom error message")


class ReportParameter(BaseModel):
    """Report parameter definition."""
    name: str = Field(..., description="Parameter name (used in queries)")
    label: str = Field(..., description="Display label")
    parameter_type: ParameterType = Field(..., description="Parameter type")
    required: bool = Field(False, description="Is parameter required")
    default_value: Optional[Any] = Field(None, description="Default value")
    description: Optional[str] = Field(None, description="Parameter description/help text")
    lookup_config: Optional[LookupConfig] = Field(None, description="Lookup configuration")
    validation_rules: Optional[List[ValidationRule]] = Field(None, description="Validation rules")
    order: int = Field(0, description="Display order")


# Column Schemas

class ColumnConfig(BaseModel):
    """Column configuration for report."""
    name: str = Field(..., description="Column name/field")
    label: str = Field(..., description="Display label")
    data_type: str = Field("string", description="Data type")
    visible: bool = Field(True, description="Is column visible")
    sortable: bool = Field(True, description="Is column sortable")
    filterable: bool = Field(True, description="Is column filterable")
    aggregation: AggregationType = Field(AggregationType.NONE, description="Aggregation type")
    format_string: Optional[str] = Field(None, description="Format string (e.g., ${0:,.2f})")
    width: Optional[int] = Field(None, description="Column width in pixels")
    order: int = Field(0, description="Display order")


class ConditionalFormat(BaseModel):
    """Conditional formatting rule."""
    condition: str = Field(..., description="Condition expression")
    style: Dict[str, Any] = Field(..., description="CSS styles to apply")
    applies_to: List[str] = Field(..., description="Column names to apply to")


# Query Schemas

class JoinConfig(BaseModel):
    """Join configuration."""
    entity: str = Field(..., description="Entity to join")
    join_type: str = Field("inner", description="Join type (inner, left, right, outer)")
    on_condition: str = Field(..., description="Join condition")
    alias: Optional[str] = Field(None, description="Table alias")


class FilterCondition(BaseModel):
    """Filter condition."""
    field: str = Field(..., description="Field name")
    operator: str = Field(..., description="Operator (eq, ne, gt, lt, like, in, etc.)")
    value: Any = Field(..., description="Filter value")
    parameter: Optional[str] = Field(None, description="Parameter name to use")


class FilterGroup(BaseModel):
    """Group of filter conditions."""
    logic: str = Field("AND", description="Logic operator (AND, OR)")
    conditions: List[FilterCondition] = Field(..., description="Filter conditions")
    groups: Optional[List['FilterGroup']] = Field(None, description="Nested filter groups")


# Support recursive model
FilterGroup.model_rebuild()


class QueryConfig(BaseModel):
    """Query configuration."""
    joins: Optional[List[JoinConfig]] = Field(None, description="Join configurations")
    filters: Optional[FilterGroup] = Field(None, description="Filter configuration")
    group_by: Optional[List[str]] = Field(None, description="Group by fields")
    order_by: Optional[List[Dict[str, str]]] = Field(None, description="Order by configuration")
    limit: Optional[int] = Field(None, description="Result limit")


# Visualization Schemas

class ChartConfig(BaseModel):
    """
    Chart / visualization configuration.

    Supported chart_type values
    ───────────────────────────
    Comparison  : bar, bar_horizontal, bar_stacked, bar_grouped, combo
    Trend       : line, area, area_stacked
    Composition : pie, donut, waterfall, funnel
    Distribution: scatter, bubble, heatmap
    KPI         : gauge, metric_card
    """
    chart_type: Optional[str] = Field(None, description="Chart type identifier (see docstring)")
    x_axis: Optional[str] = Field(None, description="Category / time-axis field name")
    y_axis: Optional[List[str]] = Field(None, description="Measure field name(s)")
    y_axis_secondary: Optional[str] = Field(None, description="Second measure axis (combo charts)")
    group_by: Optional[str] = Field(None, description="Series / color grouping field")
    title: Optional[str] = Field(None, description="Chart title (overrides report name)")
    show_legend: bool = Field(True, description="Display the chart legend")
    show_data_labels: bool = Field(False, description="Show value labels on data points")
    color_scheme: Optional[str] = Field("default", description="Palette: default|blue|green|purple|rainbow|monochrome")
    sort_order: Optional[str] = Field(None, description="asc|desc — sort bars/slices")
    options: Optional[Dict[str, Any]] = Field(None, description="Chart-library-specific overrides")


# Report Definition Schemas

class ReportDefinitionBase(BaseModel):
    """Base report definition schema."""
    name: str = Field(..., min_length=1, max_length=255)
    title: Optional[str] = Field(None, description="Display title shown to users")
    description: Optional[str] = None
    category: Optional[str] = None
    module_id: Optional[UUID] = None
    report_type: ReportType = ReportType.TABULAR
    # base_entity is optional — derived from data_source on save if not provided
    base_entity: Optional[str] = Field(None, description="Base entity/table (auto-derived from data_source)")
    # Designer format fields
    data_source: Optional[Dict[str, Any]] = Field(None, description="Data source config from visual designer")
    columns: Optional[List[Dict[str, Any]]] = Field(None, description="Selected columns from drag-drop designer")
    chart_config: Optional[Dict[str, Any]] = Field(None, description="Chart config from visual designer")
    # Legacy / processed format fields
    query_config: Optional[Dict[str, Any]] = None
    columns_config: Optional[List[Dict[str, Any]]] = None
    parameters: Optional[List[Any]] = None
    visualization_config: Optional[Dict[str, Any]] = None
    formatting_rules: Optional[List[ConditionalFormat]] = None
    is_public: bool = False
    allowed_roles: Optional[List[int]] = None
    allowed_users: Optional[List[int]] = None
    is_template: bool = False

    class Config:
        extra = "allow"  # Accept any extra fields from the frontend without erroring


class ReportDefinitionCreate(ReportDefinitionBase):
    """Create report definition schema."""
    pass


class ReportDefinitionUpdate(BaseModel):
    """Update report definition schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    module_id: Optional[UUID] = None
    report_type: Optional[ReportType] = None
    base_entity: Optional[str] = None
    data_source: Optional[Dict[str, Any]] = None
    columns: Optional[List[Dict[str, Any]]] = None
    chart_config: Optional[Dict[str, Any]] = None
    query_config: Optional[Dict[str, Any]] = None
    columns_config: Optional[List[Dict[str, Any]]] = None
    parameters: Optional[List[Any]] = None
    visualization_config: Optional[Dict[str, Any]] = None
    formatting_rules: Optional[List[ConditionalFormat]] = None
    is_public: Optional[bool] = None
    allowed_roles: Optional[List[int]] = None
    allowed_users: Optional[List[int]] = None
    is_active: Optional[bool] = None

    class Config:
        extra = "allow"


class ReportDefinitionResponse(ReportDefinitionBase):
    """Report definition response schema."""
    id: UUID
    tenant_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
        extra = "allow"


# Report Execution Schemas

class ReportPreviewRequest(BaseModel):
    """Ad-hoc report preview request — no saved report ID required.

    Accepts both the legacy flat format (base_entity / columns_config) and the
    report-designer format (data_source / columns) so the frontend can POST its
    live reportData object directly.
    """
    # Legacy flat fields
    base_entity: Optional[str] = Field(None, description="Primary entity/table to query (flat format)")
    columns_config: Optional[List[Dict[str, Any]]] = Field(None, description="Column definitions (flat format)")
    query_config: Optional[Dict[str, Any]] = Field(None, description="Filters, order, group-by config")
    parameters: Optional[Any] = Field(None, description="Parameter values dict or parameter definition list — both accepted")
    limit: int = Field(10, ge=1, le=500, description="Maximum rows to return")

    # Report-designer format (frontend sends the full reportData object)
    data_source: Optional[Dict[str, Any]] = Field(None, description="Nested data source config from report designer")
    columns: Optional[List[Dict[str, Any]]] = Field(None, description="Column list from report designer (uses 'alias' as label)")

    class Config:
        extra = "allow"  # absorb any other top-level reportData fields without error


class ReportPreviewResponse(BaseModel):
    """Ad-hoc report preview response."""
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int


class ReportExecutionRequest(BaseModel):
    """Report execution request."""
    report_definition_id: UUID
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameter values")
    export_format: Optional[ExportFormat] = None
    use_cache: bool = Field(True, description="Use cached results if available")


class ReportExecutionResponse(BaseModel):
    """Report execution response."""
    id: UUID
    report_definition_id: UUID
    status: str
    executed_by: UUID
    executed_at: datetime
    parameters_used: Optional[Dict[str, Any]]
    row_count: Optional[int]
    execution_time_ms: Optional[int]
    error_message: Optional[str]
    export_format: Optional[ExportFormat]
    export_file_path: Optional[str]
    data: Optional[Any] = Field(None, description="Report data if not exported to file")

    class Config:
        from_attributes = True


# Report Schedule Schemas

class ReportScheduleBase(BaseModel):
    """Base report schedule schema."""
    report_definition_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True
    cron_expression: str = Field(..., description="Cron expression for scheduling")
    timezone: str = Field("UTC", description="Timezone for schedule")
    default_parameters: Optional[Dict[str, Any]] = None
    export_format: ExportFormat = ExportFormat.PDF
    email_recipients: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    storage_path: Optional[str] = None


class ReportScheduleCreate(ReportScheduleBase):
    """Create report schedule schema."""
    pass


class ReportScheduleUpdate(BaseModel):
    """Update report schedule schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    default_parameters: Optional[Dict[str, Any]] = None
    export_format: Optional[ExportFormat] = None
    email_recipients: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    storage_path: Optional[str] = None


class ReportScheduleResponse(ReportScheduleBase):
    """Report schedule response schema."""
    id: UUID
    tenant_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]

    class Config:
        from_attributes = True


# Report Template Schemas

class ReportTemplateResponse(BaseModel):
    """Report template response schema."""
    id: UUID
    name: str
    description: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    template_config: Dict[str, Any]
    preview_image_url: Optional[str]
    is_builtin: bool
    usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# Lookup Data Schemas

class LookupDataRequest(BaseModel):
    """Request for lookup data."""
    entity: str
    display_field: str
    value_field: str
    filter_conditions: Optional[Dict[str, Any]] = None
    parent_value: Optional[Any] = Field(None, description="Parent parameter value for cascading")
    search: Optional[str] = Field(None, description="Search term")
    limit: int = Field(100, le=1000)


class LookupDataItem(BaseModel):
    """Lookup data item."""
    label: str
    value: Any


class LookupDataResponse(BaseModel):
    """Lookup data response."""
    items: List[LookupDataItem]
    total_count: int


class JoinSuggestionsRequest(BaseModel):
    """Request body for join suggestions."""
    entities: List[str] = Field(..., description="List of entity names to derive join suggestions for")
