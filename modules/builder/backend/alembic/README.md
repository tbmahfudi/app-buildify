# Builder Module - Database Migrations

This directory contains Alembic migrations for the Builder module.

## Running Migrations

### Prerequisites

1. Set the `DATABASE_URL` environment variable:
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/buildify"
```

Or if using a separate database for the builder module:
```bash
export MODULE_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/builder_module"
export DATABASE_STRATEGY="separate"
```

### Run Migrations

From the builder backend directory:

```bash
cd modules/builder/backend

# Upgrade to latest version
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history --verbose
```

### Create New Migration

```bash
cd modules/builder/backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration
alembic revision -m "description of changes"
```

## Tables Created

The initial migration creates the following tables:

- `builder_pages` - Stores builder page definitions
- `builder_page_versions` - Stores version history for pages
- `builder_alembic_version` - Tracks migration version (module-specific)

## Notes

- Each module maintains its own alembic version table (e.g., `builder_alembic_version`)
- This allows multiple modules to coexist in the same database
- Migrations are run independently per module
