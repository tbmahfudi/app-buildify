#!/usr/bin/env python3
"""
Migration helper script to run Alembic migrations.
This script helps fix the "relation 'tenants' does not exist" error.

Usage:
    python run_migrations.py [database_url]

Examples:
    python run_migrations.py
    python run_migrations.py postgresql://user:pass@localhost:5432/dbname
    python run_migrations.py sqlite:///./app.db

Environment Variables:
    SQLALCHEMY_DATABASE_URL - Database connection string
    DATABASE_URL - Alternative database connection string
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

try:
    from alembic.config import Config
    from alembic import command
    from sqlalchemy import create_engine, text
    from app.core.config import get_settings
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install required packages: pip install alembic sqlalchemy psycopg2-binary python-dotenv pydantic pydantic-settings")
    sys.exit(1)


def get_database_url():
    """Get database URL from various sources"""
    # 1. Command line argument
    if len(sys.argv) > 1:
        return sys.argv[1]

    # 2. Environment variable
    db_url = os.getenv('SQLALCHEMY_DATABASE_URL')
    if db_url:
        return db_url

    # 3. Alternative environment variable
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        return db_url

    # 4. From settings (which reads from .env)
    try:
        settings = get_settings()
        return settings.SQLALCHEMY_DATABASE_URL
    except Exception as e:
        print(f"Warning: Could not load settings: {e}")

    return None


def detect_db_type(url: str) -> str:
    """Detect database type from URL"""
    if url.startswith('sqlite'):
        return 'sqlite'
    elif url.startswith('mysql'):
        return 'mysql'
    elif 'postgresql' in url or url.startswith('postgres://'):
        return 'postgresql'
    else:
        return 'unknown'


def check_database_connection(db_url: str) -> bool:
    """Test database connection"""
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def check_tenants_table_exists(db_url: str) -> bool:
    """Check if tenants table already exists"""
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            if 'postgresql' in db_url:
                result = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tenants')"))
                return result.scalar()
            elif 'mysql' in db_url:
                result = conn.execute(text("SHOW TABLES LIKE 'tenants'"))
                return result.fetchone() is not None
            else:  # SQLite
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='tenants'"))
                return result.fetchone() is not None
    except Exception as e:
        print(f"Warning: Could not check for tenants table: {e}")
        return False


def run_migrations(db_url: str):
    """Run Alembic migrations"""
    db_type = detect_db_type(db_url)

    print(f"\n{'='*60}")
    print(f"Database Migration Tool")
    print(f"{'='*60}")
    print(f"Database Type: {db_type}")
    print(f"Database URL: {db_url[:30]}..." if len(db_url) > 30 else f"Database URL: {db_url}")
    print(f"{'='*60}\n")

    # Check connection
    if not check_database_connection(db_url):
        print("\nPlease check your database connection and try again.")
        sys.exit(1)

    # Check if tenants table exists
    if check_tenants_table_exists(db_url):
        print("ℹ Tenants table already exists.")
        response = input("Do you want to run migrations anyway? (y/n): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            sys.exit(0)

    # Set environment variable for Alembic
    os.environ['SQLALCHEMY_DATABASE_URL'] = db_url

    # Configure Alembic
    alembic_ini = backend_dir / "alembic.ini"
    if not alembic_ini.exists():
        print(f"Error: alembic.ini not found at {alembic_ini}")
        sys.exit(1)

    config = Config(str(alembic_ini))

    try:
        # Check current migration version
        print("\n1. Checking current migration status...")
        try:
            command.current(config)
        except Exception as e:
            print(f"   Note: {e}")

        # Run migrations
        print("\n2. Running migrations to latest version...")
        command.upgrade(config, "heads")

        print("\n3. Verifying migration status...")
        command.current(config)

        # Verify tenants table
        if check_tenants_table_exists(db_url):
            print("\n✓ SUCCESS! Tenants table has been created.")
        else:
            print("\n⚠ Warning: Migration completed but tenants table may not exist.")

        print(f"\n{'='*60}")
        print("Migration completed successfully!")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        print("\nTroubleshooting steps:")
        print("1. Ensure your database is running and accessible")
        print("2. Check database credentials in your .env file or environment variables")
        print("3. Verify that you have necessary permissions to create tables")
        print("4. For PostgreSQL, ensure the database exists")
        print("\nFor more help, see the README.md file")
        sys.exit(1)


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("Alembic Migration Helper")
    print("="*60)

    # Get database URL
    db_url = get_database_url()

    if not db_url:
        print("\nNo database URL found!")
        print("\nPlease provide a database URL in one of these ways:")
        print("1. Pass as argument: python run_migrations.py postgresql://user:pass@localhost:5432/dbname")
        print("2. Set environment variable: export SQLALCHEMY_DATABASE_URL=...")
        print("3. Create .env file in backend directory with: SQLALCHEMY_DATABASE_URL=...")
        print("\nExample database URLs:")
        print("  PostgreSQL: postgresql://user:password@localhost:5432/appdb")
        print("  MySQL: mysql+pymysql://user:password@localhost:3306/appdb")
        print("  SQLite: sqlite:///./app.db")
        sys.exit(1)

    # Run migrations
    run_migrations(db_url)


if __name__ == "__main__":
    main()
