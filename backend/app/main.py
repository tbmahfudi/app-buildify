from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import APP_NAME, ALLOWED_ORIGINS
from app.routers import org, auth, metadata, data, audit, settings

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

app = FastAPI(title=APP_NAME)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=ALLOWED_ORIGINS, 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Include routers
app.include_router(auth.router)
app.include_router(org.router)
app.include_router(metadata.router)
app.include_router(data.router)
app.include_router(audit.router)
app.include_router(settings.router)

@app.get("/api/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/api/system/info")
async def system_info():
    return {
        "app": APP_NAME,
        "version": "0.2.0",
        "features": [
            "auth",
            "org",
            "metadata",
            "data",
            "audit",
            "settings"
        ]
    }