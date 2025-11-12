"""
Scheduler models for configurable task scheduling.

Supports hierarchical configuration at:
- System level (applies to all tenants)
- Tenant level (applies to specific tenant)
- Company level (applies to specific company within tenant)
- Branch level (applies to specific branch within company)
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models import Base
from app.models.base import GUID


class ConfigLevel(str, enum.Enum):
    """Configuration hierarchy levels."""
    SYSTEM = "system"      # System-wide configuration
    TENANT = "tenant"      # Tenant-specific configuration
    COMPANY = "company"    # Company-specific configuration
    BRANCH = "branch"      # Branch-specific configuration


class JobStatus(str, enum.Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class JobType(str, enum.Enum):
    """Types of scheduled jobs."""
    REPORT_GENERATION = "report_generation"
    DATA_SYNC = "data_sync"
    NOTIFICATION_BATCH = "notification_batch"
    BACKUP = "backup"
    CLEANUP = "cleanup"
    CUSTOM = "custom"
    WEBHOOK = "webhook"
    API_CALL = "api_call"


class SchedulerConfig(Base):
    """
    Hierarchical scheduler configuration.

    Configuration is resolved in order of specificity:
    Branch > Company > Tenant > System

    Each level can override settings from higher levels.
    """
    __tablename__ = "scheduler_configs"

    id = Column(Integer, primary_key=True, index=True)

    # Hierarchy identifiers
    config_level = Column(SQLEnum(ConfigLevel), nullable=False, default=ConfigLevel.SYSTEM)
    tenant_id = Column(GUID, nullable=True, index=True)  # NULL for system level
    company_id = Column(GUID, nullable=True, index=True)  # NULL for system/tenant level
    branch_id = Column(GUID, nullable=True, index=True)   # NULL for system/tenant/company level

    # Configuration name and description
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Scheduler settings
    is_enabled = Column(Boolean, default=True)
    max_concurrent_jobs = Column(Integer, default=5)  # Max parallel jobs at this level
    default_timezone = Column(String(50), default="UTC")

    # Job execution settings
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=300)  # 5 minutes
    job_timeout_seconds = Column(Integer, default=3600)  # 1 hour

    # Notification settings
    notify_on_failure = Column(Boolean, default=True)
    notify_on_success = Column(Boolean, default=False)
    notification_recipients = Column(JSON, nullable=True)  # List of email addresses

    # Advanced settings
    extra_config = Column(JSON, nullable=True)  # Additional custom settings

    # Metadata
    created_by = Column(GUID, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    jobs = relationship("SchedulerJob", back_populates="config", cascade="all, delete-orphan")

    __table_args__ = (
        # Ensure unique configuration per level
        Index('idx_scheduler_config_system', 'config_level',
              unique=True,
              postgresql_where=(config_level == ConfigLevel.SYSTEM)),
        Index('idx_scheduler_config_tenant', 'config_level', 'tenant_id',
              unique=True,
              postgresql_where=(config_level == ConfigLevel.TENANT)),
        Index('idx_scheduler_config_company', 'config_level', 'tenant_id', 'company_id',
              unique=True,
              postgresql_where=(config_level == ConfigLevel.COMPANY)),
        Index('idx_scheduler_config_branch', 'config_level', 'tenant_id', 'company_id', 'branch_id',
              unique=True,
              postgresql_where=(config_level == ConfigLevel.BRANCH)),
    )


class SchedulerJob(Base):
    """
    Scheduled job definition.

    Jobs are associated with a configuration level and can be
    scheduled using CRON expressions or interval-based scheduling.
    """
    __tablename__ = "scheduler_jobs"

    id = Column(Integer, primary_key=True, index=True)

    # Configuration reference
    config_id = Column(Integer, ForeignKey("scheduler_configs.id"), nullable=False)

    # Hierarchy context (for filtering/scoping)
    tenant_id = Column(GUID, nullable=True, index=True)
    company_id = Column(GUID, nullable=True, index=True)
    branch_id = Column(GUID, nullable=True, index=True)

    # Job identification
    job_type = Column(SQLEnum(JobType), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Scheduling
    is_active = Column(Boolean, default=True)
    cron_expression = Column(String(100), nullable=True)  # e.g., "0 9 * * 1"
    timezone = Column(String(50), default="UTC")

    # Alternative: Interval-based scheduling
    interval_seconds = Column(Integer, nullable=True)  # Run every N seconds
    start_time = Column(DateTime, nullable=True)  # When to start
    end_time = Column(DateTime, nullable=True)  # When to stop

    # Job execution details
    handler_class = Column(String(255), nullable=True)  # Python class to execute
    handler_method = Column(String(100), nullable=True)  # Method name
    job_parameters = Column(JSON, nullable=True)  # Parameters to pass to handler

    # Execution constraints
    max_runtime_seconds = Column(Integer, nullable=True)  # Override config timeout
    max_retries = Column(Integer, nullable=True)  # Override config retries
    retry_delay_seconds = Column(Integer, nullable=True)  # Override config retry delay

    # Execution tracking
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    last_status = Column(SQLEnum(JobStatus), nullable=True)
    run_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)

    # Metadata
    created_by = Column(GUID, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    config = relationship("SchedulerConfig", back_populates="jobs")
    executions = relationship("SchedulerJobExecution", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_scheduler_job_active', 'is_active', 'next_run_at'),
        Index('idx_scheduler_job_tenant', 'tenant_id', 'is_active'),
        Index('idx_scheduler_job_company', 'company_id', 'is_active'),
        Index('idx_scheduler_job_branch', 'branch_id', 'is_active'),
    )


class SchedulerJobExecution(Base):
    """
    Job execution history and tracking.

    Records each execution attempt with detailed status and metrics.
    """
    __tablename__ = "scheduler_job_executions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scheduler_jobs.id"), nullable=False)

    # Execution context
    tenant_id = Column(GUID, nullable=True, index=True)
    company_id = Column(GUID, nullable=True, index=True)
    branch_id = Column(GUID, nullable=True, index=True)

    # Execution details
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    scheduled_at = Column(DateTime, default=datetime.utcnow)  # When it was supposed to run

    # Execution metrics
    execution_time_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0)

    # Results
    result_data = Column(JSON, nullable=True)  # Execution results
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)

    # Process information
    worker_id = Column(String(100), nullable=True)  # Which worker executed this
    process_id = Column(Integer, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("SchedulerJob", back_populates="executions")
    logs = relationship("SchedulerJobLog", back_populates="execution", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_scheduler_execution_status', 'status', 'scheduled_at'),
        Index('idx_scheduler_execution_job', 'job_id', 'started_at'),
    )


class SchedulerJobLog(Base):
    """
    Detailed logging for job executions.

    Captures step-by-step progress and debugging information.
    """
    __tablename__ = "scheduler_job_logs"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("scheduler_job_executions.id"), nullable=False)

    # Log details
    log_level = Column(String(20), default="INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    log_data = Column(JSON, nullable=True)  # Structured log data

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    execution = relationship("SchedulerJobExecution", back_populates="logs")

    __table_args__ = (
        Index('idx_scheduler_log_execution', 'execution_id', 'created_at'),
    )
