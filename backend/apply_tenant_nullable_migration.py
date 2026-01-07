#!/usr/bin/env python3
"""
Apply the tenant_id nullable migration to fix platform-level templates.

This script directly applies the SQL ALTER COLUMN statements to make tenant_id
nullable in all no-code platform tables.

Usage:
    python apply_tenant_nullable_migration.py [database_url]

Examples:
    python apply_tenant_nullable_migration.py
    python apply_tenant_nullable_migration.py postgresql://user:pass@localhost:5432/dbname
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

try:
    from sqlalchemy import create_engine, text
    from app.core.config import get_settings
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install: pip install sqlalchemy psycopg2-binary python-dotenv pydantic pydantic-settings")
    sys.exit(1)


def get_database_url():
    """Get database URL from various sources"""
    if len(sys.argv) > 1:
        return sys.argv[1]

    db_url = os.getenv('SQLALCHEMY_DATABASE_URL') or os.getenv('DATABASE_URL')
    if db_url:
        return db_url

    try:
        settings = get_settings()
        return settings.SQLALCHEMY_DATABASE_URL
    except Exception as e:
        print(f"Warning: Could not load settings: {e}")
        return None


def apply_migration(db_url: str):
    """Apply the tenant_id nullable migration"""
    print("\n" + "="*70)
    print("Applying tenant_id Nullable Migration")
    print("="*70)
    print(f"Database: {db_url[:50]}..." if len(db_url) > 50 else f"Database: {db_url}")
    print("="*70 + "\n")

    try:
        engine = create_engine(db_url)

        # List of tables and their order
        tables = [
            # Parent tables
            ('entity_definitions', 'Parent table for data models'),
            ('workflow_definitions', 'Parent table for workflows'),
            ('automation_rules', 'Parent table for automation rules'),
            ('lookup_configurations', 'Parent table for lookups'),
            # Child tables - Data Model
            ('field_definitions', 'Fields for data models'),
            ('relationship_definitions', 'Relationships between entities'),
            ('index_definitions', 'Database indexes'),
            ('entity_migrations', 'Entity migration history'),
            # Child tables - Workflow
            ('workflow_states', 'Workflow states'),
            ('workflow_transitions', 'Workflow transitions'),
            ('workflow_instances', 'Workflow instances'),
            ('workflow_history', 'Workflow history'),
            # Child tables - Automation
            ('automation_executions', 'Automation execution logs'),
            ('webhook_configs', 'Webhook configurations'),
            # Child tables - Lookup
            ('lookup_cache', 'Lookup cache'),
            ('cascading_lookup_rules', 'Cascading lookup rules'),
        ]

        with engine.begin() as conn:
            print("Starting migration...\n")

            for table_name, description in tables:
                try:
                    # Check if table exists
                    result = conn.execute(text(
                        "SELECT EXISTS (SELECT FROM information_schema.tables "
                        "WHERE table_name = :table_name)"
                    ), {"table_name": table_name})

                    if not result.scalar():
                        print(f"⊘ Skipping {table_name:30} (table does not exist)")
                        continue

                    # Check current nullability
                    result = conn.execute(text(
                        "SELECT is_nullable FROM information_schema.columns "
                        "WHERE table_name = :table_name AND column_name = 'tenant_id'"
                    ), {"table_name": table_name})

                    row = result.fetchone()
                    if not row:
                        print(f"⊘ Skipping {table_name:30} (no tenant_id column)")
                        continue

                    current_nullable = row[0]

                    if current_nullable == 'YES':
                        print(f"✓ Skipping {table_name:30} (already nullable)")
                        continue

                    # Apply the ALTER COLUMN
                    print(f"  Altering {table_name:30} ... ", end='', flush=True)
                    conn.execute(text(
                        f"ALTER TABLE {table_name} "
                        f"ALTER COLUMN tenant_id DROP NOT NULL"
                    ))
                    print("✓ Done")

                except Exception as e:
                    print(f"✗ Error on {table_name}: {e}")
                    raise

            print("\n" + "="*70)
            print("Migration completed successfully!")
            print("="*70)
            print("\nAll tenant_id columns are now nullable.")
            print("Platform-level templates can now be created with tenant_id=NULL.\n")

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running and accessible")
        print("2. Check database credentials")
        print("3. Verify you have ALTER TABLE permissions")
        print("4. Check if the tables exist in the database\n")
        sys.exit(1)


def main():
    """Main entry point"""
    db_url = get_database_url()

    if not db_url:
        print("\n✗ No database URL found!")
        print("\nProvide database URL via:")
        print("1. Argument: python apply_tenant_nullable_migration.py postgresql://...")
        print("2. Environment: export SQLALCHEMY_DATABASE_URL=postgresql://...")
        print("3. .env file: SQLALCHEMY_DATABASE_URL=postgresql://...\n")
        sys.exit(1)

    if 'postgresql' not in db_url and 'postgres' not in db_url:
        print("\n✗ This migration is for PostgreSQL databases only!")
        print(f"Detected URL: {db_url}\n")
        sys.exit(1)

    # Confirm before proceeding
    print("\nThis will modify the database schema to make tenant_id nullable.")
    response = input("Do you want to proceed? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled.")
        sys.exit(0)

    apply_migration(db_url)


if __name__ == "__main__":
    main()
