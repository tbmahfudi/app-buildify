-- Housekeeping: remove e2e test artifacts (entities named e2e_* and their
-- physical tables) left behind by black-box test runs. Safe: only touches the
-- e2e_* namespace used exclusively by the test suite.
DO $$
DECLARE
    t text;
BEGIN
    -- Drop leftover physical tables created by publish during tests.
    FOR t IN
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name LIKE 'e2e_%'
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS public.%I CASCADE', t);
    END LOOP;
END $$;

-- Remove the entity-definition rows and their dependents.
DELETE FROM field_definitions
 WHERE entity_id IN (SELECT id FROM entity_definitions WHERE name LIKE 'e2e_%');
DELETE FROM entity_migrations
 WHERE entity_id IN (SELECT id FROM entity_definitions WHERE name LIKE 'e2e_%');
DELETE FROM entity_definitions WHERE name LIKE 'e2e_%';
