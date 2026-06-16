SELECT (t.table_name IS NOT NULL) AS table_exists, count(*)
FROM entity_definitions ed
LEFT JOIN information_schema.tables t
  ON t.table_name = ed.table_name AND t.table_schema = COALESCE(ed.schema_name, 'public')
WHERE ed.status = 'published'
GROUP BY 1 ORDER BY 1;
