from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import APP_NAME, ALLOWED_ORIGINS
from app.routers import org

app = FastAPI(title=APP_NAME)
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(org.router)

@app.get("/api/healthz")
async def healthz():
    return {"status": "ok"}
