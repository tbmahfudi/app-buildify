from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime

from app.core.config import get_settings
from app.core.logging_config import setup_logging, get_logger
from app.core.exceptions import register_exception_handlers
from app.core.rate_limiter import setup_rate_limiting
from app.core.redis_client import redis_client
from app.core.db import SessionLocal
from app.routers import org, auth, metadata, data, audit, settings, modules
from app.core.module_system.registry import ModuleRegistryService
from pathlib import Path

# Initialize settings and logging
settings_instance = get_settings()
setup_logging()
logger = get_logger(__name__)

# Global module registry instance
module_registry: ModuleRegistryService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.
    """
    global module_registry

    # Startup
    logger.info("Starting application", app_name=settings_instance.APP_NAME, environment=settings_instance.ENVIRONMENT)

    # Initialize Redis connection (optional, fails gracefully if unavailable)
    redis_client.connect()

    # Initialize module system
    try:
        logger.info("Initializing module system...")
        db = SessionLocal()
        modules_path = Path(__file__).parent / "modules"
        module_registry = ModuleRegistryService(db, modules_path)

        # Sync modules from filesystem
        module_registry.sync_modules()

        # Include routers from installed modules
        for router in module_registry.get_all_routers():
            app.include_router(router)
            logger.info(f"Included router from module")

        # Make module_registry available to routes
        from app.routers import modules as modules_router
        modules_router.module_registry = module_registry

        logger.info(f"Module system initialized: {module_registry.get_module_count()} modules loaded")
    except Exception as e:
        logger.error(f"Failed to initialize module system: {e}", exc_info=True)
        # Continue even if module system fails to initialize

    # Initialize Sentry if configured
    if settings_instance.SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            sentry_sdk.init(
                dsn=settings_instance.SENTRY_DSN,
                environment=settings_instance.ENVIRONMENT,
                traces_sample_rate=0.1,
                integrations=[
                    FastApiIntegration(),
                    SqlalchemyIntegration(),
                ],
            )
            logger.info("Sentry error tracking initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Sentry: {e}")

    yield

    # Shutdown
    logger.info("Shutting down application")
    redis_client.disconnect()


# Create FastAPI app with API versioning
app = FastAPI(
    title=settings_instance.APP_NAME,
    version="0.3.0",
    description="Multi-tenant NoCode Application API with enhanced security",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_instance.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Module access control middleware
@app.middleware("http")
async def module_access_middleware(request: Request, call_next):
    """
    Middleware to check if user has access to module endpoints.
    Validates that the module is enabled for the tenant.
    """
    # Only check module endpoints
    if request.url.path.startswith("/api/v1/") and module_registry:
        path_parts = request.url.path.split("/")

        # Check if this is a potential module endpoint
        # Format: /api/v1/{module_name}/...
        if len(path_parts) >= 4:
            potential_module = path_parts[3]

            # Skip core endpoints
            core_endpoints = ["auth", "org", "metadata", "data", "audit", "settings", "modules", "health", "healthz", "system"]
            if potential_module not in core_endpoints:
                # This might be a module endpoint
                # Check if module exists and is enabled
                try:
                    # Get user's tenant from JWT token
                    auth_header = request.headers.get("authorization")
                    if auth_header and auth_header.startswith("Bearer "):
                        # We would need to decode JWT to get tenant_id
                        # For now, we'll let the endpoint handle authorization
                        # This middleware is a placeholder for future enhancement
                        pass
                except Exception as e:
                    logger.warning(f"Module access check failed: {e}")

    response = await call_next(request)
    return response

# Setup rate limiting
limiter = setup_rate_limiting(app)

# Register exception handlers
register_exception_handlers(app)

# Include routers with API versioning
# v1 API endpoints
app.include_router(auth.router, prefix="/api/v1")
app.include_router(org.router, prefix="/api/v1")
app.include_router(metadata.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")
app.include_router(modules.router, prefix="/api/v1")

# Also maintain backward compatibility with old endpoints (deprecated)
app.include_router(auth.router, tags=["deprecated"])
app.include_router(org.router, tags=["deprecated"])
app.include_router(metadata.router, tags=["deprecated"])
app.include_router(data.router, tags=["deprecated"])
app.include_router(audit.router, tags=["deprecated"])
app.include_router(settings.router, tags=["deprecated"])


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": f"Welcome to {settings_instance.APP_NAME}",
        "version": "0.3.0",
        "api_version": "v1",
        "docs": "/api/docs",
        "health": "/api/health"
    }


@app.get("/api/health")
@limiter.limit("30/minute")
async def health_check(request: Request):
    """
    Comprehensive health check endpoint.
    Returns detailed status of all system components.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.3.0",
        "environment": settings_instance.ENVIRONMENT,
        "components": {}
    }

    # Check database
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Check Redis
    if redis_client.is_available:
        health_status["components"]["redis"] = {"status": "healthy"}
    else:
        health_status["components"]["redis"] = {
            "status": "unavailable",
            "note": "Token revocation disabled"
        }

    # Check rate limiting
    health_status["components"]["rate_limiting"] = {
        "status": "enabled" if settings_instance.RATE_LIMIT_ENABLED else "disabled"
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=health_status
    )


@app.get("/api/healthz")
async def healthz():
    """Simple health check endpoint (backward compatibility)"""
    return {"status": "ok"}


@app.get("/api/system/info")
async def system_info():
    """System information endpoint"""
    return {
        "app": settings_instance.APP_NAME,
        "version": "0.3.0",
        "api_version": "v1",
        "environment": settings_instance.ENVIRONMENT,
        "features": [
            "multi-tenant-isolation",
            "jwt-authentication",
            "token-revocation",
            "rate-limiting",
            "audit-logging",
            "rbac",
            "api-versioning",
            "structured-logging",
            "health-monitoring",
            "pluggable-modules"
        ],
        "loaded_modules": module_registry.get_module_count() if module_registry else 0
    }