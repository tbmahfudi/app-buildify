"""Configuration for the Document Management (DMS) standalone module."""

import os
from typing import List


class Settings:
    # Module info
    MODULE_NAME: str = "dms"
    MODULE_DISPLAY_NAME: str = "Document Management"
    MODULE_VERSION: str = "1.0.0"
    MODULE_PORT: int = int(os.getenv("MODULE_PORT", "9003"))
    API_PREFIX: str = "/api/v1/dms"

    # Path to manifest.json (read for /manifest + self-registration). In dev it is
    # bind-mounted from modules/dms/manifest.json to a path OUTSIDE /app so the
    # nested mount can't create a stray placeholder under backend/.
    MANIFEST_PATH: str = os.getenv("MANIFEST_PATH", "/app/manifest.json")

    # Database — shared platform DB (same instance the core backend uses)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://appuser:apppass@postgres:5432/appdb",
    )

    # Auth — MUST equal the core backend SECRET_KEY so platform JWTs validate.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # Core platform integration (registration + audit/notification callbacks)
    CORE_PLATFORM_URL: str = os.getenv("CORE_PLATFORM_URL", "http://core-platform:8000")

    # Shared secret guarding internal batch endpoints (e.g. the expiry-reminder
    # scan the platform scheduler invokes as a webhook). Not user-facing.
    INTERNAL_SECRET: str = os.getenv("DMS_INTERNAL_SECRET", "dev-dms-internal-secret")

    # Blob storage (S3 / MinIO)
    STORAGE_ENDPOINT_URL: str = os.getenv("STORAGE_ENDPOINT_URL", "http://minio:9000")
    STORAGE_ACCESS_KEY: str = os.getenv("STORAGE_ACCESS_KEY", "minioadmin")
    STORAGE_SECRET_KEY: str = os.getenv("STORAGE_SECRET_KEY", "minioadmin")
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "dms-documents")
    STORAGE_REGION: str = os.getenv("STORAGE_REGION", "us-east-1")
    # Public base used when signing download URLs handed to browsers. In dev the
    # browser reaches MinIO at localhost:9100 (host-published), not the in-cluster
    # http://minio:9000 the module uses for server-side calls.
    STORAGE_PUBLIC_ENDPOINT_URL: str = os.getenv(
        "STORAGE_PUBLIC_ENDPOINT_URL", "http://localhost:9100"
    )
    PRESIGN_EXPIRY_SECONDS: int = int(os.getenv("PRESIGN_EXPIRY_SECONDS", "900"))

    # Upload limits (E1: admin-configurable per workspace later; global default here)
    MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(100 * 1024 * 1024)))

    CORS_ORIGINS: List[str] = ["http://localhost:8080", "http://localhost:3000"]
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")


settings = Settings()
