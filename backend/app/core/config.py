from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings with type-safe configuration management.
    All settings can be overridden via environment variables.
    """
    # Application
    APP_NAME: str = "NoCode App"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MIN: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./app.db"

    # CORS
    ALLOWED_ORIGINS: str = "*"

    # Redis (for token revocation and caching)
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"

    # Sentry (Error Tracking)
    SENTRY_DSN: Optional[str] = None

    # Monitoring
    ENABLE_METRICS: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS string into a list"""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def redis_url_computed(self) -> Optional[str]:
        """Compute Redis URL from components if not explicitly set"""
        if self.REDIS_URL:
            return self.REDIS_URL
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache()
def get_settings() -> Settings:
    """
    Create and cache settings instance.
    Using lru_cache ensures we only load settings once.
    """
    return Settings()


# For backward compatibility - can be removed after updating all imports
settings = get_settings()
APP_NAME = settings.APP_NAME
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MIN = settings.ACCESS_TOKEN_EXPIRE_MIN
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
SQLALCHEMY_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URL
ALLOWED_ORIGINS = settings.allowed_origins_list