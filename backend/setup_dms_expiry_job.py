"""Register the daily DMS expiry-reminder job on the platform scheduler.

Creates (idempotently) a SYSTEM scheduler config + a WEBHOOK job that POSTs to
the DMS module's internal expiry scan once a day. DMS is standalone, so the
scheduler reaches it over the docker network at http://dms-module:9003.

Run inside the backend container:
    docker exec app_buildify_backend python setup_dms_expiry_job.py
"""
import os

from app.core.db import SessionLocal
from app.models.scheduler import ConfigLevel, JobType, SchedulerConfig, SchedulerJob
from app.services.scheduler_service import SchedulerService

JOB_NAME = "DMS document expiry reminders"
CONFIG_NAME = "DMS"
SCAN_URL = os.getenv("DMS_SCAN_URL", "http://dms-module:9003/api/v1/dms/expiry/scan")
SECRET = os.getenv("DMS_INTERNAL_SECRET", "dev-dms-internal-secret")
CRON = os.getenv("DMS_EXPIRY_CRON", "0 9 * * *")  # daily at 09:00


def main():
    db = SessionLocal()
    try:
        config = (
            db.query(SchedulerConfig)
            .filter(SchedulerConfig.name == CONFIG_NAME, SchedulerConfig.config_level == ConfigLevel.SYSTEM)
            .first()
        )
        if not config:
            config = SchedulerService.create_config(
                db, config_level=ConfigLevel.SYSTEM, name=CONFIG_NAME,
                description="System jobs for the Document Management module",
            )
            print(f"+ created scheduler config {config.id}")
        else:
            print(f"• scheduler config exists {config.id}")

        existing = db.query(SchedulerJob).filter(SchedulerJob.name == JOB_NAME).first()
        params = {
            "url": SCAN_URL,
            "method": "POST",
            "headers": {"X-DMS-Internal-Secret": SECRET},
            "data": {},
        }
        if existing:
            existing.cron_expression = CRON
            existing.job_parameters = params
            existing.is_active = True
            db.commit()
            print(f"• updated job {existing.id} (cron={CRON})")
        else:
            job = SchedulerService.create_job(
                db, config_id=config.id, job_type=JobType.WEBHOOK, name=JOB_NAME,
                description="Daily 30/7/1/0-day document expiry reminders for DMS",
                cron_expression=CRON, timezone="UTC", job_parameters=params, is_active=True,
            )
            print(f"+ created webhook job {job.id} (cron={CRON}) -> {SCAN_URL}")
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
