-- SUPERSEDED 2026-06-16 by Alembic migration ec859b2a490c
--   (versions/postgresql/ec859b2a490c_enforce_org_tenant_id_not_null_.py),
--   which enforces NOT NULL on companies/branches/departments.tenant_id in
--   version control. Kept only as a record of the original one-off dev repair.
--
-- DEF-001 repair: /api/v1/org/companies returned 500 because an orphan company
-- row had tenant_id = NULL, which the required CompanyResponse.tenant_id (str)
-- could not serialize. The Company model already declares tenant_id nullable=False;
-- this repairs an existing DB whose column had drifted to NULL-able.
--
-- Safe: deletes only tenant-less companies (invalid per the model) that have no
-- dependent branches/departments, then enforces the model invariant.
BEGIN;

DELETE FROM companies c
WHERE c.tenant_id IS NULL
  AND NOT EXISTS (SELECT 1 FROM branches b     WHERE b.company_id = c.id)
  AND NOT EXISTS (SELECT 1 FROM departments d  WHERE d.company_id = c.id);

ALTER TABLE companies ALTER COLUMN tenant_id SET NOT NULL;

COMMIT;
