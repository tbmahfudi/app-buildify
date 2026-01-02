-- Phase 1 No-Code Platform RBAC Permissions
-- Permissions for Data Model Designer, Workflow Designer, Automation System, and Lookup Configuration

-- ==================== Priority 1: Data Model Designer Permissions ====================

INSERT INTO permissions (id, code, name, description, scope, resource, action, created_at, updated_at)
VALUES
    ('dm-create-tenant', 'data_model:create:tenant', 'Create Data Models', 'Permission to create entity definitions', 'tenant', 'data_model', 'create', NOW(), NOW()),
    ('dm-read-tenant', 'data_model:read:tenant', 'Read Data Models', 'Permission to view entity definitions', 'tenant', 'data_model', 'read', NOW(), NOW()),
    ('dm-update-tenant', 'data_model:update:tenant', 'Update Data Models', 'Permission to edit entity definitions', 'tenant', 'data_model', 'update', NOW(), NOW()),
    ('dm-delete-tenant', 'data_model:delete:tenant', 'Delete Data Models', 'Permission to delete entity definitions', 'tenant', 'data_model', 'delete', NOW(), NOW()),
    ('dm-execute-tenant', 'data_model:execute:tenant', 'Execute Migrations', 'Permission to publish entities and execute migrations', 'tenant', 'data_model', 'execute', NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ==================== Priority 2: Workflow Designer Permissions ====================

INSERT INTO permissions (id, code, name, description, scope, resource, action, created_at, updated_at)
VALUES
    ('wf-create-tenant', 'workflows:create:tenant', 'Create Workflows', 'Permission to create workflow definitions', 'tenant', 'workflows', 'create', NOW(), NOW()),
    ('wf-read-tenant', 'workflows:read:tenant', 'Read Workflows', 'Permission to view workflow definitions', 'tenant', 'workflows', 'read', NOW(), NOW()),
    ('wf-update-tenant', 'workflows:update:tenant', 'Update Workflows', 'Permission to edit workflow definitions', 'tenant', 'workflows', 'update', NOW(), NOW()),
    ('wf-delete-tenant', 'workflows:delete:tenant', 'Delete Workflows', 'Permission to delete workflow definitions', 'tenant', 'workflows', 'delete', NOW(), NOW()),
    ('wf-execute-tenant', 'workflows:execute:tenant', 'Execute Workflows', 'Permission to execute workflow transitions', 'tenant', 'workflows', 'execute', NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ==================== Priority 3: Automation System Permissions ====================

INSERT INTO permissions (id, code, name, description, scope, resource, action, created_at, updated_at)
VALUES
    ('auto-create-tenant', 'automations:create:tenant', 'Create Automations', 'Permission to create automation rules', 'tenant', 'automations', 'create', NOW(), NOW()),
    ('auto-read-tenant', 'automations:read:tenant', 'Read Automations', 'Permission to view automation rules', 'tenant', 'automations', 'read', NOW(), NOW()),
    ('auto-update-tenant', 'automations:update:tenant', 'Update Automations', 'Permission to edit automation rules', 'tenant', 'automations', 'update', NOW(), NOW()),
    ('auto-delete-tenant', 'automations:delete:tenant', 'Delete Automations', 'Permission to delete automation rules', 'tenant', 'automations', 'delete', NOW(), NOW()),
    ('auto-execute-tenant', 'automations:execute:tenant', 'Execute Automations', 'Permission to execute and test automation rules', 'tenant', 'automations', 'execute', NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ==================== Priority 4: Lookup Configuration Permissions ====================

INSERT INTO permissions (id, code, name, description, scope, resource, action, created_at, updated_at)
VALUES
    ('lookup-create-tenant', 'lookups:create:tenant', 'Create Lookups', 'Permission to create lookup configurations', 'tenant', 'lookups', 'create', NOW(), NOW()),
    ('lookup-read-tenant', 'lookups:read:tenant', 'Read Lookups', 'Permission to view lookup configurations and data', 'tenant', 'lookups', 'read', NOW(), NOW()),
    ('lookup-update-tenant', 'lookups:update:tenant', 'Update Lookups', 'Permission to edit lookup configurations', 'tenant', 'lookups', 'update', NOW(), NOW()),
    ('lookup-delete-tenant', 'lookups:delete:tenant', 'Delete Lookups', 'Permission to delete lookup configurations', 'tenant', 'lookups', 'delete', NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ==================== Assign Permissions to System Admin Role ====================

-- Get the system admin role ID (assuming it exists with code 'sysadmin')
DO $$
DECLARE
    admin_role_id VARCHAR(36);
BEGIN
    SELECT id INTO admin_role_id FROM roles WHERE code = 'sysadmin' LIMIT 1;

    IF admin_role_id IS NOT NULL THEN
        -- Assign all Phase 1 permissions to sysadmin role
        INSERT INTO role_permissions (role_id, permission_id, granted_at)
        SELECT admin_role_id, id, NOW()
        FROM permissions
        WHERE code IN (
            -- Data Model Designer
            'data_model:create:tenant',
            'data_model:read:tenant',
            'data_model:update:tenant',
            'data_model:delete:tenant',
            'data_model:execute:tenant',
            -- Workflow Designer
            'workflows:create:tenant',
            'workflows:read:tenant',
            'workflows:update:tenant',
            'workflows:delete:tenant',
            'workflows:execute:tenant',
            -- Automation System
            'automations:create:tenant',
            'automations:read:tenant',
            'automations:update:tenant',
            'automations:delete:tenant',
            'automations:execute:tenant',
            -- Lookup Configuration
            'lookups:create:tenant',
            'lookups:read:tenant',
            'lookups:update:tenant',
            'lookups:delete:tenant'
        )
        ON CONFLICT (role_id, permission_id) DO NOTHING;
    END IF;
END $$;
