"""
Financial Module - Independent Microservice

This is the main FastAPI application for the Financial module.
It can run independently and communicate with the core platform via API calls and events.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .core.database import engine, get_db
from .core.event_handler import FinancialEventHandler
from .routers import accounts, invoices

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.
    """
    # Startup
    print(f"Starting {settings.MODULE_NAME} v{settings.MODULE_VERSION}")

    # Initialize event handlers
    event_handler = FinancialEventHandler(settings.EVENT_BUS_CONNECTION_STRING)
    await event_handler.start()
    app.state.event_handler = event_handler

    # Register with core platform
    # await register_with_platform()

    print(f"{settings.MODULE_NAME} started successfully on port {settings.MODULE_PORT}")

    yield

    # Shutdown
    print(f"Shutting down {settings.MODULE_NAME}")
    if hasattr(app.state, 'event_handler'):
        await app.state.event_handler.stop()


# Create FastAPI application
app = FastAPI(
    title=f"{settings.MODULE_DISPLAY_NAME} API",
    version=settings.MODULE_VERSION,
    description="Financial management microservice",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and service discovery."""
    return {
        "status": "healthy",
        "module": settings.MODULE_NAME,
        "version": settings.MODULE_VERSION,
        "service": "financial-module"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with module information."""
    return {
        "module": settings.MODULE_NAME,
        "display_name": settings.MODULE_DISPLAY_NAME,
        "version": settings.MODULE_VERSION,
        "status": "running",
        "docs": "/docs"
    }


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "module": settings.MODULE_NAME
        }
    )


# Include routers
app.include_router(
    accounts.router,
    prefix=f"{settings.API_PREFIX}/accounts",
    tags=["accounts"]
)

app.include_router(
    invoices.router,
    prefix=f"{settings.API_PREFIX}/invoices",
    tags=["invoices"]
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.MODULE_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
