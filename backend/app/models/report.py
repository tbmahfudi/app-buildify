"""
Report models for the reporting system.
"""
import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models import Base
from app.models.base import GUID


class ParameterType(str, enum.Enum):
    """Parameter types for report parameters."""
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    LOOKUP = "lookup"
    MULTI_SELECT = "multi_select"


class ExportFormat(str, enum.Enum):
    """Export formats for reports."""
    PDF = "pdf"
    EXCEL_FORMATTED = "excel_formatted"
    EXCEL_RAW = "excel_raw"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


class ReportType(str, enum.Enum):
    """Report types."""
    TABULAR = "tabular"
    SUMMARY = "summary"
    CHART = "chart"
    DASHBOARD = "dashboard"


class AggregationType(str, enum.Enum):
    """Aggregation types for report columns."""
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    NONE = "none"


class ReportDefinition(Base):
    """Report definition model."""
    __tablename__ = "report_definitions"

    id = Column(GUID, primary_key=True, index=True)
    tenant_id = Column(GUID, nullable=False, index=True)

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    report_type = Column(String(50), default="tabular")

    # Data source
    base_entity = Column(String(100), nullable=False)  # Main table/entity
    query_config = Column(JSON, nullable=True)  # Joins, filters, etc.

    # Columns configuration
    columns_config = Column(JSON, nullable=True)  # Column definitions, ordering, formatting

    # Parameters
    parameters = Column(JSON, nullable=True)  # List of parameter definitions

    # Visualization
    visualization_config = Column(JSON, nullable=True)  # Chart configs if applicable

    # Formatting
    formatting_rules = Column(JSON, nullable=True)  # Conditional formatting

    # Permissions
    is_public = Column(Boolean, default=False)
    allowed_roles = Column(JSON, nullable=True)  # List of role IDs
    allowed_users = Column(JSON, nullable=True)  # List of user IDs

    # Metadata
    created_by = Column(GUID, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_template = Column(Boolean, default=False)

    # Relationships
    executions = relationship("ReportExecution", back_populates="report_definition", cascade="all, delete-orphan")
    schedules = relationship("ReportSchedule", back_populates="report_definition", cascade="all, delete-orphan")


class ReportExecution(Base):
    """Report execution history."""
    __tablename__ = "report_executions"

    id = Column(GUID, primary_key=True, index=True)
    tenant_id = Column(GUID, nullable=False, index=True)
    report_definition_id = Column(GUID, ForeignKey("report_definitions.id"), nullable=False)

    # Execution details
    executed_by = Column(GUID, nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow)
    parameters_used = Column(JSON, nullable=True)  # Parameter values used

    # Results
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    row_count = Column(Integer, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Export
    export_format = Column(String(50), nullable=True)
    export_file_path = Column(String(500), nullable=True)
    export_file_size = Column(Integer, nullable=True)

    # Relationships
    report_definition = relationship("ReportDefinition", back_populates="executions")


class ReportSchedule(Base):
    """Report scheduling configuration."""
    __tablename__ = "report_schedules"

    id = Column(GUID, primary_key=True, index=True)
    tenant_id = Column(GUID, nullable=False, index=True)
    report_definition_id = Column(GUID, ForeignKey("report_definitions.id"), nullable=False)

    # Schedule details
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    # Cron expression for scheduling
    cron_expression = Column(String(100), nullable=False)  # e.g., "0 9 * * 1" for every Monday at 9 AM
    timezone = Column(String(50), default="UTC")

    # Parameters
    default_parameters = Column(JSON, nullable=True)

    # Delivery
    export_format = Column(String(50), default="pdf")
    email_recipients = Column(JSON, nullable=True)  # List of email addresses
    webhook_url = Column(String(500), nullable=True)
    storage_path = Column(String(500), nullable=True)  # Cloud storage path

    # Metadata
    created_by = Column(GUID, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)

    # Relationships
    report_definition = relationship("ReportDefinition", back_populates="schedules")


class ReportTemplate(Base):
    """Pre-built report templates."""
    __tablename__ = "report_templates"

    id = Column(GUID, primary_key=True, index=True)

    # Template info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)

    # Template configuration (same structure as ReportDefinition)
    template_config = Column(JSON, nullable=False)

    # Preview
    preview_image_url = Column(String(500), nullable=True)

    # Metadata
    is_builtin = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportCache(Base):
    """Cache for report results."""
    __tablename__ = "report_cache"

    id = Column(GUID, primary_key=True, index=True)
    tenant_id = Column(GUID, nullable=False, index=True)
    report_definition_id = Column(GUID, ForeignKey("report_definitions.id"), nullable=False)

    # Cache key (hash of parameters)
    cache_key = Column(String(255), nullable=False, index=True, unique=True)
    parameters_hash = Column(String(255), nullable=False)

    # Cached data
    cached_data = Column(JSON, nullable=True)  # For small results
    cached_file_path = Column(String(500), nullable=True)  # For large results

    # Cache metadata
    row_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    hit_count = Column(Integer, default=0)
