import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import get_logger, setup_logging
from app.core.module_scope_middleware import ModuleScopeMiddleware
from app.core.module_system.registry import ModuleRegistryService
from app.core.rate_limiter import setup_rate_limiting
from app.core.security_middleware import SecurityMiddleware
from app.core.startup import ensure_default_security_policy
from app.core.tenant_listener import TenantScopeListener
from app.routers import admin_modules as admin_modules_router
from app.routers import (
    audit,
    auth,
    automations,
    builder_pages,
    dashboards,
    data,
    data_model,
    dynamic_data,
    lookups,
    menu,
    metadata,
    module_extensions,
    modules,
    modules_lifecycle,
    nocode_modules,
    org,
)
from app.routers import mfa as mfa_router
from app.routers import otp as otp_router
from app.routers import public as public_router
from app.routers import (
    rbac,
    reports,
    scheduler,
    settings,
    workflows,
)
from app.routers.admin import security as admin_security

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

    import os as _os

    # Skip slow startup tasks in test environment
    if _os.environ.get("TESTING"):
        logger.info("TESTING mode: skipping startup tasks")
        yield
        return

    # Startup
    logger.info("Starting application", app_name=settings_instance.APP_NAME, environment=settings_instance.ENVIRONMENT)

    # Run database migrations on startup (skipped when TESTING=1)
    import os as _os

    if not _os.environ.get("TESTING"):
        try:
            from alembic import command as alembic_command
            from alembic.config import Config as AlembicConfig

            alembic_cfg = AlembicConfig(_os.path.join(_os.path.dirname(__file__), "..", "alembic.ini"))
            alembic_cfg.set_main_option("script_location", _os.path.join(_os.path.dirname(__file__), "alembic"))
            alembic_command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations applied successfully")
        except Exception as e:
            logger.warning(f"Failed to run migrations on startup: {e}", exc_info=True)

    # Initialize database session for startup tasks
    db = SessionLocal()

    try:
        # Ensure default security policy exists
        logger.info("Checking default security policy...")
        ensure_default_security_policy(db)
        logger.info("Security policy check complete")
    except Exception as e:
        logger.warning(f"Failed to ensure default security policy: {e}", exc_info=True)
        # Continue even if this fails

    # Initialize module system
    try:
        logger.info("Initializing module system...")
        modules_path = Path(__file__).parent.parent / "modules"
        module_registry = ModuleRegistryService(db, modules_path)

        # Sync modules from filesystem (Python-loadable modules)
        module_registry.sync_modules()

        # Refresh DB manifests from on-disk manifest.json for ALL modules whose
        # files are mounted (e.g. /modules), so manifest edits propagate on
        # restart without a version bump. No-op if the mount is absent.
        module_registry.sync_manifests_from_disk()

        # Include routers from installed modules
        for router in module_registry.get_all_routers():
            app.include_router(router)
            logger.info("Included router from module")

        # Make module_registry available to routes
        from app.routers import modules as modules_router

        modules_router.module_registry = module_registry
        admin_modules_router.router.module_registry = module_registry  # type: ignore
        import app.routers.admin_modules as _am

        _am._module_registry = module_registry

        logger.info(f"Module system initialized: {module_registry.get_module_count()} modules loaded")
    except Exception as e:
        logger.error(f"Failed to initialize module system: {e}", exc_info=True)
        # Continue even if module system fails to initialize
    finally:
        db.close()

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

    # Optional in-process notification worker (per ADR-002)
    # Default OFF; small/dev deployments enable via NOTIFICATION_WORKER_INPROCESS=true
    notification_worker = None
    notification_worker_thread = None
    if os.environ.get("NOTIFICATION_WORKER_INPROCESS", "false").strip().lower() in ("1", "true", "yes", "on"):
        try:
            import threading

            from app.workers.notification_worker import NotificationWorker

            notification_worker = NotificationWorker()
            notification_worker_thread = threading.Thread(
                target=notification_worker.run,
                kwargs={"setup_signals": False},
                daemon=True,
                name="notification-worker",
            )
            notification_worker_thread.start()
            logger.info("notification-worker started in-process (NOTIFICATION_WORKER_INPROCESS=true)")
        except Exception as e:
            logger.error(f"Failed to start in-process notification worker: {e}", exc_info=True)
            notification_worker = None
            notification_worker_thread = None

    # Install ORM tenant-scope listener (T-22.005).
    # Installed LAST in startup — after tenant_scoped_session is live on all
    # tenant routes (T-22.009) — to prevent HTTP 500 storms on unscoped requests.
    # arch-22 section 3.2 and tasks-22 rollout order.
    #
    # GATED (default OFF): the fail-loud listener is only safe once *every*
    # tenant route sets scope via tenant_scoped_session. Only 3 services are
    # migrated so far (36 router violations remain), and pre-auth routes such as
    # /auth/login query tenant-scoped models (User) with no tenant context by
    # design — enabling globally now causes a 500 storm. Enable per-environment
    # with ENABLE_TENANT_SCOPE_LISTENER=true once the migration is complete.
    import os as _os

    if _os.environ.get("ENABLE_TENANT_SCOPE_LISTENER", "false").lower() in ("1", "true", "yes"):
        from app.core.db import engine as _db_engine

        TenantScopeListener()
        TenantScopeListener.install(_db_engine)
        logger.info("TenantScopeListener ENABLED (ENABLE_TENANT_SCOPE_LISTENER set)")
    else:
        logger.info("TenantScopeListener disabled (set ENABLE_TENANT_SCOPE_LISTENER=true to enable)")

    yield

    # Shutdown
    logger.info("Shutting down application")
    if notification_worker is not None:
        logger.info("Stopping in-process notification-worker")
        notification_worker.stop()
        if notification_worker_thread is not None:
            notification_worker_thread.join(timeout=10)
            if notification_worker_thread.is_alive():
                logger.warning("notification-worker did not stop within 10s; leaving as daemon")


# Create FastAPI app with API versioning
app = FastAPI(
    title=settings_instance.APP_NAME,
    version="0.3.0",
    description="Multi-tenant NoCode Application API with enhanced security",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


# Prometheus metrics endpoint (prometheus-client)
try:
    from prometheus_client import make_asgi_app as _make_metrics_app

    _metrics_app = _make_metrics_app()
    app.mount("/metrics", _metrics_app)
    logger.info("Prometheus /metrics endpoint mounted")
except Exception as _prom_err:
    logger.warning(f"Prometheus metrics not available: {_prom_err}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_instance.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware for session timeout and password expiration enforcement
app.middleware("http")(SecurityMiddleware(app))

# Module scope middleware — routes /api/v1/modules/{id}/... to per-tenant DB
app.add_middleware(ModuleScopeMiddleware)


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
            core_endpoints = [
                "auth",
                "org",
                "metadata",
                "data",
                "audit",
                "settings",
                "modules",
                "module-registry",
                "rbac",
                "reports",
                "dashboards",
                "scheduler",
                "menu",
                "health",
                "healthz",
                "system",
                "data-model",
                "workflows",
                "automations",
                "lookups",
                "dynamic-data",
            ]
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

# ============================================================================
# API Routers - All use /api/v1 prefix (defined in router files)
# ============================================================================

# Core API routers (prefix defined in each router file)
app.include_router(auth.router)
app.include_router(org.router)
app.include_router(metadata.router)
app.include_router(data.router)
app.include_router(audit.router)
app.include_router(settings.router)
app.include_router(modules.router)
app.include_router(modules._modules_v1_router)
app.include_router(modules_lifecycle.router)
app.include_router(modules_lifecycle.admin_router)
app.include_router(admin_modules_router.router, prefix="/api/v1/admin/modules", tags=["admin-modules"])
app.include_router(rbac.router)
app.include_router(reports.router)
app.include_router(dashboards.router)
app.include_router(scheduler.router)
app.include_router(menu.router)
app.include_router(builder_pages.router, prefix="/api/v1/builder", tags=["builder"])
app.include_router(admin_security.router)

# Phase 1 No-Code Platform routers (prefix defined in router files)
app.include_router(data_model.router)
app.include_router(workflows.router)
app.include_router(automations.router)
app.include_router(lookups.router)

# Phase 2 No-Code Platform routers (prefix defined in router files)
app.include_router(dynamic_data.router)

# Phase 4 No-Code Platform routers - Module System Foundation (prefix defined in router files)
app.include_router(nocode_modules.router)
app.include_router(module_extensions.router)

# Platform services
app.include_router(otp_router.router)
app.include_router(public_router.router)
app.include_router(mfa_router.router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": f"Welcome to {settings_instance.APP_NAME}",
        "version": "0.3.0",
        "api_version": "v1",
        "docs": "/api/docs",
        "health": "/api/health",
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
        "components": {},
    }

    # Check database
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"] = {"status": "unhealthy", "error": str(e)}

    # Check rate limiting
    health_status["components"]["rate_limiting"] = {
        "status": "enabled" if settings_instance.RATE_LIMIT_ENABLED else "disabled"
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=health_status,
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
            "pluggable-modules",
            "security-policy-system",
            "password-validation",
            "account-lockout",
            "session-management",
            "password-expiration",
            "login-attempt-tracking",
            "hierarchical-scheduler",
            "nocode-data-model-designer",
            "nocode-workflow-designer",
            "nocode-automation-system",
            "nocode-lookup-configuration",
            "nocode-runtime-data-layer",
        ],
        "loaded_modules": module_registry.get_module_count() if module_registry else 0,
    }
