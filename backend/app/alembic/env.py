from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from alembic.script import ScriptDirectory
import os
import sys
from pathlib import Path

# Add your project directory to the path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# Add the backend directory to the Python path
# This ensures the 'app' module can be imported regardless of where alembic is run from
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Now proceed with the rest of your imports
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

from app.core.config import SQLALCHEMY_DATABASE_URL
from app.models.base import Base

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
target_metadata = Base.metadata

# Configure version_locations based on database type
def configure_version_location():
    """
    Dynamically set version_locations based on database type.
    This ensures only the correct migrations are loaded.
    """
    try:
        url = get_database_url()
        db_type = detect_db_type(url)

        # Get the base directory (where alembic.ini is located)
        config_dir = os.path.dirname(config.config_file_name) if config.config_file_name else '.'

        # Map database types to their migration folders
        db_folders = {
            'postgresql': os.path.join(config_dir, 'app/alembic/versions/postgresql'),
            'mysql': os.path.join(config_dir, 'app/alembic/versions/mysql'),
        }

        version_location = db_folders.get(db_type)
        if version_location:
            # Override version_locations to only use the correct folder
            config.set_main_option('version_locations', version_location)
            print(f"[INFO] Configured version_locations for {db_type}: {version_location}")
        else:
            raise ValueError(f"No migration folder configured for database type: {db_type}")
    except Exception as e:
        # If we can't determine database type yet, that's okay - it will be determined later
        pass

# Call configure_version_location early to set up the correct migration folder
configure_version_location()


def get_database_url():
    """Get database URL from environment variable or config"""
    # Try SQLALCHEMY_DATABASE_URL first (from docker-compose)
    db_url = os.getenv('SQLALCHEMY_DATABASE_URL')
    
    # If not found, try DATABASE_URL
    if not db_url:
        db_url = os.getenv('DATABASE_URL')
    
    # If still not found, try importing from config
    if not db_url:
        try:
            from app.core.config import SQLALCHEMY_DATABASE_URL
            db_url = SQLALCHEMY_DATABASE_URL
        except ImportError:
            pass
    
    # Last resort: check alembic config
    if not db_url:
        db_url = config.get_main_option("sqlalchemy.url")
    
    if not db_url:
        raise ValueError("Database URL not found in environment or config")
    
    return db_url


def detect_db_type(url: str) -> str:
    """Detect database type from URL"""
    if url.startswith('mysql'):
        return 'mysql'
    elif url.startswith('postgresql'):
        return 'postgresql'
    else:
        raise ValueError(f"Unsupported database type in URL: {url}. Only PostgreSQL and MySQL are supported.")


def get_db_specific_options(db_type: str) -> dict:
    """Get database-specific options for migrations"""
    options = {
        'compare_type': True,
        'compare_server_default': True,
        'render_as_batch': False,
    }

    return options


def log_migration_location(db_type: str):
    """
    Logs which migration folder is being used.
    The actual filtering is done by configure_version_location() which
    dynamically sets version_locations in the config.
    """
    db_locations = {
        'mysql': 'versions/mysql/',
        'postgresql': 'versions/postgresql/',
    }

    location = db_locations.get(db_type, 'unknown')
    print(f"[INFO] Using {db_type} migrations from {location}")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Configure version_locations before loading migrations
    configure_version_location()

    url = get_database_url()
    db_type = detect_db_type(url)
    options = get_db_specific_options(db_type)

    print(f"[INFO] Running offline migrations for: {db_type}")
    log_migration_location(db_type)  # Log which migrations are being used
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **options
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Configure version_locations before loading migrations
    configure_version_location()

    url = get_database_url()
    db_type = detect_db_type(url)
    options = get_db_specific_options(db_type)

    print(f"[INFO] Running online migrations for: {db_type}")
    log_migration_location(db_type)  # Log which migrations are being used

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = url

    connect_args = {}
    if db_type == 'mysql':
        connect_args = {
            'charset': 'utf8mb4',
        }

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            **options
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
