"""
Scheduler schemas for request/response validation.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


class ConfigLevel(str, Enum):
    """Configuration hierarchy levels."""
    SYSTEM = "system"
    TENANT = "tenant"
    COMPANY = "company"
    BRANCH = "branch"


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class JobType(str, Enum):
    """Types of scheduled jobs."""
    REPORT_GENERATION = "report_generation"
    DATA_SYNC = "data_sync"
    NOTIFICATION_BATCH = "notification_batch"
    BACKUP = "backup"
    CLEANUP = "cleanup"
    CUSTOM = "custom"
    WEBHOOK = "webhook"
    API_CALL = "api_call"


# ========== Scheduler Configuration Schemas ==========

class SchedulerConfigBase(BaseModel):
    """Base schema for scheduler configuration."""
    name: str = Field(..., description="Configuration name")
    description: Optional[str] = Field(None, description="Configuration description")
    is_enabled: bool = Field(True, description="Is scheduler enabled")
    max_concurrent_jobs: int = Field(5, description="Maximum concurrent jobs", ge=1, le=100)
    default_timezone: str = Field("UTC", description="Default timezone")
    max_retries: int = Field(3, description="Maximum retry attempts", ge=0, le=10)
    retry_delay_seconds: int = Field(300, description="Retry delay in seconds", ge=0)
    job_timeout_seconds: int = Field(3600, description="Job timeout in seconds", ge=60)
    notify_on_failure: bool = Field(True, description="Send notification on job failure")
    notify_on_success: bool = Field(False, description="Send notification on job success")
    notification_recipients: Optional[List[str]] = Field(None, description="Notification email addresses")
    extra_config: Optional[Dict[str, Any]] = Field(None, description="Additional custom settings")


class SchedulerConfigCreate(SchedulerConfigBase):
    """Schema for creating scheduler configuration."""
    config_level: ConfigLevel = Field(..., description="Configuration level")
    tenant_id: Optional[UUID] = Field(None, description="Tenant ID (required for tenant/company/branch level)")
    company_id: Optional[UUID] = Field(None, description="Company ID (required for company/branch level)")
    branch_id: Optional[UUID] = Field(None, description="Branch ID (required for branch level)")

    @validator('tenant_id')
    def validate_tenant_id(cls, v, values):
        """Validate tenant_id based on config_level."""
        if 'config_level' in values:
            level = values['config_level']
            if level in [ConfigLevel.TENANT, ConfigLevel.COMPANY, ConfigLevel.BRANCH] and not v:
                raise ValueError(f"{level} level config requires tenant_id")
        return v

    @validator('company_id')
    def validate_company_id(cls, v, values):
        """Validate company_id based on config_level."""
        if 'config_level' in values:
            level = values['config_level']
            if level in [ConfigLevel.COMPANY, ConfigLevel.BRANCH] and not v:
                raise ValueError(f"{level} level config requires company_id")
        return v

    @validator('branch_id')
    def validate_branch_id(cls, v, values):
        """Validate branch_id based on config_level."""
        if 'config_level' in values:
            level = values['config_level']
            if level == ConfigLevel.BRANCH and not v:
                raise ValueError("Branch level config requires branch_id")
        return v


class SchedulerConfigUpdate(BaseModel):
    """Schema for updating scheduler configuration."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    max_concurrent_jobs: Optional[int] = Field(None, ge=1, le=100)
    default_timezone: Optional[str] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=0)
    job_timeout_seconds: Optional[int] = Field(None, ge=60)
    notify_on_failure: Optional[bool] = None
    notify_on_success: Optional[bool] = None
    notification_recipients: Optional[List[str]] = None
    extra_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class SchedulerConfigResponse(SchedulerConfigBase):
    """Schema for scheduler configuration response."""
    id: int
    config_level: ConfigLevel
    tenant_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ========== Scheduler Job Schemas ==========

class SchedulerJobBase(BaseModel):
    """Base schema for scheduler job."""
    name: str = Field(..., description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    job_type: JobType = Field(..., description="Job type")
    is_active: bool = Field(True, description="Is job active")
    cron_expression: Optional[str] = Field(None, description="CRON expression (e.g., '0 9 * * 1')")
    timezone: str = Field("UTC", description="Timezone for scheduling")
    interval_seconds: Optional[int] = Field(None, description="Interval in seconds (alternative to CRON)", ge=60)
    start_time: Optional[datetime] = Field(None, description="Start time for interval/one-time jobs")
    end_time: Optional[datetime] = Field(None, description="End time for interval jobs")
    handler_class: Optional[str] = Field(None, description="Handler class name for custom jobs")
    handler_method: Optional[str] = Field(None, description="Handler method name")
    job_parameters: Optional[Dict[str, Any]] = Field(None, description="Job parameters")
    max_runtime_seconds: Optional[int] = Field(None, description="Maximum runtime in seconds", ge=60)
    max_retries: Optional[int] = Field(None, description="Maximum retry attempts", ge=0, le=10)
    retry_delay_seconds: Optional[int] = Field(None, description="Retry delay in seconds", ge=0)

    @validator('cron_expression')
    def validate_scheduling(cls, v, values):
        """Validate that either cron_expression or interval_seconds is provided."""
        if not v and not values.get('interval_seconds') and not values.get('start_time'):
            raise ValueError("Must provide either cron_expression, interval_seconds, or start_time")
        return v


class SchedulerJobCreate(SchedulerJobBase):
    """Schema for creating scheduler job."""
    config_id: int = Field(..., description="Configuration ID to associate with")
    tenant_id: Optional[UUID] = Field(None, description="Tenant ID for scoping")
    company_id: Optional[UUID] = Field(None, description="Company ID for scoping")
    branch_id: Optional[UUID] = Field(None, description="Branch ID for scoping")


class SchedulerJobUpdate(BaseModel):
    """Schema for updating scheduler job."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    interval_seconds: Optional[int] = Field(None, ge=60)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    handler_class: Optional[str] = None
    handler_method: Optional[str] = None
    job_parameters: Optional[Dict[str, Any]] = None
    max_runtime_seconds: Optional[int] = Field(None, ge=60)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=0)


class SchedulerJobResponse(SchedulerJobBase):
    """Schema for scheduler job response."""
    id: int
    config_id: int
    tenant_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_status: Optional[JobStatus] = None
    run_count: int
    failure_count: int
    success_count: int
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== Job Execution Schemas ==========

class SchedulerJobExecutionResponse(BaseModel):
    """Schema for job execution response."""
    id: int
    job_id: int
    tenant_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    status: JobStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    scheduled_at: datetime
    execution_time_ms: Optional[int] = None
    retry_count: int
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    worker_id: Optional[str] = None
    process_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SchedulerJobLogResponse(BaseModel):
    """Schema for job log response."""
    id: int
    execution_id: int
    log_level: str
    message: str
    log_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========== List Responses ==========

class SchedulerConfigListResponse(BaseModel):
    """Schema for listing configurations."""
    items: List[SchedulerConfigResponse]
    total: int
    skip: int
    limit: int


class SchedulerJobListResponse(BaseModel):
    """Schema for listing jobs."""
    items: List[SchedulerJobResponse]
    total: int
    skip: int
    limit: int


class SchedulerJobExecutionListResponse(BaseModel):
    """Schema for listing executions."""
    items: List[SchedulerJobExecutionResponse]
    total: int
    skip: int
    limit: int


class SchedulerJobLogListResponse(BaseModel):
    """Schema for listing logs."""
    items: List[SchedulerJobLogResponse]
    total: int
    skip: int
    limit: int


# ========== Action Schemas ==========

class JobExecuteRequest(BaseModel):
    """Schema for manual job execution request."""
    override_parameters: Optional[Dict[str, Any]] = Field(None, description="Override job parameters for this execution")


class JobExecuteResponse(BaseModel):
    """Schema for manual job execution response."""
    execution_id: int
    message: str
