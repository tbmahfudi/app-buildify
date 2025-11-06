#!/bin/bash
# Script to diagnose and fix Alembic version state

echo "=== Checking Alembic State ==="
echo ""

echo "1. Current version in database:"
docker exec -it app_buildify_postgresql psql -U appuser -d appdb -c "SELECT * FROM alembic_version;"

echo ""
echo "2. What Alembic thinks is the current version:"
docker exec -it app_buildify_backend bash -c "cd /app && alembic current"

echo ""
echo "3. Available heads:"
docker exec -it app_buildify_backend bash -c "cd /app && alembic heads"

echo ""
echo "4. Migration history:"
docker exec -it app_buildify_backend bash -c "cd /app && alembic history | head -20"

echo ""
echo "=== Diagnosis Complete ==="
