"""
Builder Module - Independent Microservice

This is the main FastAPI application for the Builder module.
It provides UI building capabilities with GrapeJS integration.
"""

import os
import json
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx

from .config import settings
from .core.database import engine, get_db
from .routers import pages

async def register_with_core_platform(max_retries: int = 5):
    """
    Register this module with the core platform.

    Implements retry logic with exponential backoff in case core platform
    is not yet ready.

    Args:
        max_retries: Maximum number of registration attempts
    """
    manifest_path = Path(__file__).parent.parent.parent / "manifest.json"

    if not manifest_path.exists():
        print(f"ERROR: Manifest file not found at {manifest_path}")
        return False

    # Load manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    # Prepare registration payload
    registration_data = {
        "manifest": manifest,
        "backend_service_url": settings.CORE_PLATFORM_URL.replace('core-platform', 'builder-module').replace('8000', str(settings.MODULE_PORT)),
        "health_check_url": f"http://builder-module:{settings.MODULE_PORT}/health"
    }

    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{settings.CORE_PLATFORM_URL}/api/v1/modules/register",
                    json=registration_data
                )

                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ Successfully registered with core platform: {result.get('message')}")
                    return True
                else:
                    print(f"✗ Registration failed (attempt {attempt + 1}/{max_retries}): {response.status_code} - {response.text}")

        except httpx.ConnectError as e:
            print(f"✗ Cannot connect to core platform (attempt {attempt + 1}/{max_retries}): {e}")
        except Exception as e:
            print(f"✗ Registration error (attempt {attempt + 1}/{max_retries}): {e}")

        # Wait before retry with exponential backoff: 2s, 4s, 8s, 16s, 32s
        if attempt < max_retries - 1:
            wait_time = 2 ** (attempt + 1)
            print(f"  Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)

    print(f"✗ Failed to register with core platform after {max_retries} attempts")
    return False


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.
    """
    # Startup
    print(f"Starting {settings.MODULE_NAME} v{settings.MODULE_VERSION}")

    # Register with core platform
    print(f"Registering {settings.MODULE_NAME} with core platform...")
    await register_with_core_platform()

    print(f"{settings.MODULE_NAME} started successfully on port {settings.MODULE_PORT}")

    yield

    # Shutdown
    print(f"Shutting down {settings.MODULE_NAME}")


# Create FastAPI application
app = FastAPI(
    title=f"{settings.MODULE_DISPLAY_NAME} API",
    version=settings.MODULE_VERSION,
    description="UI Builder microservice with GrapeJS integration",
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
        "service": "builder-module"
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


# Manifest endpoint
@app.get("/manifest")
async def get_manifest():
    """
    Get module manifest.

    Returns the manifest.json file that describes the module's
    configuration, routes, permissions, and frontend components.
    """
    try:
        # Path to manifest.json (two levels up from app directory)
        manifest_path = Path(__file__).parent.parent.parent / "manifest.json"

        if not manifest_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Manifest file not found at {manifest_path}"
            )

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        return manifest
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid manifest JSON: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading manifest: {str(e)}"
        )


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
    pages.router,
    prefix=f"{settings.API_PREFIX}/pages",
    tags=["pages"]
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
