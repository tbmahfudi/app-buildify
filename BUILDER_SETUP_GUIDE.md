# Builder Setup Guide

## Database Setup Required

The Pages Showcase and Builder features require database tables that haven't been created yet.

## Steps to Set Up

### 1. Run Database Migration

Navigate to the backend directory and run the Alembic migration:

```bash
cd backend

# Run the migration to create builder_pages table
alembic upgrade head
```

This will create the following tables:
- `builder_pages` - Stores page designs and metadata
- `builder_page_versions` - Stores version history

### 2. Seed Menu Items

After the migration, run the menu seed script to add the UI Builder menu:

```bash
# From the backend directory
python -m app.seeds.seed_builder_menu
```

This will create menu items:
- **Developer Tools** → **UI Builder**
  - Page Designer
  - Manage Pages
  - Pages Showcase

### 3. Verify Setup

Check if the tables were created:

```bash
# Connect to your database and verify
psql -d your_database_name -c "\dt builder*"
```

You should see:
```
             List of relations
 Schema |         Name          | Type  | Owner
--------+-----------------------+-------+-------
 public | builder_pages         | table | ...
 public | builder_page_versions | table | ...
```

## Troubleshooting

### If Alembic is not installed:

```bash
cd backend
pip install alembic
```

### If migration fails:

1. Check database connection in `backend/app/core/db.py`
2. Ensure PostgreSQL is running
3. Verify database user has CREATE TABLE permissions

### If seed script fails:

The seed script requires:
- SQLAlchemy installed
- Database connection configured
- Migrations already run

```bash
pip install sqlalchemy psycopg2-binary
```

## Alternative: Manual SQL

If you prefer to run SQL directly:

```sql
-- Run the SQL from the migration file
-- Located at: backend/app/alembic/versions/001_initial_builder_tables.py
-- Copy the CREATE TABLE statements and run them in your database
```

## After Setup

Once the migration and seeding are complete:

1. **Refresh the application** - Reload your browser
2. **Check the menu** - Look for Developer Tools → UI Builder
3. **Access Pages Showcase** - Navigate to `/#builder/showcase`

The showcase will now load successfully! 🎉

## Quick Setup Script

For convenience, you can run all steps at once:

```bash
#!/bin/bash
cd backend

# Run migration
echo "Running database migration..."
alembic upgrade head

# Seed menu
echo "Seeding UI Builder menu..."
python -m app.seeds.seed_builder_menu

echo "✅ Setup complete!"
```

Save this as `setup_builder.sh` and run:
```bash
chmod +x setup_builder.sh
./setup_builder.sh
```
