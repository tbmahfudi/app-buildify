"""
Configuration for Financial Module
"""

import os
from typing import List


class Settings:
    """Module configuration settings."""

    # Module Info
    MODULE_NAME: str = "financial"
    MODULE_DISPLAY_NAME: str = "Financial Management"
    MODULE_VERSION: str = "2.0.0"
    MODULE_PORT: int = int(os.getenv("MODULE_PORT", "9001"))

    # API Configuration
    API_PREFIX: str = "/api/v1/financial"

    # Database Configuration
    # Strategy: 'shared' or 'separate'
    DATABASE_STRATEGY: str = os.getenv("DATABASE_STRATEGY", "shared")

    # For shared strategy: use core platform database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/buildify"
    )

    # For separate strategy: use dedicated database
    MODULE_DATABASE_URL: str = os.getenv(
        "MODULE_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/financial_module"
    )

    # Schema prefix for shared database strategy
    SCHEMA_PREFIX: str = "financial_"

    # Core Platform Integration
    CORE_PLATFORM_URL: str = os.getenv(
        "CORE_PLATFORM_URL",
        "http://localhost:8000"
    )

    # Module API Key (for authenticating to core platform)
    MODULE_API_KEY: str = os.getenv(
        "MODULE_API_KEY",
        "financial-module-secret-key-change-in-production"
    )

    # Event Bus Configuration
    EVENT_BUS_CONNECTION_STRING: str = os.getenv(
        "EVENT_BUS_CONNECTION_STRING",
        DATABASE_URL  # Use same as database for PostgreSQL event bus
    )

    # JWT Configuration (from core platform)
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "your-secret-key-change-in-production"
    )
    JWT_ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000"
    ]

    # Environment
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    @property
    def effective_database_url(self) -> str:
        """Get the effective database URL based on strategy."""
        if self.DATABASE_STRATEGY == "separate":
            return self.MODULE_DATABASE_URL
        return self.DATABASE_URL


settings = Settings()
