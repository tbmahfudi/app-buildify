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
    if url.startswith('sqlite'):
        return 'sqlite'
    elif url.startswith('mysql'):
        return 'mysql'
    elif url.startswith('postgresql'):
        return 'postgresql'
    else:
        return 'unknown'


def get_db_specific_options(db_type: str) -> dict:
    """Get database-specific options for migrations"""
    options = {
        'compare_type': True,
        'compare_server_default': True,
    }
    
    if db_type == 'sqlite':
        options.update({
            'render_as_batch': True,
            'compare_type': False,
        })
    elif db_type == 'mysql':
        options.update({
            'render_as_batch': False,
        })
    elif db_type == 'postgresql':
        options.update({
            'render_as_batch': False,
        })
    
    return options


def filter_migrations_by_db(db_type: str):
    """Filter migrations to only include ones for the current database type"""
    script = ScriptDirectory.from_config(config)
    
    # Map database types to migration prefixes
    db_prefixes = {
        'sqlite': 'sqlite',
        'mysql': 'mysql',
        'postgresql': 'pg',
    }
    
    prefix = db_prefixes.get(db_type, '')
    
    if prefix:
        # Get all revisions
        all_revisions = list(script.walk_revisions())
        
        # Filter to only matching prefix
        matching_revisions = [
            rev for rev in all_revisions 
            if rev.revision and rev.revision.startswith(prefix)
        ]
        
        if matching_revisions:
            print(f"[INFO] Using {db_type} migrations (prefix: {prefix}_)")
            return matching_revisions
        else:
            print(f"[WARNING] No migrations found for {db_type}. Using all migrations.")
            return all_revisions
    
    return list(script.walk_revisions())


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    db_type = detect_db_type(url)
    options = get_db_specific_options(db_type)
    
    print(f"[INFO] Running offline migrations for: {db_type}")
    
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

    url = get_database_url()
    db_type = detect_db_type(url)
    options = get_db_specific_options(db_type)

    print(f"[INFO] Running online migrations for: {db_type}")

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = url

    connect_args = {}
    if db_type == 'sqlite':
        connect_args = {
            'check_same_thread': False,
        }
    elif db_type == 'mysql':
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
