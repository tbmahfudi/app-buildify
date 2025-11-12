"""
Scheduler API router.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.scheduler import JobStatus, JobType
from app.models.user import User
from app.schemas.scheduler import (
    JobExecuteRequest,
    JobExecuteResponse,
    SchedulerConfigCreate,
    SchedulerConfigListResponse,
    SchedulerConfigResponse,
    SchedulerConfigUpdate,
    SchedulerJobCreate,
    SchedulerJobExecutionListResponse,
    SchedulerJobExecutionResponse,
    SchedulerJobListResponse,
    SchedulerJobLogListResponse,
    SchedulerJobLogResponse,
    SchedulerJobResponse,
    SchedulerJobUpdate,
)
from app.services.scheduler_service import SchedulerService

router = APIRouter(prefix="/scheduler", tags=["scheduler"])
logger = logging.getLogger(__name__)


# ========== Configuration Endpoints ==========

@router.post("/configs", response_model=SchedulerConfigResponse, status_code=status.HTTP_201_CREATED)
def create_scheduler_config(
    config_data: SchedulerConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new scheduler configuration.

    Requires appropriate permissions based on configuration level:
    - SYSTEM: Admin only
    - TENANT: Tenant admin
    - COMPANY: Company admin
    - BRANCH: Branch admin
    """
    try:
        config = SchedulerService.create_config(
            db=db,
            config_level=config_data.config_level,
            name=config_data.name,
            tenant_id=config_data.tenant_id,
            company_id=config_data.company_id,
            branch_id=config_data.branch_id,
            created_by=current_user.id,
            description=config_data.description,
            is_enabled=config_data.is_enabled,
            max_concurrent_jobs=config_data.max_concurrent_jobs,
            default_timezone=config_data.default_timezone,
            max_retries=config_data.max_retries,
            retry_delay_seconds=config_data.retry_delay_seconds,
            job_timeout_seconds=config_data.job_timeout_seconds,
            notify_on_failure=config_data.notify_on_failure,
            notify_on_success=config_data.notify_on_success,
            notification_recipients=config_data.notification_recipients,
            extra_config=config_data.extra_config
        )
        return config
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/configs/effective", response_model=SchedulerConfigResponse)
def get_effective_config(
    tenant_id: Optional[UUID] = Query(None, description="Tenant ID"),
    company_id: Optional[UUID] = Query(None, description="Company ID"),
    branch_id: Optional[UUID] = Query(None, description="Branch ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the effective scheduler configuration for the given hierarchy.

    Resolution order: Branch > Company > Tenant > System
    """
    # Default to current user's context if not specified
    if tenant_id is None:
        tenant_id = current_user.tenant_id

    config = SchedulerService.get_effective_config(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        branch_id=branch_id
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scheduler configuration found"
        )

    return config


@router.get("/configs/{config_id}", response_model=SchedulerConfigResponse)
def get_scheduler_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific scheduler configuration."""
    config = db.query(SchedulerConfig).filter(
        SchedulerConfig.id == config_id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )

    return config


@router.put("/configs/{config_id}", response_model=SchedulerConfigResponse)
def update_scheduler_config(
    config_id: int,
    config_data: SchedulerConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a scheduler configuration."""
    # Filter out None values
    update_data = {k: v for k, v in config_data.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    config = SchedulerService.update_config(db=db, config_id=config_id, **update_data)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )

    return config


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduler_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a scheduler configuration."""
    deleted = SchedulerService.delete_config(db=db, config_id=config_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )


# ========== Job Endpoints ==========

@router.post("/jobs", response_model=SchedulerJobResponse, status_code=status.HTTP_201_CREATED)
def create_scheduler_job(
    job_data: SchedulerJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new scheduled job."""
    try:
        job = SchedulerService.create_job(
            db=db,
            config_id=job_data.config_id,
            job_type=job_data.job_type,
            name=job_data.name,
            tenant_id=job_data.tenant_id or current_user.tenant_id,
            company_id=job_data.company_id,
            branch_id=job_data.branch_id,
            created_by=current_user.id,
            description=job_data.description,
            is_active=job_data.is_active,
            cron_expression=job_data.cron_expression,
            timezone=job_data.timezone,
            interval_seconds=job_data.interval_seconds,
            start_time=job_data.start_time,
            end_time=job_data.end_time,
            handler_class=job_data.handler_class,
            handler_method=job_data.handler_method,
            job_parameters=job_data.job_parameters,
            max_runtime_seconds=job_data.max_runtime_seconds,
            max_retries=job_data.max_retries,
            retry_delay_seconds=job_data.retry_delay_seconds
        )
        return job
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/jobs", response_model=SchedulerJobListResponse)
def list_scheduler_jobs(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    company_id: Optional[UUID] = Query(None, description="Filter by company"),
    branch_id: Optional[UUID] = Query(None, description="Filter by branch"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    job_type: Optional[JobType] = Query(None, description="Filter by job type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List scheduled jobs with optional filters."""
    # Default to current user's tenant if not specified
    if tenant_id is None:
        tenant_id = current_user.tenant_id

    jobs = SchedulerService.list_jobs(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        branch_id=branch_id,
        is_active=is_active,
        job_type=job_type,
        skip=skip,
        limit=limit
    )

    # Get total count
    from app.models.scheduler import SchedulerJob
    query = db.query(SchedulerJob)
    if tenant_id:
        query = query.filter(SchedulerJob.tenant_id == tenant_id)
    if company_id:
        query = query.filter(SchedulerJob.company_id == company_id)
    if branch_id:
        query = query.filter(SchedulerJob.branch_id == branch_id)
    if is_active is not None:
        query = query.filter(SchedulerJob.is_active == is_active)
    if job_type:
        query = query.filter(SchedulerJob.job_type == job_type)
    total = query.count()

    return {
        "items": jobs,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/jobs/{job_id}", response_model=SchedulerJobResponse)
def get_scheduler_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific scheduled job."""
    job = SchedulerService.get_job(db=db, job_id=job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Check tenant access
    if job.tenant_id and job.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return job


@router.put("/jobs/{job_id}", response_model=SchedulerJobResponse)
def update_scheduler_job(
    job_id: int,
    job_data: SchedulerJobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a scheduled job."""
    # Filter out None values
    update_data = {k: v for k, v in job_data.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    job = SchedulerService.update_job(db=db, job_id=job_id, **update_data)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # TODO: Notify scheduler engine to reload the job

    return job


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduler_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a scheduled job."""
    deleted = SchedulerService.delete_job(db=db, job_id=job_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # TODO: Notify scheduler engine to remove the job


@router.post("/jobs/{job_id}/execute", response_model=JobExecuteResponse)
def execute_job_manually(
    job_id: int,
    request: JobExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger a job execution."""
    job = SchedulerService.get_job(db=db, job_id=job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Check tenant access
    if job.tenant_id and job.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Create execution record
    execution = SchedulerService.create_execution(
        db=db,
        job_id=job_id,
        tenant_id=job.tenant_id,
        company_id=job.company_id,
        branch_id=job.branch_id
    )

    # TODO: Trigger immediate job execution in scheduler engine

    return {
        "execution_id": execution.id,
        "message": "Job execution triggered"
    }


# ========== Execution Endpoints ==========

@router.get("/jobs/{job_id}/executions", response_model=SchedulerJobExecutionListResponse)
def list_job_executions(
    job_id: int,
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get execution history for a job."""
    job = SchedulerService.get_job(db=db, job_id=job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    executions = SchedulerService.get_job_executions(
        db=db,
        job_id=job_id,
        status=status,
        skip=skip,
        limit=limit
    )

    # Get total count
    from app.models.scheduler import SchedulerJobExecution
    query = db.query(SchedulerJobExecution).filter(SchedulerJobExecution.job_id == job_id)
    if status:
        query = query.filter(SchedulerJobExecution.status == status)
    total = query.count()

    return {
        "items": executions,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/executions/{execution_id}", response_model=SchedulerJobExecutionResponse)
def get_job_execution(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific job execution."""
    from app.models.scheduler import SchedulerJobExecution

    execution = db.query(SchedulerJobExecution).filter(
        SchedulerJobExecution.id == execution_id
    ).first()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    return execution


@router.get("/executions/{execution_id}/logs", response_model=SchedulerJobLogListResponse)
def get_execution_logs(
    execution_id: int,
    log_level: Optional[str] = Query(None, description="Filter by log level"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get logs for a job execution."""
    logs = SchedulerService.get_execution_logs(
        db=db,
        execution_id=execution_id,
        log_level=log_level,
        skip=skip,
        limit=limit
    )

    # Get total count
    from app.models.scheduler import SchedulerJobLog
    query = db.query(SchedulerJobLog).filter(SchedulerJobLog.execution_id == execution_id)
    if log_level:
        query = query.filter(SchedulerJobLog.log_level == log_level)
    total = query.count()

    return {
        "items": logs,
        "total": total,
        "skip": skip,
        "limit": limit
    }


# Import required for endpoint
from app.models.scheduler import SchedulerConfig
