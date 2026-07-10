-- hcs_003 — Room assignment on weekly provider schedules + per-date overrides
-- (substitution / unavailability). Idempotent; safe to re-run. Applied directly
-- to the shared appdb (dev). Tables: hcs_provider_schedules (+room_id),
-- hcs_schedule_overrides (new). Convention: day_of_week 0=Sunday..6=Saturday.

-- 1. Room on the weekly schedule block (which room the doctor practices in).
ALTER TABLE hcs_provider_schedules
    ADD COLUMN IF NOT EXISTS room_id VARCHAR(36) NULL REFERENCES hc_rooms(id);
CREATE INDEX IF NOT EXISTS idx_hcs_psch_room ON hcs_provider_schedules(room_id);

-- 2. Per-date overrides: on a specific future date the scheduled doctor is
--    unavailable, optionally covered by a substitute doctor for that day.
CREATE TABLE IF NOT EXISTS hcs_schedule_overrides (
    id                      VARCHAR(36) PRIMARY KEY,
    tenant_id               VARCHAR(36) NOT NULL,
    branch_id               VARCHAR(36) NOT NULL REFERENCES hc_branches(id),
    schedule_id             VARCHAR(36) NOT NULL REFERENCES hcs_provider_schedules(id) ON DELETE CASCADE,
    override_date           DATE        NOT NULL,
    status                  VARCHAR(20) NOT NULL,           -- 'unavailable' | 'substituted'
    substitute_provider_id  VARCHAR(36) NULL REFERENCES hc_providers(id),
    reason                  TEXT        NULL,
    created_by              VARCHAR(36) NULL,
    created_at              TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP   NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_hcs_ovr_status CHECK (status IN ('unavailable','substituted')),
    CONSTRAINT ck_hcs_ovr_sub CHECK (
        (status = 'substituted' AND substitute_provider_id IS NOT NULL) OR
        (status = 'unavailable' AND substitute_provider_id IS NULL)
    ),
    CONSTRAINT uq_hcs_ovr_sched_date UNIQUE (schedule_id, override_date)
);
CREATE INDEX IF NOT EXISTS idx_hcs_ovr_tenant       ON hcs_schedule_overrides(tenant_id);
CREATE INDEX IF NOT EXISTS idx_hcs_ovr_branch_date  ON hcs_schedule_overrides(branch_id, override_date);
CREATE INDEX IF NOT EXISTS idx_hcs_ovr_schedule     ON hcs_schedule_overrides(schedule_id);
