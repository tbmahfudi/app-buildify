"""
Scheduler execution engine for running scheduled jobs.

This module provides the background worker that monitors and executes scheduled jobs
using APScheduler with hierarchical configuration support.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
import traceback
import os
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.scheduler import SchedulerJob, JobStatus, JobType
from app.services.scheduler_service import SchedulerService

logger = logging.getLogger(__name__)


class SchedulerEngine:
    """
    Scheduler execution engine with hierarchical configuration.

    Manages scheduled job execution using APScheduler with support for:
    - CRON-based scheduling
    - Interval-based scheduling
    - One-time scheduled execution
    - Hierarchical configuration (System, Tenant, Company, Branch)
    - Execution tracking and logging
    - Retry logic
    """

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the scheduler engine.

        Args:
            db_url: Database URL (defaults to settings.DATABASE_URL)
        """
        self.db_url = db_url or settings.DATABASE_URL
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # Initialize APScheduler
        self.scheduler = AsyncIOScheduler(
            jobstores={
                'default': MemoryJobStore()
            },
            executors={
                'default': ThreadPoolExecutor(10)
            },
            job_defaults={
                'coalesce': False,
                'max_instances': 3,
                'misfire_grace_time': 300  # 5 minutes
            }
        )

        # Job handlers registry
        self.job_handlers: Dict[str, Callable] = {}

        # Worker ID for tracking
        self.worker_id = f"worker-{os.getpid()}"

        logger.info(f"Scheduler engine initialized with worker ID: {self.worker_id}")

    def register_handler(self, handler_name: str, handler_func: Callable):
        """
        Register a job handler function.

        Args:
            handler_name: Name to identify the handler
            handler_func: Callable that executes the job
        """
        self.job_handlers[handler_name] = handler_func
        logger.info(f"Registered handler: {handler_name}")

    def start(self):
        """Start the scheduler engine."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler engine started")

            # Load all active jobs from database
            self._load_jobs_from_database()

    def shutdown(self):
        """Shutdown the scheduler engine gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler engine stopped")

    def _load_jobs_from_database(self):
        """Load all active jobs from the database and schedule them."""
        db = self.SessionLocal()
        try:
            service = SchedulerService()
            jobs = service.list_jobs(db, is_active=True, limit=1000)

            for job in jobs:
                try:
                    self._schedule_job(job)
                except Exception as e:
                    logger.error(f"Error scheduling job {job.id}: {str(e)}")

            logger.info(f"Loaded {len(jobs)} active jobs from database")
        finally:
            db.close()

    def _schedule_job(self, job: SchedulerJob):
        """
        Schedule a single job in APScheduler.

        Args:
            job: SchedulerJob instance to schedule
        """
        job_id = f"job_{job.id}"

        # Remove existing job if it exists
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        # Determine trigger
        trigger = None

        if job.cron_expression:
            # CRON-based scheduling
            trigger = CronTrigger.from_crontab(
                job.cron_expression,
                timezone=job.timezone
            )
        elif job.interval_seconds:
            # Interval-based scheduling
            trigger = IntervalTrigger(
                seconds=job.interval_seconds,
                timezone=job.timezone,
                start_date=job.start_time,
                end_date=job.end_time
            )
        elif job.start_time:
            # One-time scheduled execution
            trigger = DateTrigger(
                run_date=job.start_time,
                timezone=job.timezone
            )

        if trigger:
            self.scheduler.add_job(
                func=self._execute_job,
                trigger=trigger,
                args=[job.id],
                id=job_id,
                name=job.name,
                replace_existing=True
            )
            logger.info(f"Scheduled job: {job.name} (ID: {job.id})")

    def add_job(self, job_id: int):
        """
        Add or update a job in the scheduler.

        Args:
            job_id: Job ID to add/update
        """
        db = self.SessionLocal()
        try:
            job = SchedulerService.get_job(db, job_id)
            if job and job.is_active:
                self._schedule_job(job)
        finally:
            db.close()

    def remove_job(self, job_id: int):
        """
        Remove a job from the scheduler.

        Args:
            job_id: Job ID to remove
        """
        apscheduler_job_id = f"job_{job_id}"
        if self.scheduler.get_job(apscheduler_job_id):
            self.scheduler.remove_job(apscheduler_job_id)
            logger.info(f"Removed job {job_id} from scheduler")

    def _execute_job(self, job_id: int):
        """
        Execute a scheduled job.

        Args:
            job_id: Job ID to execute
        """
        db = self.SessionLocal()
        execution_id = None

        try:
            # Get job details
            job = SchedulerService.get_job(db, job_id)
            if not job or not job.is_active:
                logger.warning(f"Job {job_id} not found or inactive")
                return

            # Get effective configuration
            config = SchedulerService.get_effective_config(
                db,
                tenant_id=job.tenant_id,
                company_id=job.company_id,
                branch_id=job.branch_id
            )

            if not config or not config.is_enabled:
                logger.info(f"Scheduler disabled for job {job_id}")
                return

            # Check concurrent job limit
            running_count = db.query(SchedulerJobExecution).filter(
                SchedulerJobExecution.status == JobStatus.RUNNING
            ).count()

            if running_count >= config.max_concurrent_jobs:
                logger.warning(
                    f"Max concurrent jobs ({config.max_concurrent_jobs}) reached, "
                    f"skipping job {job_id}"
                )
                return

            # Create execution record
            execution = SchedulerService.create_execution(
                db,
                job_id=job_id,
                tenant_id=job.tenant_id,
                company_id=job.company_id,
                branch_id=job.branch_id,
                scheduled_at=datetime.utcnow()
            )
            execution_id = execution.id

            # Update job last run
            job.last_run_at = datetime.utcnow()
            job.run_count += 1
            db.commit()

            # Add log entry
            SchedulerService.add_execution_log(
                db,
                execution_id,
                "INFO",
                f"Job execution started by worker {self.worker_id}"
            )

            # Update status to running
            SchedulerService.update_execution_status(
                db,
                execution_id,
                JobStatus.RUNNING
            )

            # Execute the job with retry logic
            max_retries = job.max_retries if job.max_retries is not None else config.max_retries
            retry_delay = job.retry_delay_seconds if job.retry_delay_seconds is not None else config.retry_delay_seconds

            result = None
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    # Execute the job handler
                    result = self._run_job_handler(db, job, execution_id)

                    # Success - update status
                    SchedulerService.update_execution_status(
                        db,
                        execution_id,
                        JobStatus.COMPLETED,
                        result_data=result
                    )

                    SchedulerService.add_execution_log(
                        db,
                        execution_id,
                        "INFO",
                        "Job completed successfully"
                    )

                    # Update job success count
                    job.success_count += 1
                    job.last_status = JobStatus.COMPLETED
                    db.commit()

                    # Send success notification if configured
                    if config.notify_on_success:
                        self._send_notification(db, job, execution, config, success=True)

                    break  # Success, exit retry loop

                except Exception as e:
                    last_error = e
                    error_trace = traceback.format_exc()

                    SchedulerService.add_execution_log(
                        db,
                        execution_id,
                        "ERROR",
                        f"Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}",
                        log_data={"traceback": error_trace}
                    )

                    if attempt < max_retries:
                        logger.warning(
                            f"Job {job_id} failed (attempt {attempt + 1}), "
                            f"retrying in {retry_delay} seconds"
                        )
                        asyncio.sleep(retry_delay)
                    else:
                        # Final failure
                        SchedulerService.update_execution_status(
                            db,
                            execution_id,
                            JobStatus.FAILED,
                            error_message=str(e),
                            error_traceback=error_trace
                        )

                        # Update job failure count
                        job.failure_count += 1
                        job.last_status = JobStatus.FAILED
                        db.commit()

                        # Send failure notification if configured
                        if config.notify_on_failure:
                            self._send_notification(db, job, execution, config, success=False)

        except Exception as e:
            logger.error(f"Unexpected error executing job {job_id}: {str(e)}")
            if execution_id:
                SchedulerService.update_execution_status(
                    db,
                    execution_id,
                    JobStatus.FAILED,
                    error_message=str(e),
                    error_traceback=traceback.format_exc()
                )
        finally:
            db.close()

    def _run_job_handler(
        self,
        db: Session,
        job: SchedulerJob,
        execution_id: int
    ) -> Dict[str, Any]:
        """
        Execute the actual job handler.

        Args:
            db: Database session
            job: Job to execute
            execution_id: Execution ID for logging

        Returns:
            Job execution results

        Raises:
            Exception: If job execution fails
        """
        # Built-in job type handlers
        if job.job_type == JobType.REPORT_GENERATION:
            return self._handle_report_generation(db, job, execution_id)
        elif job.job_type == JobType.WEBHOOK:
            return self._handle_webhook(db, job, execution_id)
        elif job.job_type == JobType.CUSTOM:
            # Use registered handler
            if job.handler_class and job.handler_class in self.job_handlers:
                handler = self.job_handlers[job.handler_class]
                return handler(db, job, execution_id)
            else:
                raise ValueError(f"No handler registered for: {job.handler_class}")
        else:
            raise ValueError(f"Unsupported job type: {job.job_type}")

    def _handle_report_generation(
        self,
        db: Session,
        job: SchedulerJob,
        execution_id: int
    ) -> Dict[str, Any]:
        """Handle report generation jobs."""
        # This would integrate with the existing report service
        SchedulerService.add_execution_log(
            db,
            execution_id,
            "INFO",
            "Report generation job - implementation pending"
        )
        return {"status": "success", "message": "Report generation placeholder"}

    def _handle_webhook(
        self,
        db: Session,
        job: SchedulerJob,
        execution_id: int
    ) -> Dict[str, Any]:
        """Handle webhook jobs."""
        import requests

        params = job.job_parameters or {}
        url = params.get("url")
        method = params.get("method", "POST")
        headers = params.get("headers", {})
        data = params.get("data", {})

        if not url:
            raise ValueError("Webhook URL not specified in job parameters")

        SchedulerService.add_execution_log(
            db,
            execution_id,
            "INFO",
            f"Sending {method} request to {url}"
        )

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            timeout=30
        )

        response.raise_for_status()

        return {
            "status_code": response.status_code,
            "response": response.json() if response.content else None
        }

    def _send_notification(
        self,
        db: Session,
        job: SchedulerJob,
        execution: Any,
        config: Any,
        success: bool
    ):
        """Send notification about job execution."""
        # This would integrate with the existing notification service
        status = "succeeded" if success else "failed"
        logger.info(
            f"Notification: Job '{job.name}' (ID: {job.id}) {status}"
        )
