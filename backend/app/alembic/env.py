from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add your project directory to the path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base
from app.models import *  # Import all your models

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
target_metadata = Base.metadata

def get_database_url():
    """Get database URL from environment variable or config"""
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        db_url = config.get_main_option("sqlalchemy.url")
    
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
        # SQLite specific options
        options.update({
            'render_as_batch': True,  # Required for ALTER operations in SQLite
            'compare_type': False,  # SQLite doesn't enforce types strictly
        })
    elif db_type == 'mysql':
        # MySQL specific options
        options.update({
            'render_as_batch': False,
        })
    elif db_type == 'postgresql':
        # PostgreSQL specific options
        options.update({
            'render_as_batch': False,
        })
    
    return options

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    db_type = detect_db_type(url)
    options = get_db_specific_options(db_type)
    
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
    
    # Get database URL
    url = get_database_url()
    db_type = detect_db_type(url)
    options = get_db_specific_options(db_type)
    
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = url
    
    # Database-specific engine configuration
    connect_args = {}
    if db_type == 'sqlite':
        # SQLite specific connection args
        connect_args = {
            'check_same_thread': False,
        }
    elif db_type == 'mysql':
        # MySQL specific connection args
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