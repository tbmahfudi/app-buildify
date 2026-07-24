"""DMS Module — standalone FastAPI microservice.

Runs independently on port 9003, behind the platform nginx which forwards
`/api/v1/dms/...` (and the Authorization header) here. On startup it ensures the
storage bucket exists and registers its manifest with the core platform so RBAC
permissions and menu items get seeded.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .core.storage import storage
from .routers import audit, documents, folders

MANIFEST_PATH = Path(settings.MANIFEST_PATH)


async def register_with_core_platform(max_retries: int = 5) -> bool:
    if not MANIFEST_PATH.exists():
        print(f"[dms] manifest not found at {MANIFEST_PATH}; skipping registration")
        return False
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    payload = {
        "manifest": manifest,
        "backend_service_url": f"http://dms-module:{settings.MODULE_PORT}",
        "health_check_url": f"http://dms-module:{settings.MODULE_PORT}/health",
    }
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{settings.CORE_PLATFORM_URL}/api/v1/module-registry/register",
                    json=payload,
                )
            if resp.status_code == 200:
                print("[dms] registered with core platform")
                return True
            print(f"[dms] registration failed ({attempt+1}/{max_retries}): "
                  f"{resp.status_code} {resp.text[:200]}")
        except Exception as e:  # noqa: BLE001 - best-effort registration
            print(f"[dms] registration error ({attempt+1}/{max_retries}): {e}")
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** (attempt + 1))
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[dms] starting {settings.MODULE_NAME} v{settings.MODULE_VERSION} on :{settings.MODULE_PORT}")
    try:
        await storage.ensure_bucket()
    except Exception as e:  # noqa: BLE001
        print(f"[dms] WARNING: could not ensure storage bucket: {e}")
    # Fire-and-forget registration so a slow/absent core doesn't block startup.
    asyncio.create_task(register_with_core_platform())
    yield
    print("[dms] shutting down")


app = FastAPI(
    title=f"{settings.MODULE_DISPLAY_NAME} API",
    version=settings.MODULE_VERSION,
    description="Document Management System microservice",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "module": settings.MODULE_NAME,
        "version": settings.MODULE_VERSION,
        "service": "dms-module",
    }


@app.get("/manifest")
async def get_manifest():
    with open(MANIFEST_PATH) as f:
        return json.load(f)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc), "module": settings.MODULE_NAME},
    )


app.include_router(
    documents.router,
    prefix=f"{settings.API_PREFIX}/documents",
    tags=["documents"],
)

app.include_router(
    folders.router,
    prefix=f"{settings.API_PREFIX}/folders",
    tags=["folders"],
)

app.include_router(
    audit.router,
    prefix=f"{settings.API_PREFIX}/audit",
    tags=["audit"],
)
