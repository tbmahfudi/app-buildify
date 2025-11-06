#!/bin/bash
# Script to fix Alembic multiple heads error
# This ensures the new merge migration is detected

echo "=== Alembic Multiple Heads Fix ==="
echo ""

# Step 1: Restart backend to ensure new migration files are loaded
echo "Step 1: Restarting backend container..."
docker-compose -f docker-compose.dev.yml restart backend
echo "Waiting for backend to start..."
sleep 5

# Step 2: Check what Alembic sees
echo ""
echo "Step 2: Checking Alembic heads..."
docker exec -it app_buildify_backend bash -c "cd /app && alembic heads"

# Step 3: Show current revision in database
echo ""
echo "Step 3: Checking current database revision..."
docker exec -it app_buildify_backend bash -c "cd /app && alembic current"

# Step 4: Attempt upgrade
echo ""
echo "Step 4: Running migration..."
docker exec -it app_buildify_backend bash -c "cd /app && alembic upgrade head"

echo ""
echo "=== Migration Complete ==="
