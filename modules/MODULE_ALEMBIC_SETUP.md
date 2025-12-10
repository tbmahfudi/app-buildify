# Module Alembic Setup - Standard Pattern

## Overview

This document describes the standard Alembic configuration pattern for all modules in the App Buildify platform. When modules share a database, each module gets its own version tracking table.

## Multi-Module Migration Strategy

### Version Table Naming Convention

Each module automatically gets its own Alembic version table using the pattern:
```
{module_name}_alembic_version
```

**Examples:**
- Financial Module: `financial_alembic_version`
- Inventory Module: `inventory_alembic_version`
- HR Module: `hr_alembic_version`
- Core Platform: `alembic_version` (default)

### How It Works

The version table name is dynamically generated from the `MODULE_NAME` setting in your module's config:

```python
# In alembic/env.py
VERSION_TABLE_NAME = f"{settings.MODULE_NAME}_alembic_version"

context.configure(
    connection=connection,
    target_metadata=target_metadata,
    version_table=VERSION_TABLE_NAME,  # Dynamic per module
)
```

## Setting Up a New Module

### 1. Module Configuration

Ensure your module has `MODULE_NAME` set in `app/config.py`:

```python
class Settings:
    MODULE_NAME: str = "your_module_name"  # e.g., "inventory", "hr", "crm"
    # ... other settings
```

### 2. Alembic Configuration Template

Copy this standard `alembic/env.py` template:

```python
"""
Alembic Environment Configuration for [Your Module Name]

This file is used by Alembic to run migrations.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add the parent directory to the path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import Base
from app.config import settings

# Import all models to ensure they are registered with Base
from app.models import (
    # Import all your models here
)

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = Base.metadata

# Dynamically set version table name based on module name
# This allows each module to have its own version table in a shared database
# Format: {module_name}_alembic_version
VERSION_TABLE_NAME = f"{settings.MODULE_NAME}_alembic_version"


def get_url():
    """Get database URL from settings"""
    # Convert async URL to sync URL for Alembic
    # asyncpg -> psycopg (psycopg3) for synchronous migrations
    url = settings.effective_database_url
    url = url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
    # If no driver specified, add psycopg
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://")
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=VERSION_TABLE_NAME,  # Dynamic version table per module
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table=VERSION_TABLE_NAME,  # Dynamic version table per module
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 3. Docker Compose Environment Variables

Ensure your module's docker-compose service sets the `MODULE_NAME`:

```yaml
your-module:
  container_name: app_buildify_your_module
  environment:
    MODULE_NAME: your_module_name  # Must match config.py
    DATABASE_URL: postgresql://appuser:apppass@postgres:5432/appdb
    # ... other env vars
```

## Database Architecture

### Shared Database Example

```
Database: appdb
├── alembic_version              ← Core platform migrations
├── financial_alembic_version    ← Financial module migrations
├── inventory_alembic_version    ← Inventory module migrations
├── hr_alembic_version           ← HR module migrations
│
├── [core tables]                ← Core platform tables
├── financial_*                  ← Financial module tables
├── inventory_*                  ← Inventory module tables
└── hr_*                         ← HR module tables
```

### Benefits

1. **Independent Migration History** - Each module tracks its own migrations
2. **No Conflicts** - Modules don't interfere with each other's migrations
3. **Flexible Deployment** - Deploy modules independently
4. **Clear Ownership** - Each module owns its schema changes
5. **Standard Pattern** - Same configuration works for all modules

## Running Migrations

### For Each Module Independently

```bash
# Financial Module
docker exec -it app_buildify_financial alembic upgrade head

# Inventory Module
docker exec -it app_buildify_inventory alembic upgrade head

# HR Module
docker exec -it app_buildify_hr alembic upgrade head
```

### Creating New Migrations

```bash
# Auto-generate migration based on model changes
docker exec -it app_buildify_your_module alembic revision --autogenerate -m "Description of changes"

# Create empty migration for manual changes
docker exec -it app_buildify_your_module alembic revision -m "Description of changes"
```

### Checking Migration Status

```bash
# Current revision
docker exec -it app_buildify_your_module alembic current

# Migration history
docker exec -it app_buildify_your_module alembic history

# Pending migrations
docker exec -it app_buildify_your_module alembic heads
```

## Troubleshooting

### Issue: "Can't locate revision identified by..."

**Cause:** The module's version table exists but references a non-existent revision.

**Solution:**
```bash
# Option 1: Drop the version table and start fresh
docker exec -it app_buildify_postgresql psql -U appuser -d appdb -c "DROP TABLE IF EXISTS your_module_alembic_version;"

# Option 2: Check what revision is stored
docker exec -it app_buildify_postgresql psql -U appuser -d appdb -c "SELECT * FROM your_module_alembic_version;"
```

### Issue: Wrong version table being used

**Cause:** MODULE_NAME not set correctly in environment or config.

**Solution:**
1. Check environment variable: `docker exec app_buildify_your_module env | grep MODULE_NAME`
2. Verify config.py has correct MODULE_NAME
3. Restart container after changes

## Best Practices

1. **Always set MODULE_NAME** in both config.py and docker-compose environment
2. **Use descriptive migration messages** that explain what changed
3. **Test migrations** in development before production
4. **Backup database** before running migrations in production
5. **Version your migration files** in git
6. **Don't modify** existing migration files after they've been deployed
7. **Use alembic stamp** to mark a revision without running migrations (advanced)

## Example: Creating a New Module

```bash
# 1. Create module structure
mkdir -p modules/inventory/backend
cd modules/inventory/backend

# 2. Initialize Alembic
alembic init alembic

# 3. Copy the standard env.py template from this document

# 4. Set MODULE_NAME in app/config.py
# MODULE_NAME: str = "inventory"

# 5. Add to docker-compose.yml
# environment:
#   MODULE_NAME: inventory

# 6. Create initial migration
alembic revision --autogenerate -m "Initial inventory tables"

# 7. Run migration
docker exec -it app_buildify_inventory alembic upgrade head
```

## Summary

This standard pattern ensures that all modules in the App Buildify platform can:
- Share the same database while maintaining independent migration histories
- Use identical Alembic configuration with automatic module-specific versioning
- Deploy and migrate independently without conflicts
- Follow a consistent, predictable pattern across the entire platform

The key is the **dynamic version table name** based on `MODULE_NAME`, making this a true "set it and forget it" pattern for all modules.
