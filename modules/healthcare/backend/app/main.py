"""
Healthcare Module — Independent Microservice entry point.

Packages the healthcare backend (modules/healthcare/backend) as a standalone
FastAPI service on :9002, mirroring the financial-module microservice.

Architecture notes
-------------------
The healthcare routers and SDK were written to run *inside* the core platform:
they import the platform package (``app.core.*``, ``app.models.base``) via the
shared module SDK (``modules.sdk.*``).  To run standalone this image is built
FROM the core backend image so the entire ``app`` package and its dependencies
are present, and the healthcare source is mounted at ``modules/healthcare`` with
the shared SDK at ``modules/sdk`` (PYTHONPATH=/app).

Patient JWTs are HS256-signed with ``SECRET_KEY`` and validated by the platform
``decode_token`` (also ``SECRET_KEY``) — so this service MUST share the same
``SECRET_KEY`` as the core backend for patient tokens to validate.  The Phase-2
tenant enforcement (PatientTokenData.require_tenant) therefore executes live
here on every ``/api/v1/patients/me/*`` request.
"""

from __future__ import annotations

import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("healthcare-module")

MODULE_NAME = os.getenv("MODULE_NAME", "healthcare")
MODULE_VERSION = os.getenv("MODULE_VERSION", "1.0.0")
MODULE_PORT = int(os.getenv("MODULE_PORT", "9002"))

# CORS — parse JSON list or comma string, with a permissive dev default.
import json as _json

def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    if not raw:
        return ["http://localhost:8080", "http://localhost:3000"]
    try:
        parsed = _json.loads(raw)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass
    return [o.strip() for o in raw.split(",") if o.strip()]


app = FastAPI(
    title="Healthcare Module API",
    version=MODULE_VERSION,
    description="Healthcare management microservice (clinics, patient auth, patient data)",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "service": "healthcare-module",
    }


@app.get("/api/healthz")
async def api_healthz():
    return {"status": "ok", "service": "healthcare-module"}


# ---------------------------------------------------------------------------
# Router registration
#
# Every healthcare router declares its OWN absolute path (e.g.
# "/api/v1/clinics/{slug}", prefix="/api/v1/patients/me", ...), so routers are
# included WITHOUT an extra prefix. The list below mirrors module.py and adds
# the Sprint-4+ routers (billing, lab, pharmacy, reviews, encounter_history)
# that module.py had not yet wired.
# ---------------------------------------------------------------------------
def _register_routers() -> None:
    from modules.healthcare.routes_branches import router as branches_router
    from modules.healthcare.routes_staff import router as staff_router
    from modules.healthcare.routes_providers import router as providers_router
    from modules.healthcare.routes_audit import router as audit_router
    from modules.healthcare.routes_patients import router as patients_router
    from modules.healthcare.routes_departments import router as departments_router
    from modules.healthcare.routes_visits import router as visits_router
    from modules.healthcare.routes_coding import router as coding_router
    from modules.healthcare.routes_hr import router as hr_router
    from modules.healthcare.routes_reports import router as reports_router
    from modules.healthcare.routes_clinic_signup import router as clinic_signup_router
    from modules.healthcare.routes_patient_auth import router as patient_auth_router
    from modules.healthcare.routes_household import router as household_router
    from modules.healthcare.routes_public import router as public_router
    from modules.healthcare.routes_i18n import router as i18n_router
    from modules.healthcare.routes_i18n_admin import router as i18n_admin_router
    from modules.healthcare.routes_schedules import router as schedules_router
    from modules.healthcare.routes_appointments import router as appointments_router
    from modules.healthcare.routes_waitlist import router as waitlist_router
    from modules.healthcare.routes_patient_appointments import router as patient_appointments_router
    from modules.healthcare.routes_patient_profile import router as patient_profile_router
    from modules.healthcare.routes_encounter_history import router as encounter_history_router
    from modules.healthcare.routes_reviews import router as reviews_router
    from modules.healthcare.routes_billing import router as billing_router
    from modules.healthcare.routes_lab import router as lab_router
    from modules.healthcare.routes_pharmacy import router as pharmacy_router

    routers = [
        ("branches", branches_router),
        ("staff", staff_router),
        ("providers", providers_router),
        ("audit", audit_router),
        ("patients", patients_router),
        ("departments", departments_router),
        ("visits", visits_router),
        ("coding", coding_router),
        ("hr", hr_router),
        ("reports", reports_router),
        ("clinic_signup", clinic_signup_router),
        ("patient_auth", patient_auth_router),
        ("household", household_router),
        ("public", public_router),
        ("i18n", i18n_router),
        ("i18n_admin", i18n_admin_router),
        ("schedules", schedules_router),
        ("appointments", appointments_router),
        ("waitlist", waitlist_router),
        ("patient_appointments", patient_appointments_router),
        ("patient_profile", patient_profile_router),
        ("encounter_history", encounter_history_router),
        ("reviews", reviews_router),
        ("billing", billing_router),
        ("lab", lab_router),
        ("pharmacy", pharmacy_router),
    ]
    for name, r in routers:
        app.include_router(r)
        logger.info("Registered healthcare router: %s (%d routes)", name, len(r.routes))


# ---------------------------------------------------------------------------
# Table creation — create ONLY the hc_* tables, never the platform tables.
#
# Healthcare models register on the shared platform Base.metadata. We therefore
# select just the tables whose names start with "hc_" and create_all() those
# with checkfirst=True so existing tables/data are left untouched.
# ---------------------------------------------------------------------------
def _create_healthcare_tables() -> None:
    try:
        from app.core.db import engine
        from modules.sdk.db import Base
        import modules.healthcare.models  # noqa: F401 — registers hc_* tables on Base

        hc_tables = [
            t for name, t in Base.metadata.tables.items() if name.startswith("hc_")
        ]
        if hc_tables:
            Base.metadata.create_all(bind=engine, tables=hc_tables, checkfirst=True)
            logger.info(
                "Healthcare tables ensured (%d hc_* tables, existing left intact)",
                len(hc_tables),
            )
    except Exception as exc:  # don't crash the service if DDL fails — log loudly
        logger.error("Healthcare table creation failed: %s", exc, exc_info=True)


@app.on_event("startup")
async def _on_startup() -> None:
    logger.info("Starting %s v%s on port %s", MODULE_NAME, MODULE_VERSION, MODULE_PORT)
    _create_healthcare_tables()
    _register_routers()
    _prime_shared_tenant()
    logger.info("%s started — %d total routes", MODULE_NAME, len(app.routes))


def _prime_shared_tenant() -> None:
    """Resolve + cache the shared SAAS hc tenant id (ADR-HC-010) so every hc query
    scopes to the migrated data tenant rather than the staff user's platform tenant."""
    try:
        from app.core.db import SessionLocal
        from modules.healthcare.sdk.hc_tenant import resolve_shared_tenant_id
        db = SessionLocal()
        try:
            tid = resolve_shared_tenant_id(db)
            logger.info("hc shared tenant primed: %s", tid)
        finally:
            db.close()
    except Exception as exc:  # pragma: no cover — defensive; helper falls back lazily
        logger.warning("Could not prime hc shared tenant id at startup: %s", exc)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "modules.healthcare.app.main:app",
        host="0.0.0.0",
        port=MODULE_PORT,
        reload=os.getenv("DEBUG", "true").lower() == "true",
        log_level="info",
    )
