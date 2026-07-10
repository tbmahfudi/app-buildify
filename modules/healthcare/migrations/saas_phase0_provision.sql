-- SaaS tenancy migration — PHASE 0 (provision target structure, NON-DESTRUCTIVE, reversible)
-- migration-plan-saas-tenancy-01 §Phase 0. Creates the shared SAAS tenant + a Company per legacy
-- clinic + one Branch (clinic site) each, and a scratch mapping table. Touches NO existing hc_* data.
-- Idempotent (fixed UUIDs + ON CONFLICT). Apply to appdb.

BEGIN;

-- Shared SaaS tenant (the single tenant that will hold all clinics)
INSERT INTO tenants (id, code, name) VALUES
  ('5aa50000-0000-4000-8000-000000000001', 'SAAS', 'Healthcare SaaS (Shared)')
ON CONFLICT (id) DO NOTHING;

-- One Company per legacy clinic, under the shared tenant (owner = clinic business)
INSERT INTO companies (id, code, name, tenant_id) VALUES
  ('c0000001-0000-4000-8000-000000000001', 'MEDCARE',    'MedCare',    '5aa50000-0000-4000-8000-000000000001'),
  ('c0000002-0000-4000-8000-000000000001', 'HEALTHPOINT','HealthPoint','5aa50000-0000-4000-8000-000000000001')
ON CONFLICT (id) DO NOTHING;

-- One platform Branch (clinic site) per Company
INSERT INTO branches (id, company_id, code, name, tenant_id) VALUES
  ('b0000001-0000-4000-8000-000000000001', 'c0000001-0000-4000-8000-000000000001', 'MAIN', 'MedCare Main Clinic',    '5aa50000-0000-4000-8000-000000000001'),
  ('b0000002-0000-4000-8000-000000000001', 'c0000002-0000-4000-8000-000000000001', 'MAIN', 'HealthPoint Main Clinic','5aa50000-0000-4000-8000-000000000001')
ON CONFLICT (id) DO NOTHING;

-- Scratch mapping table that drives Phases 2–3 (old per-clinic tenant -> new Company/Branch/shared tenant)
CREATE TABLE IF NOT EXISTS saas_migration_map (
    old_tenant_id  VARCHAR(36) PRIMARY KEY,
    clinic         TEXT        NOT NULL,
    new_company_id VARCHAR(36) NOT NULL,
    new_branch_id  VARCHAR(36) NOT NULL,
    saas_tenant_id VARCHAR(36) NOT NULL
);

INSERT INTO saas_migration_map (old_tenant_id, clinic, new_company_id, new_branch_id, saas_tenant_id) VALUES
  ('50f10a52-66ad-4c38-a0b2-6015db8dd42c', 'MEDCARE',    'c0000001-0000-4000-8000-000000000001', 'b0000001-0000-4000-8000-000000000001', '5aa50000-0000-4000-8000-000000000001'),
  ('f9026af6-4951-44c5-a84f-fc9331848b12', 'HEALTHPOINT','c0000002-0000-4000-8000-000000000001', 'b0000002-0000-4000-8000-000000000001', '5aa50000-0000-4000-8000-000000000001')
ON CONFLICT (old_tenant_id) DO NOTHING;

COMMIT;
