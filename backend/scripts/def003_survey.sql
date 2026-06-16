SELECT ed.name,
       ed.table_name,
       ed.tenant_id,
       (t.table_name IS NOT NULL) AS table_exists
FROM entity_definitions ed
LEFT JOIN information_schema.tables t
  ON t.table_name = ed.table_name
 AND t.table_schema = COALESCE(ed.schema_name, 'public')
WHERE ed.status = 'published'
ORDER BY table_exists, ed.table_name, ed.tenant_id;
