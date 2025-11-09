"""
Report schemas for request/response validation.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


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
    """Report types."""
    TABULAR = "tabular"
    SUMMARY = "summary"
    CHART = "chart"
    DASHBOARD = "dashboard"


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
    """Chart configuration."""
    chart_type: str = Field(..., description="Chart type (bar, line, pie, etc.)")
    x_axis: str = Field(..., description="X-axis field")
    y_axis: List[str] = Field(..., description="Y-axis fields")
    title: Optional[str] = Field(None, description="Chart title")
    options: Optional[Dict[str, Any]] = Field(None, description="Chart-specific options")


# Report Definition Schemas

class ReportDefinitionBase(BaseModel):
    """Base report definition schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    report_type: ReportType = ReportType.TABULAR
    base_entity: str = Field(..., description="Base entity/table")
    query_config: Optional[QueryConfig] = None
    columns_config: Optional[List[ColumnConfig]] = None
    parameters: Optional[List[ReportParameter]] = None
    visualization_config: Optional[ChartConfig] = None
    formatting_rules: Optional[List[ConditionalFormat]] = None
    is_public: bool = False
    allowed_roles: Optional[List[int]] = None
    allowed_users: Optional[List[int]] = None
    is_template: bool = False


class ReportDefinitionCreate(ReportDefinitionBase):
    """Create report definition schema."""
    pass


class ReportDefinitionUpdate(BaseModel):
    """Update report definition schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    report_type: Optional[ReportType] = None
    base_entity: Optional[str] = None
    query_config: Optional[QueryConfig] = None
    columns_config: Optional[List[ColumnConfig]] = None
    parameters: Optional[List[ReportParameter]] = None
    visualization_config: Optional[ChartConfig] = None
    formatting_rules: Optional[List[ConditionalFormat]] = None
    is_public: Optional[bool] = None
    allowed_roles: Optional[List[int]] = None
    allowed_users: Optional[List[int]] = None
    is_active: Optional[bool] = None


class ReportDefinitionResponse(ReportDefinitionBase):
    """Report definition response schema."""
    id: int
    tenant_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# Report Execution Schemas

class ReportExecutionRequest(BaseModel):
    """Report execution request."""
    report_definition_id: int
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameter values")
    export_format: Optional[ExportFormat] = None
    use_cache: bool = Field(True, description="Use cached results if available")


class ReportExecutionResponse(BaseModel):
    """Report execution response."""
    id: int
    report_definition_id: int
    status: str
    executed_by: int
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
    report_definition_id: int
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
    id: int
    tenant_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]

    class Config:
        from_attributes = True


# Report Template Schemas

class ReportTemplateResponse(BaseModel):
    """Report template response schema."""
    id: int
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
