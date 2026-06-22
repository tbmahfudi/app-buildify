from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter

from modules.sdk import BaseModule, PlatformBridge


class HealthcareModule(BaseModule):

    def __init__(self, module_path: Path, bridge: PlatformBridge = None):
        super().__init__(module_path)
        self.bridge = bridge or PlatformBridge()

    def get_router(self) -> APIRouter:
        combined = APIRouter()

        from modules.healthcare.routes_branches import router as branches_router
        from modules.healthcare.routes_staff import router as staff_router
        from modules.healthcare.routes_providers import router as providers_router
        from modules.healthcare.routes_audit import router as audit_router
        from modules.healthcare.routes_patients import router as patients_router
        from modules.healthcare.routes_clinic_signup import router as clinic_signup_router
        from modules.healthcare.routes_patient_auth import router as patient_auth_router
        from modules.healthcare.routes_public import router as public_router
        from modules.healthcare.routes_i18n import router as i18n_router
        from modules.healthcare.routes_i18n_admin import router as i18n_admin_router
        # Sprint 3 -- scheduling
        from modules.healthcare.routes_schedules import router as schedules_router
        from modules.healthcare.routes_appointments import router as appointments_router
        from modules.healthcare.routes_waitlist import router as waitlist_router

        for r in (
            branches_router,
            staff_router,
            providers_router,
            audit_router,
            patients_router,
            clinic_signup_router,
            patient_auth_router,
            public_router,
            i18n_router,
            i18n_admin_router,
            schedules_router,
            appointments_router,
            waitlist_router,
        ):
            combined.include_router(r)

        return combined

    def get_permissions(self) -> List[Dict[str, Any]]:
        return self.manifest.get("permissions", [])

    def get_models(self):
        from modules.healthcare import models  # noqa: F401
        return []


def create_module(module_path: Path, bridge: PlatformBridge = None) -> HealthcareModule:
    return HealthcareModule(module_path, bridge)
