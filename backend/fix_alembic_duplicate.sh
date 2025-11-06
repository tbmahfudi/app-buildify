#!/bin/bash
# Script to fix Alembic duplicate key error

echo "=== Fixing Alembic Duplicate Key Error ==="
echo ""

echo "Step 1: Checking current state..."
CURRENT_VERSION=$(docker exec app_buildify_postgresql psql -U appuser -d appdb -t -c "SELECT version_num FROM alembic_version;")
echo "Database shows version: $CURRENT_VERSION"

echo ""
echo "Step 2: Clearing the alembic_version table..."
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "DELETE FROM alembic_version;"

echo ""
echo "Step 3: Stamping with the merge head..."
docker exec app_buildify_backend bash -c "cd /app && alembic stamp pg_merge_all_heads"

echo ""
echo "Step 4: Verifying the fix..."
docker exec app_buildify_postgresql psql -U appuser -d appdb -c "SELECT * FROM alembic_version;"

echo ""
echo "Step 5: Now try upgrading to apply audit_logs changes..."
docker exec app_buildify_backend bash -c "cd /app && alembic upgrade head"

echo ""
echo "=== Fix Complete ==="
echo ""
echo "If you still see errors, you can manually apply the SQL changes:"
echo "  docker cp backend/fix_audit_logs_schema.sql app_buildify_postgresql:/tmp/"
echo "  docker exec app_buildify_postgresql psql -U appuser -d appdb -f /tmp/fix_audit_logs_schema.sql"
