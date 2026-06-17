-- One-time cleanup of orphaned test scheduler data left by an interrupted test run.
-- The config with id=9a620d02-... is a TENANT-level config for techstart tenant
-- created by the e2e test fixture but never cleaned up when the run was interrupted.
DO $$
DECLARE cfg_id uuid := '9a620d02-a88a-48ef-9329-2aebeed24258';
BEGIN
  DELETE FROM scheduler_job_logs sfl
    USING scheduler_job_executions sje
    WHERE sfl.execution_id = sje.id AND sje.job_id IN (SELECT id FROM scheduler_jobs WHERE config_id = cfg_id);
  DELETE FROM scheduler_job_executions WHERE job_id IN (SELECT id FROM scheduler_jobs WHERE config_id = cfg_id);
  DELETE FROM scheduler_jobs WHERE config_id = cfg_id;
  DELETE FROM scheduler_configs WHERE id = cfg_id;
  RAISE NOTICE 'Deleted stale test config and all children';
END;
$$;
