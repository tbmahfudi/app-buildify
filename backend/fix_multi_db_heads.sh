#!/bin/bash
# Fix for multiple database type heads (PostgreSQL, MySQL, SQLite)

echo "=== Fixing Multiple Database Type Heads ==="
echo ""

echo "The error shows migrations for multiple databases:"
echo "  - PostgreSQL: pg_merge_all_heads"
echo "  - MySQL: mysql_a7f6e5d4c3b2, mysql_m1n2o3p4q5r6"
echo "  - SQLite: sqlite_m1n2o3p4q5r6"
echo ""

echo "Since we're using PostgreSQL, we'll target only the PostgreSQL head."
echo ""

echo "Step 1: Clear alembic_version table..."
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "DELETE FROM alembic_version;"

echo ""
echo "Step 2: Upgrade ONLY PostgreSQL migrations..."
docker exec app_buildify_backend bash -c "cd /app && alembic upgrade pg_merge_all_heads"

echo ""
echo "Step 3: Verify the version..."
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "SELECT * FROM alembic_version;"

echo ""
echo "Step 4: Check if audit_logs has the new columns..."
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'audit_logs'
AND column_name IN ('company_id', 'branch_id', 'department_id', 'request_method')
ORDER BY column_name;
"

echo ""
echo "=== Fix Complete ==="
echo ""
echo "If columns are missing, run:"
echo "  docker cp backend/fix_audit_logs_schema.sql app_buildify_postgresql:/tmp/"
echo "  docker exec app_buildify_postgresql psql -U appuser -d appdb -f /tmp/fix_audit_logs_schema.sql"
