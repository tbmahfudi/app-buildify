"""
Scheduler service for managing hierarchical scheduler configurations and jobs.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.models.scheduler import (
    SchedulerConfig,
    SchedulerJob,
    SchedulerJobExecution,
    SchedulerJobLog,
    ConfigLevel,
    JobStatus,
    JobType
)


class SchedulerService:
    """Service for scheduler operations with hierarchical configuration."""

    # ========== Configuration Management ==========

    @staticmethod
    def get_effective_config(
        db: Session,
        tenant_id: Optional[uuid.UUID] = None,
        company_id: Optional[uuid.UUID] = None,
        branch_id: Optional[uuid.UUID] = None
    ) -> Optional[SchedulerConfig]:
        """
        Get the most specific configuration for the given hierarchy.

        Resolution order: Branch > Company > Tenant > System

        Args:
            db: Database session
            tenant_id: Tenant ID (optional)
            company_id: Company ID (optional)
            branch_id: Branch ID (optional)

        Returns:
            Most specific active configuration, or None if no config exists
        """
        # Try branch level first
        if branch_id and company_id and tenant_id:
            config = db.query(SchedulerConfig).filter(
                SchedulerConfig.config_level == ConfigLevel.BRANCH,
                SchedulerConfig.tenant_id == tenant_id,
                SchedulerConfig.company_id == company_id,
                SchedulerConfig.branch_id == branch_id,
                SchedulerConfig.is_active == True
            ).first()
            if config:
                return config

        # Try company level
        if company_id and tenant_id:
            config = db.query(SchedulerConfig).filter(
                SchedulerConfig.config_level == ConfigLevel.COMPANY,
                SchedulerConfig.tenant_id == tenant_id,
                SchedulerConfig.company_id == company_id,
                SchedulerConfig.is_active == True
            ).first()
            if config:
                return config

        # Try tenant level
        if tenant_id:
            config = db.query(SchedulerConfig).filter(
                SchedulerConfig.config_level == ConfigLevel.TENANT,
                SchedulerConfig.tenant_id == tenant_id,
                SchedulerConfig.is_active == True
            ).first()
            if config:
                return config

        # Fall back to system level
        config = db.query(SchedulerConfig).filter(
            SchedulerConfig.config_level == ConfigLevel.SYSTEM,
            SchedulerConfig.is_active == True
        ).first()

        return config

    @staticmethod
    def create_config(
        db: Session,
        config_level: ConfigLevel,
        name: str,
        tenant_id: Optional[uuid.UUID] = None,
        company_id: Optional[uuid.UUID] = None,
        branch_id: Optional[uuid.UUID] = None,
        created_by: Optional[uuid.UUID] = None,
        **kwargs
    ) -> SchedulerConfig:
        """
        Create a new scheduler configuration.

        Args:
            db: Database session
            config_level: Configuration level (SYSTEM, TENANT, COMPANY, BRANCH)
            name: Configuration name
            tenant_id: Tenant ID (required for TENANT, COMPANY, BRANCH levels)
            company_id: Company ID (required for COMPANY, BRANCH levels)
            branch_id: Branch ID (required for BRANCH level)
            created_by: User ID who created this config
            **kwargs: Additional configuration parameters

        Returns:
            Created configuration
        """
        # Validate hierarchy
        if config_level == ConfigLevel.BRANCH and (not tenant_id or not company_id or not branch_id):
            raise ValueError("Branch level config requires tenant_id, company_id, and branch_id")
        if config_level == ConfigLevel.COMPANY and (not tenant_id or not company_id):
            raise ValueError("Company level config requires tenant_id and company_id")
        if config_level == ConfigLevel.TENANT and not tenant_id:
            raise ValueError("Tenant level config requires tenant_id")

        config = SchedulerConfig(
            config_level=config_level,
            tenant_id=tenant_id,
            company_id=company_id,
            branch_id=branch_id,
            name=name,
            created_by=created_by,
            **kwargs
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def update_config(
        db: Session,
        config_id: int,
        **kwargs
    ) -> Optional[SchedulerConfig]:
        """
        Update an existing scheduler configuration.

        Args:
            db: Database session
            config_id: Configuration ID
            **kwargs: Fields to update

        Returns:
            Updated configuration or None if not found
        """
        config = db.query(SchedulerConfig).filter(
            SchedulerConfig.id == config_id
        ).first()

        if not config:
            return None

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        config.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def delete_config(db: Session, config_id: int) -> bool:
        """
        Delete a scheduler configuration.

        Args:
            db: Database session
            config_id: Configuration ID

        Returns:
            True if deleted, False if not found
        """
        config = db.query(SchedulerConfig).filter(
            SchedulerConfig.id == config_id
        ).first()

        if not config:
            return False

        db.delete(config)
        db.commit()
        return True

    # ========== Job Management ==========

    @staticmethod
    def create_job(
        db: Session,
        config_id: int,
        job_type: JobType,
        name: str,
        tenant_id: Optional[uuid.UUID] = None,
        company_id: Optional[uuid.UUID] = None,
        branch_id: Optional[uuid.UUID] = None,
        created_by: Optional[uuid.UUID] = None,
        **kwargs
    ) -> SchedulerJob:
        """
        Create a new scheduled job.

        Args:
            db: Database session
            config_id: Configuration ID to associate with
            job_type: Type of job
            name: Job name
            tenant_id: Tenant ID for scoping
            company_id: Company ID for scoping
            branch_id: Branch ID for scoping
            created_by: User ID who created this job
            **kwargs: Additional job parameters (cron_expression, handler_class, etc.)

        Returns:
            Created job
        """
        job = SchedulerJob(
            config_id=config_id,
            job_type=job_type,
            name=name,
            tenant_id=tenant_id,
            company_id=company_id,
            branch_id=branch_id,
            created_by=created_by,
            **kwargs
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_job(db: Session, job_id: int) -> Optional[SchedulerJob]:
        """
        Get a job by ID.

        Args:
            db: Database session
            job_id: Job ID

        Returns:
            Job or None if not found
        """
        return db.query(SchedulerJob).filter(
            SchedulerJob.id == job_id
        ).first()

    @staticmethod
    def list_jobs(
        db: Session,
        tenant_id: Optional[uuid.UUID] = None,
        company_id: Optional[uuid.UUID] = None,
        branch_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        job_type: Optional[JobType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SchedulerJob]:
        """
        List scheduled jobs with optional filters.

        Args:
            db: Database session
            tenant_id: Filter by tenant
            company_id: Filter by company
            branch_id: Filter by branch
            is_active: Filter by active status
            job_type: Filter by job type
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of jobs
        """
        query = db.query(SchedulerJob)

        if tenant_id is not None:
            query = query.filter(SchedulerJob.tenant_id == tenant_id)
        if company_id is not None:
            query = query.filter(SchedulerJob.company_id == company_id)
        if branch_id is not None:
            query = query.filter(SchedulerJob.branch_id == branch_id)
        if is_active is not None:
            query = query.filter(SchedulerJob.is_active == is_active)
        if job_type is not None:
            query = query.filter(SchedulerJob.job_type == job_type)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_job(
        db: Session,
        job_id: int,
        **kwargs
    ) -> Optional[SchedulerJob]:
        """
        Update a scheduled job.

        Args:
            db: Database session
            job_id: Job ID
            **kwargs: Fields to update

        Returns:
            Updated job or None if not found
        """
        job = db.query(SchedulerJob).filter(
            SchedulerJob.id == job_id
        ).first()

        if not job:
            return None

        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)

        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def delete_job(db: Session, job_id: int) -> bool:
        """
        Delete a scheduled job.

        Args:
            db: Database session
            job_id: Job ID

        Returns:
            True if deleted, False if not found
        """
        job = db.query(SchedulerJob).filter(
            SchedulerJob.id == job_id
        ).first()

        if not job:
            return False

        db.delete(job)
        db.commit()
        return True

    # ========== Job Execution Management ==========

    @staticmethod
    def create_execution(
        db: Session,
        job_id: int,
        tenant_id: Optional[uuid.UUID] = None,
        company_id: Optional[uuid.UUID] = None,
        branch_id: Optional[uuid.UUID] = None,
        scheduled_at: Optional[datetime] = None
    ) -> SchedulerJobExecution:
        """
        Create a new job execution record.

        Args:
            db: Database session
            job_id: Job ID
            tenant_id: Tenant ID for context
            company_id: Company ID for context
            branch_id: Branch ID for context
            scheduled_at: When this execution was scheduled

        Returns:
            Created execution record
        """
        execution = SchedulerJobExecution(
            job_id=job_id,
            tenant_id=tenant_id,
            company_id=company_id,
            branch_id=branch_id,
            scheduled_at=scheduled_at or datetime.utcnow(),
            status=JobStatus.PENDING
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution

    @staticmethod
    def update_execution_status(
        db: Session,
        execution_id: int,
        status: JobStatus,
        error_message: Optional[str] = None,
        error_traceback: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None
    ) -> Optional[SchedulerJobExecution]:
        """
        Update execution status and results.

        Args:
            db: Database session
            execution_id: Execution ID
            status: New status
            error_message: Error message if failed
            error_traceback: Error traceback if failed
            result_data: Execution results
            execution_time_ms: Execution time in milliseconds

        Returns:
            Updated execution or None if not found
        """
        execution = db.query(SchedulerJobExecution).filter(
            SchedulerJobExecution.id == execution_id
        ).first()

        if not execution:
            return None

        execution.status = status

        if status == JobStatus.RUNNING and not execution.started_at:
            execution.started_at = datetime.utcnow()
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            execution.completed_at = datetime.utcnow()
            if execution.started_at:
                execution.execution_time_ms = int(
                    (execution.completed_at - execution.started_at).total_seconds() * 1000
                )

        if error_message:
            execution.error_message = error_message
        if error_traceback:
            execution.error_traceback = error_traceback
        if result_data:
            execution.result_data = result_data
        if execution_time_ms:
            execution.execution_time_ms = execution_time_ms

        db.commit()
        db.refresh(execution)
        return execution

    @staticmethod
    def add_execution_log(
        db: Session,
        execution_id: int,
        log_level: str,
        message: str,
        log_data: Optional[Dict[str, Any]] = None
    ) -> SchedulerJobLog:
        """
        Add a log entry to a job execution.

        Args:
            db: Database session
            execution_id: Execution ID
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            log_data: Structured log data

        Returns:
            Created log entry
        """
        log = SchedulerJobLog(
            execution_id=execution_id,
            log_level=log_level,
            message=message,
            log_data=log_data
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_execution_logs(
        db: Session,
        execution_id: int,
        log_level: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SchedulerJobLog]:
        """
        Get logs for an execution.

        Args:
            db: Database session
            execution_id: Execution ID
            log_level: Filter by log level
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of log entries
        """
        query = db.query(SchedulerJobLog).filter(
            SchedulerJobLog.execution_id == execution_id
        )

        if log_level:
            query = query.filter(SchedulerJobLog.log_level == log_level)

        return query.order_by(
            SchedulerJobLog.created_at.asc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_job_executions(
        db: Session,
        job_id: int,
        status: Optional[JobStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[SchedulerJobExecution]:
        """
        Get execution history for a job.

        Args:
            db: Database session
            job_id: Job ID
            status: Filter by status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of executions
        """
        query = db.query(SchedulerJobExecution).filter(
            SchedulerJobExecution.job_id == job_id
        )

        if status:
            query = query.filter(SchedulerJobExecution.status == status)

        return query.order_by(
            SchedulerJobExecution.scheduled_at.desc()
        ).offset(skip).limit(limit).all()
