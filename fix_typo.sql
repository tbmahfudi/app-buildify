-- Fix typo in field_definitions: is_acrive -> is_active
UPDATE field_definitions 
SET name = 'is_active' 
WHERE name = 'is_acrive';
