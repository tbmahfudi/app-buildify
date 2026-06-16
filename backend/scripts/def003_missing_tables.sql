SELECT DISTINCT ON (ed.table_name)
       ed.id, ed.name, ed.table_name, ed.tenant_id
FROM entity_definitions ed
LEFT JOIN information_schema.tables t
  ON t.table_name = ed.table_name
 AND t.table_schema = COALESCE(ed.schema_name, 'public')
WHERE ed.status = 'published'
  AND t.table_name IS NULL
ORDER BY ed.table_name, ed.id;
