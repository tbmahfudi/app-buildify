"""
Template Management API Router

API endpoints for template versioning, packaging, and distribution.
"""

from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import io

from app.core.dependencies import get_db, get_current_user
from app.services.template_version_service import TemplateVersionService
from app.services.template_package_service import TemplatePackageService


router = APIRouter(prefix="/api/v1/templates", tags=["Template Management"])


# ==================== Version Endpoints ====================

@router.post("/versions")
async def create_version(
    template_type: str = Query(..., description="Type of template: entity, workflow, automation, lookup"),
    template_id: UUID = Query(..., description="ID of the template"),
    change_summary: str = Query(..., description="Summary of changes"),
    change_type: str = Query("minor", description="Type of change: major, minor, patch, hotfix"),
    changelog: Optional[str] = Query(None, description="Detailed changelog"),
    version_name: Optional[str] = Query(None, description="Version name (e.g., v1.0)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new version snapshot of a template."""
    service = TemplateVersionService(db, current_user)
    return await service.create_version(
        template_type, template_id, change_summary,
        change_type, changelog, version_name
    )


@router.get("/versions")
async def list_versions(
    template_type: str = Query(...),
    template_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all versions of a template."""
    service = TemplateVersionService(db, current_user)
    return await service.list_versions(template_type, template_id)


@router.get("/versions/{version_id}")
async def get_version(
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific version by ID."""
    service = TemplateVersionService(db, current_user)
    return await service.get_version(version_id)


@router.post("/versions/rollback")
async def rollback_version(
    template_type: str = Query(...),
    template_id: UUID = Query(...),
    version_number: int = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Rollback a template to a previous version."""
    service = TemplateVersionService(db, current_user)
    return await service.rollback_to_version(template_type, template_id, version_number)


@router.get("/versions/compare")
async def compare_versions(
    template_type: str = Query(...),
    template_id: UUID = Query(...),
    from_version: int = Query(...),
    to_version: int = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Compare two versions of a template."""
    service = TemplateVersionService(db, current_user)
    return await service.compare_versions(template_type, template_id, from_version, to_version)


# ==================== Export Endpoints ====================

@router.get("/export/entity/{entity_id}")
async def export_entity(
    entity_id: UUID,
    include_fields: bool = Query(True),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Export an entity template as JSON."""
    service = TemplatePackageService(db, current_user)
    return await service.export_entity_template(entity_id, include_fields)


@router.post("/packages")
async def create_package(
    name: str = Query(...),
    description: str = Query(...),
    template_ids: str = Query(..., description="JSON array of template references"),
    category_code: Optional[str] = Query(None),
    version: str = Query("1.0.0"),
    author: Optional[str] = Query(None),
    license: str = Query("MIT"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a template package from multiple templates."""
    import json
    template_refs = json.loads(template_ids)

    service = TemplatePackageService(db, current_user)
    return await service.create_package(
        name, description, template_refs,
        category_code, version, author, license
    )


@router.get("/packages")
async def list_packages(
    category_id: Optional[UUID] = Query(None),
    is_verified: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List available template packages."""
    service = TemplatePackageService(db, current_user)
    return await service.list_packages(category_id, is_verified)


@router.get("/packages/{package_id}/download")
async def download_package(
    package_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Download a template package as ZIP file."""
    service = TemplatePackageService(db, current_user)
    zip_data = await service.export_package_as_zip(package_id)

    return StreamingResponse(
        io.BytesIO(zip_data),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=template-package-{package_id}.zip"}
    )


# ==================== Import Endpoints ====================

@router.post("/import/entity")
async def import_entity(
    template_data: dict,
    target_tenant_id: Optional[UUID] = Query(None),
    make_platform_level: bool = Query(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Import an entity template from JSON."""
    service = TemplatePackageService(db, current_user)
    return await service.import_entity_template(template_data, target_tenant_id, make_platform_level)


@router.post("/import/package")
async def import_package(
    package_data: dict,
    target_tenant_id: Optional[UUID] = Query(None),
    make_platform_level: bool = Query(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Import a complete template package."""
    service = TemplatePackageService(db, current_user)
    return await service.import_package(package_data, target_tenant_id, make_platform_level)


@router.post("/import/zip")
async def import_from_zip(
    file: UploadFile = File(...),
    target_tenant_id: Optional[UUID] = Query(None),
    make_platform_level: bool = Query(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Import templates from a ZIP file."""
    service = TemplatePackageService(db, current_user)
    return await service.import_from_zip(file, target_tenant_id, make_platform_level)
