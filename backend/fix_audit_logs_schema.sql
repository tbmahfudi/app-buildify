-- Fix audit_logs table schema
-- Add missing columns that are in the model but not in the database

-- Add missing columns
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS company_id UUID;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS branch_id UUID;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS department_id UUID;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS request_method VARCHAR(10);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS request_path VARCHAR(500);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS error_code VARCHAR(50);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS duration_ms VARCHAR(20);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_audit_logs_company_id ON audit_logs(company_id);
CREATE INDEX IF NOT EXISTS ix_audit_company_created ON audit_logs(company_id, created_at);
CREATE INDEX IF NOT EXISTS ix_audit_tenant_company ON audit_logs(tenant_id, company_id);

-- Verify the changes
\d audit_logs
